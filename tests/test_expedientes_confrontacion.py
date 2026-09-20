"""Contrato de confrontacion F5 con datos completamente ficticios."""

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


@pytest.fixture
def expediente_confrontacion(usuario_ficticio):
    from expedientes.models import Expediente

    return Expediente.objects.create(
        codigo="EXP-FICTICIO-F5", creado_por=usuario_ficticio
    )


@pytest.fixture
def crear_documento_listo(usuario_ficticio):
    from expedientes.models import Documento, TextoExtraido

    def crear(expediente, rol, nombre, texto, *, estado=Documento.LISTO):
        extraido = TextoExtraido.objects.create(
            hash_archivo=(nombre.replace(".", "")[:64]).ljust(64, "0"),
            version_extractor="extractor-ficticio-v1",
            texto=texto,
            ultimo_uso_el=timezone.now(),
        )
        return Documento.objects.create(
            expediente=expediente,
            rol=rol,
            nombre_original=nombre,
            hash_archivo=extraido.hash_archivo,
            tamano_bytes=max(len(texto), 1),
            estado=estado,
            texto_extraido=extraido,
            subido_por=usuario_ficticio,
        )

    return crear


def test_precondiciones_no_confrontan_texto_vacio_ni_documento_no_listo(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "",
    )
    llamadas = []
    monkeypatch.setattr(
        "expedientes.services.verificar.diagnostico",
        lambda *args: llamadas.append(args),
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "NO_DISPONIBLE"
    assert llamadas == []


def test_orquestacion_conserva_nombres_extensiones_y_umbral(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.FUENTE,
        "minuta-ficticia.txt",
        "fuente de texto ficticia",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.FUENTE,
        "identidad-ficticia.jpg",
        "fuente de identidad ficticia",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "borrador de texto ficticio",
    )
    llamadas = {"catalogo": [], "diagnostico": [], "revisar": [], "parrafos": []}
    monkeypatch.setattr(
        "expedientes.services.verificar.catalogo",
        lambda fuentes: (
            llamadas["catalogo"].append(fuentes)
            or {"NOMBRE": set(), "DNI": set(), "PARTIDA": set(), "MONTO": set()}
        ),
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.diagnostico",
        lambda fuentes, texto: llamadas["diagnostico"].append((fuentes, texto)) or None,
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar",
        lambda cat, texto, umbral: (
            llamadas["revisar"].append(umbral)
            or ["[DNI] «90000002» no coincide con ninguna fuente"]
        ),
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar_parrafos",
        lambda minutas, texto, umbral: (
            llamadas["parrafos"].append((minutas, umbral))
            or ["[PARRAFO] falta: fragmento ficticio…"]
        ),
    )
    monkeypatch.setattr(
        "expedientes.services.diccionario.diccionario", lambda: (None, [])
    )
    monkeypatch.setattr("expedientes.services.diccionario.lista_casa", lambda: set())
    monkeypatch.setattr("expedientes.services.ortografia.revisar", lambda *args: [])
    documentos_antes = Documento.objects.count()

    resultado = confrontar_borrador(expediente_confrontacion, borrador)
    repetido = confrontar_borrador(expediente_confrontacion, borrador)

    assert set(llamadas["catalogo"][0]) == {
        "minuta-ficticia.txt",
        "identidad-ficticia.jpg",
    }
    assert set(llamadas["diagnostico"][0][0]) == set(llamadas["catalogo"][0])
    assert llamadas["parrafos"] == [(["fuente de texto ficticia"], 88)] * 2
    assert llamadas["revisar"] == [88] * 2
    assert [item["campo"] for item in resultado["regla"]] == ["DNI", "PARRAFO"]
    assert resultado["ortografia"] == []
    assert repetido == resultado
    assert Documento.objects.count() == documentos_antes


def test_orquestacion_pasa_nombres_del_catalogo_a_ortografia(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.FUENTE,
        "fuente-ficticia.txt",
        "fuente ficticia",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "borrador ficticio",
    )
    propios = []
    cat = {"NOMBRE": {"LUCAS PEREZ"}, "DNI": set(), "PARTIDA": set(), "MONTO": set()}
    monkeypatch.setattr("expedientes.services.verificar.catalogo", lambda _: cat)
    monkeypatch.setattr("expedientes.services.verificar.diagnostico", lambda *_: None)
    monkeypatch.setattr("expedientes.services.verificar.revisar", lambda *_: [])
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar_parrafos", lambda *_: []
    )
    monkeypatch.setattr(
        "expedientes.services.diccionario.diccionario", lambda: (None, [])
    )
    monkeypatch.setattr("expedientes.services.diccionario.lista_casa", lambda: set())
    monkeypatch.setattr(
        "expedientes.services.ortografia.revisar",
        lambda texto, diccionario, lemas, lista, extra: (
            propios.append(extra) or [("palabraficticia", "motivo ficticio", "?")]
        ),
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert propios == [{"LUCAS", "PEREZ"}]
    assert resultado["ortografia"] == [
        {
            "palabra": "palabraficticia",
            "motivo": "motivo ficticio",
            "sugerencia": "Sin sugerencia",
            "ubicacion": {"linea": None, "fragmento": "No ubicada"},
        }
    ]


def test_diagnostico_bloqueante_detiene_toda_ejecucion(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.FUENTE,
        "fuente-ficticia.txt",
        "fuente ficticia",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "borrador ficticio",
    )
    llamadas = []
    monkeypatch.setattr(
        "expedientes.services.verificar.diagnostico", lambda *_: "aviso ficticio"
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.catalogo",
        lambda *_: llamadas.append("catalogo"),
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar", lambda *_: llamadas.append("regla")
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar_parrafos",
        lambda *_: llamadas.append("parrafos"),
    )
    monkeypatch.setattr(
        "expedientes.services.ortografia.revisar",
        lambda *_: llamadas.append("ortografia"),
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "ADVERTENCIA_CORRESPONDENCIA"
    assert resultado["mensaje"] == "aviso ficticio"
    assert llamadas == []


def test_confrontacion_real_detecta_dni_nombre_y_monto_alterados(
    expediente_confrontacion, crear_documento_listo
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    fuente = (
        "OPERACION FICTICIA DE PRUEBA.\n"
        "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001.\n"
        "PARTIDA ELECTRONICA N° 80000001. MONTO S/ 12,345.67.\n"
        "Esta clausula adicional describe una operacion completamente inventada "
        "para que el texto tenga el contexto habitual de un documento."
    )
    borrador = fuente.replace("LUMARIA", "LUNARIA")
    borrador = borrador.replace("90000001", "90000002")
    borrador = borrador.replace("12,345.67", "12,346.67")
    crear_documento_listo(
        expediente_confrontacion,
        Documento.FUENTE,
        "fuente-ficticia.txt",
        fuente,
    )
    documento_borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        borrador,
    )

    resultado = confrontar_borrador(expediente_confrontacion, documento_borrador)

    assert resultado["estado"] == "RESULTADO"
    assert any(
        observacion["campo"] == "DNI"
        and observacion["hallado"] == "90000002"
        and observacion["esperado"] == "90000001"
        for observacion in resultado["regla"]
    )
    assert any(
        observacion["campo"] == "NOMBRE"
        and observacion["hallado"] == "ALBA ZURBELIA LUNARIA"
        and observacion["esperado"] == "ALBA ZURBELIA LUMARIA"
        for observacion in resultado["regla"]
    )
    assert any(
        observacion["campo"] == "MONTO"
        and observacion["hallado"] == "12,346.67"
        and observacion["esperado"] == "12,345.67"
        for observacion in resultado["regla"]
    )
    assert not any(
        observacion["campo"] == "PARTIDA" for observacion in resultado["regla"]
    )


def test_confrontacion_real_identica_no_produce_observaciones_de_regla(
    expediente_confrontacion, crear_documento_listo
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    texto = (
        "OPERACION FICTICIA.\n"
        "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001.\n"
        "PARTIDA ELECTRONICA N° 80000001. MONTO S/ 12,345.67."
    )
    crear_documento_listo(
        expediente_confrontacion, Documento.FUENTE, "fuente-ficticia.txt", texto
    )
    borrador = crear_documento_listo(
        expediente_confrontacion, Documento.BORRADOR, "borrador-ficticio.txt", texto
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "RESULTADO"
    assert resultado["regla"] == []


@pytest.mark.parametrize(
    ("salida", "campo", "hallado", "esperado"),
    [
        (
            "[DNI] «90000002» debe decir «90000001»",
            "DNI",
            "90000002",
            "90000001",
        ),
        (
            "[MONTO] «12,346.67» no coincide con ninguna fuente",
            "MONTO",
            "12,346.67",
            "No coincide con ninguna fuente",
        ),
        (
            "[PARTIDA] FALTA: «80000001» esta en las fuentes y no aparece en el destino",
            "PARTIDA",
            "No aparece en el borrador",
            "80000001",
        ),
        (
            "[PARRAFO] falta o alterado (87.50%): texto de fuente ficticia…",
            "PARRAFO",
            "No aparece o fue alterado",
            "texto de fuente ficticia…",
        ),
    ],
)
def test_parser_de_regla_devuelve_observacion_comun(salida, campo, hallado, esperado):
    from expedientes.services import parsear_observacion_regla

    observacion = parsear_observacion_regla(salida, "Línea sin el valor.")

    assert observacion["formato"] == "regla"
    assert observacion["campo"] == campo
    assert observacion["hallado"] == hallado
    assert observacion["esperado"] == esperado
    assert "ubicacion" in observacion


def test_ubicacion_normaliza_mayusculas_tildes_y_usa_la_primera_linea():
    from expedientes.services import ubicar_valor

    ubicacion = ubicar_valor(
        "Primera línea ficticia.\nLa Clausula útil aparece aquí.\nClausula repetida.",
        "cláusula",
    )

    assert ubicacion["linea"] == 2
    assert "Clausula útil" in ubicacion["fragmento"]
    assert len(ubicacion["fragmento"]) <= 160


def test_ubicacion_ausente_es_explicita_y_no_expone_texto_completo():
    from expedientes.services import ubicar_valor

    ubicacion = ubicar_valor("Texto ficticio breve.", "valor ausente ficticio")

    assert ubicacion == {"linea": None, "fragmento": "No ubicada"}


def test_ubicacion_de_valor_repetido_se_queda_en_una_sola_observacion():
    from expedientes.services import adaptar_observaciones_regla

    observaciones = adaptar_observaciones_regla(
        ["[DNI] «90000002» no coincide con ninguna fuente"],
        "DNI 90000002.\nOtra línea con DNI 90000002.",
    )

    assert len(observaciones) == 1
    assert observaciones[0]["ubicacion"]["linea"] == 1


def test_adaptador_de_ortografia_mapea_tupla_y_sugerencia_desconocida():
    from expedientes.services import adaptar_observaciones_ortografia

    observaciones = adaptar_observaciones_ortografia(
        [
            ("palabraficticia", "motivo ficticio", "?"),
            ("otrapalabra", "tilde mal puesta", "otra"),
        ],
        "Palabraficticia y otra palabra en una línea ficticia.",
    )

    assert observaciones[0]["palabra"] == "palabraficticia"
    assert observaciones[0]["motivo"] == "motivo ficticio"
    assert observaciones[0]["sugerencia"] == "Sin sugerencia"
    assert observaciones[0]["ubicacion"]["linea"] == 1
    assert observaciones[1]["sugerencia"] == "otra"


def test_contrato_parser_usa_salida_real_del_nucleo():
    from expedientes.services import adaptar_observaciones_regla
    from nucleo import verificar

    fuente = (
        "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001.\n"
        "PARTIDA ELECTRONICA N° 80000001. MONTO S/ 12,345.67.\n"
        "Esta cláusula larga y completamente ficticia describe una obligación "
        "notarial adicional para probar la comparación de párrafos con contexto "
        "suficiente."
    )
    borrador = (
        "ALBA ZURBELIA LUNARIA, DE NACIONALIDAD PERUANA. DNI 90000002.\n"
        "MONTO S/ 12,346.67.\n"
        "Esta cláusula larga y completamente ficticia describe un contenido "
        "notarial diferente para probar la comparación de párrafos con contexto "
        "alternativo."
    )
    catalogo = verificar.catalogo({"fuente-ficticia.txt": fuente})
    salidas = verificar.revisar(catalogo, borrador, 88)
    salidas += verificar.revisar_parrafos([fuente], borrador, 88)

    observaciones = adaptar_observaciones_regla(salidas, borrador)

    assert salidas
    assert len(observaciones) == len(salidas)
    assert all(item["formato"] == "regla" for item in observaciones)
    assert {item["campo"] for item in observaciones} >= {"DNI", "NOMBRE", "MONTO"}
    assert any(item["campo"] == "PARRAFO" for item in observaciones)


def test_contrato_parser_usa_salida_real_de_revisar_parrafos():
    from expedientes.services import adaptar_observaciones_regla
    from nucleo import verificar

    minuta = (
        "Este párrafo de minuta ficticia es suficientemente extenso y contiene "
        "texto notarial inventado para forzar una observación de comparación."
    )
    borrador = (
        "Este párrafo de borrador ficticio es suficientemente extenso y contiene "
        "contenido notarial alternativo para forzar una diferencia visible."
    )
    salidas = verificar.revisar_parrafos([minuta], borrador, 88)

    observaciones = adaptar_observaciones_regla(salidas, borrador)

    assert salidas
    assert len(observaciones) == len(salidas)
    assert all(item["formato"] == "regla" for item in observaciones)
    assert all(item["campo"] == "PARRAFO" for item in observaciones)


def test_diccionario_no_aprovisionado_devuelve_mensaje_controlado(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from adaptadores.diccionario import DiccionarioNoAprovisionado
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    texto = "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001."
    crear_documento_listo(
        expediente_confrontacion, Documento.FUENTE, "fuente-ficticia.txt", texto
    )
    borrador = crear_documento_listo(
        expediente_confrontacion, Documento.BORRADOR, "borrador-ficticio.txt", texto
    )

    def sin_diccionario():
        raise DiccionarioNoAprovisionado("recurso ausente")

    monkeypatch.setattr("expedientes.services.diccionario.diccionario", sin_diccionario)

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "NO_DISPONIBLE"
    assert "Falta aprovisionar el diccionario es_PE" in resultado["mensaje"]
    assert "recurso ausente" not in resultado["mensaje"]


def test_diccionario_no_aprovisionado_no_intenta_descargar(tmp_path, monkeypatch):
    import adaptadores.diccionario as recursos
    import urllib.request

    monkeypatch.setattr(recursos, "DIC", tmp_path / "es_PE")
    monkeypatch.setattr(
        urllib.request,
        "urlretrieve",
        lambda *_: pytest.fail("la carga no debe descargar recursos"),
    )
    recursos.diccionario.cache_clear()

    try:
        with pytest.raises(recursos.DiccionarioNoAprovisionado, match="aprovisionar"):
            recursos.diccionario()
    finally:
        recursos.diccionario.cache_clear()
