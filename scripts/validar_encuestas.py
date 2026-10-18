#!/usr/bin/env python3
"""Valida encuestas/encuestas.csv contra el esquema v3.
Salida: errores duros (bloquean) y warnings (revisar). Exit 1 si errores duros.
Uso: python3 scripts/validar_encuestas.py
"""
import csv, json, re, sys, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "raw" / "encuestas.csv"
JSON_REVOLICO = ROOT / "data" / "processed" / "triciclos_aceptados_normalizado.json"

CABECERA = ("id_encuesta,fecha,encuestador,provincia,municipio,marca,modelo,es_duenio,"
            "precio_vehiculo_usd,modalidad,tiempo_en_negocio,capacidad,vida_bateria,"
            "km_por_carga,ingreso_diario_cup,tc_usd_cup,dias_semana,costo_luz_mes_cup,"
            "precio_pasaje_fijo,fijacion_precio,hizo_inversiones,usa_panel_solar,"
            "tendencia_ganancias,recupero_inversion,recuperacion_anios,tipo_triciclo,"
            "afectado_estatales,demanda_costo_vida,como_adquirio,"
            "piezas_gomas,piezas_bateria,piezas_motor,piezas_caja_bola,piezas_otras,piezas_ninguna,"
            "doc_licencia,doc_circular,doc_onat,doc_operativa,doc_otros,doc_ninguno,notas").split(",")

ENUMS = {
    "provincia": ["Mayabeque","Artemisa","La Habana","Matanzas","Otra"],
    "modalidad": ["urbano","intermunicipal","carga","mixto"],
    "tiempo_en_negocio": ["lt6m","6m_1a","1_3a","gt3a"],
    "capacidad": ["hasta_5","mas_5"],
    "vida_bateria": ["lt6m","6_12m","1_2a","2_3a","3_5a","gt5a","no_sabe"],
    "fijacion_precio": ["onat","choferes","otro"],
    "tendencia_ganancias": ["aumentado","estable","disminuido"],
    "demanda_costo_vida": ["aumentado","estable","disminuido"],
    "tipo_triciclo": ["electrico","hibrido"],
    "como_adquirio": ["comprado_aqui","importado","otro"],
}

BOOLS = ["es_duenio","precio_pasaje_fijo","hizo_inversiones","usa_panel_solar",
         "recupero_inversion","afectado_estatales",
         "piezas_gomas","piezas_bateria","piezas_motor","piezas_caja_bola","piezas_otras","piezas_ninguna",
         "doc_licencia","doc_circular","doc_onat","doc_operativa","doc_otros","doc_ninguno"]

NUMS = {
    "precio_vehiculo_usd": (0, 20000),
    "km_por_carga": (10, 300),
    "ingreso_diario_cup": (0, 50000),
    "tc_usd_cup": (100, 1000),
    "costo_luz_mes_cup": (0, 50000),
    "recuperacion_anios": (0.1, 20),
}

REQUERIDOS = ["id_encuesta","provincia","precio_vehiculo_usd","modalidad",
              "tiempo_en_negocio","tc_usd_cup","dias_semana",
              "precio_pasaje_fijo","hizo_inversiones","usa_panel_solar","tendencia_ganancias",
              "tipo_triciclo","afectado_estatales","como_adquirio"]

OUTLIER_COLS = ["precio_vehiculo_usd","ingreso_diario_cup","km_por_carga","dias_semana"]

def cargar_marcas_revolico():
    if not JSON_REVOLICO.exists(): return None
    try:
        d = json.loads(JSON_REVOLICO.read_text(encoding="utf-8"))
    except Exception:
        return None
    items = d if isinstance(d, list) else next((v for v in d.values() if isinstance(v, list)), [])
    return {str(x.get("marca","")).strip() for x in items if isinstance(x, dict) and x.get("marca")}

def es_int(v):
    try: int(v); return True
    except: return False

def es_float(v):
    try: float(v); return True
    except: return False

def validar_fila(fila, idx, marcas_rev):
    errores, warns = [], []

    if not re.match(r"^E\d{3}$", (fila.get("id_encuesta") or "").strip()):
        errores.append((idx, "id_encuesta", f"formato inválido: {fila.get('id_encuesta')!r}"))

    for col in REQUERIDOS:
        v = (fila.get(col) or "").strip()
        if v == "" and col not in ("id_encuesta",):
            errores.append((idx, col, "requerido vacío"))

    for col, opciones in ENUMS.items():
        v = (fila.get(col) or "").strip()
        if v and v not in opciones:
            errores.append((idx, col, f"no permitido: {v!r}"))

    for col in BOOLS:
        v = (fila.get(col) or "").strip()
        if v and v not in ("0","1"):
            errores.append((idx, col, f"debe ser 0 o 1: {v!r}"))

    for col, (lo, hi) in NUMS.items():
        v = (fila.get(col) or "").strip()
        if v == "":
            continue
        if not es_float(v):
            errores.append((idx, col, f"no numérico: {v!r}")); continue
        n = float(v)
        if n < lo or n > hi:
            errores.append((idx, col, f"fuera de rango [{lo},{hi}]: {n}"))

    v = (fila.get("dias_semana") or "").strip()
    if v:
        if not es_int(v):
            errores.append((idx, "dias_semana", f"no entero: {v!r}"))
        elif not (1 <= int(v) <= 7):
            errores.append((idx, "dias_semana", f"fuera de 1-7: {v}"))

    piezas = ["piezas_gomas","piezas_bateria","piezas_motor","piezas_caja_bola","piezas_otras","piezas_ninguna"]
    vals_p = {c: (fila.get(c) or "").strip() for c in piezas}
    if vals_p["piezas_ninguna"] == "1":
        otras_uno = [c for c in piezas if c != "piezas_ninguna" and vals_p[c] == "1"]
        if otras_uno:
            errores.append((idx, "piezas_ninguna", f"mutex: =1 pero {otras_uno} también =1"))
    if all(v in ("0","") for v in vals_p.values()) and any(v == "0" for v in vals_p.values()):
        warns.append((idx, "piezas_*", "todas las piezas=0 y piezas_ninguna!=1 (¿se le olvidó marcar ninguna?)"))

    docs = ["doc_licencia","doc_circular","doc_onat","doc_operativa","doc_otros","doc_ninguno"]
    vals_d = {c: (fila.get(c) or "").strip() for c in docs}
    if vals_d["doc_ninguno"] == "1":
        otros_uno = [c for c in docs if c != "doc_ninguno" and vals_d[c] == "1"]
        if otros_uno:
            errores.append((idx, "doc_ninguno", f"mutex: =1 pero {otros_uno} también =1"))
    if all(v in ("0","") for v in vals_d.values()) and any(v == "0" for v in vals_d.values()):
        warns.append((idx, "doc_*", "todos los doc=0 y doc_ninguno!=1 (¿se le olvidó marcar ninguno?)"))

    rec = (fila.get("recupero_inversion") or "").strip()
    anios = (fila.get("recuperacion_anios") or "").strip()
    if rec == "0" and anios != "":
        errores.append((idx, "recuperacion_anios", f"recupero=0 pero anios={anios!r}"))
    if rec == "1" and anios == "":
        warns.append((idx, "recuperacion_anios", "recupero=1 sin años (válido, pero ambiguo)"))
    if rec == "" and anios != "":
        errores.append((idx, "recuperacion_anios", f"recupero vacío pero anios={anios!r}"))

    if (fila.get("hizo_inversiones") or "").strip() == "1" and vals_p["piezas_ninguna"] == "1":
        warns.append((idx, "hizo_inversiones", "dijo invertir pero ninguna pieza rota"))

    if (fila.get("usa_panel_solar") or "").strip() == "1":
        luz = (fila.get("costo_luz_mes_cup") or "").strip()
        if luz and es_float(luz) and float(luz) > 2000:
            warns.append((idx, "costo_luz_mes_cup", f"usa panel pero luz={luz} (>2000, revisar)"))

    m = (fila.get("marca") or "").strip()
    if m and marcas_rev is not None and m not in marcas_rev:
        warns.append((idx, "marca", f"marca no vista en Revolico: {m!r}"))

    return errores, warns

def outliers_mad(filas, col):
    vals = []
    for i, f in enumerate(filas, start=2):
        v = (f.get(col) or "").strip()
        if v and es_float(v):
            vals.append((i, float(v)))
    if len(vals) < 5: return []
    arr = [x for _, x in vals]
    m = statistics.median(arr)
    desv = [abs(x - m) for x in arr]
    mad = statistics.median(desv)
    if mad == 0: return []
    return [(i, x, 0.6745*(x - m)/mad) for i, x in vals if abs(0.6745*(x - m)/mad) > 3.5]

def main():
    if not CSV_PATH.exists():
        print(f"ERROR: no existe {CSV_PATH}", file=sys.stderr); sys.exit(2)

    with CSV_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        if cols != CABECERA:
            print("ERROR: cabecera no coincide.")
            print(f"  Faltan: {[c for c in CABECERA if c not in cols]}")
            print(f"  Sobran: {[c for c in cols if c not in CABECERA]}")
            sys.exit(1)
        filas = list(reader)

    marcas_rev = cargar_marcas_revolico()

    todos_e, todos_w = [], []
    ids = {}
    for i, f in enumerate(filas, start=2):
        e, w = validar_fila(f, i, marcas_rev)
        todos_e.extend(e); todos_w.extend(w)
        idv = (f.get("id_encuesta") or "").strip()
        if idv:
            if idv in ids:
                todos_e.append((i, "id_encuesta", f"duplicado (ya en fila {ids[idv]})"))
            else:
                ids[idv] = i

    for col in OUTLIER_COLS:
        for fila_i, val, z in outliers_mad(filas, col):
            todos_w.append((fila_i, col, f"outlier MAD z={z:.2f}: valor={val} (revisar, no bloquea)"))

    print(f"Archivo: {CSV_PATH}")
    print(f"Filas: {len(filas)} | Errores: {len(todos_e)} | Warnings: {len(todos_w)}")
    if marcas_rev is None:
        print("Nota: no se pudo cargar el JSON de Revolico; no se valida marca contra él.")
    else:
        print(f"Marcas Revolico cargadas: {len(marcas_rev)}")

    if todos_w:
        print("\n--- WARNINGS (revisar, no bloquean) ---")
        for f_, c, m in todos_w:
            print(f"  fila {f_:>3} | {c:<26} | {m}")

    if todos_e:
        print("\n--- ERRORES (bloquean commit) ---")
        for f_, c, m in todos_e:
            print(f"  fila {f_:>3} | {c:<26} | {m}")
        sys.exit(1)

    print("\nOK: todas las filas válidas.")

if __name__ == "__main__":
    main()
