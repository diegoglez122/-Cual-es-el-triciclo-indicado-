#!/usr/bin/env python3
"""Normaliza triciclos_aceptados.json → triciclos_aceptados_normalizado.json.

NUNCA sobrescribe el original. Duplicados detectados → duplicados_descartados.json.

Uso:
  python scripts/normalizar.py --reporte   # solo reporte previo (sin escribir nada)
  python scripts/normalizar.py --aplicar   # aplica normalización + dedup y escribe salidas
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACEPTADOS = ROOT / 'data' / 'raw' / 'triciclos_aceptados.json'
SALIDA = ROOT / 'data' / 'processed' / 'triciclos_aceptados_normalizado.json'
DESCARTES = ROOT / 'data' / 'processed' / 'duplicados_descartados.json'

# --- Mapeo de marcas: variante -> canónica. Clave en minúsculas sin espacios extra ---
MAPEO_MARCAS = {
    # Familia Jinpeng (variantes de escritura de la marca china Jinpeng)
    'jimpeng': 'Jinpeng',
    'jimpeg': 'Jinpeng',
    'jimpen': 'Jinpeng',
    'jinpen': 'Jinpeng',
    # Portobello
    'porto bello': 'Portobello',
}
# Marcas ambiguas: NO se transforman automáticamente. Se listan en el reporte
# para decisión del usuario. Valor: motivo de la ambigüedad.
MARCAS_AMBIGUAS = {
    'JIN': 'Podría ser abreviatura de Jinpeng (1 registro). No se fusiona sin OK.',
    'Rali Cargo': 'Puede ser modelo/subtipo de Rali, o marca independiente. No se fusiona sin OK.',
    'TRICICLOS': 'No es una marca (categoría genérica, 2 registros).',
    'CUATRICICLOS': 'No es una marca (categoría genérica, 1 registro).',
    'MOTOR': 'No es una marca (palabra genérica, 1 registro).',
    'Nuevos': 'No es una marca (calificador, 1 registro).',
    'DIRECTO': 'No es una marca (calificador, 1 registro).',
    'Llc': 'Sufijo societario, no una marca (10 registros).',
}


def cargar_aceptados():
    if not ACEPTADOS.exists():
        sys.exit(f'ERROR: no existe {ACEPTADOS}')
    with open(ACEPTADOS, encoding='utf-8') as f:
        return json.load(f)


def clave_enlace(enlace):
    """'/item/xxx-57991810' a partir de la URL completa."""
    e = (enlace or '').strip()
    e = re.sub(r'^https?://(www\.)?revolico\.com', '', e)
    if not e.startswith('/'):
        e = '/' + e
    return e


def id_desde_enlace(enlace):
    m = re.search(r'(\d+)\s*$', clave_enlace(enlace))
    return int(m.group(1)) if m else 0


def normalizar_marca(valor):
    if not valor:
        return None, None
    original = str(valor).strip()
    clave = original.lower()
    if clave in MAPEO_MARCAS:
        can = MAPEO_MARCAS[clave]
        if can != original:
            return can, original
        return original, None
    return original, None


def normalizar_voltaje(valor):
    """72V/72v/v72 -> 72. No numérico -> None."""
    if valor is None:
        return None
    m = re.search(r'\d+', str(valor))
    return int(m.group()) if m else None


def normalizar_autonomia(valor):
    """Rango '100-120' -> (None, 100, 120). Número v -> (v, v, v)."""
    if valor is None:
        return None, None, None
    if isinstance(valor, str):
        m = re.match(r'^\s*(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*$', valor)
        if m:
            mn, mx = float(m.group(1)), float(m.group(2))
            if mn > mx:
                mn, mx = mx, mn
            return None, mn, mx
        m2 = re.match(r'^\s*(\d+(?:\.\d+)?)\s*$', valor)
        if m2:
            v = float(m2.group(1))
            return v, v, v
        return None, None, None
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None, None, None
    if v <= 0:
        return None, None, None
    return v, v, v


def cargar_indice_estado():
    """indice[clave_enlace] = {'gcsKey':..., 'phone':...} desde revolico_state_p*.json."""
    indice = {}
    for path in sorted(ROOT.glob('scraping/data/revolico_state_p*.json')):
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            st = data['props']['pageProps']['__APOLLO_STATE__']
        except (KeyError, json.JSONDecodeError):
            continue
        for key, ad in st.items():
            if not key.startswith('AdType:') or not isinstance(ad, dict):
                continue
            perm = ad.get('permalink')
            if not perm:
                continue
            gcs = None
            mi = ad.get('mainImage')
            if isinstance(mi, dict):
                gcs = mi.get('gcsKey')
            phone = None
            pi = ad.get('phoneInfo')
            if isinstance(pi, dict):
                fp = pi.get('firstPhone')
                if isinstance(fp, dict) and fp.get('number'):
                    phone = f"{fp.get('prefix') or ''}{fp['number']}"
            reg = indice.setdefault(clave_enlace(perm), {'gcsKey': None, 'phone': None})
            if reg['gcsKey'] is None and gcs:
                reg['gcsKey'] = gcs
            if reg['phone'] is None and phone:
                reg['phone'] = phone
    return indice


def reporte(aceptados):
    marcas = Counter(str(r.get('marca_detectada')) for r in aceptados)
    print(f'REPORTE PREVIO — {len(aceptados)} registros, {len(marcas)} marcas distintas\n')
    print('=== 1. Valores distintos de marca_detectada (con conteo) ===')
    for marca, n in marcas.most_common():
        print(f'{n:5d}  {marca}')
    print('\n=== 2. Propuesta de mapeo de variantes ===')
    inverso = defaultdict(list)
    for var, can in MAPEO_MARCAS.items():
        inverso[can].append(var)
    for can, variantes in sorted(inverso.items()):
        afectados = {v: marcas.get(next((m for m in marcas if m.lower() == v), ''), 0)
                     for v in variantes}
        variantes_conteo = ', '.join(f'{v!r}({n})' for v, n in afectados.items() if n)
        total = sum(n for n in afectados.values())
        if total:
            print(f'  {variantes_conteo}  ->  {can!r}  [afecta {total} registros]')
    print('\n  (las variantes que no aparecen arriba no existen en los datos)')
    print('\n=== 3. CASOS AMBIGUOS (no se tocan sin tu OK) ===')
    for marca, motivo in MARCAS_AMBIGUAS.items():
        n = marcas.get(marca, 0)
        if n:
            print(f'  {marca!r} ({n} reg.): {motivo}')
    print('\n=== 4. Previsualización técnica ===')
    volt = Counter(str(r.get('voltaje_bateria')) for r in aceptados)
    print('  voltaje_bateria:', dict(volt.most_common()))
    tipos = Counter(type(r.get('autonomia_km')).__name__ for r in aceptados)
    rangos = [r.get('autonomia_km') for r in aceptados
              if isinstance(r.get('autonomia_km'), str)
              and re.search(r'\d\s*[-–—]\s*\d', str(r.get('autonomia_km')))]
    print(f'  autonomia_km tipos: {dict(tipos)} | rangos str detectados: {len(rangos)}')
    indice = cargar_indice_estado()
    enlaces = [clave_enlace(r.get('enlace')) for r in aceptados]
    match = sum(1 for e in enlaces if e in indice)
    print(f'  cruce estado: {match}/{len(enlaces)} enlaces con match en revolico_state_p*.json')
    print('\nFIN REPORTE. No se escribió nada. Esperando OK para --aplicar.')


def aplicar(aceptados):
    indice = cargar_indice_estado()
    unificados = Counter()
    voltajes_no_numericos = Counter()
    autonomias_rango = 0
    sin_match_estado = 0

    out = []
    for r in aceptados:
        r = dict(r)
        marca_antes = r.get('marca_detectada')
        marca_despues, cambiada = normalizar_marca(marca_antes)
        r['marca_detectada'] = marca_despues
        if cambiada:
            unificados[(cambiada, marca_despues)] += 1

        vb = r.get('voltaje_bateria')
        r['voltaje_bateria'] = normalizar_voltaje(vb)
        if vb is not None and r['voltaje_bateria'] is None:
            voltajes_no_numericos[str(vb)] += 1

        antes = r.get('autonomia_km')
        aut, mn, mx = normalizar_autonomia(antes)
        if isinstance(antes, str) and re.match(r'^\s*\d+(?:\.\d+)?\s*[-–—]\s*\d+', antes):
            autonomias_rango += 1
        r['autonomia_km'] = aut
        r['autonomia_km_min'] = mn
        r['autonomia_km_max'] = mx

        enlace_clave = clave_enlace(r.get('enlace'))
        match = indice.get(enlace_clave)
        if match:
            r['gcsKey'] = match['gcsKey']
            r['phone'] = match['phone']
        else:
            r['gcsKey'] = None
            r['phone'] = None
            sin_match_estado += 1
        out.append(r)

    # --- DEDUP por (gcsKey, phone) ---
    grupos = defaultdict(list)
    for i, r in enumerate(out):
        # dedup solo con gcsKey y phone ambos no-nulos; (None, phone) o (gcsKey, None) no agrupan
        if r['gcsKey'] is None or r['phone'] is None:
            continue
        grupos[(r['gcsKey'], r['phone'])].append(i)

    descartar = set()
    descartados = []
    n_grupos_dup = 0
    for (gcs, phone), idxs in grupos.items():
        if len(idxs) < 2:
            continue
        n_grupos_dup += 1
        # conservar: fecha más reciente; empate -> menor id de enlace
        mejor = max(idxs, key=lambda i: ((out[i].get('fecha_publicacion') or ''),
                                         -id_desde_enlace(out[i].get('enlace'))))
        for i in idxs:
            if i == mejor:
                continue
            descartar.add(i)
            descartados.append({
                'enlace': out[i].get('enlace'),
                'gcsKey': gcs,
                'phone': phone,
                'fecha_publicacion': out[i].get('fecha_publicacion'),
                'motivo': 'DUPLICADO_IMG_TEL',
            })

    final = [r for i, r in enumerate(out) if i not in descartar]

    with open(SALIDA, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    with open(DESCARTES, 'w', encoding='utf-8') as f:
        json.dump(descartados, f, ensure_ascii=False, indent=2)

    print('=== RESUMEN ===')
    print(f'Registros IN:   {len(aceptados)}')
    print(f'Registros OUT:  {len(final)}  (esperado 757)')
    if len(final) != 757:
        print('*** AVISO: el número final difiere de 757. Revisar antes de dar por bueno. ***')
    print(f'\nMarcas unificadas ({sum(unificados.values())} cambios):')
    for (antes, despues), n in unificados.most_common():
        print(f'  {antes!r} -> {despues!r}: {n}')
    print(f'\nVoltajes no numéricos -> null: {sum(voltajes_no_numericos.values())}')
    for v, n in voltajes_no_numericos.most_common():
        print(f'  {v!r}: {n}')
    print(f'\nAutonomías convertidas a rango (min/max, autonomia_km=null): {autonomias_rango}')
    print(f'Sin match en estado (gcsKey=phone=null): {sin_match_estado}')
    print(f'\nDuplicados: {n_grupos_dup} grupos, {len(descartados)} registros descartados')
    print(f'Salidas: {SALIDA.name} ({len(final)}), {DESCARTES.name} ({len(descartados)})')
    print('Original intacto: triciclos_aceptados.json no fue tocado.')


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('--reporte', '--aplicar'):
        sys.exit(__doc__)
    aceptados = cargar_aceptados()
    if sys.argv[1] == '--reporte':
        reporte(aceptados)
    else:
        aplicar(aceptados)


if __name__ == '__main__':
    main()
