"""UI de prueba del confrontamiento local (sin nube, sin modelo).

  streamlit run app.py

Sube las fuentes (minuta + DNIs escaneados) y el borrador; corre el mismo
extraer.py + verificar.py de la CLI.
"""

import re
import tempfile
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from adaptadores.extraccion import IMGS, leer
from experimental.revisor_llm import revisar_prosa
from nucleo.verificar import catalogo, diagnostico, revisar, revisar_parrafos

# Calibracion, no opcion de usuario: por debajo aparecen parrafos alterados que no
# lo estan, y a 100 se marca todo lo que no sea identico caracter a caracter. 88 es
# el valor con el que se midieron los dos expedientes.
UMBRAL_PARRAFO = 88

st.set_page_config(
    page_title="Confrontación de Documentos", page_icon="📄", layout="wide"
)
st.title("Notaría Espinosa - Confrontación de Documentos - FedatIA")
st.caption(
    "Se realiza la comparación de información del cliente comparandola con un borrador de minuta. "
    "Se revisa la prosa con Gemini (opcional) y se aplican reglas deterministas."
)


def textos(archivos) -> dict[str, str]:
    """Streamlit entrega bytes en memoria; leer() trabaja sobre rutas."""
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        for f in archivos:
            p = Path(tmp) / f.name
            p.write_bytes(f.getbuffer())
            out[f.name] = leer(p)
    return out


izq, der = st.columns(2)
fuentes_up = izq.file_uploader(
    "Minuta y documentos del cliente", accept_multiple_files=True
)
borrador_up = der.file_uploader("Proyecto (borrador)", accept_multiple_files=True)
usar_ia = st.sidebar.checkbox(
    "Revisar la prosa con Gemini",
    value=True,
    help="Solo ortografía y gramática. Los datos duros "
    "(DNI, partida, montos, nombres) los decide la regla.",
)
modelo = st.sidebar.selectbox(
    "Modelo",
    [
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
    ],
    disabled=not usar_ia,
    help="3.7 encuentra 2 defectos más que 3.6 pero ahora está saturado.",
)
if usar_ia:
    st.sidebar.caption(
        "⚠️ El borrador se envía a Google. Desmárcalo para trabajar 100% local."
    )

if st.button("Comparar", type="primary", disabled=not (fuentes_up and borrador_up)):
    inicio = time.perf_counter()
    with st.spinner("Extrayendo texto (OCR en la primera pasada de cada archivo)…"):
        fuentes = textos(fuentes_up)
        destinos = textos(borrador_up)
        cat = catalogo(fuentes)
        minutas = [v for k, v in fuentes.items() if Path(k).suffix.lower() not in IMGS]
    segundos = time.perf_counter() - inicio

    with st.expander(f"Catálogo extraído de las {len(fuentes)} fuentes"):
        st.json({k: sorted(v) for k, v in cat.items()})

    for nombre, txt in destinos.items():
        if aviso := diagnostico(fuentes, txt):
            st.subheader(nombre)
            st.error(
                f"**{aviso}**\n\nNo se compara campo por campo porque serían "
                f"cientos de filas sin valor. Revisa que el borrador y las fuentes "
                f"sean del mismo expediente."
            )
            continue
        obs = revisar(cat, txt, UMBRAL_PARRAFO) + revisar_parrafos(
            minutas, txt, UMBRAL_PARRAFO
        )
        # ponytail: se parsea el string que arma revisar(); el formato es nuestro.
        # Si la UI necesita mas campos, que revisar() devuelva tuplas.
        filas = [
            {"Origen": "Regla", "Campo": c, "Observación": o}
            for c, o in (re.match(r"\[(\w+)\] (.*)", x).groups() for x in obs)
        ]

        prosa, descartados, error = [], [], None
        if usar_ia:
            with st.spinner(f"Revisando prosa con {modelo}…"):
                try:
                    prosa, descartados = revisar_prosa(txt, "\n".join(minutas), modelo)
                except Exception as e:  # 503 tras los reintentos
                    error = str(e)
            filas += [
                {
                    "Origen": "IA",
                    "Campo": "Prosa",
                    "Observación": f"«{h['encontrado']}» debe decir «{h['correccion']}»"
                    f"   ({h['respaldo']})",
                }
                for h in prosa
            ]

        st.subheader(nombre)
        a, b, c = st.columns(3)
        a.metric(
            "Observaciones", len(filas), f"{len(prosa)} de prosa" if usar_ia else None
        )
        b.metric(
            "Extracción + análisis",
            f"{segundos:.1f} s",
            help="Solo el cómputo local. El OCR se cachea por hash del archivo: "
            "la primera pasada de cada imagen cuesta ~4 s, las siguientes 0.",
        )
        c.metric(
            "Descartados por el filtro",
            len(descartados),
            help="Hallazgos del modelo que no sobrevivieron la validación mecánica.",
        )

        if error:
            st.warning(
                f"La revisión de prosa falló y se muestran solo las reglas: {error}"
            )
        if not filas:
            st.success("Sin observaciones: el borrador concuerda con las fuentes.")
            continue
        st.dataframe(pd.DataFrame(filas), width="stretch", hide_index=True)

        if descartados:
            with st.expander(f"{len(descartados)} hallazgos del modelo bloqueados"):
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Señalaba": h.get("encontrado"),
                                "Proponía": h.get("correccion"),
                                "Motivo del descarte": h["descartado_por"],
                            }
                            for h in descartados
                        ],
                    ),
                    width="stretch",
                    hide_index=True,
                )

    with st.expander("Texto extraído (lo que realmente se comparó)"):
        for nombre, txt in (fuentes | destinos).items():
            st.text_area(nombre, txt, height=180)
