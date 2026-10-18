#!/usr/bin/env python3
"""Chequeo de duplicados en triciclos_aceptados.json. SOLO LECTURA."""
import json
from collections import defaultdict

ACEPT = 'triciclos_aceptados.json'
aceptados = json.load(open(ACEPT))
print(f'Total aceptados: {len(aceptados)}\n')

# --- 1. Estructura del primer registro ---
print('=== CAMPOS EN aceptados[0] ===')
for k, v in aceptados[0].items():
    s = str(v)
    if len(s) > 70:
        s = s[:67] + '...'
    print(f'  {k!r}: {s}')

# --- 2. Campos comunes a TODOS ---
common = set(aceptados[0])
for r in aceptados[1:]:
    common &= set(r)
print(f'\nCampos comunes a TODOS: {sorted(common)}')

# --- 3. Detectar campos candidatos ---
def pick(cands, pool):
    return next((c for c in cands if c in pool), None)

id_f  = pick(['id','item_id','itemId','ad_id'], common)
img_f = pick(['gcsKey','gcs_key','image','imagen','img','foto','photo','image_key'], common)
ph_f  = pick(['phone','telefono','teléfono','whatsapp','contacto','phone_number','tel'], common)

print(f'\nDetectados -> id: {id_f} | imagen: {img_f} | telefono: {ph_f}')

# --- 4. Dedup por id (sanity) ---
if id_f:
    by_id = defaultdict(list)
    for i, r in enumerate(aceptados):
        if r.get(id_f) is not None:
            by_id[r[id_f]].append(i)
    dups_id = {k: v for k, v in by_id.items() if len(v) > 1}
    print(f'\nDuplicados por {id_f}: {len(dups_id)} grupos')
    for k, v in list(dups_id.items())[:5]:
        print(f'   id={k} -> indices {v}')

# --- 5. Dedup por (imagen, telefono) ---
if img_f and ph_f:
    by_pair = defaultdict(list)
    for i, r in enumerate(aceptados):
        img, ph = r.get(img_f), r.get(ph_f)
        if img and ph:
            by_pair[(str(img), str(ph))].append(i)
    dups = {k: v for k, v in by_pair.items() if len(v) > 1}
    print(f'\n*** Duplicados por (imagen, telefono): {len(dups)} grupos, '
          f'{sum(len(v) for v in dups.values())} registros afectados ***')
    title_f = next((f for f in ('titulo','title','name','nombre') if f in aceptados[0]), id_f)
    for k, idxs in dups.items():
        print(f'\n   Img={k[0][:50]}... | Tel={k[1]} -> {len(idxs)} registros')
        for i in idxs:
            t = str(aceptados[i].get(title_f, ''))[:60]
            print(f'      [{i}] id={aceptados[i].get(id_f)} | {t}')
else:
    print('\n!! Faltan campos imagen/telefono en aceptados -> no se puede dedup por (img, tel)')
    print('   Opciones: a) enriquecer desde state JSONs  b) quedar solo con dedup por id')

# --- 6. Extras: imagen sola / telefono solo ---
if img_f:
    by_img = defaultdict(list)
    for i, r in enumerate(aceptados):
        v = r.get(img_f)
        if v:
            by_img[str(v)].append(i)
    dups_img = {k: v for k, v in by_img.items() if len(v) > 1}
    print(f'\nSolo por imagen: {len(dups_img)} grupos con imagenes repetidas')

if ph_f:
    by_ph = defaultdict(list)
    for i, r in enumerate(aceptados):
        v = r.get(ph_f)
        if v:
            by_ph[str(v)].append(i)
    print(f'Solo por telefono: {len(by_ph)} telefonos unicos; top repeticiones:')
    for ph, idxs in sorted(by_ph.items(), key=lambda x: -len(x[1]))[:5]:
        print(f'   tel={ph} -> {len(idxs)} anuncios')

print('\nOK. Fin del chequeo. No se modifico nada.')
