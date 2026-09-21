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
