"""Interfaz web en Streamlit para el recomendador de triciclos."""

import sys
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.recommend import cargar_catalogo, recomendar_triciclo

ANUNCIOS_ANALIZADOS = 757
RESPUESTAS_ENCUESTA = 40

st.set_page_config(
    page_title="Triciclos Cuba",
    page_icon="🛺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ESTILOS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
:root {
    --ink: #12263A; --teal: #0E7C86; --sun: #F2B705;
    --mute: #5B6B7A; --line: #DCE3E8; --surface: #FFFFFF;
}
html, body, .stApp, [data-testid="stMarkdownContainer"], .hero, .card {
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.block-container { max-width: 1080px; padding-top: 1.5rem; }
#MainMenu, footer { visibility: hidden; }

.hero {
    background: var(--ink); border-radius: 18px;
    border-bottom: 6px solid var(--sun);
    padding: 2rem 1.75rem; margin-bottom: 1.25rem;
}
.hero-title { color: #FFFFFF; font-weight: 800; font-size: 2.2rem; line-height: 1.15; }
.hero-text { color: #C9D6E2; margin-top: .5rem; max-width: 52ch; font-size: 1.02rem; line-height: 1.5; }

.card {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 14px; padding: 1.1rem 1.2rem; margin-bottom: .5rem;
}
.card-top { border-left: 6px solid var(--sun); }
.badge {
    display: inline-block; background: var(--sun); color: var(--ink);
    font-weight: 700; font-size: .78rem; border-radius: 999px;
    padding: .15rem .65rem; margin-bottom: .5rem;
}
.card-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
.card-title { font-size: 1.2rem; font-weight: 800; color: var(--ink); }
.card-sub { color: var(--mute); font-size: .9rem; }
.card-price { font-size: 1.6rem; font-weight: 800; color: var(--teal); }
.chips { margin: .6rem 0 .8rem; display: flex; gap: .4rem; flex-wrap: wrap; }
.chip { background: #E6F2F3; color: #0A5C64; border-radius: 999px; padding: .15rem .65rem; font-size: .8rem; font-weight: 600; }
.chip-warn { background: #FFF3CD; color: #7A5B00; }
.specs {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: .75rem; border-top: 1px solid var(--line); padding-top: .75rem;
}
.specs span { display: block; color: var(--mute); font-size: .78rem; }
.specs b { color: var(--ink); font-size: 1.05rem; }
.specs b.nd { color: var(--mute); font-weight: 400; font-size: .95rem; }

.footer {
    margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--line);
    text-align: center; color: var(--mute); font-size: .85rem;
}
</style>
"""
st.markdown(ESTILOS, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def obtener_catalogo():
    return cargar_catalogo()

def etiqueta(valor):
    if pd.isna(valor):
        return ""
    return str(valor).replace("_", " ").strip().capitalize()

def dato(valor, formato):
    if pd.isna(valor):
        return '<b class="nd">No disponible</b>'
    return f"<b>{formato.format(valor)}</b>"

def es_verdadero(valor):
    return str(valor).strip().lower() in {"true", "1", "si", "sí", "yes"}

def tarjeta_html(fila, destacada):
    modelo = escape(str(fila["modelo"])) if pd.notna(fila["modelo"]) else "Modelo sin nombre"
    importadora = escape(etiqueta(fila["nombre_importadora"]))
    marca = escape(str(fila["marca"])) if pd.notna(fila["marca"]) else ""
    subtitulo = importadora if not marca or marca == importadora else f"{importadora}, marca {marca}"

    chips = []
    if pd.notna(fila["tipo"]):
        chips.append(f'<span class="chip">{escape(etiqueta(fila["tipo"]))}</span>')
    if pd.notna(fila["disponibilidad"]):
        en_stock = str(fila["disponibilidad"]).strip().lower() in {"en stock", "in stock", "en_stock"}
        clase = "chip" if en_stock else "chip chip-warn"
        chips.append(f'<span class="{clase}">{escape(etiqueta(fila["disponibilidad"]))}</span>')
    if es_verdadero(fila["tiene_panel_solar"]):
        chips.append('<span class="chip">Panel solar</span>')

    precio = "Precio no disponible" if pd.isna(fila["precio_usd"]) else f"${fila['precio_usd']:,.0f}"
    badge = '<div class="badge">Mejor opción para tu prioridad</div>' if destacada else ""
    clase_tarjeta = "card card-top" if destacada else "card"

    return (
        f'<div class="{clase_tarjeta}">{badge}'
        f'<div class="card-head"><div>'
        f'<div class="card-title">{modelo}</div>'
        f'<div class="card-sub">{subtitulo}</div></div>'
        f'<div class="card-price">{precio}</div></div>'
        f'<div class="chips">{"".join(chips)}</div>'
        f'<div class="specs">'
        f'<div><span>Capacidad de carga</span>{dato(fila["capacidad_carga_kg"], "{:,.0f} kg")}</div>'
        f'<div><span>Autonomía</span>{dato(fila["autonomia_km"], "{:,.0f} km")}</div>'
        f'</div></div>'
    )

catalogo = obtener_catalogo()

st.markdown(
    '<div class="hero">'
    '<div class="hero-title">Triciclos Cuba</div>'
    '<div class="hero-text">Compara triciclos de importadoras en Cuba según tu '
    'presupuesto, el uso que le vas a dar y lo que más te importa.</div>'
    '</div>',
    unsafe_allow_html=True,
)

tab_recomendador, tab_mercado, tab_metodologia = st.tabs(
    ["Recomendador", "Entiende el Mercado", "Metodología"]
)

with tab_recomendador:
    with st.container(border=True):
        with st.form("form_recomendador", border=False):
            col_izq, col_der = st.columns(2)
            with col_izq:
                presupuesto = st.number_input(
                    "Presupuesto máximo (USD)", min_value=0, value=4000, step=100
                )
                uso = st.radio("¿Para qué lo vas a usar?", ["Pasajeros", "Carga"], horizontal=True)
            with col_der:
                tipo = st.selectbox(
                    "Tipo de motor", ["Me da igual", "Eléctrico", "Combustible", "Híbrido"]
                )
                prioridad = st.radio(
                    "¿Qué te importa más?", ["Precio", "Autonomía", "Capacidad"], horizontal=True
                )
            solo_en_stock = st.checkbox("Mostrar solo los que están en stock")
            enviado = st.form_submit_button("Buscar triciclos", type="primary", use_container_width=True)

    if enviado:
        st.session_state["resultados"] = recomendar_triciclo(
            presupuesto, uso, tipo, prioridad, solo_en_stock, catalogo=catalogo
        )
        st.session_state["busqueda_realizada"] = True
        st.session_state["criterios"] = {
            "presupuesto": presupuesto,
            "uso": uso,
            "tipo": tipo,
            "prioridad": prioridad,
            "solo_en_stock": solo_en_stock,
        }

    if not st.session_state.get("busqueda_realizada"):
        st.info("Elige tus criterios y pulsa **Buscar triciclos** para ver hasta 3 opciones.")
    else:
        criterios = st.session_state.get("criterios", {})
        st.subheader("Tus mejores opciones")
        st.caption(
            f"Hasta ${criterios.get('presupuesto', 0):,.0f} USD, para "
            f"{criterios.get('uso', '').lower()}, motor: {criterios.get('tipo', '').lower()}, "
            f"prioridad: {criterios.get('prioridad', '').lower()}"
            f"{', solo en stock' if criterios.get('solo_en_stock') else ''}."
        )

        if criterios.get("prioridad") == "Autonomía":
            con_dato = int(catalogo["autonomia_km"].notna().sum())
            st.warning(
                f"La autonomía solo está registrada en {con_dato} de {len(catalogo)} modelos. "
                "Los modelos sin ese dato aparecen al final de la lista."
            )

        resultados = st.session_state.get("resultados")
        if resultados is None or resultados.empty:
            st.warning(
                "No hay triciclos con esos criterios. Sube el presupuesto, "
                "cambia el tipo de motor o quita el filtro de stock."
            )
        else:
            for i, (_, fila) in enumerate(resultados.iterrows()):
                st.markdown(tarjeta_html(fila, destacada=(i == 0)), unsafe_allow_html=True)
                url = fila.get("url")
                if isinstance(url, str) and url.startswith("http"):
                    st.link_button("Ver ficha del modelo", url)
                st.write("")

            fechas = pd.to_datetime(resultados["fecha_scraping"], errors="coerce").dropna()
            if not fechas.empty:
                st.caption(f"Datos del catálogo al {fechas.max():%d/%m/%Y}. Los precios pueden cambiar.")

with tab_mercado:
    st.markdown(
        "Resumen de la oferta de las importadoras. Los gráficos de los anuncios de "
        "Revolico se añadirán cuando estén listos en Datawrapper."
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Modelos en el catálogo", len(catalogo))
    m2.metric("Importadoras", catalogo["nombre_importadora"].nunique())
    m3.metric("Anuncios analizados", ANUNCIOS_ANALIZADOS)
    m4.metric("Respuestas de encuesta", RESPUESTAS_ENCUESTA)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Modelos por tipo de motor**")
        por_tipo = catalogo["tipo"].map(etiqueta).value_counts()
        st.bar_chart(por_tipo, color="#0E7C86", x_label="Tipo", y_label="Modelos")
    with col_b:
        st.markdown("**Precio medio por importadora (USD)**")
        precio_medio = catalogo.groupby("nombre_importadora")["precio_usd"].mean().round(0)
        precio_medio.index = precio_medio.index.map(etiqueta)
        st.bar_chart(precio_medio, color="#12263A", x_label="Importadora", y_label="USD")

    st.markdown("**Precio frente a capacidad de carga**")
    puntos = catalogo.dropna(subset=["capacidad_carga_kg", "precio_usd"]).copy()
    puntos["tipo"] = puntos["tipo"].map(etiqueta)
    st.scatter_chart(
        puntos, x="capacidad_carga_kg", y="precio_usd", color="tipo",
        x_label="Capacidad de carga (kg)", y_label="Precio (USD)",
    )
    st.caption(
        f"Se muestran {len(puntos)} de {len(catalogo)} modelos: "
        "los demás no tienen capacidad de carga registrada."
    )

with tab_metodologia:
    st.markdown(
        """
### Scraping
Los datos de Revolico se extrajeron de la subcategoría de Motos Eléctricas
y Triciclos. Se recorrieron las páginas 1 a 90 de un total de 253, obteniendo
1378 anuncios únicos. Tras aplicar los filtros de calidad quedaron 769 anuncios aceptados
y 609 descartados. Después de eliminar duplicados, el conjunto final quedó en 757 anuncios.
El catálogo de importadoras reúne 32 modelos de MZ Products, Kikihabana y Nihao53.

### KMeans
Se aplicó clustering KMeans para segmentar la oferta. En importadoras se
obtuvieron 3 segmentos: combustión premium, eléctricos de carga media e
híbridos económicos. En las encuestas se obtuvieron 2 perfiles.

### Limitaciones de la muestra
- El scraping cubre 90 de las 253 páginas de la categoría.
- La autonomía solo está disponible en 4 de los 32 modelos.
- La capacidad de carga falta en 10 de los 32 modelos.
- La encuesta cuenta con 40 respuestas válidas.
"""
    )

st.markdown(
    '<div class="footer">Proyecto de Ciencia de Datos - 2026</div>',
    unsafe_allow_html=True,
) 
