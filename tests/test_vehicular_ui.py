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

    for respuesta in (vehicular, notarial):
        assert "Ya existe un kardex activo con ese número" in respuesta.content.decode()
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
