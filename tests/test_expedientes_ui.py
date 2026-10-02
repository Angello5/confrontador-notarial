"""Contrato de estado derivado, polling y mensajes accesibles de F4."""

import pytest

pytestmark = pytest.mark.django_db


def test_estado_json_no_expone_texto_ruta_ni_contenido(client, usuario_ficticio):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-040", creado_por=usuario_ficticio
    )
    client.force_login(usuario_ficticio)
    respuesta = client.get(f"/expedientes/{expediente.pk}/estado/")

    assert respuesta.status_code == 200
    assert "texto" not in respuesta.json()
    assert "ruta_temporal" not in respuesta.json()


def test_estado_json_actualiza_disponibilidad_por_borrador(client, usuario_ficticio):
    from django.utils import timezone

    from expedientes.models import Documento, Expediente, TextoExtraido

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-DISPONIBILIDAD", creado_por=usuario_ficticio
    )
    documentos = []
    for rol, nombre in (
        (Documento.CLIENTE, "cliente-disponibilidad.txt"),
        (Documento.MINUTA, "minuta-disponibilidad.txt"),
        (Documento.BORRADOR, "borrador-disponibilidad.txt"),
    ):
        texto = TextoExtraido.objects.create(
            hash_archivo=(nombre.replace(".", "")[:64]).ljust(64, "0"),
            version_extractor="extractor-ficticio-v1",
            texto="texto ficticio disponible",
            ultimo_uso_el=timezone.now(),
        )
        documentos.append(
            Documento.objects.create(
                expediente=expediente,
                rol=rol,
                nombre_original=nombre,
                hash_archivo=texto.hash_archivo,
                tamano_bytes=10,
                estado=Documento.PENDIENTE,
                texto_extraido=texto,
                subido_por=usuario_ficticio,
            )
        )

    client.force_login(usuario_ficticio)
    ruta = f"/expedientes/{expediente.pk}/estado/"
    no_disponible = client.get(ruta).json()

    assert no_disponible["borradores"] == [
        {
            "id": documentos[-1].pk,
            "disponible": False,
            "mensaje": "Espere a que termine la extracción de los documentos.",
            "resultado_listo": False,
        }
    ]

    Documento.objects.filter(pk__in=[documento.pk for documento in documentos]).update(
        estado=Documento.LISTO
    )
    disponible = client.get(ruta).json()

    assert disponible["borradores"] == [
        {
            "id": documentos[-1].pk,
            "disponible": True,
            "mensaje": "",
            "resultado_listo": False,
        }
    ]


@pytest.mark.parametrize(
    ("estado", "mensaje"),
    [
        ("PENDIENTE", "Pendiente"),
        ("PROCESANDO", "Procesando"),
        ("LISTO", "Listo"),
        ("ERROR", "No se pudo procesar"),
    ],
)
def test_pantalla_muestra_estado_y_accion_en_espanol(
    client, usuario_ficticio, estado, mensaje
):
    from expedientes.models import Documento, Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-041", creado_por=usuario_ficticio
    )
    Documento.objects.create(
        expediente=expediente,
        rol="CLIENTE",
        nombre_original="estado-ficticio.txt",
        hash_archivo=estado.lower().ljust(64, "0"),
        tamano_bytes=4,
        estado=estado,
        error="motivo ficticio" if estado == "ERROR" else "",
        subido_por=usuario_ficticio,
    )
    client.force_login(usuario_ficticio)
    respuesta = client.get(f"/expedientes/{expediente.pk}/")

    assert mensaje.encode() in respuesta.content
    if estado == "ERROR":
        contenido = respuesta.content.lower()
        assert b"motivo" in contenido
        assert b"elimine el documento y vuelva a subirlo" in contenido
        assert b"reintentar" not in contenido


def test_detalle_separa_las_tres_zonas_obligatorias(client, usuario_ficticio):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-ZONAS", creado_por=usuario_ficticio
    )
    client.force_login(usuario_ficticio)

    respuesta = client.get(f"/expedientes/{expediente.pk}/")
    contenido = respuesta.content.decode()

    assert "Documentos del cliente" in contenido
    assert "Minuta" in contenido
    assert "Proyecto (borrador)" in contenido
    assert contenido.count("multiple") == 3
    assert contenido.count("Obligatorio") >= 3
    assert "Faltan:" in contenido


def test_eliminar_sin_confirmacion_conserva_documento_y_temporal(
    client, usuario_ficticio, tmp_path
):
    from expedientes.models import Documento, Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-042", creado_por=usuario_ficticio
    )
    ruta = tmp_path / "no-eliminar-ficticio.tmp"
    ruta.write_bytes(b"contenido ficticio")
    documento = Documento.objects.create(
        expediente=expediente,
        rol="CLIENTE",
        nombre_original="no-eliminar-ficticio.txt",
        hash_archivo="8" * 64,
        tamano_bytes=ruta.stat().st_size,
        ruta_temporal=str(ruta),
        subido_por=usuario_ficticio,
    )
    client.force_login(usuario_ficticio)

    respuesta = client.post(
        f"/expedientes/{expediente.pk}/documentos/{documento.pk}/eliminar/"
    )

    assert respuesta.status_code == 400
    assert Documento.objects.filter(pk=documento.pk).exists()
    assert ruta.exists()
    assert b"Confirme la eliminaci\xc3\xb3n" in respuesta.content


def test_ninguna_pantalla_filtra_marcas_de_plantilla(client, usuario_ficticio):
    """Un comentario `{# #}` partido en dos líneas se renderiza como texto.

    Django solo admite la forma corta en una línea. El HTML sigue siendo válido,
    así que ni el lint ni el CI lo detectan: el fallo solo se ve en pantalla.
    """
    from expedientes.models import Documento, Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-MARCAS", creado_por=usuario_ficticio
    )
    Documento.objects.create(
        expediente=expediente,
        rol=Documento.CLIENTE,
        nombre_original="fuente-ficticia.txt",
        hash_archivo="e" * 64,
        tamano_bytes=10,
        subido_por=usuario_ficticio,
    )
    client.force_login(usuario_ficticio)

    contenido = client.get(f"/expedientes/{expediente.pk}/").content.decode()

    for marca in ("{#", "#}", "{% comment", "{% endcomment", "{{", "{%"):
        assert marca not in contenido, f"la pantalla filtra la marca {marca!r}"


# F14 · Rediseño de interfaz


def _expediente_con(usuario, codigo, documentos):
    from expedientes.models import Documento, Expediente

    expediente = Expediente.objects.create(codigo=codigo, creado_por=usuario)
    for indice, (rol, estado) in enumerate(documentos):
        Documento.objects.create(
            expediente=expediente,
            rol=rol,
            nombre_original=f"riel-{indice}.txt",
            hash_archivo=f"{codigo}{indice}".lower().ljust(64, "0")[:64],
            tamano_bytes=4,
            estado=estado,
            subido_por=usuario,
        )
    return expediente


@pytest.mark.parametrize(
    ("documentos", "actual"),
    [
        ([], "1"),
        ([("CLIENTE", "LISTO"), ("BORRADOR", "LISTO")], "1"),
        ([("CLIENTE", "LISTO"), ("MINUTA", "LISTO")], "2"),
        ([("CLIENTE", "LISTO"), ("MINUTA", "PENDIENTE"), ("BORRADOR", "LISTO")], "3"),
        ([("CLIENTE", "LISTO"), ("MINUTA", "ERROR"), ("BORRADOR", "LISTO")], "3"),
        ([("CLIENTE", "LISTO"), ("MINUTA", "LISTO"), ("BORRADOR", "LISTO")], "4"),
    ],
)
def test_riel_marca_el_paso_actual_por_estado(
    client, usuario_ficticio, documentos, actual
):
    expediente = _expediente_con(
        usuario_ficticio, f"EXP-FICTICIO-R{actual}", documentos
    )
    client.force_login(usuario_ficticio)

    contenido = client.get(f"/expedientes/{expediente.pk}/").content.decode()

    assert f'class="riel" data-actual="{actual}"' in contenido
    nombres = ["Fuentes", "Borrador", "Procesamiento", "Resultado"]
    assert "Paso actual: <span" in contenido
    assert f">{nombres[int(actual) - 1]}</span>" in contenido


def test_detalle_usa_paneles_chips_y_privacidad(client, usuario_ficticio):
    expediente = _expediente_con(
        usuario_ficticio, "EXP-FICTICIO-PANEL", [("CLIENTE", "LISTO")]
    )
    client.force_login(usuario_ficticio)

    contenido = client.get(f"/expedientes/{expediente.pk}/").content.decode()

    assert "Documentos del expediente" in contenido
    assert "Borrador a confrontar" in contenido
    assert 'class="chip" data-estado="LISTO"' in contenido
    assert "se procesan localmente y se eliminan al terminar" in contenido
    assert contenido.count('class="zona-arrastre"') == 3


def test_lista_muestra_chip_documentos_y_actualizado(client, usuario_ficticio):
    _expediente_con(usuario_ficticio, "EXP-FICTICIO-L1", [("CLIENTE", "ERROR")])
    client.force_login(usuario_ficticio)

    contenido = client.get("/expedientes/").content.decode()

    assert "Nuevo expediente" in contenido
    assert 'class="chip" data-estado="ERROR"' in contenido
    assert ">Documentos</th>" in contenido
    assert 'class="th-orden" @click="ordenar()">Actualizado' in contenido
    assert "abierto: false" in contenido


def test_lista_con_error_de_codigo_deja_el_formulario_abierto(client, usuario_ficticio):
    client.force_login(usuario_ficticio)

    contenido = client.post("/expedientes/", {"codigo": ""}).content.decode()

    assert "abierto: true" in contenido
    assert 'role="alert"' in contenido
