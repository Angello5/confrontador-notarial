"""F25: abrir, editar y eliminar (archivar) expedientes desde el panel."""

# ruff: noqa: F811
import pytest
from django.test import Client

from tests.test_expedientes_confrontacion import crear_documento_listo  # noqa: F401

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
    assert "Ya existe un kardex activo con ese número" in duplicado.content.decode()
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


# F59 · Total de errores y hora real de actualización en la lista


def _fila(contenido, codigo):
    inicio = contenido.index(f'data-codigo="{codigo}"')
    return contenido[inicio : contenido.index("</tr>", inicio)]


def _confrontado(crear, usuario, codigo, tipo="NOTARIAL", **observaciones):
    """Kardex ficticio con sus documentos listos y la corrida de su borrador."""
    from expedientes.models import Expediente
    from expedientes.services import registrar_corrida

    expediente = Expediente.objects.create(codigo=codigo, creado_por=usuario, tipo=tipo)
    for rol, _ in expediente.roles:  # el borrador es el último
        documento = crear(expediente, rol, f"{codigo}-{rol}.txt", "TEXTO FICTICIO")
    registrar_corrida(
        expediente, documento, usuario, {"estado": "RESULTADO", **observaciones}
    )
    return expediente, documento


def test_lista_muestra_el_total_de_errores_de_la_confrontacion_vigente(
    client, usuario_ficticio, crear_documento_listo
):
    from expedientes.models import Documento, Expediente
    from expedientes.services import registrar_corrida

    crear = crear_documento_listo
    con_errores, borrador = _confrontado(
        crear,
        usuario_ficticio,
        "KDX-F59-A",
        personas=[{"tipo": "DOCUMENTO_SIN_TITULAR"}],
        regla=[{"campo": "DNI"}, {"campo": "PARTIDA"}],
        ortografia=[{"palabra": "cassa", "motivo": "no existe"}],
    )
    _confrontado(crear, usuario_ficticio, "KDX-F59-B")
    cambiado, _ = _confrontado(
        crear, usuario_ficticio, "KDX-F59-C", regla=[{"campo": "DNI"}]
    )
    crear(
        cambiado,
        Documento.CLIENTE,
        "KDX-F59-C-nuevo.txt",
        "OTRO",
        estado=Documento.PENDIENTE,
    )
    advertido, otro_borrador = _confrontado(crear, usuario_ficticio, "KDX-F59-D")
    registrar_corrida(
        advertido,
        otro_borrador,
        usuario_ficticio,
        {"estado": "ADVERTENCIA_CORRESPONDENCIA", "mensaje": "Revise."},
    )
    Expediente.objects.create(codigo="KDX-F59-E", creado_por=usuario_ficticio)
    client.force_login(usuario_ficticio)

    respuesta = client.get("/expedientes/")

    errores = {
        e.codigo: resumen["observaciones"]
        for e, resumen in respuesta.context["expedientes"]
    }
    assert errores == {
        "KDX-F59-A": 4,
        "KDX-F59-B": 0,
        "KDX-F59-C": None,
        "KDX-F59-D": None,
        "KDX-F59-E": None,
    }
    contenido = respuesta.content.decode()
    assert ">Errores</th>" in contenido
    assert "<td>4</td>" in _fila(contenido, "KDX-F59-A")
    assert "<td>0</td>" in _fila(contenido, "KDX-F59-B")
    for codigo in ("KDX-F59-C", "KDX-F59-D", "KDX-F59-E"):
        assert "<td>—</td>" in _fila(contenido, codigo)
    # El mismo total que la pantalla de resultado (F48).
    resultado = client.get(
        f"/expedientes/{con_errores.pk}/documentos/{borrador.pk}/resultado/"
    ).content.decode()
    assert resultado.count('<li data-id="') == 4


def test_lista_resuelve_los_errores_en_bloque(
    client, usuario_ficticio, crear_documento_listo
):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    def consultas_de_corridas():
        with CaptureQueriesContext(connection) as capturadas:
            client.get("/expedientes/")
        return sum('"expedientes_corrida"' in q["sql"] for q in capturadas)

    client.force_login(usuario_ficticio)
    _confrontado(crear_documento_listo, usuario_ficticio, "KDX-F59-Q1")
    una = consultas_de_corridas()
    for codigo in ("KDX-F59-Q2", "KDX-F59-Q3", "KDX-F59-Q4"):
        _confrontado(crear_documento_listo, usuario_ficticio, codigo)

    assert consultas_de_corridas() == una <= 2


def test_lista_tv_y_archivados_muestran_los_errores(
    client, usuario_ficticio, administrador_ficticio, crear_documento_listo
):
    from django.utils import timezone

    _confrontado(
        crear_documento_listo,
        usuario_ficticio,
        "TV-F59-A",
        tipo="VEHICULAR",
        regla=[{"campo": "PLACA"}],
    )
    archivado, _ = _confrontado(
        crear_documento_listo,
        usuario_ficticio,
        "KDX-F59-ARCH",
        regla=[{"campo": "DNI"}, {"campo": "NOMBRE"}],
    )
    archivado.archivado_el = timezone.now()
    archivado.save()
    client.force_login(administrador_ficticio)

    vehicular = client.get("/expedientes/vehicular/").content.decode()
    archivados = client.get("/expedientes/?archivados=1").content.decode()

    assert ">Errores</th>" in vehicular
    assert "<td>1</td>" in _fila(vehicular, "TV-F59-A")
    assert ">Errores</th>" in archivados
    assert "<td>2</td>" in _fila(archivados, "KDX-F59-ARCH")


def test_actualizado_es_la_hora_del_ultimo_documento_procesado_y_ordena(
    client, usuario_ficticio
):
    from datetime import datetime

    from django.utils import timezone

    from expedientes.models import Documento, Expediente

    def kardex(codigo, procesados=()):
        expediente = Expediente.objects.create(
            codigo=codigo, creado_por=usuario_ficticio
        )
        for indice, procesado_el in enumerate((*procesados, None)):
            Documento.objects.create(
                expediente=expediente,
                rol=Documento.CLIENTE,
                nombre_original=f"recaudo-{indice}.txt",
                hash_archivo=f"{codigo}{indice}".lower().ljust(64, "0"),
                tamano_bytes=4,
                estado=Documento.LISTO if procesado_el else Documento.PENDIENTE,
                procesado_el=procesado_el,
                subido_por=usuario_ficticio,
            )
        return expediente

    def hora(*partes):
        return timezone.make_aware(datetime(*partes))

    marzo = kardex("KDX-F59-MARZO", [hora(2026, 3, 1, 8, 0), hora(2026, 3, 2, 9, 5)])
    junio = kardex("KDX-F59-JUNIO", [hora(2026, 6, 1, 17, 45)])
    sin_procesar = kardex("KDX-F59-MAYO")
    Expediente.objects.filter(pk=sin_procesar.pk).update(
        actualizado_el=hora(2026, 5, 1, 12, 0)
    )
    marzo.save()  # editar el kardex no cambia la hora de sus documentos
    client.force_login(usuario_ficticio)

    respuesta = client.get("/expedientes/")

    codigos = [e.codigo for e, _ in respuesta.context["expedientes"]]
    assert codigos == ["KDX-F59-JUNIO", "KDX-F59-MAYO", "KDX-F59-MARZO"]
    contenido = respuesta.content.decode()
    for expediente, esperada in (
        (marzo, hora(2026, 3, 2, 9, 5)),
        (junio, hora(2026, 6, 1, 17, 45)),
        (sin_procesar, hora(2026, 5, 1, 12, 0)),
    ):
        fila = _fila(contenido, expediente.codigo)
        assert f'data-t="{int(esperada.timestamp())}"' in fila
        assert esperada.strftime("%d/%m/%Y %H:%M") in fila
