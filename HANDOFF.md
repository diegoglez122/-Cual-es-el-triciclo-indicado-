# HANDOFF — Revolico Triciclos

**Asignación del proyecto (clase):** sábado 2026-09-26
**Última actualización:** sábado 2026-10-31
**Responsable:** diegogonza
**Estado general:** App MVP DESPLEGADA y funcional en Streamlit Cloud. Rediseño visual completado (tarjetas, gráficos nativos, CSS personalizado). Scraping y análisis de datos COMPLETADOS. Pendiente: integrar Datawrapper y redactar el informe final.

---

## 1. Objetivo

Extraer anuncios de **triciclos** de Revolico.com (Vehículos > Motos Eléctricas y Triciclos), aplicar 7 filtros estrictos y generar:

- `data/raw/triciclos_aceptados.json` — cumplen TODOS los filtros.
- `scraping/data/triciclos_descartados.json` — rechazados, con motivo y datos crudos.

**Meta original:** 500 aceptados → **SUPERADA** (769).
**Decisión del usuario (2026-10-17):** parar el scraping. p91–253 NO se harán.
**Restricción dura:** SOLO triciclos. Nada de motos, bicimotos, cuatriciclos ni otros vehículos.

---

## 2. Estado actual

- **Páginas scrapeadas:** p1–p90 (de 253 reales). Los 90 states + 90 raw están integrados en `scraping/data/` (los p31–60 venían de `_p31_60_hold/`, ya eliminada).
- **Permalinks únicos:** 1378. **Caché:** 1298 descripciones en `scraping/data/cache_descripciones.json`.
- **Pipeline:** 1378 procesados → **769 aceptados**, **609 descartados**.
- **Descartes por motivo:**
  - `AUTONOMIA_NO_INDICADA`: 397
  - `MARCA_NO_DETECTADA`: 285
  - `TIPO_NO_DETERMINADO`: 125
  - `DESCARGA_FALLIDA`: 80 (challenge Cloudflare cortado, no anuncios reales perdidos)
  - `PRECIO_INVALIDO`: 71
  - `MONEDA_NO_DETECTADA`: 71
- **Duplicados detectados** (por `(gcsKey, phone)`): 12 grupos / 24 registros → **757 tras dedup** (ya aplicado en `data/processed/triciclos_aceptados_normalizado.json`; `data/processed/duplicados_descartados.json` registra los descartes).
- Cloudflare resuelto con perfil persistente `chrome_profile_revolico/` + `DISPLAY=:0` + Chrome real.
- **Reorganización (2026-10-18):** raíz limpia; scripts de scraping en `scraping/`, crudos y backups en `scraping/data/`, informe en `docs/`, datos limpios en `data/`. Rutas de los scripts ajustadas (backups en `scraping/data/*.bak.20261018_123614`).
- **App MVP (2026-10-31):** desplegada y funcional en Streamlit Cloud. Nuevo diseño con hero, tarjetas, gráficos nativos (`st.bar_chart`, `st.scatter_chart`) y CSS personalizado.
- **Despliegue optimizado:** `requirements.txt` reducido a `pandas` + `streamlit`; dependencias pesadas del pipeline en `requirements-dev.txt`; `runtime.txt` fija Python 3.11; `packages.txt` incluye `build-essential`.
- **API de recomendación:** `app/recommend.py` expone `cargar_catalogo()`, acepta `catalogo=` y devuelve `modelo`, `disponibilidad`, `tiene_panel_solar` y `fecha_scraping` para las tarjetas.

---

## 3. Estado por categoría

### Estable
- `scraping/pipeline.py` con 7 filtros (respaldado en `scraping/data/pipeline.py.bak.20261018_123614` y versiones anteriores).
- Esquemas JSON (`triciclo_aceptado_schema.json`, `triciclo_descartado_schema.json`).
- Validación con `scraping/validar_salidas.py` (aceptados en `data/raw/`, descartados en `scraping/data/`).
- Caché incremental `scraping/data/cache_descripciones.json` (1298 entradas, snapshot `cache_descripciones.1298.json`).
- Chrome + perfil persistente funcionando contra Cloudflare.
- `scripts/normalizar.py` apunta a `scraping/data/revolico_state_p*.json` para el índice de dedup.
- `scripts/analisis_mercado.py` escribe el informe en `docs/informe_mercado.md` (`drivers_precio.py` lo importa).
- `app/streamlit_app.py` — UI rediseñada y desplegada en Streamlit Cloud.
- `app/recommend.py` — motor de recomendación con API compatible con las tarjetas.
- `requirements.txt` (runtime mínimo) y `requirements-dev.txt` (pipeline pesado).

### Completado
- Scraping p1–p90. Meta 500 superada (769 → 757 con dedup).
- Detección de duplicados con `scripts/check_duplicados.py`.
- Reorganización de archivos (raíz limpia, `scraping/`, `docs/`).
- Rediseño de la UI y despliegue exitoso en Streamlit Cloud (2026-10-31).

### En progreso / pendiente
- Integrar los gráficos de Datawrapper en la pestaña "Entiende el Mercado".
- Redactar `docs/informe_final.md` con los resultados del análisis.

---

## 4. Bloqueante actual

**No hay bloqueante.** La app MVP está desplegada y funcional en Streamlit Cloud. El despliegue quedó optimizado con Python 3.11 y un `requirements.txt` mínimo. El análisis de datos está completado; solo queda la capa de visualización e informe final.

---

## 5. Próximos pasos ordenados

1. **Integrar Datawrapper** en la pestaña "Entiende el Mercado" con los CSVs exportados (`dw_tipos`, `dw_precios_importadora`, `dw_precio_tipo`, etc.).
2. **Redactar `docs/informe_final.md`** con los resultados del scraping, EDA, clustering y las conclusiones del estudio.

---

## 6. Comandos útiles

```bash
cd ~/proyectos/revolico-triciclos
source venv/bin/activate
python scraping/pipeline.py          # desde la raíz (rutas relativas al CWD)
python scraping/validar_salidas.py
python scripts/check_duplicados.py   # desde la raíz (usa rutas relativas)
python scripts/normalizar.py         # anclado vía __file__
python scripts/analisis_mercado.py   # escribe docs/informe_mercado.md
```

---

## 7. Archivos clave

- `scraping/pipeline.py` — script principal del pipeline de filtros.
- `scraping/data/cache_descripciones.json` — 1298 descripciones cacheadas. **No borrar.**
- `data/raw/triciclos_aceptados.json` — 769 aceptados (entrada de la normalización).
- `scraping/data/triciclos_descartados.json` — 609 descartados.
- `scraping/data/triciclos_aceptados.769.json` — snapshot del conteo post-pipeline.
- `data/processed/triciclos_aceptados_normalizado.json` — 757 aceptados (post-dedup).
- `data/processed/duplicados_descartados.json` — 24 duplicados descartados.
- `docs/informe_mercado.md` — informe de mercado.
- `app/streamlit_app.py` — UI rediseñada y desplegada en Streamlit Cloud.
- `app/recommend.py` — motor de recomendación (`cargar_catalogo`, `recomendar_triciclo`).
- `.streamlit/config.toml` — tema base de Streamlit.
- `requirements.txt` — dependencias mínimas del runtime (`pandas`, `streamlit`).
- `requirements-dev.txt` — dependencias pesadas del pipeline (`scipy`, `scikit-learn`, etc.).
- `runtime.txt` — Python 3.11 para Streamlit Cloud.
- `packages.txt` — `build-essential` para el entorno de despliegue.
- `scripts/check_duplicados.py`, `scripts/normalizar.py`, `scripts/analisis_mercado.py`, `scripts/drivers_precio.py` — análisis e informe.
- `chrome_profile_revolico/` — perfil persistente que resuelve Cloudflare.
- `scraping/scraper_revolico_nodriver.py`, `scraping/prefetch_descripciones_nodriver.py` — scraping con Chrome real.
- `scraping/data/revolico_raw_p1-p90.html`, `scraping/data/revolico_state_p1-p90.json` — datos crudos (p1–p90 completos).
- `scraping/data/*.bak*` — todos los backups históricos (incl. `pipeline.py.bak*`, `*.bak.20261018_123614`).
- `JOURNAL.md`, `HANDOFF.md`, `AGENTS.md` — documentación del proyecto.

---

## 8. Lo que NO se debe hacer

- No reanudar el scraping de p91 en adelante sin petición explícita del usuario.
- No ejecutar `python - << 'EOF'` con scripts largos dentro de opencode (se cuelga).
- No modificar `scraping/pipeline.py` mientras corre; si se toca, crear `.bakN` en `scraping/data/` antes.
- No hacer `git add` de `venv/`, `scraping/data/` ni los JSON de salida (`data/raw/`, `data/processed/`).
- No borrar `scraping/data/cache_descripciones.json`.
- No tocar las motos: el trabajo es SOLO sobre triciclos.
- No bajar `PAUSA` por debajo de 3s si se retoma scraping.
- Los scripts de `scraping/` usan rutas relativas al CWD: ejecutarlos SIEMPRE desde la raíz del proyecto.
- `scripts/check_duplicados.py` usa ruta relativa: ejecutar SIEMPRE desde la raíz.

---

## 9. Registro de sesiones (opencode)

| Fecha | Sesión | Directorio | Evento |
|---|---|---|---|
| 2026-10-03 13:31 | nimble-engine | triciclos_cuba | Explorar archivos del proyecto |
| 2026-10-03 15:08 | proud-otter | triciclos_cuba | Plan del pipeline |
| 2026-10-04 11:56 | stellar-cabin | triciclos_cuba | Tres tipos de triciclos |
| 2026-10-06 12:24 | tidy-rocket | triciclos_cuba | Requisitos para scraping |
| 2026-10-06 13:34 | silent-knight | /home/diegogonza | Estructura `triciclos-revolico/` |
| 2026-10-06 14:11 | crisp-mountain | revolico-triciclos | Discusión de agentes |
| 2026-10-06 14:25 | witty-comet | revolico-triciclos | Scraping a JSON |
| 2026-10-06 14:25 | brave-planet | revolico-triciclos | Scrape 2 páginas (subagente) |
| 2026-10-17 | (sesión anterior) | revolico-triciclos | Scraping p61-90 + pipeline 769 + reorganización scripts/ |
| 2026-10-18 | (sesión anterior) | revolico-triciclos | Reorganización final: scraping/, docs/, raíz limpia + ajuste de rutas |
| 2026-10-31 | (sesión de rediseño) | revolico-triciclos | Rediseño UI + despliegue en Streamlit Cloud + requirements optimizado |

## Actualización 2026-10-31 (App MVP desplegada)

- **Estado general:** App MVP desplegada y funcional en Streamlit Cloud con el nuevo diseño.
- **UI:** hero, tarjetas de resultados, badges, chips, gráficos nativos y CSS personalizado.
- **Despliegue:** `requirements.txt` mínimo para evitar OOM; `requirements-dev.txt` conserva las dependencias pesadas; Python 3.11 fijado en `runtime.txt`.
- **Datos:** 757 anuncios analizados, 32 modelos de importadoras y 40 respuestas de encuesta.
- **Próximos pasos:**
  1. Integrar los gráficos de Datawrapper en la pestaña "Entiende el Mercado".
  2. Redactar `docs/informe_final.md`.
