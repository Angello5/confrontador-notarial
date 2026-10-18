"""F53: Inicio del administrador y avisos de documento ilegible."""

from datetime import date, datetime
from unittest import mock
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

LIMA = ZoneInfo("America/Lima")


def _expediente(codigo, usuario, tipo="NOTARIAL", archivado=False):
    from django.utils import timezone

    from expedientes.models import Expediente

    return Expediente.objects.create(
        codigo=codigo,
        tipo=tipo,
        creado_por=usuario,
        archivado_el=timezone.now() if archivado else None,
        archivado_por=usuario if archivado else None,
    )


def _documento(expediente, usuario, estado):
    from expedientes.models import Documento

    indice = expediente.documentos.count()
    return Documento.objects.create(
        expediente=expediente,
        rol=Documento.CLIENTE,
        nombre_original=f"ficticio-{indice}.txt",
        hash_archivo=f"{expediente.codigo}{indice}".lower().ljust(64, "0")[:64],
        tamano_bytes=4,
        estado=estado,
        subido_por=usuario,
    )


def _corrida(expediente, usuario, cuando):
    from expedientes.models import Corrida

    # creado_el es auto_now_add y la corrida es inmutable: se fija la hora.
    with mock.patch("django.utils.timezone.now", return_value=cuando):
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


# --- US1: cifras por tipo ---------------------------------------------------


def _kardex_de_varios_tipos(usuario, administrador):
    vacio = _expediente("EXP-FICTICIO-N1", usuario)
    en_proceso = _expediente("EXP-FICTICIO-N2", usuario)
    _documento(en_proceso, usuario, "PROCESANDO")
    _documento(en_proceso, usuario, "ERROR")
    _expediente("EXP-FICTICIO-N3", administrador)
    _expediente("EXP-FICTICIO-V1", usuario, tipo="VEHICULAR")
    _expediente("EXP-FICTICIO-V2", administrador, tipo="VEHICULAR")
    _expediente("EXP-FICTICIO-ARCH", usuario, archivado=True)
    return vacio, en_proceso


def test_cifras_por_tipo_cuadran_y_respetan_visibilidad(
    usuario_ficticio, administrador_ficticio
):
    from expedientes.services import cifras_por_tipo

    _kardex_de_varios_tipos(usuario_ficticio, administrador_ficticio)

    cifras = cifras_por_tipo(administrador_ficticio)
    assert cifras == {"notariales": 3, "vehiculares": 2, "total": 5}
    assert cifras["total"] == cifras["notariales"] + cifras["vehiculares"]
    assert cifras_por_tipo(usuario_ficticio) == {
        "notariales": 2,
        "vehiculares": 1,
        "total": 3,
    }


def test_inicio_de_administrador_muestra_cifras_enlazadas_sin_paneles_retirados(
    client, usuario_ficticio, administrador_ficticio
):
    _kardex_de_varios_tipos(usuario_ficticio, administrador_ficticio)
    client.force_login(administrador_ficticio)

    respuesta = client.get(reverse("home"))

    assert respuesta.context["cifras"] == {
        "notariales": 3,
        "vehiculares": 2,
        "total": 5,
    }
    content = respuesta.content.decode()
    assert 'href="/expedientes/"' in content
    assert 'href="/expedientes/vehicular/"' in content
    for retirado in (
        "Procesando",
        "Con error",
        "Requieren su atención",
        "Acceso rápido",
        "Control administrativo",
        "Administrar usuarios",
    ):
        assert retirado not in content


def test_inicio_de_administrador_no_crece_en_consultas_con_los_kardex(
    client, usuario_ficticio, administrador_ficticio, django_assert_max_num_queries
):
    _kardex_de_varios_tipos(usuario_ficticio, administrador_ficticio)
    client.force_login(administrador_ficticio)
    client.get(reverse("home"))
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    with CaptureQueriesContext(connection) as pocas:
        client.get(reverse("home"))
    cuando = datetime(2026, 10, 14, 10, tzinfo=LIMA)
    for numero in range(30):
        expediente = _expediente(f"EXP-FICTICIO-Q{numero}", usuario_ficticio)
        _documento(expediente, usuario_ficticio, "LISTO")
        _corrida(expediente, usuario_ficticio, cuando)

    with django_assert_max_num_queries(len(pocas)):
        client.get(reverse("home"))


# --- US2: actividad semanal y últimas confrontaciones -----------------------


def test_actividad_semanal_cuenta_kardex_distintos_por_semana_de_lima(
    usuario_ficticio,
):
    from expedientes.services import actividad_semanal

    a = _expediente("EXP-FICTICIO-A", usuario_ficticio)
    b = _expediente("EXP-FICTICIO-B", usuario_ficticio)
    archivado = _expediente("EXP-FICTICIO-ARCH", usuario_ficticio, archivado=True)
    for dia in (12, 13, 14):  # tres corridas del mismo kardex en una semana
        _corrida(a, usuario_ficticio, datetime(2026, 10, dia, 9, tzinfo=LIMA))
    _corrida(b, usuario_ficticio, datetime(2026, 10, 13, 9, tzinfo=LIMA))
    # Domingo 23:30 en Lima ya es lunes en UTC: debe quedar en su semana.
    _corrida(b, usuario_ficticio, datetime(2026, 10, 11, 23, 30, tzinfo=LIMA))
    _corrida(archivado, usuario_ficticio, datetime(2026, 9, 29, 9, tzinfo=LIMA))
    _corrida(a, usuario_ficticio, datetime(2026, 7, 15, 9, tzinfo=LIMA))  # fuera

    actividad = actividad_semanal(hoy=date(2026, 10, 14))

    assert len(actividad) == 12
    assert actividad[0]["inicio"] == date(2026, 7, 27)
    assert actividad[-1]["inicio"] == date(2026, 10, 12)
    assert all(semana["inicio"].weekday() == 0 for semana in actividad)
    por_semana = {semana["inicio"]: semana["kardex"] for semana in actividad}
    assert por_semana[date(2026, 10, 12)] == 2
    assert por_semana[date(2026, 10, 5)] == 1
    assert por_semana[date(2026, 9, 28)] == 1
    assert sum(por_semana.values()) == 4


def test_ultimas_confrontaciones_un_kardex_por_fila_con_su_ultima_corrida(
    usuario_ficticio, administrador_ficticio
):
    from expedientes.services import ultimas_confrontaciones

    usuario_ficticio.first_name = "Ana"
    usuario_ficticio.last_name = "Prueba"
    usuario_ficticio.save()
    kardex = [
        _expediente(f"EXP-FICTICIO-K{numero}", usuario_ficticio) for numero in range(7)
    ]
    for numero, expediente in enumerate(kardex):
        _corrida(
            expediente, usuario_ficticio, datetime(2026, 10, 1 + numero, tzinfo=LIMA)
        )
    _corrida(kardex[0], administrador_ficticio, datetime(2026, 10, 10, tzinfo=LIMA))
    archivado = _expediente("EXP-FICTICIO-ARCH", usuario_ficticio, archivado=True)
    _corrida(archivado, usuario_ficticio, datetime(2026, 10, 12, tzinfo=LIMA))

    filas = ultimas_confrontaciones()

    assert [fila["expediente"].codigo for fila in filas] == [
        "EXP-FICTICIO-K0",
        "EXP-FICTICIO-K6",
        "EXP-FICTICIO-K5",
        "EXP-FICTICIO-K4",
        "EXP-FICTICIO-K3",
    ]
    assert filas[0]["usuario"] == "administrador_ficticio"
    assert filas[0]["fecha"] == datetime(2026, 10, 10, tzinfo=LIMA)
    assert filas[1]["usuario"] == "Ana Prueba"


def test_inicio_de_administrador_muestra_actividad_y_confrontaciones(
    client, usuario_ficticio, administrador_ficticio
):
    from expedientes.models import Corrida

    expediente = _expediente("EXP-FICTICIO-C1", usuario_ficticio, tipo="VEHICULAR")
    _documento(expediente, usuario_ficticio, "LISTO")
    corrida = _corrida(
        expediente, usuario_ficticio, datetime(2026, 10, 14, 9, tzinfo=LIMA)
    )
    client.force_login(administrador_ficticio)

    content = client.get(reverse("home")).content.decode()

    assert 'aria-label="Kardex confrontados por semana, últimas 12 semanas"' in content
    assert content.count('<li class="semana"') == 12
    assert 'aria-label="Últimas confrontaciones"' in content
    assert "EXP-FICTICIO-C1" in content
    assert "usuario_ficticio" in content
    assert "Transferencia vehicular" in content
    assert f'href="/expedientes/{expediente.pk}/"' in content
    assert "ficticio-" not in content
    assert "hash" not in content.lower()
    assert Corrida.objects.filter(pk=corrida.pk).exists()


def test_inicio_de_administrador_sin_confrontaciones_lo_explica(
    client, administrador_ficticio
):
    client.force_login(administrador_ficticio)

    content = client.get(reverse("home")).content.decode()

    assert "Aún no hay confrontaciones" in content
    assert content.count('<li class="semana"') == 12


# --- US3: aviso de documento ilegible para quien lo subió -------------------

AVISO = "Un documento que usted subió no se pudo leer"


def test_avisos_solo_de_lo_que_subio_cada_quien_y_sin_limite_de_antiguedad(
    usuario_ficticio, administrador_ficticio
):
    from expedientes.services import avisos_documentos_ilegibles

    antiguo = _expediente("EXP-FICTICIO-A0", usuario_ficticio)
    _documento(antiguo, usuario_ficticio, "ERROR")
    for numero in range(6):  # seis kardex más recientes que el antiguo
        reciente = _expediente(f"EXP-FICTICIO-R{numero}", usuario_ficticio)
        _documento(reciente, usuario_ficticio, "LISTO")
    doble = _expediente("EXP-FICTICIO-B1", usuario_ficticio)
    _documento(doble, usuario_ficticio, "ERROR")
    _documento(doble, usuario_ficticio, "ERROR")
    ajeno = _expediente("EXP-FICTICIO-C1", usuario_ficticio)
    _documento(ajeno, administrador_ficticio, "ERROR")
    archivado = _expediente("EXP-FICTICIO-D1", usuario_ficticio, archivado=True)
    _documento(archivado, usuario_ficticio, "ERROR")

    assert [e.codigo for e in avisos_documentos_ilegibles(usuario_ficticio)] == [
        "EXP-FICTICIO-A0",
        "EXP-FICTICIO-B1",
    ]
    assert [e.codigo for e in avisos_documentos_ilegibles(administrador_ficticio)] == [
        "EXP-FICTICIO-C1"
    ]


def test_inicio_avisa_a_quien_subio_el_documento_ilegible(
    client, usuario_ficticio, administrador_ficticio
):
    expediente = _expediente("EXP-FICTICIO-E1", usuario_ficticio)
    documento = _documento(expediente, usuario_ficticio, "ERROR")

    client.force_login(usuario_ficticio)
    content = client.get(reverse("home")).content.decode()
    assert AVISO in content
    assert "EXP-FICTICIO-E1" in content
    assert f'href="/expedientes/{expediente.pk}/"' in content
    assert "ficticio-0.txt" not in content
    assert "Requieren su atención" not in content

    client.force_login(administrador_ficticio)
    content = client.get(reverse("home")).content.decode()
    assert AVISO not in content
    assert "Requieren su atención" not in content

    propio = _expediente("EXP-FICTICIO-E2", administrador_ficticio)
    _documento(propio, administrador_ficticio, "ERROR")
    content = client.get(reverse("home")).content.decode()
    assert AVISO in content
    assert "EXP-FICTICIO-E2" in content
    assert "EXP-FICTICIO-E1" not in content

    documento.delete()
    client.force_login(usuario_ficticio)
    assert AVISO not in client.get(reverse("home")).content.decode()


def test_inicio_de_usuaria_no_muestra_datos_de_toda_la_notaria(
    client, usuario_ficticio, administrador_ficticio
):
    ajeno = _expediente("EXP-FICTICIO-AJENO", administrador_ficticio)
    _corrida(ajeno, administrador_ficticio, datetime(2026, 10, 14, tzinfo=LIMA))
    _expediente("EXP-FICTICIO-V1", usuario_ficticio, tipo="VEHICULAR")
    client.force_login(usuario_ficticio)

    respuesta = client.get(reverse("home"))

    content = respuesta.content.decode()
    for exclusivo in (
        "Últimas confrontaciones",
        "Actividad por semana",
        "Transferencias vehiculares",
        "EXP-FICTICIO-AJENO",
    ):
        assert exclusivo not in content
    for clave in ("cifras", "actividad", "confrontaciones"):
        assert clave not in respuesta.context
    assert "Nueva confrontación" in content
    assert "Listos para confrontar" in content
