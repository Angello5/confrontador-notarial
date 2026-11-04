"""F43: submenú, kardex sin minuta y confrontación vehicular (datos ficticios)."""

import hashlib
import re

import pytest
from django.urls import reverse
from django.utils import timezone

from tests.test_vehicular import BOLETA, BORRADOR, CHEQUE

pytestmark = pytest.mark.django_db

DNI = "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001.\n"


def _texto(contenido):
    from expedientes.models import TextoExtraido

    return TextoExtraido.objects.create(
        hash_archivo=hashlib.sha256(contenido.encode()).hexdigest(),
        version_extractor="extractor-ficticio-v1",
        texto=contenido,
        ultimo_uso_el=timezone.now(),
    )


def _documento(expediente, rol, nombre, contenido, usuario):
    from expedientes.models import Documento

    return Documento.objects.create(
        expediente=expediente,
        rol=rol,
        nombre_original=nombre,
        hash_archivo=hashlib.sha256(nombre.encode()).hexdigest(),
        tamano_bytes=10,
        estado=Documento.LISTO,
        texto_extraido=_texto(contenido),
        subido_por=usuario,
    )


@pytest.fixture
def vehicular(usuario_ficticio):
    from expedientes.models import Documento, Expediente

    expediente = Expediente.objects.create(
        codigo="VEH-FICTICIO-1",
        tipo=Expediente.VEHICULAR,
        creado_por=usuario_ficticio,
    )
    _documento(expediente, Documento.CLIENTE, "boleta.pdf", BOLETA, usuario_ficticio)
    _documento(expediente, Documento.CLIENTE, "cheque.jpg", CHEQUE, usuario_ficticio)
    # Sin una identidad en común el diagnóstico de correspondencia bloquea.
    _documento(expediente, Documento.CLIENTE, "dni.pdf", DNI, usuario_ficticio)
    borrador = _documento(
        expediente,
        Documento.BORRADOR,
        "acta-ficticia.docx",
        BORRADOR.replace("PLACA: QWE123", "PLACA: QWE128") + DNI,
        usuario_ficticio,
    )
    return expediente, borrador


def test_submenu_transferencia_vehicular(client, usuario_ficticio):
    client.force_login(usuario_ficticio)
    html = client.get(reverse("expediente_lista")).content.decode()
    assert f'href="{reverse("vehicular_lista")}"' in html
    assert "Transferencia vehicular" in html


def test_crear_y_listar_solo_vehiculares(client, usuario_ficticio):
    from expedientes.models import Expediente

    Expediente.objects.create(codigo="KARDEX-FICTICIO", creado_por=usuario_ficticio)
    client.force_login(usuario_ficticio)
    respuesta = client.post(reverse("vehicular_lista"), {"codigo": "VEH-FICTICIO-2"})
    creado = Expediente.objects.get(codigo="VEH-FICTICIO-2")
    assert creado.tipo == Expediente.VEHICULAR
    assert respuesta.url == reverse("expediente_detalle", args=[creado.pk])

    html = client.get(reverse("vehicular_lista")).content.decode()
    assert "VEH-FICTICIO-2" in html
    assert "KARDEX-FICTICIO" not in html
    assert (
        "VEH-FICTICIO-2" not in client.get(reverse("expediente_lista")).content.decode()
    )


def test_detalle_vehicular_sin_minuta(client, usuario_ficticio, vehicular):
    expediente, _ = vehicular
    client.force_login(usuario_ficticio)
    html = client.get(
        reverse("expediente_detalle", args=[expediente.pk])
    ).content.decode()
    assert 'aria-label="Información"' in html
    assert 'aria-label="Minuta"' not in html
    assert "Boleta informativa, DNI y cheques" in html
    assert f'href="{reverse("vehicular_lista")}">Transferencia vehicular' in html


def test_vehicular_no_acepta_minuta(client, usuario_ficticio, vehicular):
    from django.core.files.uploadedfile import SimpleUploadedFile

    expediente, _ = vehicular
    client.force_login(usuario_ficticio)
    respuesta = client.post(
        reverse("documento_subir", args=[expediente.pk]),
        {
            "rol": "MINUTA",
            "archivos": SimpleUploadedFile("minuta.txt", b"MINUTA FICTICIA"),
        },
    )
    assert respuesta.status_code == 400
    assert not expediente.documentos.filter(rol="MINUTA").exists()


def test_confronta_sin_minuta_con_reglas_vehiculares(vehicular):
    from expedientes.services import confrontar_borrador, estado_confrontacion

    expediente, borrador = vehicular
    assert estado_confrontacion(expediente, borrador)["disponible"]
    resultado = confrontar_borrador(expediente, borrador)
    assert resultado["estado"] == "RESULTADO"
    placa = [o for o in resultado["regla"] if o["campo"] == "PLACA"]
    assert [(o["hallado"], o["esperado"]) for o in placa] == [("QWE128", "QWE123")]


def test_kardex_notarial_sigue_pidiendo_minuta(usuario_ficticio):
    from expedientes.models import Documento, Expediente
    from expedientes.services import estado_confrontacion

    expediente = Expediente.objects.create(
        codigo="KARDEX-FICTICIO-2", creado_por=usuario_ficticio
    )
    _documento(expediente, Documento.CLIENTE, "boleta.pdf", BOLETA, usuario_ficticio)
    borrador = _documento(
        expediente, Documento.BORRADOR, "b.docx", BORRADOR, usuario_ficticio
    )
    estado = estado_confrontacion(expediente, borrador)
    assert not estado["disponible"]
    assert "Minuta" in estado["mensaje"]


def test_resultado_vehicular_avisa_al_informe(client, usuario_ficticio, vehicular):
    """F44: el informe Word no habla de minuta en una transferencia vehicular."""
    from expedientes.services import confrontar_borrador, registrar_corrida

    expediente, borrador = vehicular
    registrar_corrida(
        expediente,
        borrador,
        usuario_ficticio,
        confrontar_borrador(expediente, borrador),
    )
    client.force_login(usuario_ficticio)
    html = client.get(
        reverse("documento_resultado", args=[expediente.pk, borrador.pk])
    ).content.decode()
    assert "vehicular: 'VEHICULAR' === 'VEHICULAR'," in html
    # F56: el ítem de la lista muestra la placa hallada y la correcta sin abrirlo.
    item = re.search(
        r'<button type="button" class="obs-item"(?:(?!</button>).)*>Placa<.*?</button>',
        html,
        re.S,
    ).group(0)
    assert re.search(
        r'<span class="obs-rot">Dice</span> <span class="tachado"><mark>QWE128</mark>'
        r'.*?<span class="obs-rot">Debe decir</span> <span class="correcto">'
        r"<mark>QWE123</mark>",
        item,
        re.S,
    )


def test_menu_expedientes_agrupa_kardex_y_transferencia_vehicular(
    client, usuario_ficticio
):
    """F47: «Expedientes» solo rotula el grupo; sus hijos son los destinos."""
    client.force_login(usuario_ficticio)
    html = client.get(reverse("vehicular_lista")).content.decode()
    grupo = html.index(">Expedientes</span>")
    submenu = html.index('<ul class="submenu" aria-label="Expedientes">', grupo)
    assert "<a" not in html[html.rindex("<li>", 0, grupo) : submenu]
    kardex = f'href="{reverse("expediente_lista")}"'
    vehicular = f'href="{reverse("vehicular_lista")}"'
    fin = html.index("</ul>", submenu)
    assert submenu < html.index(kardex, submenu) < html.index(vehicular, submenu) < fin
    assert ">Kardex</span>" in html[submenu:fin]
    assert ">Transferencia vehicular</span>" in html[submenu:fin]
    assert re.search(vehicular + r'[^>]*aria-current="page"', html)
    assert not re.search(kardex + r"[^>]*aria-current", html)


def test_ruc_sin_ficha_ruc_no_es_error_en_vehicular(vehicular):
    """F45: sin ficha RUC entre la información el RUC no se puede verificar."""
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    expediente, borrador = vehicular
    texto = borrador.texto_extraido
    texto.texto += "LA EMPRESA FICTICIA DEMO S.A.C., CON RUC 20000000001.\n"
    texto.save()
    borrador = Documento.objects.get(pk=borrador.pk)
    ruc = [
        o
        for o in confrontar_borrador(expediente, borrador)["regla"]
        if "20000000001" in o["hallado"]
    ]
    assert [o["campo"] for o in ruc] == ["SIN_FICHA"]


def test_numero_no_se_repite_entre_kardex_y_vehicular(client, usuario_ficticio):
    from expedientes.models import Expediente

    Expediente.objects.create(codigo="NUM-FICTICIO-1", creado_por=usuario_ficticio)
    Expediente.objects.create(
        codigo="NUM-FICTICIO-2",
        tipo=Expediente.VEHICULAR,
        creado_por=usuario_ficticio,
    )
    client.force_login(usuario_ficticio)

    vehicular = client.post(reverse("vehicular_lista"), {"codigo": "NUM-FICTICIO-1"})
    notarial = client.post(reverse("expediente_lista"), {"codigo": "NUM-FICTICIO-2"})

    # F55: el mensaje nombra el tipo que ya usa el número.
    assert "Ya existe un kardex activo con ese número" in vehicular.content.decode()
    assert "Número de TV" in vehicular.content.decode()
    assert "Ya existe una TV activa con ese número" in notarial.content.decode()
    assert "Número de kardex" in notarial.content.decode()
    otra_tv = client.post(reverse("vehicular_lista"), {"codigo": "NUM-FICTICIO-2"})
    assert "Ya existe una TV activa con ese número" in otra_tv.content.decode()
    assert Expediente.objects.count() == 2


def test_bd_rechaza_numero_repetido_entre_tipos(usuario_ficticio):
    from django.db import IntegrityError, transaction

    from expedientes.models import Expediente

    Expediente.objects.create(codigo="NUM-FICTICIO-3", creado_por=usuario_ficticio)
    with pytest.raises(IntegrityError), transaction.atomic():
        Expediente.objects.create(
            codigo="NUM-FICTICIO-3",
            tipo=Expediente.VEHICULAR,
            creado_por=usuario_ficticio,
        )


# F55: en el flujo vehicular «kardex» pasa a «Transferencia vehicular» (títulos)
# y «TV» (botones, columnas, etiquetas y textos cortos).


def _sin_menu(html):
    """El menú lateral nombra los dos tipos; el resto de la pantalla, solo el suyo."""
    return re.sub(r"<aside .*?</aside>", "", html, flags=re.S)


def _migas(html):
    return html.split('class="migas">', 1)[1].split("</nav>", 1)[0]


def test_pantallas_vehiculares_dicen_tv_y_no_kardex(
    client, usuario_ficticio, vehicular
):
    from expedientes.services import confrontar_borrador, registrar_corrida

    expediente, borrador = vehicular
    corrida = registrar_corrida(
        expediente,
        borrador,
        usuario_ficticio,
        confrontar_borrador(expediente, borrador),
    )["corrida_id"]
    pk = expediente.pk
    client.force_login(usuario_ficticio)
    pantallas = {
        reverse("vehicular_lista"): [
            "<title>Transferencia vehicular ·",
            "<h1>Transferencia vehicular</h1>",
            "Cree la TV con su número",
            "Nueva TV",
            "Crear TV",
            "Número de TV",
            "Mis TV",
            'placeholder="Buscar por N.° de TV"',
            "TV visibles y su estado derivado",
            ">N.° de TV</th>",
            "Eliminar TV",
            "Ninguna TV coincide con el filtro.",
            "</span> TV</div>",
            "¿Eliminar la TV ",
        ],
        reverse("expediente_detalle", args=[pk]): [
            'aria-label="Eliminar TV"',
            "Estado de la TV",
            "Esta TV aún no tiene documentos.",
        ],
        reverse("expediente_editar", args=[pk]): [
            '<p class="eyebrow">Transferencia vehicular</p>',
            "Número de TV",
            "Tras archivar una TV, su número puede reutilizarse.",
            "Editar TV",
            "Eliminar TV",
        ],
        reverse("expediente_eliminar", args=[pk]): [
            '<p class="eyebrow">Transferencia vehicular</p>',
            "¿Eliminar la TV VEH-FICTICIO-1?",
        ],
        reverse("expediente_historial", args=[pk]): [
            '<p class="eyebrow">Transferencia vehicular / Historial</p>',
            "Volver a la TV",
            "Confrontaciones de la TV",
        ],
        reverse("corrida_detalle", args=[pk, corrida]): [
            '<p class="eyebrow">Transferencia vehicular / Historial</p>',
        ],
        reverse("documento_resultado", args=[pk, borrador.pk]): [
            "Volver a la TV",
            "El informe registra TV, borrador",
        ],
    }
    for url, textos in pantallas.items():
        html = client.get(url).content.decode()
        assert "kardex" not in _sin_menu(html).lower(), url
        assert "<li>Expedientes</li>" in _migas(html), url
        for texto in textos:
            assert texto in html, (url, texto)
    lista = client.get(reverse("vehicular_lista")).content.decode()
    assert (
        '<li>Expedientes</li><li aria-current="page">Transferencia vehicular</li>'
        in _migas(lista)
    )

    # Sin confirmar, «Aplicar correcciones» muestra su página con el error.
    aplicar = client.post(reverse("correcciones_aplicar", args=[pk, borrador.pk]))
    html = aplicar.content.decode()
    assert aplicar.status_code == 400
    assert "kardex" not in _sin_menu(html).lower()
    assert '<p class="eyebrow">Transferencia vehicular / Correcciones</p>' in html
    assert "Volver a la TV" in html


def test_lista_vehicular_vacia_y_archivadas_dicen_tv(client, administrador_ficticio):
    client.force_login(administrador_ficticio)
    vacia = client.get(reverse("vehicular_lista")).content.decode()
    assert "Aún no hay TV visibles." in vacia
    assert "Cree una con su número" in vacia
    assert 'aria-label="Filtro de TV"' in vacia
    html = client.get(reverse("vehicular_lista") + "?archivados=1").content.decode()
    assert "TV archivadas" in html
    assert "No hay TV archivadas." in html
    assert "kardex" not in _sin_menu(html).lower()


def test_mensajes_de_la_tv(client, usuario_ficticio, administrador_ficticio):
    from expedientes.models import Expediente

    client.force_login(usuario_ficticio)
    creada = client.post(
        reverse("vehicular_lista"), {"codigo": "VEH-FICTICIO-5"}, follow=True
    )
    assert "TV creada. Ahora puede cargar sus documentos." in creada.content.decode()
    tv = Expediente.objects.get(codigo="VEH-FICTICIO-5")
    editada = client.post(
        reverse("expediente_editar", args=[tv.pk]),
        {"codigo": "VEH-FICTICIO-6"},
        follow=True,
    )
    assert "TV actualizada." in editada.content.decode()
    eliminada = client.post(reverse("expediente_eliminar", args=[tv.pk]), follow=True)
    assert "TV VEH-FICTICIO-6 eliminada." in eliminada.content.decode()

    client.force_login(administrador_ficticio)
    restaurada = client.post(reverse("expediente_restaurar", args=[tv.pk]), follow=True)
    assert "TV VEH-FICTICIO-6 restaurada." in restaurada.content.decode()


def test_restaurar_nombra_el_tipo_que_ocupa_el_numero(
    client, usuario_ficticio, administrador_ficticio
):
    from expedientes.models import Expediente

    ahora = timezone.now()
    tv_archivada = Expediente.objects.create(
        codigo="NUM-FICTICIO-7",
        tipo=Expediente.VEHICULAR,
        creado_por=usuario_ficticio,
        archivado_el=ahora,
    )
    kardex_archivado = Expediente.objects.create(
        codigo="NUM-FICTICIO-8", creado_por=usuario_ficticio, archivado_el=ahora
    )
    Expediente.objects.create(codigo="NUM-FICTICIO-7", creado_por=usuario_ficticio)
    Expediente.objects.create(
        codigo="NUM-FICTICIO-8",
        tipo=Expediente.VEHICULAR,
        creado_por=usuario_ficticio,
    )
    client.force_login(administrador_ficticio)

    tv = client.post(
        reverse("expediente_restaurar", args=[tv_archivada.pk]), follow=True
    )
    kardex = client.post(
        reverse("expediente_restaurar", args=[kardex_archivado.pk]), follow=True
    )

    assert (
        "ya existe un kardex activo con el número NUM-FICTICIO-7. "
        "Cambie o elimine ese kardex primero."
    ) in tv.content.decode()
    assert (
        "ya existe una TV activa con el número NUM-FICTICIO-8. "
        "Cambie o elimine esa TV primero."
    ) in kardex.content.decode()


def test_pantallas_notariales_siguen_diciendo_kardex(client, usuario_ficticio):
    from expedientes.models import Expediente

    client.force_login(usuario_ficticio)
    creado = client.post(
        reverse("expediente_lista"), {"codigo": "KARDEX-FICTICIO-5"}, follow=True
    )
    assert "Kardex creado. Ahora puede cargar sus documentos." in (
        creado.content.decode()
    )
    pk = Expediente.objects.get(codigo="KARDEX-FICTICIO-5").pk
    pantallas = {
        reverse("expediente_lista"): [
            "Nuevo kardex",
            "Mis kardex",
            ">N.° de kardex</th>",
            "Eliminar kardex",
        ],
        reverse("expediente_detalle", args=[pk]): [
            'aria-label="Eliminar kardex"',
            "Este kardex aún no tiene documentos.",
        ],
        reverse("expediente_editar", args=[pk]): [
            '<p class="eyebrow">Kardex</p>',
            "Número de kardex",
            "Eliminar kardex",
        ],
        reverse("expediente_eliminar", args=[pk]): [
            "¿Eliminar el kardex KARDEX-FICTICIO-5?",
        ],
        reverse("expediente_historial", args=[pk]): [
            '<p class="eyebrow">Kardex / Historial</p>',
            "Volver al kardex",
        ],
    }
    for url, textos in pantallas.items():
        html = client.get(url).content.decode()
        resto = _sin_menu(html)
        assert not re.search(r"\bTV\b|Transferencia vehicular", resto), url
        # Las migas siguen al menú lateral: Expedientes › Kardex, como en la TV.
        assert _migas(html).count("Expedientes") == 1, url
        assert "Kardex" in _migas(html), url
        for texto in textos:
            assert texto in html, (url, texto)


def test_eliminar_y_restaurar_fallido_vuelven_a_la_lista_de_su_tipo(
    client, usuario_ficticio, administrador_ficticio
):
    from expedientes.models import Expediente

    tv = Expediente.objects.create(
        codigo="NUM-FICTICIO-9", tipo=Expediente.VEHICULAR, creado_por=usuario_ficticio
    )
    kardex = Expediente.objects.create(
        codigo="NUM-FICTICIO-10", creado_por=usuario_ficticio
    )
    client.force_login(usuario_ficticio)
    for expediente, lista in ((tv, "vehicular_lista"), (kardex, "expediente_lista")):
        respuesta = client.post(reverse("expediente_eliminar", args=[expediente.pk]))
        assert respuesta.url == reverse(lista)

    # Con el número ocupado por otro activo, la restauración falla.
    Expediente.objects.create(codigo="NUM-FICTICIO-9", creado_por=usuario_ficticio)
    Expediente.objects.create(
        codigo="NUM-FICTICIO-10",
        tipo=Expediente.VEHICULAR,
        creado_por=usuario_ficticio,
    )
    client.force_login(administrador_ficticio)
    for expediente, lista in ((tv, "vehicular_lista"), (kardex, "expediente_lista")):
        respuesta = client.post(reverse("expediente_restaurar", args=[expediente.pk]))
        assert respuesta.url == f"{reverse(lista)}?archivados=1"
