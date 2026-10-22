# Scraping de catálogos — Mercados e instituciones

Este directorio aloja los scripts de la **segunda línea de scraping** del proyecto: catálogos
de precios de productos en mercados e instituciones cubanas (ferreterías, (super)mercados,
organismos, etc.), distintos de los anuncios clasificados de Revolico.

Los scripts de Revolico (`scraping/scraper_revolico*.py`, `scraping/pipeline.py`) y los de
análisis (`scripts/`) **no se tocan** desde aquí.

---

## 1. Instituciones a scrapear

> **Espacio reservado — completar antes de escribir el primer script.**
> Añade una fila por institución. Deja en blanco lo que aún no sepas.

| # | Institución | URL / sección | Tipo de catálogo | Cobertura (provincias / categorías) | Campos esperados | Anti-bot | Estado | Script |
|---|---|---|---|---|---|---|---|---|
| 1 | MZ Products | `https://www.mzproducts.com/categoria-producto/transporte/triciclos-transporte/` | Precios de venta (importación a Cuba) | Vehículos > Transporte > Triciclos | id, nombre_importadora, precio_usd, marca, modelo, tipo, tiene_panel_solar, capacidad_carga_kg, autonomia_km, voltaje_bateria, disponibilidad, url, fecha_scraping | ninguno (requests + bs4 bastan) | **Funcionando** (7 triciclos) | `scraper_mzproducts.py` |
| 2 |  |  |  |  |  |  | Pendiente | `scraper_<institucion>.py` |
| 3 |  |  |  |  |  |  | Pendiente | `scraper_<institucion>.py` |
| 4 |  |  |  |  |  |  | Pendiente | `scraper_<institucion>.py` |
| 5 |  |  |  |  |  |  | Pendiente | `scraper_<institucion>.py` |

**Leyenda**

- **Tipo de catálogo:** precios de venta / precios mayoristas / catálogo de productos / tarifario /
  licitaciones / inventarios.
- **Anti-bot:** `requests` (HTTP simple), `curl_cffi` (TLS fingerprint), `nodriver` (Chrome real),
  `playwright`, ninguno.
- **Estado:** `Pendiente` → `En curso` → `Funcionando` → `Descartado` (con motivo).

### Notas por institución

<!-- Una nota corta por institución: peculiaridades del sitio, paginación, sesión obligatoria,
     captcha, rate limit observado, campos que no se pueden extraer. -->

- **MZ Products** — WooCommerce con tema Woodmart + Elementor.
  - Descubrimiento: la categoría de triciclos lista los 7 productos sin paginación;
    la búsqueda `?s=triciclo&post_type=product` devuelve 9 resultados (2 son
    "extensores de rango" que sólo mencionan triciclos en la descripción) y la
    página 2 da 404 → no hay paginación real.
  - Precio: JSON-LD `offers[0].price` en USD. Ojo con los precios de productos
    relacionados que también están en la página; el script toma el del widget
    `.wd-single-price` y el JSON-LD de la ficha.
  - Disponibilidad: `outofstock` / `instock` viven en la clase del `<article>`
    del producto, no en el `<body>`; la etiqueta "Sin existencias" la pinta el
    JS, por eso se reconstruye desde la clase.
  - Specs: dos formatos (`<strong>Etiqueta:</strong> Valor` y `Etiqueta: Valor`).
    El editor parte algunos valores dentro del `<strong>` ("<strong>Potencia del
    motor: 3</strong>000W"), así que el parseo usa el primer `:` del texto plano.
  - Sin taxonomía de marcas: la marca es la propia importadora ("MZ Products").
  - `tiene_panel_solar` = false en los 7: "Panel de instrumentos" no cuenta.
  - Salida: `scraping/data/catalogos/mzproducts_raw.json` y
    `data/processed/catalogos/mzproducts_limpio.csv`.
  - Comando: `python scraping/catalogos/scraper_mzproducts.py` (ficha única:
    `--solo <URL>`).

---

## 2. Estructura de carpetas

```
scraping/
├── catalogos/                    # ← scripts de esta línea (tú escribes aquí)
│   └── README.md
└── data/
    └── catalogos/                # ← crudo: HTML/JSON por página (IGNORADO por git)
        ├── .gitkeep
        └── manifest_<institucion>.json   # ← metadata liviana, SÍ se versiona

data/processed/catalogos/         # ← salida limpia en CSV (se versiona)
    ├── .gitkeep
    └── <institucion>.csv
```

**Regla de oro:** el crudo nunca se versiona; el CSV limpio siempre.

---

## 3. Convenciones

### Scripts (`scraping/catalogos/`)

- Nombre: `scraper_<institucion>.py` (minúsculas, sin acentos, `_` como separador).
- Un script por institución. Si una institución tiene varios catálogos, un solo script con
  subcomandos o flags (`--seccion`, `--paginas`).
- Ejecutar **siempre desde la raíz del proyecto**: `python scraping/catalogos/scraper_x.py`.
- Rutas ancladas con `Path(__file__).parent.parent.parent` para las salidas, para que no dependan
  del CWD (a diferencia de los scripts de Revolico).
- Respetar las reglas del proyecto: pausa ≥ 3 s entre peticiones, `requests` con timeout y
  `User-Agent` identificable, sin resolución automática de CAPTCHAs.

### Crudos (`scraping/data/catalogos/`)

- Un archivo por página/endpoint: `<institucion>_p<NNN>.html` (o `.json` si es endpoint JSON).
- Formato de salida del sitio preservado tal cual, sin transformar.
- Metadata en `manifest_<institucion>.json` (SÍ se versiona): URL, fecha de descarga, código HTTP,
  hash del contenido, nº de items extraídos, notas.

### Salida limpia (`data/processed/catalogos/`)

- Un CSV por institución: `<institucion>.csv`, UTF-8, separador `,`.
- Cabecera estable y documentada en el README de la institución o en un `SCHEMA` al inicio del script.
- Filas: un item del catálogo por fila. Nada de campos embebidos como JSON dentro de una celda.
- Sin valores inventados: si un campo no está en el origen, celda vacía.

---

## 4. Checklist antes de dar por terminado un scraper

- [ ] Script en `scraping/catalogos/` con nombre estandarizado.
- [ ] Crudo guardado en `scraping/data/catalogos/` y **no** commiteado.
- [ ] `manifest_<institucion>.json` generado y commiteado.
- [ ] CSV generado en `data/processed/catalogos/`.
- [ ] Re-ejecución idempotente (no duplica filas si se corre dos veces).
- [ ] Probado con `source venv/bin/activate` desde la raíz.
- [ ] Fila completada en la tabla de la sección 1.
- [ ] Entrada en `JOURNAL.md` + `HANDOFF.md` actualizado.

---

## 5. Estado actual

- **MZ Products**: scrapeado completo. 7 triciclos extraídos, 0 errores
  (ejecución del 2026-10-22).
- Resto de instituciones: pendiente de definir la lista.
