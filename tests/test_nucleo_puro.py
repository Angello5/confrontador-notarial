"""Pruebas ficticias de fronteras y dependencias del núcleo."""

import ast
from pathlib import Path

NUCLEO = Path(__file__).resolve().parents[1] / "nucleo"
IMPORTS_PERMITIDOS = {
    "collections",
    "nucleo",  # F43: un módulo del núcleo usa otro; todos pasan esta revisión.
    "datetime",  # date valida fechas; el núcleo no consulta el reloj.
    "difflib",  # F61: alineación palabra por palabra; algoritmo puro, sin E/S.
    "hashlib",  # F21: ids estables de corrección; sin E/S.
    "rapidfuzz",
    "re",
    "unicodedata",
}


def _errores_pureza(codigo):
    arbol = ast.parse(codigo)
    errores = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            errores.extend(
                alias.name.split(".")[0]
                for alias in nodo.names
                if alias.name.split(".")[0] not in IMPORTS_PERMITIDOS
            )
        elif isinstance(nodo, ast.ImportFrom):
            raiz = (nodo.module or "").split(".")[0]
            if nodo.level or raiz not in IMPORTS_PERMITIDOS:
                errores.append(raiz or "import relativo")
        elif isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
            if nodo.func.id in {"open", "exec", "eval", "compile", "__import__"}:
                errores.append(nodo.func.id)
        elif isinstance(nodo, ast.Name) and nodo.id == "__builtins__":
            errores.append(nodo.id)
    return errores


def test_reglas_reciben_texto_sintetico():
    from nucleo.lexico import contar, erratas, sin_tilde
    from nucleo.ortografia import plano
    from nucleo.verificar import nombre_reniec, nombres, norm

    assert norm("LÍNEA Ñ ñ") == "LINEA Ñ Ñ"
    assert norm("MUÑÓZ") == "MUÑOZ"
    assert sin_tilde("MUÑÓZ") == "MUÑOZ"
    assert plano("MUÑÓZ") == "muñoz"
    assert nombres("ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA") == [
        "ALBA ZURBELIA LUMARIA"
    ]
    # F45: las actas vehiculares escriben «, PERUANO,» sin «DE NACIONALIDAD».
    assert nombres("ENTRE ALBA ZURBELIA LUMARIA, PERUANA, IDENTIFICADA") == [
        "ALBA ZURBELIA LUMARIA"
    ]
    assert (
        nombre_reniec(
            "NOMBRES  ALBA\nAPELLIDO PATERNO  ZURBELIA\nAPELLIDO MATERNO  LUMARIA"
        )
        == "ALBA ZURBELIA LUMARIA"
    )
    vocab = contar(["OCTAVO URBANIZACION"])
    assert [(palabra, cerca) for palabra, cerca, _ in erratas("OCTAO", vocab)] == [
        ("OCTAO", "OCTAVO")
    ]
    assert plano("ACCIÓN") == "accion"


def test_eñe_en_nombre_genera_observacion_con_el_valor_esperado():
    from nucleo.verificar import catalogo, revisar

    con_enye = "ROSA ELENA MUÑOZ PEÑA, DE NACIONALIDAD PERUANA"
    con_n = con_enye.replace("Ñ", "N")
    observaciones = revisar(catalogo({"minuta.docx": con_enye}), con_n, 90)
    assert (
        "[NOMBRE] «ROSA ELENA MUNOZ PENA» debe decir «ROSA ELENA MUÑOZ PEÑA»"
        in observaciones
    )


def test_eñe_igual_en_ambos_lados_no_genera_observacion():
    from nucleo.verificar import catalogo, revisar

    texto = "ROSA ELENA MUÑOZ PEÑA, DE NACIONALIDAD PERUANA"
    assert revisar(catalogo({"minuta.docx": texto}), texto, 90) == []


def test_nombres_con_eñe_se_detectan_con_y_sin_tilde_vocal():
    from nucleo.verificar import nombres, norm

    assert nombres("NUÑEZ IBAÑEZ, DE NACIONALIDAD PERUANA") == ["NUÑEZ IBAÑEZ"]
    assert nombres(norm("NÚÑEZ IBAÑEZ, DE NACIONALIDAD PERUANA")) == ["NUÑEZ IBAÑEZ"]


def test_heuristica_de_caratula_admite_eñe():
    from nucleo.verificar import catalogo, revisar

    fuente = "ROSA ELENA MUÑOZ PEÑA, DE NACIONALIDAD PERUANA"
    observaciones = revisar(
        catalogo({"minuta.docx": fuente}), "ROSA ELENA MUNOZ PENA", 90
    )
    assert any(
        obs.startswith("[NOMBRE]") and "MUÑOZ PEÑA" in obs for obs in observaciones
    )


def test_tildes_de_vocales_siguen_siendo_indiferentes():
    from nucleo.verificar import catalogo, norm, revisar

    assert norm("PERÚ") == norm("PERU")
    texto = "ROSA ELENA MUÑOZ PEÑA, DE NACIONALIDAD PERÚ"
    assert (
        revisar(catalogo({"minuta.docx": texto}), texto.replace("PERÚ", "PERU"), 90)
        == []
    )


def test_nucleo_solo_importa_lista_blanca_y_no_abre_accesos():
    for archivo in sorted(NUCLEO.glob("*.py")):
        assert not _errores_pureza(archivo.read_text(encoding="utf-8")), archivo.name


def test_guard_ast_detecta_imports_peligrosos_y_diferidos():
    for codigo in (
        "import subprocess",
        "import socket",
        "import shutil",
        "import glob",
        "import http.client",
        "import os",
        "import io",
        "import pathlib",
        "import urllib.request",
        "def fn():\n import pathlib",
        "def fn():\n open('x')",
        "eval('1')",
        "from dataclasses import dataclass",
        "from typing import Any",
        "from . import adaptadores",
        "__builtins__",
    ):
        assert _errores_pureza(codigo), codigo


def test_shims_reutilizan_nucleo_y_adaptadores():
    import extraer
    import lexico
    import ortografia
    import verificar
    from adaptadores import extraccion
    from nucleo import lexico as nucleo_lexico, ortografia as nucleo_ortografia
    from nucleo import verificar as nucleo_verificar

    assert extraer.leer is extraccion.leer
    assert extraer.IMGS is nucleo_verificar.IMGS
    assert lexico.contar is nucleo_lexico.contar
    assert verificar.catalogo is nucleo_verificar.catalogo
    assert ortografia._revisar is nucleo_ortografia.revisar


def test_shim_ortografia_conserva_firma_y_resultado_con_extra():
    import ortografia
    from adaptadores.diccionario import diccionario, lista_casa
    from nucleo.ortografia import revisar

    texto = "ZURBELIA LAMPARA CLAÚSULA"
    extra = {"ZURBELIA", "LAMPARA"}
    d, lemas = diccionario()
    assert ortografia.revisar(texto, extra) == revisar(
        texto, d, lemas, lista_casa(), extra
    )


def test_los_tres_modulos_tratan_la_enie_igual():
    """La Ñ se conserva y las tildes de vocales se ignoran, en los tres.

    Cada módulo normaliza por su cuenta. Cuando solo `verificar` conservó la Ñ,
    `lexico` y `ortografia` siguieron convirtiéndola en N y nadie se enteró
    hasta probarlo a mano. Esta prueba falla si alguien vuelve a tocar uno y se
    olvida de los otros dos.
    """
    from nucleo.lexico import sin_tilde
    from nucleo.ortografia import plano
    from nucleo.verificar import norm

    normalizadores = {
        "verificar.norm": norm,
        "lexico.sin_tilde": sin_tilde,
        "ortografia.plano": plano,
    }

    for nombre, fn in normalizadores.items():
        assert "Ñ" in fn("MUÑOZ").upper(), f"{nombre} descarta la Ñ"
        assert fn("MUÑOZ").upper() != fn("MUNOZ").upper(), (
            f"{nombre} confunde MUÑOZ con MUNOZ"
        )
        assert fn("PERÚ").upper() == fn("PERU").upper(), (
            f"{nombre} distingue tildes de vocales, y no debe"
        )


_PARRAFO_A = (
    "LA PARTE COMPRADORA FICTICIA PAGA EL PRECIO PACTADO EN EFECTIVO ANTE EL "
    "NOTARIO FICTICIO DE ESTA CIUDAD."
)
_PARRAFO_B = (
    "EL INMUEBLE FICTICIO NO REGISTRA DEUDAS DE ARBITRIOS NI IMPUESTO PREDIAL "
    "SEGUN DECLARA LA PARTE VENDEDORA."
)
_PARRAFO_C = (
    "LAS PARTES FICTICIAS RENUNCIAN A CUALQUIER ACCION DE NULIDAD O RESCISION "
    "POR LESION SOBRE ESTE CONTRATO."
)
_MINUTA_PARRAFOS = f"{_PARRAFO_A}\n{_PARRAFO_B}\n{_PARRAFO_C}\nlínea corta\n"
_BORRADOR_PARRAFOS = (
    f"TITULO\nCLAUSULA PRIMERA: {_PARRAFO_A} Y ASI LO FIRMAN.\n"
    f"{_PARRAFO_B.replace('PREDIAL', 'PREDIALES')}\n"
)


def test_revisar_parrafos_paridad_con_salida_previa_al_atajo():
    """Salida capturada antes del atajo por subcadena exacta; no debe cambiar."""
    from nucleo.verificar import revisar_parrafos
    from tests.test_personas import _LEGAJO_BORRADOR, _LEGAJO_MINUTA

    assert revisar_parrafos(
        [_MINUTA_PARRAFOS, _LEGAJO_MINUTA], _BORRADOR_PARRAFOS + _LEGAJO_BORRADOR, 88
    ) == [
        "[PARRAFO] falta o alterado (50.96%): LAS PARTES FICTICIAS RENUNCIAN A "
        "CUALQUIER ACCION DE NULIDAD O RESCISION POR LESION SOBRE ESTE CONTR…",
        "[PARRAFO] falta o alterado (53.33%): LA VENDEDORA DECLARA QUE EL INMUEBLE "
        "FICTICIO SE ENTREGA LIBRE DE CARGAS, GRAVAMENES Y MEDIDAS JUDIC…",
    ]
    assert revisar_parrafos([_MINUTA_PARRAFOS], "", 88) == [
        "[PARRAFO] falta: LA PARTE COMPRADORA FICTICIA PAGA EL PRECIO PACTADO EN "
        "EFECTIVO ANTE EL NOTARIO FICTICIO DE ESTA CIU…",
        "[PARRAFO] falta: EL INMUEBLE FICTICIO NO REGISTRA DEUDAS DE ARBITRIOS NI "
        "IMPUESTO PREDIAL SEGUN DECLARA LA PARTE VEND…",
        "[PARRAFO] falta: LAS PARTES FICTICIAS RENUNCIAN A CUALQUIER ACCION DE "
        "NULIDAD O RESCISION POR LESION SOBRE ESTE CONTR…",
    ]


def test_revisar_parrafos_subcadena_exacta_no_llama_a_extractone(monkeypatch):
    from nucleo import verificar

    buscados = []
    original = verificar.process.extractOne

    def espia(consulta, *args, **kwargs):
        buscados.append(consulta)
        return original(consulta, *args, **kwargs)

    monkeypatch.setattr(verificar.process, "extractOne", espia)

    assert verificar.revisar_parrafos([_PARRAFO_A], _BORRADOR_PARRAFOS, 88) == []
    assert buscados == []
    assert verificar.revisar_parrafos([_PARRAFO_B], _BORRADOR_PARRAFOS, 88) == []
    assert buscados == []


def test_revisar_parrafos_solo_calcula_la_puntuacion_de_los_que_fallan(monkeypatch):
    """Un parrafo parecido sobre el umbral no necesita la busqueda completa."""
    from nucleo import verificar

    buscados = []
    original = verificar.process.extractOne

    def espia(consulta, *args, **kwargs):
        buscados.append(consulta)
        return original(consulta, *args, **kwargs)

    monkeypatch.setattr(verificar.process, "extractOne", espia)

    salida = verificar.revisar_parrafos(
        [f"{_PARRAFO_B}\n{_PARRAFO_C}"], _BORRADOR_PARRAFOS, 88
    )

    assert buscados == [verificar.norm(_PARRAFO_C)]
    assert len(salida) == 1 and salida[0].startswith("[PARRAFO] falta o alterado (")
