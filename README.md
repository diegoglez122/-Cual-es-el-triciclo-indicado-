# Estudio de Mercado: Triciclos en Cuba

## 📌 Descripción
Proyecto de ciencia de datos para analizar el mercado de triciclos en Cuba, basado en extracción web (scraping de Revolico) y encuestas de campo. El objetivo es procesar, limpiar y normalizar los datos del mercado para identificar patrones de precios y segmentos.

## 📂 Estructura del Proyecto
- `data/`: Datos crudos (`raw/`) y procesados (`processed/`).
- `scripts/`: Pipeline de análisis de datos, normalización y deduplicación.
- `scraping/`: Scripts y datos de la fase de extracción web.
- `docs/`: Informes de mercado y documentación.
- `models/`: Espacio reservado para futuros modelos.

## 🚀 Cómo ejecutar
1. Instalar dependencias: `pip install -r requirements.txt`
2. Ejecutar la normalización: `python scripts/normalizar.py --aplicar`

## 📊 Resultados actuales
- 769 registros extraídos.
- 757 registros únicos normalizados.
- 12 duplicados descartados.
