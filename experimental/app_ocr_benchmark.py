"""Interfaz Streamlit experimental para comparar motores OCR.

Ejecutar desde la raíz:
    streamlit run experimental/app_ocr_benchmark.py --server.port 8504

Las dependencias pesadas son opcionales y se cargan solo al ejecutar el motor.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from experimental.ocr_benchmark import (
    ENGINE_SPECS,
    accuracy_rate,
    benchmark,
    dependency_status,
    read_reference,
    render_pages,
)

st.set_page_config(
    page_title="Benchmark OCR experimental",
    page_icon="🔬",
    layout="wide",
)
st.title("Benchmark OCR")
st.caption(
    "Comparación experimental sobre páginas normalizadas a 200 DPI. "
    "Todos los resultados pasan por el mismo núcleo determinista de confrontación."
)

engine_ids = tuple(ENGINE_SPECS)
labels = {engine_id: spec.label for engine_id, spec in ENGINE_SPECS.items()}
seleccion = st.sidebar.selectbox(
    "Motor OCR",
    ("Todos", *(labels[engine_id] for engine_id in engine_ids)),
)
seleccionados = (
    engine_ids
    if seleccion == "Todos"
    else (
        next(engine_id for engine_id in engine_ids if labels[engine_id] == seleccion),
    )
)
st.sidebar.divider()
st.sidebar.caption(
    "Dependencias detectadas (los modelos se descargan al inicializar cada motor):"
)
for engine_id in engine_ids:
    disponible, detalle = dependency_status(engine_id)
    marca = "✅" if disponible else "⚠️"
    st.sidebar.write(f"{marca} {labels[engine_id]}: {detalle}")

archivos = st.file_uploader(
    "Documentos de prueba",
    type=["pdf", "jpg", "jpeg", "png", "bmp", "tif", "tiff", "webp"],
    accept_multiple_files=True,
    help="Puedes seleccionar más de dos archivos. Cada documento se rasteriza y se reporta por separado.",
)
referencia = st.file_uploader(
    "Texto de referencia (opcional)",
    type=["docx", "doc", "rtf", "txt", "md"],
    help="Acepta Word (DOCX/DOC/RTF) o texto. Se compara contra cada documento seleccionado.",
)

if seleccionados and any(
    ENGINE_SPECS[engine_id].warning for engine_id in seleccionados
):
    st.warning(ENGINE_SPECS[seleccionados[0]].warning)
if len(archivos) > 1 and referencia is not None:
    st.info(
        "La referencia se comparará contra cada archivo y motor seleccionado. "
        "Asegúrate de que el Word contenga el texto esperado para esos documentos."
    )

if st.button("Ejecutar benchmark", type="primary", disabled=not archivos):
    if not archivos:
        st.error("Selecciona al menos un documento")
    else:
        documentos = []
        with tempfile.TemporaryDirectory(prefix="ocr-benchmark-") as temporal:
            temporal_path = Path(temporal)
            texto_referencia = ""
            if referencia is not None:
                referencia_suffix = Path(referencia.name).suffix.lower()
                referencia_path = temporal_path / f"reference{referencia_suffix}"
                referencia_path.write_bytes(referencia.getvalue())
                try:
                    texto_referencia = read_reference(referencia_path)
                    if texto_referencia.strip():
                        st.success(
                            f"Referencia leída: {referencia.name} "
                            f"({len(texto_referencia):,} caracteres; "
                            "se usará contra cada archivo y motor)."
                        )
                    else:
                        st.warning("La referencia está vacía.")
                except Exception as exc:
                    st.error(f"No se pudo leer la referencia {referencia.name}: {exc}")
            for indice, archivo in enumerate(archivos, 1):
                nombre = Path(archivo.name).name
                origen = temporal_path / f"{indice:03d}-{nombre}"
                origen.write_bytes(archivo.getvalue())
                try:
                    paginas = render_pages(
                        origen, temporal_path / f"pages-{indice:03d}"
                    )
                    documentos.append(
                        {
                            "nombre": nombre,
                            "referencia": (
                                referencia.name
                                if referencia is not None
                                else "Sin referencia"
                            ),
                            "referencia_caracteres": len(texto_referencia),
                            "resultados": benchmark(
                                paginas,
                                seleccionados,
                                referencia=texto_referencia,
                                nombre_fuente=nombre,
                            ),
                            "error": None,
                        }
                    )
                except Exception as exc:
                    documentos.append(
                        {"nombre": nombre, "resultados": (), "error": str(exc)}
                    )
        st.session_state.ocr_benchmarks = documentos


documentos = st.session_state.get("ocr_benchmarks", ())
if documentos:
    st.divider()
    st.subheader("Tabla comparativa")
    st.caption(
        "CER y WER son tasas de error: 0 es exacto. "
        "Las precisiones son su inversa: 100% es exacto."
    )
    filas = []
    for documento in documentos:
        referencia_nombre = documento.get("referencia", "Sin referencia")
        referencia_caracteres = documento.get("referencia_caracteres", 0)
        if documento["error"]:
            filas.append(
                {
                    "Documento": documento["nombre"],
                    "Motor": "-",
                    "Referencia": referencia_nombre,
                    "Ref. caracteres": referencia_caracteres,
                    "Estado": "Error: " + documento["error"],
                }
            )
            continue
        for resultado in documento["resultados"]:
            filas.append(
                {
                    "Documento": documento["nombre"],
                    "Motor": labels[resultado.engine_id],
                    "Referencia": referencia_nombre,
                    "Ref. caracteres": referencia_caracteres,
                    "Estado": "Error" if resultado.error else "OK",
                    "Páginas": resultado.paginas,
                    "Caracteres": resultado.caracteres,
                    "Preparación (s)": round(resultado.tiempo_preparacion, 3),
                    "Procesamiento (s)": round(resultado.tiempo_procesamiento, 3),
                    "Total (s)": round(resultado.tiempo_total, 3),
                    "Personas": resultado.catalogo.get("personas", 0),
                    "DNI": resultado.catalogo.get("documentos", 0),
                    "Partidas": resultado.catalogo.get("partidas", 0),
                    "Montos": resultado.catalogo.get("montos", 0),
                    "CER": None if resultado.cer is None else round(resultado.cer, 4),
                    "WER": None if resultado.wer is None else round(resultado.wer, 4),
                    "Precisión caracteres (%)": (
                        None
                        if resultado.cer is None
                        else round(accuracy_rate(resultado.cer) or 0.0, 2)
                    ),
                    "Precisión palabras (%)": (
                        None
                        if resultado.wer is None
                        else round(accuracy_rate(resultado.wer) or 0.0, 2)
                    ),
                }
            )
    st.dataframe(pd.DataFrame(filas), width="stretch", hide_index=True)

    for documento in documentos:
        st.subheader(f"Texto extraído: {documento['nombre']}")
        if documento["error"]:
            st.error(documento["error"])
            continue
        for resultado in documento["resultados"]:
            with st.expander(labels[resultado.engine_id]):
                if resultado.error:
                    st.error(resultado.error)
                    continue
                if ENGINE_SPECS[resultado.engine_id].warning:
                    st.warning(ENGINE_SPECS[resultado.engine_id].warning)
                st.caption(
                    "El texto siguiente es exactamente el que recibió el núcleo; "
                    "las páginas están separadas por salto de página."
                )
                st.text_area(
                    "Texto extraído",
                    "\f".join(resultado.textos),
                    height=260,
                    key=f"ocr-text-{documento['nombre']}-{resultado.engine_id}",
                )
