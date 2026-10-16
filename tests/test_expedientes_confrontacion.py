"""Contrato de confrontacion F5 con datos completamente ficticios."""

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_persona_ampliada_se_presenta_con_procedencia_sin_ruta():
    from expedientes.services import _personas_legibles
    from nucleo.verificar import catalogo

    pagina = (
        "CUI: 90000011 - 5\nAPELLIDO PATERNO  LUMARIA\n"
        "APELLIDO MATERNO  ZAFIRO\nNOMBRES  ALBA\n"
        "ESTADO CIVIL  CASADA\nFECHA DE NACIMIENTO  03/07/1990\n"
        "DIRECCION  Av. Luna 12\nDISTRITO DE DOMICILIO  Miraflores"
    )
    filas = _personas_legibles(
        catalogo({"/srv/privado/reniec-ficticio.pdf": pagina}).personas
    )
    fila = filas[0]
    assert fila["estado_civil"] == "CASADO"
    assert fila["fecha_nacimiento"] == "1990-07-03"
    assert fila["domicilio"] == "Av. Luna 12"
    assert fila["distrito"] == "Miraflores"
    for campo in ("estado_civil", "fecha_nacimiento", "domicilio", "distrito"):
        assert fila[f"procedencia_{campo}"] == {
            "archivo": "reniec-ficticio.pdf",
            "pagina": 1,
        }
    assert "/srv/privado" not in str(fila)


def test_observaciones_f12_se_adaptan_a_regla_con_procedencia_segura():
    from datetime import date

    from expedientes.services import _observaciones_f12_legibles
    from nucleo.verificar import Procedencia

    observaciones = (
        {
            "tipo": "MENOR_DE_EDAD",
            "nombre": "ALBA LUMARIA ZAFIRO",
            "edad": 17,
            "fecha_referencia": date(2025, 7, 2),
            "esperado": date(2007, 7, 3),
            "hallado": "Menor de edad",
            "procedencia": Procedencia("/srv/privado/reniec-ficticio.pdf", 2),
        },
    )
    filas = _observaciones_f12_legibles(observaciones, "ALBA LUMARIA ZAFIRO")
    assert filas[0]["campo"] == "MENOR_DE_EDAD"
    assert "ALBA LUMARIA ZAFIRO" in filas[0]["hallado"]
    assert "17" in filas[0]["hallado"]
    assert "2025-07-02" in filas[0]["hallado"]
    assert "reniec-ficticio.pdf, página 2" in filas[0]["motivo"]
    assert "/srv/privado" not in str(filas)


def test_confrontacion_agrega_reglas_f12_solo_al_resultado_autorizado(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from datetime import date

    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    reniec = (
        "CUI: 90000011 - 5\nAPELLIDO PATERNO  LUMARIA\n"
        "APELLIDO MATERNO  ZAFIRO\nNOMBRES  ALBA\n"
        "ESTADO CIVIL  CASADA\nFECHA DE NACIMIENTO  03/07/2007\n"
        "DIRECCION  Av. Luna 12"
    )
    crear_documento_listo(
        expediente_confrontacion, Documento.CLIENTE, "reniec-ficticio.pdf", reniec
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.txt",
        "ALBA LUMARIA ZAFIRO",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "ALBA LUMARIA ZAFIRO, soltera, domiciliada en Calle Sol 8. DNI 90000011",
    )
    monkeypatch.setattr(
        "expedientes.services.timezone.localdate", lambda: date(2025, 7, 2)
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)
    assert resultado["estado"] == "RESULTADO"
    assert {fila["campo"] for fila in resultado["regla"]} >= {
        "ESTADO_CIVIL_DISCREPANTE",
        "MENOR_DE_EDAD",
        "DOMICILIO_NO_ENCONTRADO",
    }
    assert "17 años al 2025-07-02" in str(resultado["regla"])


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


@pytest.mark.parametrize(
    ("roles", "texto_faltante"),
    [
        (("MINUTA", "BORRADOR"), "Recaudos"),
        (("CLIENTE", "BORRADOR"), "Minuta"),
        (("CLIENTE", "MINUTA"), "Proyecto (borrador)"),
    ],
)
def test_estado_confrontacion_indica_el_rol_obligatorio_ausente(
    expediente_confrontacion, crear_documento_listo, roles, texto_faltante
):
    from expedientes.models import Documento
    from expedientes.services import estado_confrontacion

    documentos = [
        crear_documento_listo(
            expediente_confrontacion,
            getattr(Documento, rol),
            f"{rol.lower()}-ficticio.txt",
            f"texto {rol.lower()} ficticio",
        )
        for rol in roles
    ]
    borrador = next(
        (documento for documento in documentos if documento.rol == Documento.BORRADOR),
        None,
    )

    estado = estado_confrontacion(expediente_confrontacion, borrador)

    assert estado["disponible"] is False
    assert texto_faltante in estado["mensaje"]


def test_cliente_documento_de_texto_no_se_compara_como_parrafo(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "cliente-ficticio.txt",
        "texto de cliente ficticio",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.docx",
        "texto de minuta ficticia",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "texto de borrador ficticio",
    )
    llamadas = []
    monkeypatch.setattr("expedientes.services.verificar.diagnostico", lambda *_: None)
    monkeypatch.setattr(
        "expedientes.services.verificar.catalogo",
        lambda fuentes: {"NOMBRE": set()},
    )
    monkeypatch.setattr("expedientes.services.verificar.revisar", lambda *_: [])
    monkeypatch.setattr(
        "expedientes.services.verificar.anexos_omitidos",
        lambda minutas, *_: llamadas.append(minutas) or [],
    )

    confrontar_borrador(expediente_confrontacion, borrador)

    assert llamadas == [["texto de minuta ficticia"]]


def test_orquestacion_conserva_nombres_extensiones_y_umbral(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.txt",
        "fuente de texto ficticia",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
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
        lambda cat, texto, umbral, *_: (
            llamadas["revisar"].append(umbral)
            or ["[DNI] «90000002» no coincide con ninguna fuente"]
        ),
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.anexos_omitidos",
        lambda minutas, texto, umbral: (
            llamadas["parrafos"].append((minutas, umbral))
            or ["[ANEXO] FALTA: «ANEXO 1 FICTICIO»"]
        ),
    )
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
    assert [item["campo"] for item in resultado["regla"]] == ["DNI", "ANEXO"]
    assert resultado["ortografia"] == []
    assert repetido == resultado
    assert Documento.objects.count() == documentos_antes


class _DiccionarioFicticio:
    """Solo conoce el castellano común de los borradores ficticios."""

    COMUNES = {
        "dni",
        "compareciente",
        "nacionalidad",
        "peruana",
        "domicilio",
        "contrato",
    }

    def lookup(self, palabra):
        return palabra.lower() in self.COMUNES


_RENIEC_F23 = (
    "CUI: 90000011 - 5\nAPELLIDO PATERNO  LUMARIA\n"
    "APELLIDO MATERNO  ZAFIRO\nNOMBRES  ALBA\n"
    "DIRECCION  Av. Lunaria 12\nDISTRITO DE DOMICILIO  Olmedal"
)
_BORRADOR_F23 = (
    "COMPARECIENTE ALBA LUMARIO ZAFIRO, DE NACIONALIDAD PERUANA, DNI 90000011,\n"
    "DOMICILIO Av. Lunaria 12, Olmedal.\n"
    "LA CONTRATO DE DE CONTRATO palabraerrada"
)


def _expediente_f23(expediente, crear_documento_listo):
    from expedientes.models import Documento

    crear_documento_listo(expediente, Documento.CLIENTE, "reniec-f23.pdf", _RENIEC_F23)
    crear_documento_listo(
        expediente,
        Documento.MINUTA,
        "minuta-f23.docx",
        "ALBA LUMARIA ZAFIRO, DE NACIONALIDAD PERUANA, DNI 90000011.",
    )
    return crear_documento_listo(
        expediente, Documento.BORRADOR, "borrador-f23.txt", _BORRADOR_F23
    )


def test_capa_linguistica_informa_sin_tocar_datos_del_a3(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    """F23 FR-001, FR-002, FR-004, FR-005."""
    from expedientes.services import confrontar_borrador

    borrador = _expediente_f23(expediente_confrontacion, crear_documento_listo)
    monkeypatch.setattr(
        "expedientes.services.diccionario.diccionario",
        lambda: (_DiccionarioFicticio(), ["palabra"]),
    )
    monkeypatch.setattr("expedientes.services.diccionario.lista_casa", set)

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "RESULTADO"
    assert resultado["linguistico_aviso"] == ""
    assert any("LUMARIO" in fila["hallado"] for fila in resultado["regla"])
    filas = [(f["palabra"], f["motivo"]) for f in resultado["ortografia"]]
    # ni el nombre (ni su forma errada, que ya observa la regla) ni el domicilio
    assert filas == [
        ("palabraerrada", "no existe en castellano"),
        ("LA CONTRATO", "concordancia de artículo"),
        ("DE DE", "palabra repetida"),
    ]
    assert resultado["ortografia"][1]["ubicacion"]["linea"] == 3
    textos_regla = str(resultado["regla"]) + str(resultado["personas"])
    assert "palabraerrada" not in textos_regla
    assert "concordancia" not in textos_regla

    # paridad: regla y personas no dependen de la capa lingüística
    monkeypatch.setattr("expedientes.services.ortografia.revisar", lambda *_: [])
    monkeypatch.setattr("expedientes.services.ortografia.redaccion", lambda *_: [])
    sin_capa = confrontar_borrador(expediente_confrontacion, borrador)
    assert sin_capa["regla"] == resultado["regla"]
    assert sin_capa["personas"] == resultado["personas"]


def test_palabra_de_las_fuentes_no_se_marca_por_ortografia(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    """F23 FR-002b: el vocabulario del legajo se da por conocido."""
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion, Documento.CLIENTE, "reniec-f23.pdf", _RENIEC_F23
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-f23.docx",
        "ALBA LUMARIA ZAFIRO, DE NACIONALIDAD PERUANA, DNI 90000011. FUNDO Quirvanta.",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-f23.txt",
        _BORRADOR_F23 + "\nFUNDO QUIRVANTA  ZELMORIND",
    )
    monkeypatch.setattr(
        "expedientes.services.diccionario.diccionario",
        lambda: (_DiccionarioFicticio(), ["palabra"]),
    )
    monkeypatch.setattr("expedientes.services.diccionario.lista_casa", set)

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    palabras = [f["palabra"] for f in resultado["ortografia"]]
    assert "QUIRVANTA" not in palabras
    assert "FUNDO" not in palabras
    assert "ZELMORIND" in palabras
    assert "doble espacio" not in [f["motivo"] for f in resultado["ortografia"]]


def test_sin_diccionario_la_confrontacion_sigue_con_aviso(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    """F23 FR-003."""
    from adaptadores.diccionario import DiccionarioNoAprovisionado
    from expedientes.services import confrontar_borrador

    borrador = _expediente_f23(expediente_confrontacion, crear_documento_listo)

    def ausente():
        raise DiccionarioNoAprovisionado("falta")

    monkeypatch.setattr("expedientes.services.diccionario.diccionario", ausente)

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "RESULTADO"
    assert "no disponibles" in resultado["linguistico_aviso"]
    assert resultado["regla"]
    assert [f["motivo"] for f in resultado["ortografia"]] == [
        "concordancia de artículo",
        "palabra repetida",
    ]


def test_confrontacion_devuelve_catalogo_y_aporte_por_documento(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    cliente = crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "cliente-ficticio.txt",
        "NOMBRE FICTICIO DNI 90000001",
    )
    minuta = crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.docx",
        "ANEXO FICTICIO SIN CAMPOS DETECTABLES",
    )
    anexo = crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "anexo-ficticio.txt",
        "TEXTO FICTICIO SIN CAMPOS",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "borrador ficticio",
    )
    llamadas = []

    def catalogo(fuentes):
        llamadas.append(fuentes)
        if len(fuentes) > 1:
            return {
                "NOMBRE": {"NOMBRE FICTICIO"},
                "DNI": {"90000001"},
                "PARTIDA": set(),
                "MONTO": set(),
            }
        if next(iter(fuentes)) == cliente.nombre_original:
            return {
                "NOMBRE": {"NOMBRE FICTICIO"},
                "DNI": {"90000001"},
                "PARTIDA": set(),
                "MONTO": set(),
            }
        return {campo: set() for campo in ("NOMBRE", "DNI", "PARTIDA", "MONTO")}

    monkeypatch.setattr("expedientes.services.verificar.catalogo", catalogo)
    monkeypatch.setattr("expedientes.services.verificar.diagnostico", lambda *_: None)
    monkeypatch.setattr("expedientes.services.verificar.revisar", lambda *_: [])
    monkeypatch.setattr("expedientes.services.verificar.anexos_omitidos", lambda *_: [])

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["extraccion"]["catalogo"] == {
        "NOMBRE": ["NOMBRE FICTICIO"],
        "DNI": ["90000001"],
        "PARTIDA": [],
        "MONTO": [],
    }
    documentos = resultado["extraccion"]["documentos"]
    assert documentos[0] == {
        "nombre": cliente.nombre_original,
        "caracteres": len(cliente.texto_extraido.texto),
        "catalogo": {
            "NOMBRE": ["NOMBRE FICTICIO"],
            "DNI": ["90000001"],
            "PARTIDA": [],
            "MONTO": [],
        },
        "aporta": True,
    }
    assert documentos[1]["nombre"] == minuta.nombre_original
    assert documentos[1]["aporta"] is False
    assert documentos[1]["caracteres"] == len(minuta.texto_extraido.texto)
    assert documentos[2]["nombre"] == anexo.nombre_original
    assert documentos[2]["aporta"] is False
    assert "ANEXO FICTICIO SIN CAMPOS DETECTABLES" not in str(resultado)
    assert llamadas[0] == {
        cliente.nombre_original: cliente.texto_extraido.texto,
        minuta.nombre_original: minuta.texto_extraido.texto,
        anexo.nombre_original: anexo.texto_extraido.texto,
    }
    assert {next(iter(llamada)) for llamada in llamadas[1:]} == {
        cliente.nombre_original,
        minuta.nombre_original,
        anexo.nombre_original,
    }


def test_confrontacion_detecta_documentos_intercambiados_en_personas(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "fichas-personas-ficticias.txt",
        "INFORMACION PERSONAL\nPRIMER APELLIDO  ZAFIRO  SEGUNDO APELLIDO  LUMARIA\n"
        "NOMBRES  ALBA\nDNI 90000011\f"
        "INFORMACION PERSONAL\nPRIMER APELLIDO  TELURIO  SEGUNDO APELLIDO  NEBULOSA\n"
        "NOMBRES  BRUNO\nDNI 90000022",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-personas-ficticia.docx",
        "MINUTA FICTICIA",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-personas-ficticio.txt",
        "ALBA ZAFIRO LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000022\n"
        "BRUNO TELURIO NEBULOSA, DE NACIONALIDAD PERUANA. DNI 90000011",
    )
    monkeypatch.setattr("expedientes.services.verificar.diagnostico", lambda *_: None)
    monkeypatch.setattr("expedientes.services.verificar.revisar", lambda *_: [])
    monkeypatch.setattr("expedientes.services.verificar.anexos_omitidos", lambda *_: [])

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert [observacion["tipo"] for observacion in resultado["personas"]] == [
        "DOCUMENTO_CRUZADO",
        "DOCUMENTO_CRUZADO",
    ]
    assert resultado["personas"][0]["nombre"] == "ALBA ZAFIRO LUMARIA"
    assert resultado["personas"][0]["esperado"] == "90000011"


def test_diagnostico_bloqueante_detiene_toda_ejecucion(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "cliente-ficticio.txt",
        "fuente ficticia",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.docx",
        "minuta ficticia",
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
        lambda *_: (
            llamadas.append("catalogo")
            or {"NOMBRE": set(), "DNI": set(), "PARTIDA": set(), "MONTO": set()}
        ),
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.revisar", lambda *_: llamadas.append("regla")
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.anexos_omitidos",
        lambda *_: llamadas.append("parrafos"),
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "ADVERTENCIA_CORRESPONDENCIA"
    assert resultado["mensaje"] == "aviso ficticio"
    # El catalogo SI se construye antes del diagnostico, una vez para el conjunto
    # y otra por cada fuente: el usuario necesita ver que se extrajo para saber
    # si el borrador es de otro expediente o si el OCR no leyo las fuentes. Lo
    # que NO debe ejecutarse es la comparacion.
    assert set(llamadas) == {"catalogo"}


def test_diagnostico_real_bloquea_borrador_ajeno_antes_de_comparar(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "cliente-identidad-ficticia.txt",
        "ANA LUZ QUISPE MAMANI DNI 90000001",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-identidad-ficticia.docx",
        "ANA LUZ QUISPE MAMANI DNI 90000001",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ajeno-ficticio.txt",
        "BRUNO SOL PAREDES ROJAS DNI 90000002 DNI 90000003",
    )
    for nombre in ("revisar", "anexos_omitidos"):
        monkeypatch.setattr(
            f"expedientes.services.verificar.{nombre}",
            lambda *_: pytest.fail("no se compara un borrador ajeno"),
        )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "ADVERTENCIA_CORRESPONDENCIA"
    assert resultado["regla"] == []
    assert resultado["ortografia"] == []


def test_anexo_sin_identidades_no_bloquea_diagnostico(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "cliente-identidad-ficticia.txt",
        "ANA LUZ QUISPE MAMANI DNI 90000001",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-identidad-ficticia.docx",
        "ANA LUZ QUISPE MAMANI DNI 90000001",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "anexo-ficticio.txt",
        "ANEXO FICTICIO SIN IDENTIDADES NI NUMEROS PERSONALES",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.docx",
        "minuta ficticia",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-coincidente-ficticio.txt",
        "ANA LUZ QUISPE MAMANI DNI 90000001",
    )
    monkeypatch.setattr("expedientes.services.verificar.revisar", lambda *_: [])
    monkeypatch.setattr("expedientes.services.verificar.anexos_omitidos", lambda *_: [])

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "RESULTADO"
    assert resultado["regla"] == []


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
        Documento.MINUTA,
        "minuta-ficticia.txt",
        fuente,
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "cliente-ficticio.txt",
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
        expediente_confrontacion, Documento.CLIENTE, "cliente-ficticio.txt", texto
    )
    crear_documento_listo(
        expediente_confrontacion, Documento.MINUTA, "minuta-ficticia.docx", texto
    )
    borrador = crear_documento_listo(
        expediente_confrontacion, Documento.BORRADOR, "borrador-ficticio.txt", texto
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "RESULTADO"
    assert resultado["regla"] == []


def test_representante_sin_ficha_es_una_sola_observacion(
    expediente_confrontacion, crear_documento_listo
):
    """F51: sin ficha, ni «documento sin titular» (ALTA) ni avisos repetidos."""
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    fuente = (
        "OPERACION FICTICIA DE PRUEBA.\n"
        "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001.\n"
        "PARTIDA ELECTRONICA N° 80000001. MONTO S/ 12,345.67."
    )
    borrador = (
        f"{fuente}\nINVERSIONES FICTICIAS S.A.C., DEBIDAMENTE REPRESENTADA POR "
        "PEDRO PABLO SOTO VERA, DE NACIONALIDAD PERUANA, IDENTIFICADO CON DNI N° "
        "48172635.\nPEDRO PABLO SOTO VERA, DE NACIONALIDAD PERUANA, CON DNI N° "
        "48172635."
    )
    for rol, nombre in (
        (Documento.MINUTA, "minuta-ficticia.txt"),
        (Documento.CLIENTE, "cliente-ficticio.txt"),
    ):
        crear_documento_listo(expediente_confrontacion, rol, nombre, fuente)
    documento_borrador = crear_documento_listo(
        expediente_confrontacion, Documento.BORRADOR, "borrador-ficticio.txt", borrador
    )

    resultado = confrontar_borrador(expediente_confrontacion, documento_borrador)

    assert resultado["estado"] == "RESULTADO"
    assert resultado["personas"] == []
    assert [
        (fila["hallado"], fila["esperado"])
        for fila in resultado["regla"]
        if fila["campo"] == "SIN_FICHA"
    ] == [("PEDRO PABLO SOTO VERA", "Sin ficha RENIEC en los recaudos")]


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
        (
            "[SIN_FICHA] «PEDRO PABLO SOTO VERA» sin ficha RENIEC en los recaudos",
            "SIN_FICHA",
            "PEDRO PABLO SOTO VERA",
            "Sin ficha RENIEC en los recaudos",
        ),
        (
            "[SIN_FICHA] «PEDRO PABLO ZOTO VERA» sin ficha RENIEC en los recaudos; "
            "la minuta dice «PEDRO PABLO SOTO VERA»   (caratula)",
            "SIN_FICHA",
            "PEDRO PABLO ZOTO VERA",
            "Sin ficha RENIEC en los recaudos; la minuta dice «PEDRO PABLO SOTO VERA»",
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


def test_parser_conserva_motivo_de_caratula():
    from expedientes.services import parsear_observacion_regla

    observacion = parsear_observacion_regla(
        "[NOMBRE] «ANA LUZ QUISPA» debe decir «ANA LUZ QUISPE»   (caratula)",
        "ANA LUZ QUISPA",
    )

    assert observacion["formato"] == "regla"
    assert observacion["campo"] == "NOMBRE"
    assert observacion["motivo"] == "(caratula)"
    assert observacion["esperado"] == "ANA LUZ QUISPE"


def test_parser_conserva_motivo_de_caratula_de_salida_real():
    from expedientes.services import adaptar_observaciones_regla
    from nucleo import verificar

    fuente = "ANA LUZ QUISPE MAMANI, DE NACIONALIDAD PERUANA. DNI 90000001."
    borrador = f"{fuente}\nANA LUZ QUISPA"
    salidas = verificar.revisar(
        verificar.catalogo({"fuente-ficticia.txt": fuente}), borrador, 88
    )

    observaciones = adaptar_observaciones_regla(salidas, borrador)

    caratula = next(item for item in observaciones if item["motivo"])
    assert caratula["campo"] == "NOMBRE"
    assert caratula["motivo"] == "(caratula)"


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
    assert len(observaciones) == 5
    assert all(item["formato"] == "regla" for item in observaciones)
    assert {item["campo"] for item in observaciones} == {
        "DNI",
        "NOMBRE",
        "MONTO",
        "PARTIDA",
        "PARRAFO",
    }
    assert any(item["campo"] == "PARRAFO" for item in observaciones)


def test_adaptador_omite_falta_duplicada_y_conserva_falta_real():
    from expedientes.services import adaptar_observaciones_regla
    from nucleo import verificar

    fuente = "DNI 90000001. PARTIDA ELECTRONICA N° 80000001."
    borrador = "DNI 90000002."
    salidas = verificar.revisar(
        verificar.catalogo({"fuente-ficticia.txt": fuente}), borrador, 88
    )

    observaciones = adaptar_observaciones_regla(salidas, borrador)

    assert [
        (item["campo"], item["hallado"], item["esperado"]) for item in observaciones
    ] == [
        ("DNI", "90000002", "90000001"),
        ("PARTIDA", "No aparece en el borrador", "80000001"),
    ]


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


@pytest.mark.parametrize(
    "rol_suprimido",
    ["CLIENTE", "BORRADOR"],
)
def test_texto_suprimido_no_entra_al_nucleo(
    expediente_confrontacion,
    crear_documento_listo,
    monkeypatch,
    rol_suprimido,
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    fuente = crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "fuente-supresion-ficticia.txt",
        "" if rol_suprimido == "CLIENTE" else "texto ficticio disponible",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-supresion-ficticia.docx",
        "texto ficticio disponible",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-supresion-ficticio.txt",
        "" if rol_suprimido == "BORRADOR" else "texto ficticio disponible",
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.diagnostico",
        lambda *_: pytest.fail("no se confronta texto suprimido"),
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "NO_DISPONIBLE"
    assert resultado["regla"] == []
    assert resultado["ortografia"] == []
    assert fuente.texto_extraido.texto == (
        "" if rol_suprimido == "CLIENTE" else "texto ficticio disponible"
    )


def test_documento_pendiente_no_entra_al_nucleo(
    expediente_confrontacion, crear_documento_listo, monkeypatch
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "fuente-pendiente-ficticia.txt",
        "texto ficticio disponible",
        estado=Documento.PENDIENTE,
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-pendiente-ficticia.docx",
        "texto ficticio disponible",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-pendiente-ficticio.txt",
        "texto ficticio disponible",
    )
    monkeypatch.setattr(
        "expedientes.services.verificar.diagnostico",
        lambda *_: pytest.fail("no se confronta mientras extrae texto"),
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "NO_DISPONIBLE"
    assert "Espere" in resultado["mensaje"]


def test_advertencia_de_correspondencia_tambien_muestra_la_extraccion(
    expediente_confrontacion, crear_documento_listo
):
    """Es cuando más falta hace: ¿es otro expediente o falló el OCR?"""
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "dni-ficticio.png",
        "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001.",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.docx",
        "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001.",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "ajeno-ficticio.docx",
        "BRUNO TELURIO VENTORIA, DE NACIONALIDAD PERUANA. DNI 91000009.\n"
        "CARLA NEBULOSA FICTICIA, DE NACIONALIDAD PERUANA. DNI 91000008.",
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)

    assert resultado["estado"] == "ADVERTENCIA_CORRESPONDENCIA"
    assert resultado["extraccion"]["catalogo"]["DNI"] == ["90000001"]
    assert len(resultado["extraccion"]["documentos"]) == 2


def test_resumen_extraccion_separa_personas_con_ficha_y_menciones():
    from types import SimpleNamespace

    from expedientes.services import _resumen_extraccion
    from nucleo.verificar import catalogo

    textos = {
        "reniec-ficticio.pdf": (
            "CUI: 90000011 - 5\nAPELLIDO PATERNO  LUMARIA\n"
            "APELLIDO MATERNO  ZAFIRO\nNOMBRES  ALBA"
        ),
        "declaracion-ficticia.txt": (
            "DECLARACION JURADA\nAPELLIDOS: LUMARIA ZAFIRO\nNOMBRES: ALBA\n"
            "DNI: 90000011\nNOMBRES Y APELLIDOS DEL CONYUGE: EMILIO SOLANO QUIMERA"
        ),
        "minuta-ficticia.txt": (
            "CLARA FICTELIA SOLARIA, DE NACIONALIDAD PERUANA. DNI 90000033"
        ),
    }
    documentos = [
        SimpleNamespace(nombre_original=nombre, texto_extraido=SimpleNamespace(texto=t))
        for nombre, t in textos.items()
    ]
    cat = catalogo({f"/srv/privado/{nombre}": t for nombre, t in textos.items()})

    resumen = _resumen_extraccion(documentos, cat)

    (ancla,) = resumen["personas"]
    assert ancla["nombre"] == "ALBA LUMARIA ZAFIRO"
    assert ancla["estado"] == "Confirmada"
    assert ancla["conyuge"] == "EMILIO SOLANO QUIMERA"
    assert ancla["procedencia_conyuge"] == {
        "archivo": "declaracion-ficticia.txt",
        "pagina": 1,
    }
    assert ancla["adjuntos"] == [
        {
            "nombre": "ALBA LUMARIA ZAFIRO",
            "documento": "90000011",
            "procedencias": [{"archivo": "declaracion-ficticia.txt", "pagina": 1}],
        }
    ]
    (mencion,) = resumen["menciones"]
    assert mencion["nombre"] == "CLARA FICTELIA SOLARIA"
    assert mencion["documento"] == "90000033"
    assert mencion["estado"] == "Sin ficha"
    assert mencion["conyuge"] is None
    assert mencion["adjuntos"] == []
    assert mencion["procedencias"] == [{"archivo": "minuta-ficticia.txt", "pagina": 1}]
    por_documento = {
        fila["nombre"]: (len(fila["personas"]), len(fila["menciones"]))
        for fila in resumen["documentos"]
    }
    assert por_documento == {
        "reniec-ficticio.pdf": (1, 0),
        "declaracion-ficticia.txt": (0, 1),
        "minuta-ficticia.txt": (0, 1),
    }
    assert all(fila["aporta"] for fila in resumen["documentos"])
    assert "/srv/privado" not in str(resumen)


def test_adjunto_sin_nombre_se_presenta_de_forma_explicita():
    from expedientes.services import _personas_legibles
    from nucleo.verificar import catalogo

    cat = catalogo(
        {
            "reniec-ficticio.pdf": (
                "CUI: 90000011 - 5\nAPELLIDO PATERNO  LUMARIA\n"
                "APELLIDO MATERNO  ZAFIRO\nNOMBRES  ALBA"
            ),
            "suelto-ficticio.txt": "DNI 90000011",
        }
    )

    (fila,) = _personas_legibles(cat.personas)
    assert fila["adjuntos"] == [
        {
            "nombre": "Sin nombre",
            "documento": "90000011",
            "procedencias": [{"archivo": "suelto-ficticio.txt", "pagina": 1}],
        }
    ]
    assert (fila["conyuge"], fila["procedencia_conyuge"]) == (None, None)


def test_confrontacion_solo_exige_nombres_de_fichas_y_minuta(
    expediente_confrontacion, crear_documento_listo
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "reniec-ficticio.pdf",
        "CUI: 90000011 - 5\nAPELLIDO PATERNO  LUMARIA  APELLIDO MATERNO  ZAFIRO\n"
        "NOMBRES  ALBA",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "declaracion-ficticia.txt",
        "HUGO BERNAL TIRSO, DE NACIONALIDAD PERUANA.",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.txt",
        "IRMA CELESTE PORTOLA, DE NACIONALIDAD PERUANA, CON DNI 90000077.",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        "ALBA LUMARIA ZAFIRO, DE NACIONALIDAD PERUANA, CON DNI 90000011.",
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)
    assert resultado["estado"] == "RESULTADO"
    texto = str(resultado["regla"])
    assert "IRMA CELESTE PORTOLA" in texto
    assert "HUGO BERNAL TIRSO" not in texto


_F24_PERSONA = "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001.\n"


def test_confrontacion_solo_exige_montos_de_la_minuta(
    expediente_confrontacion, crear_documento_listo
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "liquidacion-ficticia.txt",
        "TASA REGISTRAL S/ 45.50. DERECHOS S/ 1,230.00.",
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.txt",
        _F24_PERSONA + "PRECIO DE VENTA S/ 150,000.00. ARRAS S/ 5,000.00.",
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        _F24_PERSONA + "PRECIO DE VENTA S/ 150,000.00. TASA S/ 45.50.",
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)
    assert resultado["estado"] == "RESULTADO"
    montos = [o for o in resultado["regla"] if o["campo"] == "MONTO"]
    assert [o["esperado"] for o in montos] == ["5,000.00"]


def test_confrontacion_monto_por_posicion_lleva_concepto_y_fuente(
    expediente_confrontacion, crear_documento_listo
):
    from expedientes.models import Documento
    from expedientes.services import confrontar_borrador

    cronograma = (
        "CUOTA 1 15/01/2027 S/ 1,000.00 S/ 1,050.00\n"
        "CUOTA 2 15/02/2027 S/ 1,000.00 S/ 1,045.00\n"
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.CLIENTE,
        "declaracion-ficticia.txt",
        _F24_PERSONA,
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.txt",
        _F24_PERSONA + cronograma,
    )
    borrador = crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        _F24_PERSONA + cronograma.replace("S/ 1,045.00", "S/ 1,050.00"),
    )

    resultado = confrontar_borrador(expediente_confrontacion, borrador)
    (monto,) = [o for o in resultado["regla"] if o["campo"] == "MONTO"]
    assert monto["hallado"] == "1,050.00"
    assert monto["esperado"] == "1,045.00"
    assert monto["concepto"] == "CUOTA 2"
    assert monto["fuente"] == {"archivo": "minuta-ficticia.txt", "pagina": 1}
    assert monto["motivo"] == "CUOTA 2 · minuta-ficticia.txt, página 1"
