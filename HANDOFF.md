# HANDOFF — Revolico Triciclos

**Asignación del proyecto (clase):** sábado 2026-09-26
**Última actualización:** sábado 2026-10-17
**Responsable:** diegogonza
**Estado general:** Scraping COMPLETADO. Meta superada. Fase de normalización + estudio de mercado.

---

## 1. Objetivo

Extraer anuncios de **triciclos** de Revolico.com (Vehículos > Motos Eléctricas y Triciclos), aplicar 7 filtros estrictos y generar:

- `triciclos_aceptados.json` — cumplen TODOS los filtros.
- `triciclos_descartados.json` — rechazados, con motivo y datos crudos.

**Meta original:** 500 aceptados → **SUPERADA** (769).
**Decisión del usuario (2026-10-17):** parar el scraping. p91–253 NO se harán.
**Restricción dura:** SOLO triciclos. Nada de motos, bicimotos, cuatriciclos ni otros vehículos.

---

## 2. Estado actual

- **Páginas scrapeadas:** p1–p90 (de 253 reales). p31–60 en `_p31_60_hold/` temporalmente.
- **Permalinks únicos:** 1378. **Caché:** 1298 descripciones en `cache_descripciones.json`.
- **Pipeline:** 1378 procesados → **769 aceptados**, **609 descartados**.
- **Descartes por motivo:**
  - `AUTONOMIA_NO_INDICADA`: 397
  - `MARCA_NO_DETECTADA`: 285
  - `TIPO_NO_DETERMINADO`: 125
  - `DESCARGA_FALLIDA`: 80 (challenge Cloudflare cortado, no anuncios reales perdidos)
  - `PRECIO_INVALIDO`: 71
  - `MONEDA_NO_DETECTADA`: 71
- **Duplicados detectados** (por `(gcsKey, phone)`): 12 grupos / 24 registros.
  - **DECISIÓN:** aplicar dedup → bajaría a **757 aceptados**. Aún NO aplicado.
- Cloudflare resuelto con perfil persistente `chrome_profile_revolico/` + `DISPLAY=:0` + Chrome real.

---

## 3. Estado por categoría

### Estable
- `pipeline.py` con 7 filtros (versión 2026-10-17, respaldada en `.bak.20261017_194105`).
- Esquemas JSON (`triciclo_aceptado_schema.json`, `triciclo_descartado_schema.json`).
- Validación con `validar_salidas.py`.
- Caché incremental `cache_descripciones.json` (1298 entradas, respaldada como `cache_descripciones.1298.json`).
- Chrome + perfil persistente funcionando contra Cloudflare.

### Completado
- Scraping p1–p90. Meta 500 superada (769).
- Detección de duplicados con `scripts/check_duplicados.py`.

### En progreso / pendiente
- Aplicar dedup (769 → 757).
- Normalización de datos (monedas, precios a valores comparables, ubicaciones, marcas).
- Estudio de mercado (distribución por provincia, marca, tipo, rango de precios).
- Limpieza de artefactos temporales (`.html`, `test_*`, `_p31_60_hold/`, `.bak*`).

---

## 4. Bloqueante actual

**No hay bloqueante.** El scraping se detuvo por decisión, no por fallo técnico. Cloudflare está resuelto (perfil + DISPLAY=:0). La fase de normalización/estudio puede avanzar sin depender de nada externo.

---

## 5. Próximos pasos ordenados

1. **Normalización** de `triciclos_aceptados.json`:
   - Unificar monedas (CUP/USD/MLC/MN) y calcular equivalente de referencia.
   - Normalizar marcas (variantes de escritura → nombre canónico).
   - Normalizar ubicaciones (provincia/municipio).
   - Validar tipos: eléctrico / combustible / híbrido.
2. **Dedup** por `(gcsKey, phone)`: 12 grupos / 24 registros → esperado **757 aceptados**. Respaldar antes.
3. **Estudio de mercado**:
   - Distribución por provincia, marca, tipo de triciclo.
   - Rango y mediana de precios (por moneda y equivalente).
   - Autonomías declaradas.
   - Informe final (markdown + tablas).

---

## 6. Comandos útiles

```bash
cd ~/proyectos/revolico-triciclos
source venv/bin/activate
python pipeline.py
python validar_salidas.py
python scripts/check_duplicados.py   # desde la raíz (usa rutas relativas)
```

---

## 7. Archivos clave

- `pipeline.py` — script principal del pipeline de filtros.
- `cache_descripciones.json` — 1298 descripciones cacheadas. **No borrar.**
- `triciclos_aceptados.json` — 769 aceptados (antes de dedup).
- `triciclos_descartados.json` — 609 descartados.
- `triciclos_aceptados.769.json` — snapshot del conteo post-pipeline.
- `scripts/check_duplicados.py` — chequeo de duplicados (solo lectura).
- `chrome_profile_revolico/` — perfil persistente que resuelve Cloudflare.
- `scraper_revolico_nodriver.py`, `prefetch_descripciones_nodriver.py` — scraping con Chrome real.
- `revolico_raw_p1-p90.html`, `revolico_state_p1-p90.json` — datos crudos (faltan p32–60 en raíz; están en `_p31_60_hold/`).
- `pipeline.py.bak*`, `triciclos_aceptados.bak*.json`, `triciclos_descartados.bak*.json` — backups.
- `JOURNAL.md`, `HANDOFF.md`, `AGENTS.md` — documentación del proyecto.

---

## 8. Lo que NO se debe hacer

- No reanudar el scraping de p91 en adelante sin petición explícita del usuario.
- No ejecutar `python - << 'EOF'` con scripts largos dentro de opencode (se cuelga).
- No modificar `pipeline.py` mientras corre; si se toca, crear `.bakN` antes.
- No hacer `git add` de `venv/`, `cache_descripciones.json`, `revolico_state_*.json`, `revolico_raw_*.html` ni los JSON de salida.
- No borrar `cache_descripciones.json`.
- No borrar `_p31_60_hold/` hasta confirmar que p31–60 están integrados en raíz.
- No tocar las motos: el trabajo es SOLO sobre triciclos.
- No bajar `PAUSA` por debajo de 3s si se retoma scraping.
- No mover a `scripts/` los scripts que usan rutas relativas a la raíz (`pipeline.py`, `scraper_*.py`, `prefetch_*.py`, `test_*.py`, `validar_salidas.py`).
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
| 2026-10-17 | (esta sesión) | revolico-triciclos | Scraping p61-90 + pipeline 769 + reorganización scripts/ |
