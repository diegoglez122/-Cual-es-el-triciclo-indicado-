#!/usr/bin/env python3
"""Lee encuestas/encuestas.csv y lo convierte a encuestas/encuestas.json. NO toca el CSV."""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "raw" / "encuestas.csv"
JSON_PATH = ROOT / "data" / "processed" / "encuestas.json"

if not CSV_PATH.exists():
    print(f"ERROR: no existe {CSV_PATH}. Corre primero generar_encuestas.py")
    raise SystemExit(1)

BOOLS = {"es_duenio","precio_pasaje_fijo","hizo_inversiones","usa_panel_solar",
         "recupero_inversion","afectado_estatales","piezas_gomas","piezas_bateria",
         "piezas_motor","piezas_caja_bola","piezas_otras","piezas_ninguna",
         "doc_licencia","doc_circular","doc_onat","doc_operativa","doc_otros","doc_ninguno"}
NUMS = {"precio_vehiculo_usd","km_por_carga","ingreso_diario_cup","tc_usd_cup",
        "costo_luz_mes_cup","recuperacion_anios"}
INTS = {"dias_semana"}

def convertir(fila):
    out = {}
    for k, v in fila.items():
        v = (v or "").strip()
        if v == "":
            out[k] = None
        elif k in BOOLS:
            out[k] = int(v)
        elif k in NUMS:
            out[k] = float(v)
        elif k in INTS:
            out[k] = int(v)
        else:
            out[k] = v
    return out

with CSV_PATH.open(encoding="utf-8") as f:
    filas = [convertir(r) for r in csv.DictReader(f)]

JSON_PATH.write_text(json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{len(filas)} encuestas -> {JSON_PATH}")
