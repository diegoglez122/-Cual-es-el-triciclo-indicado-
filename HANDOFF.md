# HANDOFF — Revolico Triciclos

**Asignación del proyecto (clase):** sábado 2026-09-26
**Última actualización:** domingo 2026-10-18
**Responsable:** diegogonza
**Estado general:** Scraping COMPLETADO. Meta superada. Fase de normalización + estudio de mercado. Reorganización de archivos COMPLETADA.

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

### Completado
- Scraping p1–p90. Meta 500 superada (769 → 757 con dedup).
- Detección de duplicados con `scripts/check_duplicados.py`.
- Reorganización de archivos (raíz limpia, `scraping/`, `docs/`).

### En progreso / pendiente
- Normalización de datos (monedas, precios a valores comparables, ubicaciones, marcas).
- Estudio de mercado (distribución por provincia, marca, tipo, rango de precios).
- Decidir si se commitea la reorganización (git tiene los renombres staged + cambios de la sesión anterior sin commitear).

---

## 4. Bloqueante actual

**No hay bloqueante.** El scraping se detuvo por decisión, no por fallo técnico. Cloudflare está resuelto (perfil + DISPLAY=:0). La fase de normalización/estudio puede avanzar sin depender de nada externo.

---

## 5. Próximos pasos ordenados

1. **Normalización** de `data/raw/triciclos_aceptados.json` (continuar en `scripts/normalizar.py`):
   - Unificar monedas (CUP/USD/MLC/MN) y calcular equivalente de referencia.
   - Normalizar marcas (variantes de escritura → nombre canónico).
   - Normalizar ubicaciones (provincia/municipio).
   - Validar tipos: eléctrico / combustible / híbrido.
2. **Estudio de mercado** (continuar en `scripts/analisis_mercado.py` + `scripts/drivers_precio.py`):
   - Distribución por provincia, marca, tipo de triciclo.
   - Rango y mediana de precios (por moneda y equivalente).
   - Autonomías declaradas.
   - Informe final (markdown + tablas) en `docs/informe_mercado.md`.
3. **Commit** de la reorganización cuando el usuario lo pida.

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
| 2026-10-18 | (esta sesión) | revolico-triciclos | Reorganización final: scraping/, docs/, raíz limpia + ajuste de rutas |

## Actualización 2026-10-24 (Fase de Ciencia de Datos completada)

- **Estado general:** Fase de Ciencia de Datos 100% completada y auditada. Clustering, EDA de encuestas e EDA global finalizados. Datos listos para visualización.
- **Análisis completados:**
  - Clustering importadoras: k=3 (combustión premium / eléctricos carga media / híbridos económicos)
  - Clustering encuestas: k=2 (propietarios eléctricos alto presupuesto / híbridos mixto)
  - Insights encuestas (Bloques A/B/C) con CSVs para Datawrapper
  - EDA global con comparativas, autonomía, marcas/batería corregida y correlaciones
- **Próximos pasos:**
  1. **Crear gráficos en Datawrapper** con los CSVs exportados.
  2. **Generar el informe final** con `scripts/generar_informe.py` (pendiente de ejecutar cuando esté listo).
  3. **App de Streamlit** es lo último pendiente.
