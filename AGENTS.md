# AGENTS.md — Proyecto de Scraping de Triciclos en Revolico

Este archivo es la guía principal para opencode dentro de este proyecto. Define el objetivo, el entorno, las herramientas y las reglas de comportamiento del agente.

## Objetivo del proyecto

**Fase 1 (COMPLETADA, 2026-10-17):** Extraer anuncios de triciclos publicados en la subcategoría de Vehículos > Motos Eléctricas y Triciclos de Revolico.com, aplicar filtros estrictos de calidad y generar dos archivos JSON:

- `data/raw/triciclos_aceptados.json` — anuncios que cumplen TODOS los criterios.
- `scraping/data/triciclos_descartados.json` — anuncios rechazados con el motivo del descarte.

El scraping terminó: se scrapeó p1–p90 (p91–253 descartados por decisión del usuario). La meta de 500 aceptados se superó con creces: **769 aceptados, 609 descartados**. Quedan identificados 12 grupos de duplicados (24 registros) que bajarán el total a **757** tras aplicar dedup.

**Fase 2 (EN CURSO):** Normalización de los datos extraídos y estudio de mercado de triciclos en Cuba. El scraping queda cerrado; no retomar salvo petición explícita.

## Estructura del proyecto

```
revolico-triciclos/
├── .opencode/agents/revolico-triciclos.md
├── scraping/                  # scripts de scraping y pipeline
│   ├── pipeline.py
│   ├── scraper_revolico.py
│   ├── scraper_revolico_nodriver.py
│   ├── prefetch_descripciones_nodriver.py
│   ├── procesar_triciclos.py
│   ├── reprocesar_descartados.py
│   ├── parche_extractor.py
│   ├── validar_salidas.py
│   ├── test_*.py
│   └── data/                  # datos crudos, temporales y backups (ignorado por git)
│       ├── revolico_raw_p1..p90.html
│       ├── revolico_state_p1..p90.json
│       ├── cache_descripciones.json
│       ├── triciclos_descartados.json
│       └── *.bak* / snapshots
├── scripts/                   # análisis, normalización e informe (rutas ancladas a la raíz)
│   ├── analisis_mercado.py
│   ├── check_duplicados.py
│   ├── drivers_precio.py
│   ├── normalizar.py
│   └── ...
├── data/                      # datos limpios de la Fase 2
│   ├── raw/triciclos_aceptados.json
│   └── processed/triciclos_aceptados_normalizado.json, duplicados_descartados.json, encuestas.json
├── docs/informe_mercado.md
├── graficos/                  # PNG generados por el análisis
├── venv/
├── AGENTS.md
├── HANDOFF.md
├── JOURNAL.md
├── requirements.txt
├── triciclo_aceptado_schema.json
└── triciclo_descartado_schema.json
```

Los scripts de scraping y pipeline (`scraping/`) usan rutas relativas al directorio de trabajo: ejecútalos SIEMPRE desde la raíz del proyecto (ej. `python scraping/pipeline.py`). Los scripts de `scripts/` se anclan solos vía `Path(__file__).parent.parent`, pero también se ejecutan desde la raíz por convención.

## Entorno Python

Este proyecto usa un entorno virtual ubicado en `./venv`. Antes de ejecutar cualquier script Python, actívalo:

```bash
source venv/bin/activate
```

Para desactivarlo:

```bash
deactivate
```

Librerías instaladas (ver `requirements.txt`):

- `requests` — peticiones HTTP
- `beautifulsoup4` — parseo de HTML
- `jsonschema` — validación de los JSON generados

Reinstalación desde cero:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Subagente especializado: @revolico-triciclos

Para tareas de scraping de triciclos, delega en el subagente `@revolico-triciclos`. Está definido en `.opencode/agents/revolico-triciclos.md` y contiene:

- Las reglas de extracción por campo.
- Los 7 criterios de aceptación.
- Los 7 códigos de descarte.
- El formato exacto de los dos archivos JSON de salida.

Cómo invocarlo:

```
@revolico-triciclos Scrapea las primeras 3 páginas de Revolico, aplica los filtros y genera los archivos de aceptados y descartados.
```

Cuándo NO delegar:

- Tareas de validación de JSON → hacerlas directamente con `scraping/validar_salidas.py`.
- Edición de esquemas o del README → hacerlas directamente.
- Consultas generales → responder directamente.

## Criterios de aceptación (filtros duros)

Un anuncio se acepta SOLO si cumple TODAS estas condiciones:

| Variable | Regla | Código de descarte |
|---|---|---|
| `precio_publicado` | Numérico y > 0 | `PRECIO_INVALIDO` |
| `tipo_triciclo` | eléctrico, combustible o híbrido | `TIPO_NO_DETERMINADO` |
| `marca_detectada` | Identificada, distinta de "Desconocida" | `MARCA_NO_DETECTADA` |
| `ubicacion` | No vacía | `UBICACION_VACIA` |
| `fecha_publicacion` | Año 2026 | `FECHA_FUERA_DE_2026` |
| `autonomia_km` | Indicada explícitamente, > 0 | `AUTONOMIA_NO_INDICADA` |
| `moneda_original` | USD, CUP, MN, EUR o MLC | `MONEDA_NO_DETECTADA` |

Si un anuncio falla múltiples criterios, se registran TODOS en `motivos_descarte`.

## Variables extraídas

Filtradas (obligatorias):
`precio_publicado`, `tipo_triciclo`, `marca_detectada`, `ubicacion`, `fecha_publicacion`, `autonomia_km`, `moneda_original`

Adicionales (opcionales):
`municipio`, `tipo_uso`, `garantia_meses`, `panel_incluido`, `voltaje_bateria`, `enlace`

## Salidas esperadas

### data/raw/triciclos_aceptados.json

Array de objetos que cumplen los 7 criterios. Validable con `triciclo_aceptado_schema.json`.

### scraping/data/triciclos_descartados.json

Array de objetos con esta estructura:

```json
{
  "enlace": "https://www.revolico.com/...",
  "titulo_crudo": "...",
  "motivos_descarte": ["AUTONOMIA_NO_INDICADA", "MARCA_NO_DETECTADA"],
  "datos_crudos": { }
}
```

Validable con `triciclo_descartado_schema.json`.

## Flujo de trabajo recomendado

1. Activar entorno virtual:

   ```bash
   source venv/bin/activate
   ```

2. Invocar al subagente desde opencode:

   ```
   @revolico-triciclos Scrapea las primeras 3 páginas y genera los JSON.
   ```

3. Validar las salidas:

   ```bash
   python scraping/validar_salidas.py
   ```

4. Revisar el reporte que imprime el agente (aceptados, descartados y conteo por criterio).

5. Si la tasa de aceptación es muy baja, considera relajar algún filtro (el más restrictivo suele ser `AUTONOMIA_NO_INDICADA`).

## Comandos útiles

| Acción | Comando |
|---|---|
| Activar entorno | `source venv/bin/activate` |
| Desactivar entorno | `deactivate` |
| Ejecutar pipeline de filtros (desde raíz) | `python scraping/pipeline.py` |
| Scraping con Chrome real (desde raíz) | `PAG_INI=91 PAG_FIN=95 python scraping/scraper_revolico_nodriver.py` |
| Validar JSON generados | `python scraping/validar_salidas.py` |
| Comprobar duplicados (desde raíz) | `python scripts/check_duplicados.py` |
| Normalizar datos (desde raíz) | `python scripts/normalizar.py` |
| Generar informe de mercado | `python scripts/analisis_mercado.py` |
| Listar agentes disponibles en opencode | `/agents` |
| Ver esquema de aceptados | `cat triciclo_aceptado_schema.json` |
| Ver esquema de descartados | `cat triciclo_descartado_schema.json` |

## Reglas de comportamiento

1. Nunca inventes datos. Si un campo no está en el anuncio, déjalo como `null` en `datos_crudos`.
2. Siempre genera los DOS archivos JSON, incluso si uno queda vacío (`[]`).
3. Aplica los filtros antes de escribir. Los aceptados no deben tener `null` en las 7 variables obligatorias.
4. Pausa de 2 segundos entre peticiones HTTP. Máximo 5 páginas por invocación.
5. Si Revolico devuelve CAPTCHA o error 403, detente y reporta; escribe los JSON con lo recolectado hasta ese punto.
6. Revolico está bloqueado desde Cuba. Si estás en la isla, usa un proxy o accede desde fuera.
7. No resuelvas CAPTCHAs automáticamente. Repórtalos al usuario.
8. Trazabilidad total: cada descarte debe incluir `enlace`, `titulo_crudo`, `motivos_descarte` y `datos_crudos`.

## Referencias

- Documentación de agentes de opencode: https://opencode.ai/docs/agents
- Documentación de AGENTS.md: https://opencode.ai/docs/rules
- Wafle-Scraper (MCP opcional): https://pypi.org/project/wafle-scraper/
- PyreCrawl (MCP con fallback): https://pypi.org/project/pyrecrawl/

## Mejoras futuras sugeridas

- Añadir extracción de teléfono visitando la página de detalle de cada anuncio.
- Implementar rotación de User-Agents y proxies.
- Guardar histórico de precios en SQLite para detectar tendencias.
- Ampliar el scraping a otras subcategorías (autos, motos, piezas).
- Integrar notificaciones (email/Telegram) cuando aparezca un triciclo que cumpla los filtros.

## Notas finales

- Este proyecto prioriza calidad sobre cantidad: es preferible obtener 5 anuncios válidos que 500 sin información útil.
- El filtro de `autonomia_km` suele descartar más del 70% de los anuncios, ya que muchos vendedores cubanos no la especifican. Si obtienes 0 aceptados, es normal; ajusta el criterio en el subagente si lo necesitas.
- El año 2026 como filtro duro descarta automáticamente anuncios antiguos o sin fecha visible.

---

## Journaling y handoff

Este proyecto usa dos artefactos obligatorios de documentación:

- `JOURNAL.md` — bitácora cronológica. Lo más reciente al final.
- `HANDOFF.md` — snapshot vivo del estado. Se actualiza cada sesión.

### Al iniciar cada sesión

1. Lee `HANDOFF.md` completo.
2. Lee las últimas 10 entradas de `JOURNAL.md`.
3. Confirma al usuario en una línea: estado actual, bloqueante y próximo paso.
4. No ejecutes cambios sin respaldar antes (`.bakN`).
5. Si un cambio puede romper algo, dilo ANTES de aplicarlo.

### Al cerrar cada sesión

Cuando el usuario diga "cerramos sesión" o equivalente:

1. Propón una entrada `HANDOFF` para `JOURNAL.md` con este formato:
   - **Contexto:** qué se hizo.
   - **Acción:** qué se cambió.
   - **Resultado:** métricas y estado.
   - **Lección:** aprendizaje reutilizable.
   - **Artefactos:** archivos tocados o creados.
   - **Próximo:** siguiente paso concreto.
2. Espera aprobación del usuario antes de escribir.
3. Al aprobar, escribe la entrada en `JOURNAL.md` y actualiza `HANDOFF.md`.
4. Si tocaste `pipeline.py`, crea `pipeline.py.bakN` antes y menciónalo en el journal.

### Reglas

- El journal es cronológico. No reordenar entradas antiguas.
- No borrar entradas. Si algo cambia, se añade una entrada nueva.
- Los días sin actividad se marcan como `SIN ACTIVIDAD`.
- El handoff refleja solo el estado actual. Se sobrescribe cada sesión.
- Las entradas se escriben en español, con lenguaje concreto y accionable.
