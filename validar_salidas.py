#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from jsonschema import Draft7Validator

ESQUEMAS = {
    "triciclos_aceptados.json": "triciclo_aceptado_schema.json",
    "triciclos_descartados.json": "triciclo_descartado_schema.json",
}

def validar_archivo(datos_path: Path, esquema_path: Path) -> bool:
    if not datos_path.exists():
        print(f"⚠️  No existe: {datos_path}")
        return False
    if not esquema_path.exists():
        print(f"❌ Falta el esquema: {esquema_path}")
        return False

    with open(datos_path, encoding="utf-8") as f:
        datos = json.load(f)
    with open(esquema_path, encoding="utf-8") as f:
        esquema = json.load(f)

    if not isinstance(datos, list):
        print(f"❌ {datos_path.name} no es un array JSON.")
        return False

    validador = Draft7Validator(esquema)
    errores_totales = 0
    for i, item in enumerate(datos):
        errores = sorted(validador.iter_errors(item), key=lambda e: e.path)
        if errores:
            errores_totales += len(errores)
            print(f"\n❌ {datos_path.name} — índice {i}:")
            for err in errores:
                ruta = ".".join(str(p) for p in err.path) or "(raíz)"
                print(f"   • {ruta}: {err.message}")

    if errores_totales == 0:
        print(f"✅ {datos_path.name}: {len(datos)} registros válidos.")
        return True
    else:
        print(f"\n❌ {datos_path.name}: {errores_totales} errores en {len(datos)} registros.")
        return False

def main():
    base = Path(__file__).parent
    todo_ok = True
    for datos_nombre, esquema_nombre in ESQUEMAS.items():
        ok = validar_archivo(base / datos_nombre, base / esquema_nombre)
        todo_ok = todo_ok and ok
    sys.exit(0 if todo_ok else 1)

if __name__ == "__main__":
    main()
