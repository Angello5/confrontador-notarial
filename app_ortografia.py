"""Via determinista: reglas + diccionario, sin modelo de lenguaje.

  streamlit run app_ortografia.py --server.port 8503

No toca app.py. Aqui la ortografia la decide hunspell (es_PE), no Gemini, y el
resultado es el mismo en cada corrida. Incluye el bucle de curacion: las
palabras que el diccionario no conoce se marcan una vez como termino de la casa
o como errata, y no vuelven a preguntarse.
"""

import time
from pathlib import Path

import pandas as pd
import streamlit as st

from adaptadores.diccionario import (
    LISTA,
    agregar_a_lista,
    diccionario,
    lista_casa,
)
from adaptadores.extraccion import IMGS, leer
from nucleo import ortografia
from nucleo.verificar import catalogo, diagnostico, revisar, revisar_parrafos

CASA = "Es término de la casa"

st.set_page_config(page_title="Vía determinista", page_icon="📐", layout="wide")
st.title("Confrontamiento determinista")
st.caption(
    "Reglas para los datos duros · hunspell es_PE para la ortografía · sin modelo de "
    "lenguaje. La misma entrada da siempre exactamente la misma salida."
)


@st.cache_resource(show_spinner="Cargando el diccionario es_PE (una sola vez)…")
def diccionario_residente():
    """Se queda en RAM entre corridas: 0.3 s de carga y ~55 MB, una sola vez."""
    t = time.perf_counter()
    _, lemas = diccionario()
    return len(lemas), time.perf_counter() - t


def textos(archivos) -> dict[str, str]:
    import tempfile

    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        for f in archivos:
            p = Path(tmp) / f.name
            p.write_bytes(f.getbuffer())
            out[f.name] = leer(p)
    return out


def revisar_ortografia(texto: str, propios: set[str]):
    d, lemas = diccionario()
    return ortografia.revisar(texto, d, lemas, lista_casa(), propios)


n_lemas, seg_carga = diccionario_residente()
st.sidebar.metric("Lemas en el diccionario", f"{n_lemas:,}".replace(",", " "))
st.sidebar.caption(
    f"Cargado en {seg_carga:.2f} s · reside en RAM (~55 MB) mientras la app viva."
)
st.sidebar.divider()
st.sidebar.metric("Términos de la casa", len(lista_casa()))
st.sidebar.caption(
    f"Se guardan en `{LISTA.name}`. Siglas, jurídico y topónimos que "
    "el diccionario general no trae."
)
umbral = st.sidebar.slider("Umbral de similitud de párrafo (%)", 70, 100, 88)

izq, der = st.columns(2)
fuentes_up = izq.file_uploader(
    "Minuta y documentos del cliente", accept_multiple_files=True
)
borrador_up = der.file_uploader("Proyecto (borrador)", accept_multiple_files=True)

if st.button("Comparar", type="primary", disabled=not (fuentes_up and borrador_up)):
    st.session_state.resultado = None
    t0 = time.perf_counter()
    with st.spinner("Extrayendo texto…"):
        fuentes, destinos = textos(fuentes_up), textos(borrador_up)
        cat = catalogo(fuentes)
        minutas = [v for k, v in fuentes.items() if Path(k).suffix.lower() not in IMGS]
    t_extraccion = time.perf_counter() - t0

    # los nombres de las partes ya los valida la capa de reglas contra el DNI:
    # no tienen por que estar en el diccionario ni en la lista de la casa
    propios = {p for n in cat["NOMBRE"] for p in n.split()}

    for nombre, txt in destinos.items():
        st.subheader(nombre)
        if aviso := diagnostico(fuentes, txt):
            st.error(aviso)
            continue

        t1 = time.perf_counter()
        obs = revisar(cat, txt, umbral) + revisar_parrafos(minutas, txt, umbral)
        t_reglas = time.perf_counter() - t1

        t2 = time.perf_counter()
        faltas = revisar_ortografia(txt, propios)
        t_orto = time.perf_counter() - t2

        a, b, c, d = st.columns(4)
        a.metric("Datos duros", len(obs))
        b.metric("Ortografía", len(faltas))
        c.metric("Tiempo total", f"{t_extraccion + t_reglas + t_orto:.2f} s")
        d.metric("Solo ortografía", f"{t_orto:.2f} s")

        if obs:
            st.markdown("**Datos duros** — verificados contra la fuente")
            st.dataframe(
                pd.DataFrame([{"Observación": o} for o in obs]),
                width="stretch",
                hide_index=True,
            )
        else:
            st.success("Datos duros sin observaciones: coinciden con las fuentes.")

        if faltas:
            st.markdown("**Ortografía** — palabras que no son castellano válido")
            st.session_state.resultado = faltas
        else:
            st.success("Ortografía sin observaciones.")

# ---------- bucle de curacion ----------
if faltas := st.session_state.get("resultado"):
    st.divider()
    st.markdown("### Revisión de palabras desconocidas")
    st.caption(
        "Marca las que sean término de la notaría —siglas, jurídico, topónimos— y guárdalas. "
        "No se volverán a reportar. Lo que dejes sin marcar es una errata."
    )

    editable = st.data_editor(
        pd.DataFrame(
            [
                {
                    CASA: False,
                    "Palabra": w,
                    "Motivo": m,
                    "Sugerencia": s,
                }
                for w, m, s in faltas
            ]
        ),
        width="stretch",
        hide_index=True,
        disabled=["Palabra", "Motivo", "Sugerencia"],
        column_config={CASA: st.column_config.CheckboxColumn(width="small")},
    )

    marcadas = editable[editable[CASA]]["Palabra"].tolist()
    if st.button(
        f"Guardar {len(marcadas)} términos en la lista", disabled=not marcadas
    ):
        n = agregar_a_lista(marcadas)
        st.success(f"{n} términos guardados en {LISTA.name}. Vuelve a comparar.")
        st.session_state.resultado = [f for f in faltas if f[0] not in marcadas]
        st.rerun()
