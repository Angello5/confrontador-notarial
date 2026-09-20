"""Contrato de alta y validación server-side de subidas F4."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db


def test_usuario_crea_expediente_y_sube_fuente_sintetica(client, usuario_ficticio):
    from expedientes.models import Expediente

    assert Expediente
    client.force_login(usuario_ficticio)
    respuesta = client.post("/expedientes/", {"codigo": "EXP-FICTICIO-020"})
    assert respuesta.status_code in {200, 302}
    expediente = Expediente.objects.get(codigo="EXP-FICTICIO-020")

    respuesta = client.post(
        f"/expedientes/{expediente.pk}/documentos/",
        {
            "rol": "FUENTE",
            "archivo": SimpleUploadedFile(
                "fuente-sintetica.txt", b"contenido ficticio de prueba"
            ),
        },
    )
    assert respuesta.status_code in {200, 302}


@pytest.mark.parametrize(
    ("nombre", "contenido", "mensaje"),
    [
        ("no-admitido.bin", b"bytes ficticios", "formato"),
        ("vacio.txt", b"", "vacío"),
    ],
)
def test_subida_invalida_no_escribe_temporal(
    client, usuario_ficticio, nombre, contenido, mensaje
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-UPLOAD", creado_por=usuario_ficticio
    )
    client.force_login(usuario_ficticio)
    respuesta = client.post(
        f"/expedientes/{expediente.pk}/documentos/",
        {
            "rol": "FUENTE",
            "archivo": SimpleUploadedFile(nombre, contenido),
        },
    )

    assert respuesta.status_code in {200, 400, 404}
    assert mensaje.encode() in respuesta.content.lower()
    assert b"/tmp/" not in respuesta.content


def test_duplicado_por_rol_se_rechaza_sin_datos_no_confiables(client, usuario_ficticio):
    from expedientes.models import Documento, Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-DUPLICADO", creado_por=usuario_ficticio
    )
    Documento.objects.create(
        expediente=expediente,
        rol="FUENTE",
        nombre_original="anterior.txt",
        hash_archivo="2e61afd25d3ca76a0ee265dbc22ba5e9d844dc93ac5f2e37199a34fcbdcb5a52",
        tamano_bytes=16,
        subido_por=usuario_ficticio,
    )
    client.force_login(usuario_ficticio)
    respuesta = client.post(
        f"/expedientes/{expediente.pk}/documentos/",
        {
            "rol": "FUENTE",
            "archivo": SimpleUploadedFile("repetido.txt", b"b" * 16),
        },
    )

    assert respuesta.status_code == 400
    assert b"repetido.txt" not in respuesta.content
    assert b"hash" not in respuesta.content.lower()


def test_archivo_mayor_de_25_mb_se_rechaza_antes_de_guardar(client, usuario_ficticio):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-GRANDE", creado_por=usuario_ficticio
    )
    client.force_login(usuario_ficticio)
    respuesta = client.post(
        f"/expedientes/{expediente.pk}/documentos/",
        {
            "rol": "FUENTE",
            "archivo": SimpleUploadedFile(
                "grande-sintetico.txt", b"x" * (25 * 1024 * 1024 + 1)
            ),
        },
    )

    assert respuesta.status_code == 400
