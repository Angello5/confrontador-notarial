"""F53: Inicio del administrador y avisos de documento ilegible."""

import json
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


def _corrida(expediente, usuario, cuando, observaciones=(), borrador="a", estado=None):
    """Corrida ficticia; `observaciones` son pares (lista, tipo) del manifiesto."""
    from expedientes.models import Corrida
    from expedientes.services import severidad

    hallazgos = {"personas": [], "regla": [], "ortografia": [], "estado": "RESULTADO"}
    for lista, tipo in observaciones:
        clave = {"personas": "tipo", "regla": "campo"}.get(lista)
        fila = {clave: tipo} if clave else {}
        tipo_catalogo = "ORTOGRAFIA" if lista == "ortografia" else tipo
        hallazgos[lista].append({**fila, "severidad": severidad(tipo_catalogo)})
    # creado_el es auto_now_add y la corrida es inmutable: se fija la hora.
    with mock.patch("django.utils.timezone.now", return_value=cuando):
        return Corrida.objects.create(
            expediente=expediente,
            id_borrador=1,
            hash_borrador=borrador * 64,
            entradas=[{"hash_archivo": borrador * 64, "hash_texto": "c" * 64}],
            version_catalogo="v-ficticia",
            version_software="0.0.0",
            usuario=usuario,
            fecha_referencia="2026-01-01",
            estado=estado or Corrida.RESULTADO,
            hallazgos=json.dumps(hallazgos),
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

    respuesta = client.get(reverse("home"))

    # US4: la pantalla se pinta con Alpine a partir de estos datos iniciales.
    datos = respuesta.context["datos_inicio"]
    content = respuesta.content.decode()
    assert 'id="datos-inicio"' in content
    assert 'aria-label="Últimas confrontaciones"' in content
    assert len(datos["actividad"]) == 12
    assert datos["confrontaciones"] == [
        {
            "codigo": "EXP-FICTICIO-C1",
            "tipo": "Transferencia vehicular",
            "usuario": "usuario_ficticio",
            "fecha": "14/10/2026 09:00",
            "url": f"/expedientes/{expediente.pk}/",
        }
    ]
    assert "ficticio-" not in content
    assert "hash" not in content.lower()
    assert Corrida.objects.filter(pk=corrida.pk).exists()


def test_inicio_de_administrador_sin_confrontaciones_lo_explica(
    client, administrador_ficticio
):
    client.force_login(administrador_ficticio)

    respuesta = client.get(reverse("home"))

    assert "Aún no hay confrontaciones" in respuesta.content.decode()
    assert respuesta.context["datos_inicio"]["confrontaciones"] == []
    assert all(s["kardex"] == 0 for s in respuesta.context["datos_inicio"]["actividad"])


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


# --- US4: por semana o por mes, con datos al día ----------------------------


def test_actividad_mensual_del_anio_en_curso_en_hora_de_lima(usuario_ficticio):
    from expedientes.services import actividad_mensual

    a = _expediente("EXP-FICTICIO-M1", usuario_ficticio)
    b = _expediente("EXP-FICTICIO-M2", usuario_ficticio)
    _corrida(a, usuario_ficticio, datetime(2026, 3, 2, 9, tzinfo=LIMA))
    _corrida(a, usuario_ficticio, datetime(2026, 3, 20, 9, tzinfo=LIMA))
    # 31/03 23:30 en Lima ya es abril en UTC: debe contar en marzo.
    _corrida(b, usuario_ficticio, datetime(2026, 3, 31, 23, 30, tzinfo=LIMA))
    _corrida(b, usuario_ficticio, datetime(2026, 10, 1, 9, tzinfo=LIMA))
    _corrida(b, usuario_ficticio, datetime(2025, 12, 20, 9, tzinfo=LIMA))  # otro año

    actividad = actividad_mensual(hoy=date(2026, 10, 14))

    assert [mes["inicio"] for mes in actividad] == [
        date(2026, numero, 1) for numero in range(1, 11)
    ]
    por_mes = {mes["inicio"].month: mes["kardex"] for mes in actividad}
    assert por_mes[3] == 2
    assert por_mes[10] == 1
    assert sum(por_mes.values()) == 3


def test_rango_de_cada_periodo():
    from expedientes.services import rango_periodo

    desde, hasta = rango_periodo("semana", date(2026, 10, 14))
    assert desde == datetime(2026, 7, 27, tzinfo=LIMA)
    assert hasta == datetime(2026, 10, 19, tzinfo=LIMA)
    desde, hasta = rango_periodo("mes", date(2026, 10, 14))
    assert desde == datetime(2026, 1, 1, tzinfo=LIMA)
    assert hasta == datetime(2026, 11, 1, tzinfo=LIMA)


def test_datos_del_inicio_en_json_solo_para_el_administrador(
    client, usuario_ficticio, administrador_ficticio
):
    expediente = _expediente("EXP-FICTICIO-J1", usuario_ficticio)
    _corrida(expediente, usuario_ficticio, datetime(2026, 10, 14, 9, tzinfo=LIMA))
    url = reverse("home_datos")

    assert client.get(url).status_code == 302  # anónimo: al login
    client.force_login(usuario_ficticio)
    assert client.get(url).status_code == 403
    client.force_login(administrador_ficticio)
    assert client.post(url).status_code == 405

    ahora = datetime(
        2026, 10, 20, 15, 30, tzinfo=LIMA
    )  # congelado: el mes no depende de hoy
    with mock.patch("django.utils.timezone.now", return_value=ahora):
        datos = client.get(url, {"periodo": "mes"}).json()
    assert datos["periodo"] == "mes"
    assert set(datos) >= {
        "cifras",
        "actividad",
        "confrontaciones",
        "indicadores",
        "periodo",
        "actualizado",
    }
    octubre = datos["actividad"][-1]
    assert octubre["etiqueta"] == "Oct"
    assert octubre["kardex"] == 1
    assert octubre["alto"] == 100
    assert octubre["explicacion"] == "1 kardex confrontado en octubre de 2026"
    assert client.get(url, {"periodo": "x"}).json()["periodo"] == "semana"
    semana = client.get(url).json()["actividad"][-1]
    assert semana["explicacion"].endswith(f"en la semana del {semana['etiqueta']}")


# --- US5: indicadores de calidad ---------------------------------------------


def test_indicadores_de_calidad_atribuyen_al_creador_sin_duplicar(
    usuario_ficticio, administrador_ficticio
):
    from expedientes.models import DecisionCorreccion
    from expedientes.services import indicadores_calidad, rango_periodo

    usuario_ficticio.first_name, usuario_ficticio.last_name = "Ana", "Prueba"
    usuario_ficticio.save()
    cuando = datetime(2026, 10, 14, 9, tzinfo=LIMA)
    de_ana = _expediente("EXP-FICTICIO-Q1", usuario_ficticio)
    obs = [("regla", "DNI"), ("regla", "DNI"), ("regla", "MONTO"), ("ortografia", "x")]
    # Confronta el administrador, pero el kardex es de Ana: cuenta para Ana.
    primera = _corrida(de_ana, administrador_ficticio, cuando, obs)
    _corrida(de_ana, usuario_ficticio, cuando, obs)  # mismos archivos: no suma
    _corrida(de_ana, usuario_ficticio, cuando, [("regla", "DNI")], borrador="d")
    del_admin = _expediente("EXP-FICTICIO-Q2", administrador_ficticio)
    _corrida(del_admin, administrador_ficticio, cuando, [("personas", "SIN_FICHA")])
    sin_resultado = _expediente("EXP-FICTICIO-Q3", administrador_ficticio)
    _corrida(sin_resultado, administrador_ficticio, cuando, estado="ERROR")
    _corrida(
        del_admin,
        administrador_ficticio,
        datetime(2026, 1, 5, tzinfo=LIMA),
        [("regla", "PARTIDA")],
        borrador="e",
    )  # fuera de las 12 semanas
    # creado_el es auto_now_add y la decisión es inmutable: se fija la hora;
    # con la de hoy la prueba falla en cuanto la semana del 14 queda atrás.
    with mock.patch("django.utils.timezone.now", return_value=cuando):
        DecisionCorreccion.objects.create(
            corrida=primera,
            usuario=usuario_ficticio,
            apariciones={"c1": 1, "c2": 2},
            hash_corregido="f" * 64,
        )
        DecisionCorreccion.objects.create(corrida=primera, usuario=usuario_ficticio)

    ind = indicadores_calidad(*rango_periodo("semana", date(2026, 10, 14)))

    assert ind["gravedad"] == {"ALTA": 4, "MEDIA": 1, "BAJA": 1}
    assert ind["usuarias"] == [
        {
            "puesto": 1,
            "usuario": "Ana Prueba",
            "kardex": 1,
            "observaciones": 5,
            "altas": 4,
            "medias": 0,
            "bajas": 1,
            "promedio": 5.0,
            "ancho": 100,
        },
        {
            "puesto": 2,
            "usuario": "administrador_ficticio",
            "kardex": 2,
            "observaciones": 1,
            "altas": 0,
            "medias": 1,
            "bajas": 0,
            "promedio": 0.5,
            "ancho": 20,
        },
    ]
    assert [f["tipo"] for f in ind["frecuentes"]] == [
        "DNI",
        "MONTO",
        "ORTOGRAFIA",
        "SIN_FICHA",
    ]
    assert ind["frecuentes"][0]["cantidad"] == 3
    assert ind["frecuentes"][0]["descripcion"].startswith("DNI del borrador")
    assert ind["frecuentes"][0]["ancho"] == 100
    assert ind["correcciones"] == {"documentos": 1, "aplicadas": 2}

    mes = indicadores_calidad(*rango_periodo("mes", date(2026, 10, 14)))
    assert mes["gravedad"]["ALTA"] == 5  # suma la PARTIDA de enero


def test_indicadores_vacios_y_json_sin_datos_sensibles(
    client, usuario_ficticio, administrador_ficticio
):
    from expedientes.services import indicadores_calidad, rango_periodo

    vacio = indicadores_calidad(*rango_periodo("semana", date(2026, 10, 14)))
    assert vacio == {
        "gravedad": {"ALTA": 0, "MEDIA": 0, "BAJA": 0},
        "usuarias": [],
        "frecuentes": [],
        "correcciones": {"documentos": 0, "aplicadas": 0},
    }

    expediente = _expediente("EXP-FICTICIO-S1", usuario_ficticio)
    _documento(expediente, usuario_ficticio, "LISTO")
    _corrida(
        expediente,
        usuario_ficticio,
        datetime(2026, 10, 14, tzinfo=LIMA),
        [("regla", "DNI")],
    )
    client.force_login(administrador_ficticio)
    for respuesta in (client.get(reverse("home")), client.get(reverse("home_datos"))):
        texto = respuesta.content.decode()
        assert "ficticio-0.txt" not in texto
        assert "hash" not in texto.lower()

    client.force_login(usuario_ficticio)
    respuesta = client.get(reverse("home"))
    assert 'id="datos-inicio"' not in respuesta.content.decode()
    assert "datos_inicio" not in respuesta.context


def test_corrida_sin_observaciones_legibles_cuenta_el_kardex_sin_sumar_errores(
    usuario_ficticio,
):
    from expedientes.models import Corrida
    from expedientes.services import indicadores_calidad, rango_periodo

    expediente = _expediente("EXP-FICTICIO-L1", usuario_ficticio)
    with mock.patch(
        "django.utils.timezone.now",
        return_value=datetime(2026, 10, 14, tzinfo=LIMA),
    ):
        Corrida.objects.create(
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

    ind = indicadores_calidad(*rango_periodo("semana", date(2026, 10, 14)))

    assert ind["usuarias"][0]["kardex"] == 1
    assert ind["usuarias"][0]["observaciones"] == 0
    assert ind["gravedad"] == {"ALTA": 0, "MEDIA": 0, "BAJA": 0}


# --- F57: ranking de errores por digitadora y versión imprimible ------------


def _digitadora(nombre):
    """Usuaria ficticia del rol Usuario."""
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    usuaria = get_user_model().objects.create_user(
        username=f"digitadora_{nombre.lower()}",
        first_name=nombre,
        last_name="Ficticia",
    )
    usuaria.groups.add(Group.objects.get(name="Usuario"))
    return usuaria


def test_ranking_ordena_por_total_y_cuenta_a_todas_las_digitadoras(
    administrador_ficticio,
):
    from expedientes.services import indicadores_calidad, rango_periodo

    cuando = datetime(2026, 10, 14, 9, tzinfo=LIMA)
    alta, media, baja = ("regla", "DNI"), ("personas", "SIN_FICHA"), ("ortografia", "x")
    errores = {  # digitadora: observaciones de cada kardex que creó
        "Bea": [[alta] * 4],  # más altas y mayor promedio, pero menos total
        "Ceci": [[baja] * 3, [baja] * 2],
        "Dora": [[media] * 2],
        "Eva": [[alta, baja]],  # empata con Dora
        "Flor": [[]],  # confrontó sin errores: también figura
        "Gina": [[media]],
        "Hilda": [[alta]],  # empata con Gina
    }
    kardex = {}
    for nombre, por_kardex in errores.items():
        autora = _digitadora(nombre)
        for numero, observaciones in enumerate(por_kardex):
            expediente = _expediente(f"EXP-FICTICIO-{nombre}{numero}", autora)
            kardex[nombre, numero] = expediente
            # Confronta el administrador: cuenta para quien creó el kardex.
            _corrida(expediente, administrador_ficticio, cuando, observaciones)
    # Confrontar de nuevo con los mismos archivos no suma dos veces.
    _corrida(kardex["Ceci", 0], administrador_ficticio, cuando, [baja] * 3)
    # Quien solo confrontó fuera del periodo no figura.
    fuera = _expediente("EXP-FICTICIO-Ines0", _digitadora("Ines"))
    _corrida(fuera, administrador_ficticio, datetime(2026, 1, 5, tzinfo=LIMA), [alta])

    ranking = indicadores_calidad(*rango_periodo("semana", date(2026, 10, 14)))[
        "usuarias"
    ]

    filas = [(p["puesto"], p["usuario"], p["observaciones"]) for p in ranking]
    assert filas == [
        (1, "Ceci Ficticia", 5),
        (2, "Bea Ficticia", 4),
        (3, "Dora Ficticia", 2),
        (3, "Eva Ficticia", 2),
        (5, "Gina Ficticia", 1),
        (5, "Hilda Ficticia", 1),
        (7, "Flor Ficticia", 0),
    ]
    ceci, bea = ranking[0], ranking[1]
    assert (ceci["kardex"], ceci["bajas"], ceci["promedio"]) == (2, 5, 2.5)
    assert (bea["altas"], bea["medias"], bea["bajas"], bea["promedio"]) == (
        4,
        0,
        0,
        4.0,
    )
    assert all(
        p["altas"] + p["medias"] + p["bajas"] == p["observaciones"] for p in ranking
    )
    assert ranking[-1]["promedio"] == 0.0
    assert "administrador_ficticio" not in {p["usuario"] for p in ranking}


def test_ranking_e_impresion_solo_para_el_administrador(
    client, usuario_ficticio, administrador_ficticio
):
    expediente = _expediente("EXP-FICTICIO-R1", usuario_ficticio)
    _corrida(expediente, usuario_ficticio, datetime(2026, 10, 14, tzinfo=LIMA))
    exclusivos = (
        "Errores por digitadora",
        "Imprimir o guardar PDF",
        "Ranking de errores por digitadora",
    )

    assert client.get(reverse("home")).status_code == 302  # anónimo: al login
    client.force_login(usuario_ficticio)
    content = client.get(reverse("home")).content.decode()
    assert not any(texto in content for texto in exclusivos)
    assert client.get(reverse("home_datos")).status_code == 403

    client.force_login(administrador_ficticio)
    content = client.get(reverse("home")).content.decode()
    assert all(texto in content for texto in exclusivos)
    assert '<th scope="col" class="num" data-sev="ALTA">Alta</th>' in content
    assert '<th scope="row" x-text="persona.usuario"></th>' in content


def test_version_imprimible_lleva_marca_periodo_y_fecha(
    client, administrador_ficticio, settings
):
    settings.ERP_NOMBRE = "Notaría Ficticia"
    settings.ERP_LOGO = "/static/img/logo-ficticio.png"
    client.force_login(administrador_ficticio)
    ahora = datetime(2026, 10, 20, 15, 30, tzinfo=LIMA)

    with mock.patch("django.utils.timezone.now", return_value=ahora):
        content = client.get(reverse("home")).content.decode()
        mes = client.get(reverse("home_datos"), {"periodo": "mes"}).json()

    inicio = content.index('<header class="solo-impresion reporte')
    impresion = content[inicio : content.index("</header>", inicio)]
    assert '<img class="marca-logo" src="/static/img/logo-ficticio.png"' in impresion
    assert "Notaría Ficticia" in impresion
    assert "Ranking de errores por digitadora" in impresion
    assert "del 03/08/2026 al 20/10/2026" in impresion
    assert '<span x-text="datos.fecha">20/10/2026</span>' in impresion
    assert '<span x-text="datos.actualizado">15:30</span>' in impresion
    assert 'onclick="window.print()"' in content
    assert (mes["rango"], mes["fecha"]) == (
        "del 01/01/2026 al 20/10/2026",
        "20/10/2026",
    )


# --- F73: barra de filtros --------------------------------------------------


def _ahora_menos(dias):
    from datetime import timedelta

    from django.utils import timezone

    return timezone.now() - timedelta(days=dias)


def _dos_personas(usuario, administrador):
    propio = _expediente("EXP-FICTICIO-F1", usuario)
    _corrida(propio, usuario, _ahora_menos(0), [("regla", "DNI")])
    ajeno = _expediente("EXP-FICTICIO-F2", administrador)
    _corrida(ajeno, administrador, _ahora_menos(1), [("regla", "DNI")], borrador="d")


def test_f73_el_filtro_de_periodo_acota_calidad_y_ultimas_no_los_totales(
    client, usuario_ficticio, administrador_ficticio
):
    _dos_personas(usuario_ficticio, administrador_ficticio)
    client.force_login(administrador_ficticio)

    hoy = client.get(reverse("home_datos"), {"filtro": "hoy"}).json()
    ayer = client.get(reverse("home_datos"), {"filtro": "ayer"}).json()

    assert hoy["filtro"] == "hoy"
    assert hoy["desde"] == hoy["hasta"] == hoy["hoy"]
    assert [fila["codigo"] for fila in hoy["confrontaciones"]] == ["EXP-FICTICIO-F1"]
    assert [p["usuario"] for p in hoy["indicadores"]["usuarias"]] == [
        "usuario_ficticio"
    ]
    assert [fila["codigo"] for fila in ayer["confrontaciones"]] == ["EXP-FICTICIO-F2"]
    assert hoy["cifras"] == ayer["cifras"]
    assert hoy["cifras"]["total"] == 2
    # La actividad conserva sus 12 semanas y resalta las del periodo.
    assert len(hoy["actividad"]) == 12
    assert hoy["actividad"][-1]["dentro"] is True
    assert hoy["actividad"][0]["dentro"] is False
    assert "dentro del periodo elegido" in hoy["actividad"][-1]["explicacion"]


def test_f73_el_rango_incluye_sus_dos_extremos(
    client, usuario_ficticio, administrador_ficticio
):
    from django.utils import timezone

    _dos_personas(usuario_ficticio, administrador_ficticio)
    client.force_login(administrador_ficticio)
    dia = timezone.localdate().isoformat()

    datos = client.get(
        reverse("home_datos"), {"filtro": "rango", "desde": dia, "hasta": dia}
    ).json()

    assert datos["filtro"] == "rango"
    assert [fila["codigo"] for fila in datos["confrontaciones"]] == ["EXP-FICTICIO-F1"]
    assert datos["rango"].startswith("el ")


@pytest.mark.parametrize(
    "consulta",
    [
        {"filtro": "siempre"},
        {"filtro": "rango"},
        {"filtro": "rango", "desde": "no-es-fecha", "hasta": "2026-01-01"},
        {"filtro": "rango", "desde": "2026-02-01", "hasta": "2026-01-01"},
    ],
)
def test_f73_un_filtro_no_valido_se_ignora_y_lo_dice(
    client, administrador_ficticio, consulta
):
    client.force_login(administrador_ficticio)

    datos = client.get(reverse("home_datos"), consulta).json()

    assert datos["filtro"] is None
    assert (datos["desde"], datos["hasta"]) == ("", "")
    assert datos["titulo_periodo"] == "las últimas 12 semanas"


def test_f73_la_persona_es_quien_creo_el_kardex_y_acota_los_indicadores(
    client, usuario_ficticio, administrador_ficticio
):
    _dos_personas(usuario_ficticio, administrador_ficticio)
    client.force_login(administrador_ficticio)

    todas = client.get(reverse("home_datos")).json()
    assert {p["nombre"] for p in todas["personas"]} == {
        "usuario_ficticio",
        administrador_ficticio.username,
    }
    assert todas["usuario"] is None

    datos = client.get(reverse("home_datos"), {"usuario": usuario_ficticio.pk}).json()

    assert datos["usuario"] == usuario_ficticio.pk
    assert datos["persona"] == "usuario_ficticio"
    assert [fila["codigo"] for fila in datos["confrontaciones"]] == ["EXP-FICTICIO-F1"]
    assert [p["usuario"] for p in datos["indicadores"]["usuarias"]] == [
        "usuario_ficticio"
    ]
    assert sum(t["kardex"] for t in datos["actividad"]) == 1
    # Elegir un periodo no borra a la persona de la lista.
    assert len(datos["personas"]) == 2


@pytest.mark.parametrize("persona", ["no-es-id", "999999"])
def test_f73_una_persona_no_valida_se_ignora(client, administrador_ficticio, persona):
    client.force_login(administrador_ficticio)

    datos = client.get(reverse("home_datos"), {"usuario": persona}).json()

    assert datos["usuario"] is None
    assert datos["persona"] == ""


def test_f73_filtrar_sigue_siendo_solo_del_administrador(client, usuario_ficticio):
    client.force_login(usuario_ficticio)

    respuesta = client.get(reverse("home_datos"), {"filtro": "hoy"})

    assert respuesta.status_code == 403


def test_f73_el_inicio_pinta_la_barra_de_filtros(client, administrador_ficticio):
    client.force_login(administrador_ficticio)

    content = client.get(reverse("home")).content.decode()

    assert 'aria-label="Filtros de los indicadores"' in content
    assert "Calidad de la confrontación" in content
    assert "no dependen del periodo" in content
    assert 'aria-label="Agrupar actividad"' in content
