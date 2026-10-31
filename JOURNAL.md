# JOURNAL — Revolico Triciclos

**Asignación del proyecto (clase):** sábado 2026-09-26
**Primer trabajo técnico:** sábado 2026-10-03
**Última actualización:** sábado 2026-10-17
**Responsable:** diegogonza

Bitácora cronológica del proyecto. Orden: del más antiguo al más reciente.
Tipos de entrada: DECISIÓN, PRUEBA, RESULTADO, CAMBIO, BLOQUEO, LECCIÓN, HANDOFF.
Los días sin actividad se marcan explícitamente para mantener la línea de tiempo honesta.
Fuentes de evidencia: logs de opencode, `prompt-history.jsonl`, DB `opencode.db`, timestamps de archivos, backups con `jq length`.

---

## [2026-09-26 · sábado] DECISIÓN — Asignación del proyecto y adopción de journaling/handoff

**Contexto:** Primera clase. El profesor asigna el trabajo sobre triciclos en Cuba y exige journaling + handoff desde el principio.
**Acción:** Definir alcance: trabajo académico/laboral exclusivamente sobre triciclos. Adoptar `JOURNAL.md` y `HANDOFF.md` como artefactos obligatorios del proyecto.
**Resultado:** Objetivo planteado. Aún sin código.
**Lección:** Documentar desde el día 1 evita reconstruir contexto después.
**Artefactos:** —
**Próximo:** Arrancar estructura del proyecto.

---

## [2026-09-27 a 2026-10-02] SIN ACTIVIDAD

Seis días sin trabajo registrado en opencode, sin cambios de archivos ni sesiones nuevas.

---

## [2026-10-03 · sábado] PRUEBA — Arranque del proyecto `triciclos_cuba` en opencode

**Contexto:** Primera sesión técnica en opencode. Directorio: `~/ciencia_datos/triciclos_cuba`.
**Acción:** Sesión `nimble-engine` (13:31, agent=build, modelo `mimo-v2.5-free`). Petición: explorar todos los archivos del proyecto. Luego sesión `proud-otter` (15:08, agent=plan) con un prompt largo pidiendo revisar y completar el pipeline.
**Resultado:** Se levantó la estructura: `config.py`, `main.py`, `src/capture.py`, `src/preprocess.py`, `src/structure.py`, `src/process.py`, `src/analyze.py`, `src/present.py`. Se poblaron datos sintéticos en `data/raw/personas|mercados-instituciones|internet/`.
**Lección:** opencode con agente `plan` sirve bien para diseñar estructura antes de escribir código.
**Artefactos:** `config.py`, `main.py`, `src/*.py`, `data/raw/**`.
**Próximo:** Instalar dependencias pesadas (numpy, pandas, scipy, matplotlib).

---

## [2026-10-03 · sábado] CAMBIO — Instalación de dependencias y simulación del pipeline

**Contexto:** El pipeline requiere librerías científicas.
**Acción:** `pip install` desde espejo de Tsinghua (21:11). Creación de `/tmp/opencode/simulate_pipeline.py` (21:12) y ejecución. Verificación con `head data/clean/triciclos_cuba_personas_clean.csv` (22:16).
**Resultado:** Pipeline simulado con datos sintéticos. Estructura validada.
**Lección:** El espejo de Tsinghua acelera la instalación en redes con peering lento.
**Artefactos:** `venv/`, `data/clean/*.csv`.
**Próximo:** Iterar sobre el pipeline real.

---

## [2026-10-04 · domingo] DECISIÓN — Reorganización por tipos de triciclo

**Contexto:** Sesión `stellar-cabin` (11:56). Prompt clave: *"hay tres tipos de triciclos, entonces el trabajo va a tener que tornar en tres directrices… Los tipos son eléctricos, de combustible o híbridos"*.
**Acción:** Añadir nuevas preguntas de investigación (panel solar, garantía, mensajería incluida). Redefinir variable `tipo_triciclo` (eléctrico/combustible/híbrido) y crear `tipo_uso` (carga/pasajeros). Eliminar bicitaxi del alcance. `garantia` por marca. `autonomia` como campo no-null.
**Resultado:** Esquema de datos reorganizado. `config.py` actualizado varias veces.
**Lección:** Separar `tipo_triciclo` de `tipo_uso` simplifica el análisis posterior.
**Artefactos:** `config.py` (editado 16:30), `src/capture.py`, `src/process.py`, `src/analyze.py`, `src/present.py`, `main.py` (editados 16:30–16:32). Datos raw actualizados.
**Próximo:** Diseñar el primer scraping real.

---

## [2026-10-04 · domingo] DECISIÓN — Definir campos obligatorios del scraping

**Contexto:** Prompt: *"quiero hacer un primer scraping… si un anuncio no tiene todos esos campos no nulos se deseche… guardes la ubicación y opcional el municipio… hagas un json con los datos… solo analiza anuncios de 2026"*.
**Acción:** Fijar campos obligatorios: precio, tipo, marca, ubicación, fecha 2026, autonomía, moneda. Municipio opcional. Salidas separadas por tipo de triciclo.
**Resultado:** Criterios de filtrado definidos. Decisión de descartar todo lo que no sea 2026.
**Lección:** Los campos obligatorios actúan como filtros duros y reducen ruido.
**Artefactos:** (decisiones registradas en prompts; código aún no).
**Próximo:** Conseguir datos crudos de Revolico.

---

## [2026-10-05 · lunes] SIN ACTIVIDAD

---

## [2026-10-06 · martes] DECISIÓN — Pivot a `~/proyectos/revolico-triciclos`

**Contexto:** Sesión `tidy-rocket` (12:24) — *"¿qué necesitas para hacer el scraping?"*. Luego `silent-knight` (13:34) — creación de estructura `triciclos-revolico/`.
**Acción:** Crear proyecto nuevo en `~/proyectos/revolico-triciclos`. Venv a las 13:45. `requirements.txt` 13:46. `AGENTS.md` 14:07.
**Resultado:** Proyecto separado del `triciclos_cuba` original. Se abandona el modelo de datos sintéticos y se apunta al scraping real.
**Lección:** Separar el prototipo (`triciclos_cuba`) del proyecto real (`revolico-triciclos`) evitó arrastrar deuda técnica.
**Artefactos:** `venv/`, `requirements.txt`, `AGENTS.md`, `AGENTS.md.save`.
**Próximo:** Configurar subagente `revolico-triciclos`.

---

## [2026-10-06 · martes] CAMBIO — Subagente, esquemas JSON y validación

**Contexto:** Sesión `crisp-mountain` (14:11) — *"agents"*. Se crea `.opencode/agents/revolico-triciclos.md`.
**Acción:** Definir 7 filtros duros con códigos de descarte. Crear `triciclo_aceptado_schema.json`, `triciclo_descartado_schema.json`, `validar_salidas.py` (14:23).
**Resultado:** Subagente operativo. Esquemas con validación por `jsonschema`.
**Lección:** Tener esquemas JSON antes del scraping fuerza disciplina en los campos.
**Artefactos:** `.opencode/agents/revolico-triciclos.md`, ambos `*_schema.json`, `validar_salidas.py`.
**Próximo:** Primer scraping con el subagente.

---

## [2026-10-06 · martes] PRUEBA — Primer scraping de 2 páginas

**Contexto:** Sesiones `witty-comet` y `brave-planet` (14:25). Prompt: *"@revolico-triciclos Scrapea las primeras 2 páginas de triciclos en Revolico, aplica los filtros y genera los dos archivos JSON"*.
**Acción:** Ejecución del subagente contra las primeras 2 páginas.
**Resultado:** Primeros JSON generados. Se confirma que el pipeline es viable.
**Lección:** El subagente puede ejecutar scraping autónomo, pero la paginación es limitada (5 páginas máx. por invocación).
**Artefactos:** `triciclos_aceptados.json`, `triciclos_descartados.json` (versión inicial).
**Próximo:** Escalar el scraping a más páginas.

---

## [2026-10-07 · miércoles] SIN ACTIVIDAD

---

## [2026-10-08 · jueves] PRUEBA — Scraping de páginas 1 a 13 con `requests`

**Contexto:** Se necesita ampliar la muestra. Se pasa del subagente a un script propio.
**Acción:** Crear `scraper_revolico.py`. Descarga de `revolico_raw_p1.html` a `revolico_raw_p13.html` (13:19–13:21) y sus `revolico_state_pN.json`.
**Resultado:** 13 páginas descargadas. **1378 anuncios totales.** 356 triciclos únicos.
**Lección:** Extraer `__NEXT_DATA__` de Next.js es más robusto que parsear HTML.
**Artefactos:** `scraper_revolico.py`, `revolico_raw_p1-p13.html`, `revolico_state_p1-p13.json`, `detalle_ejemplo.html`.
**Próximo:** Convertir anuncios crudos en JSON filtrado.

---

## [2026-10-08 · jueves] CAMBIO — De `procesar_triciclos.py` a `pipeline.py`

**Contexto:** El script inicial `procesar_triciclos.py` (10:36) no cubría caché ni reintentos.
**Acción:** Crear `pipeline.py` unificado. Añadir `cache_descripciones.json` (17:55) para evitar redescargar descripciones. Añadir reintentos (timeout 60s, 3 intentos) y pausa `PAUSA = 3`.
**Resultado:** Pipeline robusto con caché incremental. `reprocesar_descartados.py` (11:12) y `parche_extractor.py` (11:36) usados para reprocesar descartes.
**Lección:** La caché ahorró ~360 descargas.
**Artefactos:** `pipeline.py`, `cache_descripciones.json`, `reprocesar_descartados.py`, `parche_extractor.py`.
**Próximo:** Afinar filtros.

---

## [2026-10-08 · jueves] RESULTADO — Cuatro rondas de ajuste de filtros

**Contexto:** Los filtros iniciales descartaban demasiado por autonomía y marca.
**Acción:** Cuatro iteraciones sobre `pipeline.py` con backups `pipeline.py.bak`, `.bak2`, `.bak3`, `.bak4` (18:08–18:21).
**Resultado:** Secuencia real de aceptados:
- Inicial: 99
- `.bak.json`: **147** (+48, recuperación de descargas fallidas)
- `.bak2.json`: **184** (+37, regex autonomía + marca)
- `.bak3.json`: **218** (+34, patrones nuevos)
- `.bak4.json`: **197** (retroceso por regex mal aplicado)
- Final (`triciclos_aceptados.json`): **232** (+35)

Descartados finales: 124, con distribución:
`AUTONOMIA_NO_INDICADA`: 97, `MARCA_NO_DETECTADA`: 66, `TIPO_NO_DETERMINADO`: 27, `PRECIO_INVALIDO`: 12, `MONEDA_NO_DETECTADA`: 12, `DESCARGA_FALLIDA`: 4.

**Lección:** Un fix de regex puede retroceder si no se valida contra una muestra. Respaldar siempre con `.bakN` antes de tocar `pipeline.py`.
**Artefactos:** `pipeline.py.bak` … `.bak4`, `triciclos_aceptados.bak*.json`, `triciclos_descartados.bak*.json`, `triciclo_descartado_schema.json` (13:01).
**Próximo:** Ampliar el scraping más allá de p13.

---

## [2026-10-09 · viernes] SIN ACTIVIDAD

---

## [2026-10-10 · sábado] BLOQUEO — Cloudflare 403 desde la página 16

**Contexto:** Se intenta extender el scraping. `revolico_raw_p16-p20.html` (07:15) confirma que la subcategoría tiene **253 páginas reales** (`pageCount: 253`), no 15.
**Acción:** Probar `requests` directo (403 tras p15), `curl_cffi` con `impersonate='chrome'` (403), `nodriver` con Chrome real (falla: no hay Chrome instalado).
**Resultado:** Bloqueo confirmado. El universo real es ~17× mayor de lo que se creía.
**Lección:** Cloudflare no bloquea por umbral fijo, sino por reputación acumulada (TLS fingerprint, IP de VPN, ritmo). Insistir con `requests` o `curl_cffi` empeora el bloqueo.
**Artefactos:** `scraper_revolico.py` (07:14), `scraper_revolico.py.bak`, `revolico_raw_p16-p20.html`.
**Próximo:** Instalar Chrome + Xvfb, probar `nodriver`.

---

## [2026-10-10 · sábado] PRUEBA — Descarga de Chrome en curso

**Contexto:** `nodriver` requiere un binario real de Chrome.
**Acción:** `wget` del `.deb` de Chrome 155 desde `dl.google.com` a `/tmp/google-chrome-stable_current_amd64.deb`.
**Resultado:** En curso. Tamaño total: 136 MB. Velocidad: ~120 KB/s. Red con mal peering por VPN.
**Lección:** Si la descarga se vuelve insostenible, considerar cambiar servidor VPN.
**Artefactos:** `/tmp/google-chrome-stable_current_amd64.deb` (en descarga).
**Próximo:** `sudo dpkg -i`, `sudo apt install -y xvfb`, test `nodriver` contra p16.

---

## [2026-10-10 · sábado] HANDOFF — Cierre de sesión

**Contexto:** Documentar el estado para continuar sin pérdida de contexto.
**Acción:** Crear `JOURNAL.md` y `HANDOFF.md` desde el inicio del proyecto.
**Resultado:** Documentación lista. Chrome sigue descargándose.
**Lección:** Actualizar el journal al cerrar cada sesión, aunque no haya avances.
**Artefactos:** `JOURNAL.md`, `HANDOFF.md`.
**Próximo:** Test `nodriver` contra p16 cuando termine la descarga.

---

## [2026-10-17 · sábado] HANDOFF — Scraping completado (meta 500 superada) y reorganización de scripts

**Contexto:** Desde la última entrada (2026-10-10) se resolvió Cloudflare con perfil persistente de Chrome (`chrome_profile_revolico/`) + `DISPLAY=:0` y se completó el scraping hasta p90. El usuario decide parar: p91–253 NO se harán. Se cierra la fase de scraping y se abre la de normalización + estudio de mercado.
**Acción:** Pipeline final sobre 1378 permalinks únicos → 769 aceptados / 609 descartados. Detección de duplicados con `check_duplicados.py`: 12 grupos / 24 registros por `(gcsKey, phone)`; decisión de aplicar dedup (→757). Reorganización documental: crear `scripts/`, mover allí `check_duplicados.py`, actualizar `AGENTS.md` (fase 1 completada, nota de ubicación de scripts) y reescribir `HANDOFF.md` con el estado real.
**Resultado:** 769 aceptados (meta 500 superada), 609 descartados (AUTONOMIA 397, MARCA 285, TIPO 125, DESCARGA_FALLIDA 80, PRECIO 71, MONEDA 71). Caché con 1298 descripciones. Dedup pendiente de aplicar. Documentación al día.
**Lección:** El perfil persistente de Chrome + display visible resuelve el challenge de Cloudflare donde fallaron `requests`, `curl_cffi` y `nodriver` headless. Los 80 `DESCARGA_FALLIDA` eran challenges cortados, no anuncios perdidos.
**Artefactos:** `scripts/check_duplicados.py` (movido), `AGENTS.md` (editado), `HANDOFF.md` (reescrito), `JOURNAL.md` (esta entrada).
**Próximo:** Normalizar datos → aplicar dedup (769→757) → estudio de mercado.

---

## [2026-10-18 · domingo] HANDOFF — Reorganización final de archivos: raíz limpia, `scraping/` y `docs/`

**Contexto:** El usuario pidió limpiar la raíz del proyecto. Una sesión anterior (mismo día, 12:17) ya había creado `data/`, `docs/`, `app/`, `models/` y movido los JSON limpios.
**Acción:** Crear `scraping/` con 12 scripts de scraping/pipeline y `scraping/data/` con 217 artefactos crudos (90 raw HTML + 90 states —integrados los p31–60 de `_p31_60_hold/`, ya eliminada—, caché, backups, snapshots). Borrar `google-chrome.deb` (143 MB) y `main`. Mover `informe_mercado.md` a `docs/`. Ajustar rutas en 10 scripts con backup previo en `scraping/data/*.bak.20261018_123614`. Actualizar `.gitignore` (añadidos `*.html`, `cache_*.json`, `*_state_*.json`, `scraping/data/`, `basura/`), `AGENTS.md` y `HANDOFF.md`.
**Resultado:** Raíz limpia. `py_compile` OK; `validar_salidas.py` valida 769 aceptados + 609 descartados; `normalizar.py` encuentra los 90 states; `drivers_precio.INFORME` apunta a `docs/informe_mercado.md`. Renombres staged en git, sin commitear.
**Lección:** Mover scripts con rutas relativas exige ajustar TODOS los consumidores de los datos que mueven; el glob vacío de `normalizar.py` habría producido un dedup silenciosamente vacío.
**Artefactos:** `scraping/` (nuevo), `scraping/data/` (nuevo), `basura/` descartada, `google-chrome.deb` + `main` borrados, `.gitignore`, `AGENTS.md`, `HANDOFF.md`, 10 scripts editados + sus `.bak.20261018_123614`.
**Próximo:** Continuar normalización/estudio de mercado; decidir cuándo commitear la reorganización.


## [2026-10-24 · sábado] EDA, CLUSTERING Y AUDITORÍA TÉCNICA

**Contexto:** Fase de Análisis de Datos (EDA) y Clustering.

**Acción:** Creación de clústeres para importadoras (3 segmentos) y encuestas (2 perfiles). Creación del EDA de encuestas (`insights_encuestas.py`, `docs/insights_encuestas.md`) y EDA Global (Revolico, Importadoras, Correlaciones) con `scripts/eda_global.py`. Corrección del parseo de vida de batería (códigos `lt6m/6_12m/1_2a/2_3a/3_5a/gt5a` a meses) tras auditoría técnica. Actualización de marcas/encuestas 34-40, clustering de importadoras con k=3, clustering de encuestas con k=2.

**Resultado:** 40 encuestas válidas, 3 CSVs exportados para Datawrapper (dw_tipos, dw_precios_importadora, dw_precio_tipo), además de dw_clusters_importadoras, dw_clusters_encuestas, dw_documentos, dw_fallas_marcas. 6+ scripts de análisis funcionando. Datos auditados (marcas OK 40/40, booleanos correctos, imputación con mediana justificada, conteo de documentos correcto). 

**Lección:** Los códigos de encuesta (`2_3a`) requieren mapeo explícito; las afirmaciones deben basarse en cifras observables (12% más caro) en lugar de hipótesis sobre canales.

**Artefactos:** `scripts/clustering_importadoras.py`, `scripts/clustering_encuestas.py`, `scripts/eda_catalogos.py`, `scripts/insights_encuestas.py`, `scripts/eda_global.py`, `data/processed/clustering_importadoras/dw_clusters_importadoras.csv`, `data/processed/clustering_encuestas/dw_clusters_encuestas.csv`, `data/processed/encuestas_eda/dw_documentos.csv`, `data/processed/encuestas_eda/dw_fallas_marcas.csv`, `docs/insights_encuestas.md`, `docs/eda_global.md`, `docs/graficos_eda/` (4 PNG).

**Próximo:** Crear gráficos en Datawrapper y redactar el informe final.

---

## [2026-10-31 · sábado] DESPLIEGUE — Rediseño de UI y optimización de dependencias

**Contexto:** Tras completar el EDA y el clustering, quedaba pendiente la capa de presentación. El primer intento de despliegue en Streamlit Cloud falló por falta de memoria al compilar `scipy` con Python 3.14.

**Acción:** Rediseño de la UI en Streamlit (tarjetas, gráficos nativos, CSS personalizado). Reducción del `requirements.txt` para evitar el fallo OOM (Out of Memory) en Streamlit Cloud, separando las dependencias de desarrollo en `requirements-dev.txt`. Se fijó Python 3.11 en `runtime.txt` y se añadió `build-essential` en `packages.txt`. También se adaptó `app/recommend.py` para exponer `cargar_catalogo()`, aceptar el catálogo ya cargado y devolver las columnas que consumen las tarjetas.

**Resultado:** App desplegada exitosamente con el nuevo diseño. La interfaz incluye hero, tarjetas de resultados, badges, chips, gráficos nativos (`st.bar_chart`, `st.scatter_chart`) y CSS personalizado. El runtime quedó reducido a `pandas` y `streamlit`, mientras que las dependencias pesadas del pipeline se conservan en `requirements-dev.txt`.

**Lección:** Separar las dependencias de la app de las del pipeline evita compilaciones pesadas e innecesarias en el despliegue. Fijar la versión de Python y validar la API entre la UI y el motor de recomendación antes de desplegar ahorra fallos en producción.

**Artefactos:** `app/streamlit_app.py`, `app/recommend.py`, `requirements.txt`, `requirements-dev.txt`, `runtime.txt`, `packages.txt`, `.streamlit/config.toml`.

**Próximo:** Integrar los gráficos de Datawrapper en la pestaña "Entiende el Mercado" y redactar `docs/informe_final.md`.
