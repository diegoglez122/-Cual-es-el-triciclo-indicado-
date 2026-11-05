# Estudio de Mercado: Triciclos en Cuba

**Subtema: ¿Cuál es el triciclo indicado?**
Introducción a la Ciencia de Datos · Autor: Diego Miguel González Marín · Fecha: Noviembre 2026

Este proyecto nació de una pregunta práctica: si una persona en Cuba quiere comprar un triciclo para trabajar, ¿qué tipo le conviene según su presupuesto y su uso? No es una teoría, es una decisión de inversión real que miles de cubanos toman cada año.

## Tabla de contenidos:
1. Introducción
2. Objetivos del proyecto
3. Fuentes de datos
4. Estructura del análisis
5. Resultados obtenidos
6. Conclusiones
7. ¿Cómo ejecutar el proyecto?
8. Notas finales

## 1. Introducción
Este estudio analiza el mercado de triciclos en Cuba a partir de dos tipos de evidencia: anuncios publicados en Revolico (obtenidos mediante web scraping) y encuestas de campo a personas que trabajan con triciclos. Los datos se procesan siguiendo el pipeline de la asignatura: capturar, preprocesar, estructurar, procesar, analizar y presentar.

El análisis compara la oferta del mercado informal con el formal (importadoras) y evalúa la rentabilidad según la modalidad de uso: Pasaje Urbano, Pasaje Intermunicipal, Carga y Mixto. El proyecto se centra en triciclos eléctricos, de combustión e híbridos, e incluye una aplicación web interactiva para que cualquier persona pueda explorar el mercado y recibir una recomendación.

## 2. Objetivos del proyecto

### 2.1 Objetivo principal
Identificar qué tipo de triciclo resulta más conveniente comprar en Cuba según el uso previsto, comparando precios, características y rentabilidad, y ofrecer una herramienta interactiva que oriente la decisión de compra.

### 2.2 Objetivos secundarios
- Caracterizar los precios del mercado informal (Revolico) y compararlos con el mercado formal (catálogo de importadoras).
- Determinar qué uso es más rentable (carga vs. pasaje) basándonos en los ingresos diarios reportados.
- Describir las variables que influyen en la oferta: tipo (eléctrico/híbrido/combustión), marca, autonomía y capacidad de carga.
- Analizar costos, ganancias, fallas mecánicas y nivel de formalidad legal reportados por los trabajadores.
- Publicar los resultados en una aplicación web gratuita y reproducible.

## 3. Fuentes de datos
Para fundamentar el análisis se integraron tres fuentes:
- **Revolico:** 769 registros extraídos por scraping; tras la limpieza quedaron **757 anuncios únicos** (12 duplicados descartados), todos con precios en USD.
- **Catálogo de importadoras:** Extracción de **32 modelos** del mercado formal (MZ Products, Kikihabana y Nihao53), con tipo, precio, capacidad y disponibilidad.
- **Encuestas de campo:** **40 entrevistas** a dueños y choferes de triciclos, abarcando variables operativas, económicas y mecánicas.

## 4. Estructura del análisis

### 4.1 Estructura de los datos
- **4.1.1 Datos crudos (`data/raw/`):** Contiene los anuncios tal como salieron del scraping de Revolico y las encuestas sin modificar. Son la fuente primaria.
- **4.1.2 Datos normalizados (`triciclos_aceptados_normalizado.json`):** Contiene los 757 anuncios únicos y válidos. Esquema: `id`, `titulo`, `precio_publicado`, `moneda_original`, `marca_detectada`, `tipo_triciclo`, `ubicacion`, `municipio`, `autonomia_km`, `enlace`.
- **4.1.3 Esquemas de validación:** Archivos JSON que definen los campos obligatorios para aceptar o descartar un anuncio.
- **4.1.4 Catálogo de importadoras (`catalogo_consolidado.csv`):** Registro unificado de los 32 triciclos formales, permitiendo la comparación directa.
- **4.1.5 Encuestas de campo (`encuestas.json`):** Registro estructurado y validado de las 40 respuestas.

### 4.2 Estructura del código
El código está organizado en:
- `scraping/`: Scripts de extracción web.
- `scripts/`: Pipeline de análisis (`normalizar.py`, `clustering.py`, `insights_encuestas.py`, etc.).
- `data/`: Datos crudos y procesados.
- `docs/`: Informes, gráficos finales y documentación.
- `app/`: Aplicación web en Streamlit.

### 4.3 Aplicación web
Desarrollada con Streamlit y desplegada gratis en Render. Permite alternar entre buscar en Importadoras o en Revolico, filtrando por presupuesto, tipo de triciclo, uso y provincia. Está disponible en: **[https://cual-es-el-triciclo-indicado.onrender.com](https://cual-es-el-triciclo-indicado.onrender.com)**

### 4.4 Retos Técnicos Superados
Durante el desarrollo del proyecto se presentaron desafíos técnicos que requirieron soluciones avanzadas de ingeniería de datos:
- **Limpieza y normalización:** Los datos crudos presentaban inconsistencias de tipeo (ej. "Rali" vs "Raly") y formatos de texto mixtos (ej. rangos de autonomía como "120-180 km"). Se desarrollaron scripts de normalización con Expresiones Regulares (Regex) para estandarizar los datos.
- **Optimización del Despliegue (OOM Error):** El despliegue inicial en Streamlit Cloud falló por falta de memoria (Out of Memory) al intentar compilar librerías pesadas como `scipy` en versiones muy recientes de Python. Se solucionó separando las dependencias de desarrollo en un archivo `requirements-dev.txt` y dejando solo las dependencias de producción (`streamlit`, `pandas`) en el `requirements.txt`.

## 5. Resultados obtenidos
- **Precios:** El precio promedio en el mercado informal (Revolico) es de **$4,278 USD**, mientras que los encuestados reportaron haber pagado **$4,005 USD** en promedio, frente a los **$3,570 USD** de las importadoras. Existe un sobreprecio del 20% en el mercado informal.
- **Precios por tipo:** En el catálogo formal, los triciclos de combustión son los más caros (promedio $4,316 USD), seguidos por los eléctricos ($3,453 USD) e híbridos ($3,249 USD). El 68% de la oferta formal es eléctrica.
- **Relación técnica:** En las importadoras, solo 4 de los 32 modelos declaran autonomía. Los modelos de combustión tienen la mayor capacidad (hasta 2,000 kg), mientras los eléctricos promedian 660 kg.
- **Rentabilidad por uso:** Los triciclos dedicados a **Carga** generan los mayores ingresos (promedio de **6,000 CUP/día**), superando a Pasaje Intermunicipal (4,750 CUP/día) y Pasaje Urbano (3,750 CUP/día).
- **Fallas y formalidad:** Las fallas más comunes son las **gomas** (23 de 40 reportes) y la **batería** (13 reportes); el motor casi no falla (3 reportes). La mayoría de los choferes opera con solo **2 documentos** legales.
- **Impacto Estatal:** El 37.5% de los encuestados se siente afectado por los triciclos estatales, y de ellos, el 66% reporta que sus ganancias han disminuido.
- **Clustering:** KMeans agrupó la oferta formal en 3 segmentos (Combustión Premium, Eléctricos de Carga Media e Híbridos Económicos) y a los compradores en 2 perfiles (Propietarios eléctricos de alto presupuesto [89%] y Dueños de híbridos mixtos [11%]).

### Visualizaciones
A continuación se presentan los gráficos generados a partir de los datos:
![Precios comparativos](grafico_01_precios.png)
![Tipos de triciclos](grafico_08_tipos.png)
![Fallas mecánicas](grafico_02_fallas.png)
![Documentos legales](grafico_03_documentos.png)
![Afectados por estatales](grafico_04_afectados.png)
![Impacto en ganancias](grafico_05_ganancias.png)
![Clústeres de importadoras](grafico_06_clusters_imp.png)
![Clústeres de clientes](grafico_07_clusters_cli.png)
## 6. Conclusiones
Comprar un triciclo en Cuba es una decisión financiera compleja. Los datos demuestran que, aunque importar sale un 20% más barato que comprar en el mercado informal, la falta de acceso a divisas y la burocracia empujan a los cubanos a pagar sobreprecios en el mercado local.

Si el objetivo es la máxima rentabilidad, los triciclos de carga son la mejor inversión, generando hasta 6,000 CUP diarios. Sin embargo, requieren un mantenimiento más exigente (fallas de gomas y batería). Para el usuario promedio (que representa el 89% de los encuestados), el triciclo eléctrico de carga media es el punto de equilibrio perfecto entre precio, capacidad y bajo costo operativo. El alto nivel de informalidad (falta de documentos) y la competencia estatal son los principales desafíos que enfrenta el sector.

## 7. ¿Cómo ejecutar el proyecto?
### 7.1 Requisitos
- Python 3.11
- Las librerías especificadas en `requirements.txt`

### 7.2 Pasos
1. Instalar dependencias: `pip install -r requirements.txt`
2. Ejecutar la normalización de datos: `python scripts/normalizar.py --aplicar`
3. Lanzar la aplicación: `streamlit run app/streamlit_app.py`

## 8. Notas finales
- Los precios de Revolico son precios publicados (de oferta), no necesariamente de venta final.
- No se dividió el análisis por municipio ni provincia por falta de tiempo y datos suficientes.
- Los anuncios cubren principalmente La Habana, Artemisa, Matanzas y Holguín, por lo que no representan a todo el país.
- El tamaño de la muestra de las encuestas (40 personas) limita la generalización de los resultados a nivel nacional, funcionando como una fotografía representativa del mercado actual.
- Código y datos disponibles en: **[https://github.com/diegoglez122/-Cual-es-el-triciclo-indicado-](https://github.com/diegoglez122/-Cual-es-el-triciclo-indicado-)**