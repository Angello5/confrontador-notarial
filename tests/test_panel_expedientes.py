"""F25: abrir, editar y eliminar (archivar) expedientes desde el panel."""

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture
def otro_usuario(db):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    user = get_user_model().objects.create_user(username="otro_ficticio")
    user.groups.add(Group.objects.get(name="Usuario"))
    return user


@pytest.fixture
def expediente(usuario_ficticio):
    from expedientes.models import Expediente

    return Expediente.objects.create(
        codigo="EXP-FICTICIO-F25", creado_por=usuario_ficticio
    )


def test_lista_y_detalle_muestran_abrir_editar_eliminar(
    client, usuario_ficticio, expediente
):
    client.force_login(usuario_ficticio)
    lista = client.get("/expedientes/").content.decode()
    assert f'href="/expedientes/{expediente.pk}/"' in lista
    assert f'href="/expedientes/{expediente.pk}/editar/"' in lista
    assert f'href="/expedientes/{expediente.pk}/eliminar/"' in lista
    assert f'aria-label="Editar {expediente.codigo}"' in lista
    assert f'aria-label="Eliminar {expediente.codigo}"' in lista

    detalle = client.get(f"/expedientes/{expediente.pk}/").content.decode()
    assert f'href="/expedientes/{expediente.pk}/editar/"' in detalle
    assert f'href="/expedientes/{expediente.pk}/eliminar/"' in detalle


def test_editar_cambia_el_codigo(client, usuario_ficticio, expediente):
    client.force_login(usuario_ficticio)
    ruta = f"/expedientes/{expediente.pk}/editar/"
    formulario = client.get(ruta)
    assert formulario.status_code == 200
    assert 'value="EXP-FICTICIO-F25"' in formulario.content.decode()

    respuesta = client.post(ruta, {"codigo": "  EXP-FICTICIO-F25-B "})
    assert respuesta.status_code == 302
    assert respuesta["Location"] == f"/expedientes/{expediente.pk}/"
    expediente.refresh_from_db()
    assert expediente.codigo == "EXP-FICTICIO-F25-B"


def test_editar_valida_unicidad_y_obligatorio(client, usuario_ficticio, expediente):
    from expedientes.models import Expediente

    Expediente.objects.create(
        codigo="EXP-FICTICIO-OCUPADO", creado_por=usuario_ficticio
    )
    client.force_login(usuario_ficticio)
    ruta = f"/expedientes/{expediente.pk}/editar/"

    duplicado = client.post(ruta, {"codigo": "EXP-FICTICIO-OCUPADO"})
    assert duplicado.status_code == 400
    assert "Ya existe un expediente activo con ese código" in duplicado.content.decode()
    assert client.post(ruta, {"codigo": "   "}).status_code == 400
    # Guardar el mismo código no choca consigo mismo.
    assert client.post(ruta, {"codigo": "EXP-FICTICIO-F25"}).status_code == 302
    expediente.refresh_from_db()
    assert expediente.codigo == "EXP-FICTICIO-F25"


def test_otro_usuario_no_puede_editar_ni_eliminar(client, otro_usuario, expediente):
    client.force_login(otro_usuario)
    base = f"/expedientes/{expediente.pk}"
    for ruta in (f"{base}/editar/", f"{base}/eliminar/"):
        assert client.get(ruta).status_code in {403, 404}
        assert client.post(ruta, {"codigo": "EXP-FICTICIO-X"}).status_code in {
            403,
            404,
        }
    expediente.refresh_from_db()
    assert expediente.codigo == "EXP-FICTICIO-F25"
    assert expediente.archivado_el is None


def test_administrador_puede_editar_y_eliminar_ajeno(
    client, administrador_ficticio, expediente
):
    client.force_login(administrador_ficticio)
    base = f"/expedientes/{expediente.pk}"
    assert (
        client.post(f"{base}/editar/", {"codigo": "EXP-FICTICIO-ADM"}).status_code
        == 302
    )
    assert client.post(f"{base}/eliminar/").status_code == 302
    expediente.refresh_from_db()
    assert expediente.codigo == "EXP-FICTICIO-ADM"
    assert expediente.archivado_por == administrador_ficticio


def test_editar_y_eliminar_exigen_csrf(usuario_ficticio, expediente):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(usuario_ficticio)
    base = f"/expedientes/{expediente.pk}"
    assert (
        cliente.post(f"{base}/editar/", {"codigo": "EXP-FICTICIO-X"}).status_code == 403
    )
    assert cliente.post(f"{base}/eliminar/").status_code == 403
    expediente.refresh_from_db()
    assert expediente.codigo == "EXP-FICTICIO-F25"
    assert expediente.archivado_el is None


def test_eliminar_confirma_con_el_codigo_y_archiva(
    client, usuario_ficticio, expediente
):
    client.force_login(usuario_ficticio)
    ruta = f"/expedientes/{expediente.pk}/eliminar/"
    confirmacion = client.get(ruta)
    assert confirmacion.status_code == 200
    contenido = confirmacion.content.decode()
    assert "EXP-FICTICIO-F25" in contenido and 'method="post"' in contenido
    expediente.refresh_from_db()
    assert expediente.archivado_el is None

    respuesta = client.post(ruta)
    assert respuesta.status_code == 302
    assert respuesta["Location"] == "/expedientes/"
    expediente.refresh_from_db()
    assert expediente.archivado_el is not None
    assert expediente.archivado_por == usuario_ficticio


def test_archivado_oculto_en_lista_inicio_metricas_y_detalle(
    client, usuario_ficticio, expediente
):
    from django.utils import timezone

    expediente.archivado_el = timezone.now()
    expediente.archivado_por = usuario_ficticio
    expediente.save()
    client.force_login(usuario_ficticio)

    assert "EXP-FICTICIO-F25" not in client.get("/expedientes/").content.decode()
    inicio = client.get("/")
    assert "EXP-FICTICIO-F25" not in inicio.content.decode()
    assert inicio.context["metricas"]["total"] == 0
    base = f"/expedientes/{expediente.pk}"
    assert client.get(f"{base}/").status_code == 404
    assert client.get(f"{base}/estado/").status_code == 404
    assert client.get(f"{base}/confrontaciones/").status_code == 404
    assert client.post(f"{base}/documentos/", {"rol": "CLIENTE"}).status_code == 404
    assert client.get(f"{base}/editar/").status_code == 404
    # Un Usuario no ve archivados aunque pida el filtro.
    assert (
        "EXP-FICTICIO-F25"
        not in client.get("/expedientes/?archivados=1").content.decode()
    )


def test_manifiesto_intacto_tras_archivar(client, usuario_ficticio, expediente):
    from expedientes.models import Corrida, DecisionCorreccion

    corrida = Corrida.objects.create(
        expediente=expediente,
        id_borrador=1,
        hash_borrador="a" * 64,
        entradas=[],
        version_catalogo="v-ficticia",
        version_software="0.0.0",
        usuario=usuario_ficticio,
        fecha_referencia="2026-01-01",
        estado=Corrida.RESULTADO,
        hallazgos="",
        huella="b" * 64,
    )
    DecisionCorreccion.objects.create(corrida=corrida, usuario=usuario_ficticio)
    antes = list(Corrida.objects.values())

    client.force_login(usuario_ficticio)
    assert client.post(f"/expedientes/{expediente.pk}/eliminar/").status_code == 302

    assert list(Corrida.objects.values()) == antes
    assert DecisionCorreccion.objects.filter(corrida=corrida).count() == 1


def test_solo_administrador_ve_archivados_y_restaura(
    client, usuario_ficticio, administrador_ficticio, expediente
):
    client.force_login(usuario_ficticio)
    client.post(f"/expedientes/{expediente.pk}/eliminar/")
    ruta = f"/expedientes/{expediente.pk}/restaurar/"
    assert client.post(ruta).status_code == 403
    expediente.refresh_from_db()
    assert expediente.archivado_el is not None

    client.force_login(administrador_ficticio)
    archivados = client.get("/expedientes/?archivados=1").content.decode()
    assert "EXP-FICTICIO-F25" in archivados
    assert f'action="{ruta}"' in archivados
    assert "EXP-FICTICIO-F25" not in client.get("/expedientes/").content.decode()
    assert client.get(ruta).status_code == 405

    respuesta = client.post(ruta)
    assert respuesta.status_code == 302
    expediente.refresh_from_db()
    assert expediente.archivado_el is None and expediente.archivado_por is None
    assert client.get(f"/expedientes/{expediente.pk}/").status_code == 200


def test_restaurar_exige_csrf(administrador_ficticio, expediente):
    from django.utils import timezone

    expediente.archivado_el = timezone.now()
    expediente.archivado_por = administrador_ficticio
    expediente.save()
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(administrador_ficticio)
    assert cliente.post(f"/expedientes/{expediente.pk}/restaurar/").status_code == 403
