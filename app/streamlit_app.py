"""Interfaz web en Streamlit para el recomendador de triciclos."""

import sys
from pathlib import Path

import streamlit as st

# Streamlit ejecuta este archivo desde app/. Añadimos la raíz del proyecto
# para poder importar el paquete app.recommend.
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.recommend import recomendar_triciclo

st.set_page_config(page_title="Triciclos Cuba", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #ffffff 0%, #f0f2f6 100%);
    }
    h1 {
        text-align: center;
        color: #0b3d66;
        font-weight: 800;
    }
    .footer {
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #d6dbe4;
        text-align: center;
        color: #6b7280;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Triciclos Cuba")
st.caption("Recomendador y análisis del mercado de triciclos en Cuba.")

tab_recomendador, tab_mercado, tab_metodologia = st.tabs(
    ["Recomendador", "Entiende el Mercado", "Metodología"]
)

with tab_recomendador:
    with st.form("form_recomendador"):
        presupuesto = st.number_input(
            "Presupuesto (USD)",
            min_value=0,
            value=4000,
            step=100,
        )
        uso = st.selectbox("Uso", ["Pasajeros", "Carga"])
        tipo = st.selectbox(
            "Tipo", ["Me da igual", "Eléctrico", "Combustible", "Híbrido"]
        )
        prioridad = st.selectbox(
            "Prioridad", ["Precio", "Autonomía", "Capacidad"]
        )
        solo_en_stock = st.checkbox("Solo mostrar triciclos en stock")
        enviado = st.form_submit_button("Buscar")

    # Guardamos los resultados en session_state para que sobrevivan a los
    # reruns de Streamlit y al cambio de pestañas.
    if enviado:
        st.session_state["resultados"] = recomendar_triciclo(
            presupuesto,
            uso,
            tipo,
            prioridad,
            solo_en_stock,
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
        st.info("Ajusta los criterios y pulsa **Buscar**.")
    else:
        criterios = st.session_state.get("criterios", {})
        stock_texto = "sí" if criterios.get("solo_en_stock") else "no"
        st.caption(
            f"Presupuesto: {criterios.get('presupuesto')} USD · "
            f"Uso: {criterios.get('uso')} · "
            f"Tipo: {criterios.get('tipo')} · "
            f"Prioridad: {criterios.get('prioridad')} · "
            f"Solo en stock: {stock_texto}"
        )

        resultados = st.session_state.get("resultados")
        if resultados is None or resultados.empty:
            st.warning(
                "No se encontraron triciclos con esos criterios. "
                "Prueba a subir el presupuesto o cambiar el uso/tipo."
            )
        else:
            st.dataframe(
                resultados,
                width="stretch",
                hide_index=True,
                column_config={
                    "marca": "Marca",
                    "nombre_importadora": "Importadora",
                    "precio_usd": st.column_config.NumberColumn(
                        "Precio (USD)", format="$%.0f"
                    ),
                    "capacidad_carga_kg": st.column_config.NumberColumn(
                        "Capacidad (kg)", format="%.0f kg"
                    ),
                    "autonomia_km": st.column_config.NumberColumn(
                        "Autonomía (km)", format="%.0f km"
                    ),
                    "tipo": "Tipo",
                    "url": st.column_config.LinkColumn("Enlace"),
                },
            )

with tab_mercado:
    st.markdown(
        "Explora cómo se distribuye la oferta de triciclos en Cuba. "
        "Los gráficos interactivos se publicarán aquí una vez estén "
        "disponibles en Datawrapper."
    )

    col_tipos, col_importadoras, col_precios = st.columns(3)

    with col_tipos:
        st.info(
            "Placeholder: gráfico de tipos de triciclos (eléctrico, "
            "combustión e híbrido)."
        )

    with col_importadoras:
        st.info(
            "Placeholder: precio medio por importadora "
            "(MZ Products, Kikihabana y Nihao53)."
        )

    with col_precios:
        st.info(
            "Placeholder: distribución de precios por tipo de triciclo."
        )

with tab_metodologia:
    st.markdown(
        """
### Scraping

Los datos de Revolico se extrajeron de la subcategoría de Motos Eléctricas
y Triciclos. Se recorrieron las páginas 1 a 90 de un total de 253, obteniendo
1378 anuncios únicos. Tras aplicar los filtros de calidad (precio, tipo,
marca, ubicación, fecha, autonomía y moneda) quedaron 769 anuncios aceptados
y 609 descartados. Después de eliminar duplicados, el conjunto final quedó
en 757 anuncios.

El catálogo de importadoras reúne 32 modelos de MZ Products, Kikihabana y
Nihao53, con precio, capacidad de carga, autonomía y disponibilidad.

### KMeans

Se aplicó clustering KMeans para segmentar la oferta. En importadoras se
obtuvieron 3 segmentos: combustión premium, eléctricos de carga media e
híbridos económicos. En las encuestas se obtuvieron 2 perfiles: propietarios
de eléctricos con alto presupuesto e híbridos de uso mixto.

### Limitaciones de la muestra

- El scraping cubre 90 de las 253 páginas de la categoría, por lo que la
  muestra no es exhaustiva.
- La autonomía solo está disponible en 4 de los 32 modelos del catálogo.
- La capacidad de carga falta en 10 de los 32 modelos.
- La encuesta cuenta con 40 respuestas válidas y no representa a todos los
  compradores del país.
- Los precios de catálogo pueden variar y no incluyen costos de envío,
  trámites o impuestos.

La recomendación es orientativa y no sustituye una cotización formal con la
importadora.
"""
    )

st.markdown(
    '<div class="footer">Proyecto de Ciencia de Datos - 2026</div>',
    unsafe_allow_html=True,
)
