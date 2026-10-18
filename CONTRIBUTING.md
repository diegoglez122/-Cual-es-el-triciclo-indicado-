# Contribuir en revolico-triciclos

Gracias por tu interés en mejorar este proyecto. Estas son las normas básicas para contribuir:

## Normas de la comunidad del proyecto

1. **Commits descriptivos.** Cada commit debe explicar qué cambió y por qué. Prefiere mensajes concretos en español, ej. `normalizar: unificar moneda MLC a USD en precios`.

2. **No subir archivos masivos.** El `.gitignore` ya excluye HTML crudos, states JSON, cachés, backups e instaladores. Nunca hagas `git add -f` sobre esos archivos: los datos crudos viven en `scraping/data/` (62 MB) y no se versionan.

3. **Ejecuta los scripts desde la raíz.** Los scripts de `scraping/` usan rutas relativas al directorio de trabajo; ejecutarlos desde otro directorio fallará o escribirá archivos en el lugar equivocado:

   ```bash
   python scraping/pipeline.py        # bien (desde la raíz)
   cd scraping && python pipeline.py  # mal
   ```

4. **Actualiza `JOURNAL.md` antes de cada entrega.** Añade una entrada al final con el formato de siempre (Contexto / Acción / Resultado / Lección / Artefactos / Próximo) y mantén `HANDOFF.md` reflejando el estado actual.

## Antes de entregar

- Activa el entorno: `source venv/bin/activate`.
- Valida las salidas: `python scraping/validar_salidas.py`.
- Si tocas `pipeline.py` u otro script sensible, crea un backup `.bakN` en `scraping/data/` antes (regla del proyecto).
- Revisa `git status` y confirma que no se coló ningún archivo masivo.
