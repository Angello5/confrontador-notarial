"""F28: código reutilizable tras archivar y nombre de la notaría configurable."""

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

pytestmark = pytest.mark.django_db

CODIGO = "EXP-FICTICIO-F28"


def _expediente(usuario, archivado=False):
    from expedientes.models import Expediente

    return Expediente.objects.create(
        codigo=CODIGO,
        creado_por=usuario,
        archivado_el=timezone.now() if archivado else None,
        archivado_por=usuario if archivado else None,
    )


def _corrida(expediente, usuario):
    from expedientes.models import Corrida

    return Corrida.objects.create(
        expediente=expediente,
        id_borrador=1,
        hash_borrador="a" * 64,
        entradas=[],
        version_catalogo="v-ficticia",
        version_software="0.0.0",
        usuario=usuario,
        fecha_referencia="2026-01-01",
        estado=Corrida.RESULTADO,
        hallazgos="",
        huella="b" * 64,
    )


def test_crear_con_codigo_de_un_archivado_crea_uno_nuevo(client, usuario_ficticio):
    from expedientes.models import Expediente

    archivado = _expediente(usuario_ficticio, archivado=True)
    corrida = _corrida(archivado, usuario_ficticio)
    client.force_login(usuario_ficticio)

    respuesta = client.post("/expedientes/", {"codigo": CODIGO})

    assert respuesta.status_code == 302
    nuevo = Expediente.objects.get(codigo=CODIGO, archivado_el__isnull=True)
    assert nuevo.pk != archivado.pk
    assert respuesta["Location"] == f"/expedientes/{nuevo.pk}/"
    assert not nuevo.corridas.exists()
    assert list(archivado.corridas.all()) == [corrida]
    historial = client.get(f"/expedientes/{nuevo.pk}/confrontaciones/")
    assert historial.status_code == 200
    assert f"/confrontaciones/{corrida.pk}/" not in historial.content.decode()


def test_crear_o_editar_con_codigo_de_un_activo_da_error(client, usuario_ficticio):
    from expedientes.models import Expediente

    _expediente(usuario_ficticio)
    otro = Expediente.objects.create(
        codigo="EXP-FICTICIO-OTRO", creado_por=usuario_ficticio
    )
    client.force_login(usuario_ficticio)

    for ruta in ("/expedientes/", f"/expedientes/{otro.pk}/editar/"):
        respuesta = client.post(ruta, {"codigo": CODIGO})
        assert respuesta.status_code in {200, 400}
        assert "Ya existe un kardex activo con ese número" in (
            respuesta.content.decode()
        )
    assert Expediente.objects.filter(codigo=CODIGO).count() == 1


def test_la_base_impide_dos_activos_con_el_mismo_codigo(usuario_ficticio):
    from django.db import IntegrityError, transaction

    _expediente(usuario_ficticio, archivado=True)
    _expediente(usuario_ficticio, archivado=True)
    _expediente(usuario_ficticio)
    with pytest.raises(IntegrityError), transaction.atomic():
        _expediente(usuario_ficticio)


def test_restaurar_con_codigo_ocupado_muestra_mensaje_sin_cambios(
    client, usuario_ficticio, administrador_ficticio
):
    archivado = _expediente(usuario_ficticio, archivado=True)
    archivado_el = archivado.archivado_el
    _expediente(usuario_ficticio)
    client.force_login(administrador_ficticio)

    respuesta = client.post(f"/expedientes/{archivado.pk}/restaurar/", follow=True)

    assert respuesta.status_code == 200
    assert (
        f"No se puede restaurar: ya existe un kardex activo con el número {CODIGO}"
        in respuesta.content.decode()
    )
    archivado.refresh_from_db()
    assert archivado.archivado_el == archivado_el
    assert archivado.archivado_por == usuario_ficticio


def test_marca_por_defecto(client, usuario_ficticio):
    client.force_login(usuario_ficticio)
    contenido = client.get(reverse("home")).content.decode()
    assert '<span class="marca-sello" aria-hidden="true">EN</span>' in contenido
    assert '<span class="marca-nombre">ERP Notarial</span>' in contenido
    assert "CONFRONTADOR" not in contenido


@override_settings(ERP_NOMBRE="Notaria Ficticia de Prueba")
def test_marca_configurable_en_base_y_login(client, usuario_ficticio):
    client.force_login(usuario_ficticio)
    for ruta in (reverse("home"), reverse("expediente_lista")):
        contenido = client.get(ruta).content.decode()
        assert '<span class="marca-sello" aria-hidden="true">NF</span>' in contenido
        assert (
            '<span class="marca-nombre">Notaria Ficticia de Prueba</span>'
            '<span class="marca-sub">Confrontador Notarial</span>'
        ) in contenido
        assert "Notaria Ficticia de Prueba</title>" in contenido
        assert "ERP Notarial" not in contenido and "CONFRONTADOR" not in contenido
    client.logout()
    login = client.get(reverse("login")).content.decode()
    assert "<title>Ingresar · Notaria Ficticia de Prueba</title>" in login
    assert '<span class="marca-sello" aria-hidden="true">NF</span>' in login
    assert "CONFRONTADOR" not in login


@override_settings(ERP_NOMBRE="  notaria  ")
def test_marca_de_una_palabra(client, usuario_ficticio):
    client.force_login(usuario_ficticio)
    contenido = client.get(reverse("home")).content.decode()
    assert '<span class="marca-sello" aria-hidden="true">N</span>' in contenido
