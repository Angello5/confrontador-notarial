"""Contrato de autorización de expedientes y documentos."""

import pytest

pytestmark = pytest.mark.django_db


def test_creador_ve_su_expediente_y_administrador_ve_cualquiera(
    client, usuario_ficticio, administrador_ficticio
):
    from expedientes.models import Expediente

    propio = Expediente.objects.create(
        codigo="EXP-FICTICIO-010", creado_por=usuario_ficticio
    )
    client.force_login(usuario_ficticio)
    assert client.get(f"/expedientes/{propio.pk}/").status_code == 200

    client.force_login(administrador_ficticio)
    assert client.get(f"/expedientes/{propio.pk}/").status_code == 200


def test_usuario_no_puede_consultar_estado_ni_eliminar_ajeno(
    client, usuario_ficticio, administrador_ficticio
):
    from expedientes.models import Documento, Expediente

    propio = Expediente.objects.create(
        codigo="EXP-FICTICIO-011", creado_por=administrador_ficticio
    )
    documento = Documento.objects.create(
        expediente=propio,
        rol="FUENTE",
        nombre_original="fuente-ajena.txt",
        hash_archivo="c" * 64,
        tamano_bytes=8,
        subido_por=administrador_ficticio,
    )
    client.force_login(usuario_ficticio)

    assert client.get(f"/expedientes/{propio.pk}/").status_code in {403, 404}
    assert client.get(f"/expedientes/{propio.pk}/estado/").status_code in {403, 404}
    assert client.post(
        f"/expedientes/{propio.pk}/documentos/{documento.pk}/eliminar/"
    ).status_code in {403, 404}
