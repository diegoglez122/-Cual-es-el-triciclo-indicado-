#!/usr/bin/env python3
"""
Pipeline unificado de Revolico. Reemplaza a procesar_triciclos.py,
reprocesar_descartados.py y parche_extractor.py.

- Lee TODOS los revolico_state_p*.json
- Usa cache_descripciones.json para no re-descargar
- Aplica extractores v3 (con soporte 'hasta', rangos, etc.)
- Genera triciclos_aceptados.json y triciclos_descartados.json
- Guarda el caché incrementalmente
"""
import json
import re
import os
import time
import glob
import requests
from bs4 import BeautifulSoup
from collections import Counter

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}
BASE_URL = "https://www.revolico.com"
CACHE_FILE = "cache_descripciones.json"
PAUSA = 3

MARCAS_CONOCIDAS = [
    "VEDCA", "JINPENG", "JIMPENG", "JIMPEG", "MISHOZUKI", "TOPMAQ", "STAR",
    "MVP", "KVITOVA", "ONEHOT", "OIM", "MAF", "CAIMAN", "TRAKTION",
    "YAMAKI", "PORTO BELLO", "PORTOBELLO", "JINGHAN", "NAVILAM",
    "LEISURE", "JMD", "VIENTO RAPIDO", "UNIZUKI", "BRYDERK", "PANTHER",
    "JINPEN", "JIMPEN", "LLC", "POWER RED", "MOTOMANIA", "DAYUN", "TOP MAQ",
    "RACING", "FLY", "MAGICBIKE", "MIDHA", "LAZER", "MASTERSONIC",
    "ONEBOT", "CHALY", "RALI", "RALI CARGO"
]

def extraer_ads(data):
    apollo = data['props']['pageProps']['__APOLLO_STATE__']
    return [v for k, v in apollo.items() if k.startswith('AdType:')]

def construir_lookups(datas):
    provincias, municipios = {}, {}
    for data in datas:
        apollo = data['props']['pageProps']['__APOLLO_STATE__']
        for key, val in apollo.items():
            if key.startswith('ProvinceType:') and isinstance(val, dict):
                provincias[key.split(':', 1)[1]] = val.get('name')
            elif key.startswith('MunicipalityType:') and isinstance(val, dict):
                municipios[key.split(':', 1)[1]] = val.get('name')
    return provincias, municipios

def limpiar_texto(t):
    if not t: return ""
    t = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060\ufeff]', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def extraer_autonomia(texto):
    if not texto: return None
    t = limpiar_texto(texto)
    pre = r'(?:(?:de|hasta|aproximadamente|aproximad[ao]s?|aprox\.?|m[áa]x\.?|m[áa]ximo|unos|m[áa]s|~|\+)\s*)*'
    num = r'(\d+(?:[.,]\d+)?)'
    rango = r'(?:\s*(?:[-–/]|\ba\b)\s*(\d+(?:[.,]\d+)?))?'
    km  = r'\s*(?:kms?|kil[óo]metros?)\b(?!\s*/\s*h)'
    km2 = r'\s*(?:kms?|kil[óo]metros?|klms?)\b(?!\s*/\s*h)'
    patrones = [
        # --- base (fix2, no tocar) ---
        rf'[Aa]utonom[íi]a\s*[:\-]?\s*{pre}{num}{rango}{km}',
        rf'[Aa]lcance\s*[:\-]?\s*{pre}{num}{rango}{km}',
        rf'{num}{rango}{km}\s+de\s+[Aa]utonom',
        rf'recorre\s+{pre}{num}\s*(?:kms?|kil[óo]metros?)\b',
        rf'{num}{rango}{km}\s+(?:sin|con|por)\s+carga',
        rf'[Kk]ilometraje\s*[:\-]?\s*{pre}{num}',
        rf'hasta\s+{pre}{num}\s*(?:kms?|kil[óo]metros?)\b(?!\s*/\s*h)',
        # --- nuevos, SOLO al final ---
        rf'[Aa]utonom[íi]a\s+por\s+carga\s*[:\-]?\s*{pre}{num}{rango}{km2}',
        rf'[Aa]utonom[íi]a\s+(?:de\s+)?(?:kms?|kil[óo]metros?|klms?)\s*[:\-]?\s*{num}',
        rf'[Aa]utonom[íi]a\s*[:\-]?\s*{pre}{num}\s*k\b',
        rf'[Aa]utonom[íi]a\s*[:\-]?\s*{pre}{num}{rango}{km2}',
        rf'[Rr]ecorrido(?:\s+de)?\s+{pre}{num}{rango}{km2}',
        rf'[Rr]endimiento\s*[:\-]?\s*{pre}{num}{rango}{km2}',
        rf'{num}{rango}{km2}\s+(?:x|por)\s+carga',
    ]
    for p in patrones:
        m = re.search(p, t, re.IGNORECASE)
        if m:
            try:
                v1 = float(m.group(1).replace(',', '.'))
                v2 = None
                if len(m.groups()) >= 2 and m.group(2):
                    try: v2 = float(m.group(2).replace(',', '.'))
                    except ValueError: v2 = None
                v = max(v1, v2) if v2 else v1
                if 0 < v < 1000: return v
            except (ValueError, IndexError):
                pass
    return None

def _norm_upper(s):
    import unicodedata
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.upper()

def extraer_marca(titulo, descripcion):
    texto_orig = f"{titulo} {descripcion or ''}"
    texto_norm = _norm_upper(texto_orig)
    for marca in sorted(MARCAS_CONOCIDAS, key=len, reverse=True):
        if _norm_upper(marca) in texto_norm:
            return marca.title()
    m = re.search(r'[Mm]arca\s*(?::|\-|es)?\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ0-9]{2,20})', texto_orig)
    if m: return m.group(1)
    cands = re.findall(r'[Tt]riciclos?\s+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ]{2,15})\b', texto_orig)
    stop = {'ELECTRICO','ELECTRICOS','DE','CON','SIN','PARA','MODELO','CARGA','CHINO','NUEVO','NUEVA','USADO','BARATO'}
    for cand in cands:
        if _norm_upper(cand) not in stop:
            return cand
    return None

def extraer_tipo(texto):
    if not texto: return None
    t = texto.lower()
    if 'híbrido' in t or 'hibrido' in t or 'hybrid' in t: return "híbrido"
    senales = ['eléctrico','electrico','electric','batería','bateria','baterías','baterias','litio','lifepo','gel','autonomía','autonomia','cargador inteligente']
    if any(s in t for s in senales): return "eléctrico"
    if re.search(r'\b(48|60|72|84|96)\s*[Vv]\b', texto): return "eléctrico"
    if any(s in t for s in ['gasolina','combustible','nafta','motor 2t','motor 4t']): return "combustible"
    if re.search(r'\b\d{2,3}\s*cc\b', t): return "combustible"
    return None

def extraer_voltaje(texto):
    if not texto: return None
    for m in re.finditer(r'(\d{2,3})\s*[Vv]\b', texto):
        v = int(m.group(1))
        if 12 <= v <= 120: return f"{v}V"
    return None

def extraer_garantia(texto):
    if not texto: return None
    for p in [r'[Gg]arant[íi]a[:\s]+(\d+)\s*mes', r'(\d+)\s*meses?\s+de\s+[Gg]arant']:
        m = re.search(p, texto)
        if m: return int(m.group(1))
    return None

def extraer_panel(texto):
    if not texto: return None
    t = texto.lower()
    if 'sin panel' in t: return False
    if 'panel solar' in t or 'panel incl' in t or 'con panel' in t: return True
    return None

def extraer_uso(texto):
    if not texto: return None
    t = texto.lower()
    if 'carga' in t and 'pasajero' in t: return "mixto"
    if 'carga' in t or 'cargo' in t: return "carga"
    if 'pasajero' in t: return "pasajeros"
    if 'comercial' in t or 'negocio' in t: return "comercial"
    return None

def cargar_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def descargar_detalle(permalink, cache):
    """Devuelve dict {title, description} o None. Guarda en caché."""
    if permalink in cache and cache[permalink].get('description') is not None:
        return cache[permalink]
    try:
        r = requests.get(BASE_URL + permalink, headers=HEADERS, timeout=45)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script:
            return None
        data = json.loads(script.string)
        apollo = data['props']['pageProps'].get('__APOLLO_STATE__', {})
        for key, val in apollo.items():
            if key.startswith('AdType:') and isinstance(val, dict) and 'description' in val:
                resultado = {"title": val.get('title', ''), "description": val.get('description') or ''}
                cache[permalink] = resultado
                guardar_cache(cache)
                return resultado
    except Exception as e:
        print(f"    ⚠️  {e}")
    return None

def evaluar(ad_busqueda, detalle, provincias, municipios):
    """Devuelve (aceptado|None, descartado|None)."""
    titulo = detalle['title'] if detalle else ad_busqueda.get('title', '')
    descripcion = detalle['description'] if detalle else ''
    texto = f"{titulo}\n{descripcion}"

    precio = ad_busqueda.get('price')
    moneda = ad_busqueda.get('currency')
    # Extraer provincia: puede venir como provinceId (string) o province.__ref (detalle)
    prov_id = ad_busqueda.get('provinceId', '')
    if not prov_id:
        prov_ref = ad_busqueda.get('province', {})
        if isinstance(prov_ref, dict) and '__ref' in prov_ref:
            prov_id = prov_ref['__ref'].split(':', 1)[1]
    mun_id = ad_busqueda.get('municipalityId', '')
    if not mun_id:
        mun_ref = ad_busqueda.get('municipality', {})
        if isinstance(mun_ref, dict) and '__ref' in mun_ref:
            mun_id = mun_ref['__ref'].split(':', 1)[1]
    provincia = provincias.get(str(prov_id)) if prov_id else None
    municipio = municipios.get(str(mun_id)) if mun_id else None
    fecha_iso = ad_busqueda.get('updatedOnToOrder') or ad_busqueda.get('updatedOnByUser', '')
    fecha = fecha_iso[:10] if fecha_iso else None

    datos = {
        "precio_publicado": precio,
        "tipo_triciclo": extraer_tipo(texto),
        "marca_detectada": extraer_marca(titulo, descripcion),
        "ubicacion": provincia,
        "fecha_publicacion": fecha,
        "autonomia_km": extraer_autonomia(texto),
        "moneda_original": moneda,
        "municipio": municipio,
        "tipo_uso": extraer_uso(texto),
        "garantia_meses": extraer_garantia(texto),
        "panel_incluido": extraer_panel(texto),
        "voltaje_bateria": extraer_voltaje(texto),
    }

    motivos = []
    if not precio or not isinstance(precio, (int, float)) or precio <= 0:
        motivos.append("PRECIO_INVALIDO")
    if datos["tipo_triciclo"] not in ("eléctrico", "combustible", "híbrido"):
        motivos.append("TIPO_NO_DETERMINADO")
    if not datos["marca_detectada"] or datos["marca_detectada"].lower() == "desconocida":
        motivos.append("MARCA_NO_DETECTADA")
    if not provincia or provincia.strip() == "":
        motivos.append("UBICACION_VACIA")
    if not fecha or not fecha.startswith("2026-"):
        motivos.append("FECHA_FUERA_DE_2026")
    if not datos["autonomia_km"] or datos["autonomia_km"] <= 0:
        motivos.append("AUTONOMIA_NO_INDICADA")
    if not moneda or moneda not in ("USD", "CUP", "MN", "EUR", "MLC"):
        motivos.append("MONEDA_NO_DETECTADA")

    enlace = BASE_URL + ad_busqueda['permalink']
    if motivos:
        return None, {"enlace": enlace, "titulo_crudo": titulo,
                      "motivos_descarte": motivos, "datos_crudos": datos}
    return {**datos, "enlace": enlace}, None

def main():
    print("📂 Cargando archivos de estado...")
    datas = []
    for path in sorted(glob.glob('revolico_state_p*.json')):
        with open(path, encoding='utf-8') as f:
            datas.append(json.load(f))
        print(f"  → {path}")
    if not datas:
        print("❌ No hay revolico_state_p*.json")
        return

    ads_raw = []
    for d in datas:
        ads_raw.extend(extraer_ads(d))
    provincias, municipios = construir_lookups(datas)

    vistos = set()
    triciclos = []
    for a in ads_raw:
        if a['id'] in vistos: continue
        if 'triciclo' in a['title'].lower() or 'triciclo' in a.get('permalink', '').lower():
            triciclos.append(a); vistos.add(a['id'])

    print(f"\n  → {len(ads_raw)} anuncios totales")
    print(f"  → {len(triciclos)} triciclos únicos")

    cache = cargar_cache()
    print(f"  → Caché: {len(cache)} descripciones\n")

    aceptados, descartados = [], []
    descargas_nuevas = 0
    for i, ad in enumerate(triciclos, 1):
        permalink = ad['permalink']
        vino_de_cache = permalink in cache
        detalle = descargar_detalle(permalink, cache)
        if not vino_de_cache:
            descargas_nuevas += 1

        if not detalle:
            descartados.append({
                "enlace": BASE_URL + permalink,
                "titulo_crudo": ad.get('title'),
                "motivos_descarte": ["DESCARGA_FALLIDA"],
                "datos_crudos": {k: None for k in ["precio_publicado","tipo_triciclo","marca_detectada",
                    "ubicacion","fecha_publicacion","autonomia_km","moneda_original",
                    "municipio","tipo_uso","garantia_meses","panel_incluido","voltaje_bateria"]}
            })
            print(f"[{i}/{len(triciclos)}] ❌ DESCARGAR_FALLIDA: {ad['title'][:60]}")
        else:
            ac, de = evaluar(ad, detalle, provincias, municipios)
            if ac:
                aceptados.append(ac)
                print(f"[{i}/{len(triciclos)}] ✅ {ac['marca_detectada']} | {ac['autonomia_km']}km | {ad['title'][:50]}")
            else:
                descartados.append(de)
                print(f"[{i}/{len(triciclos)}] ❌ {', '.join(de['motivos_descarte'])} | {ad['title'][:50]}")

        if not vino_de_cache:
            time.sleep(PAUSA)

    with open('triciclos_aceptados.json', 'w', encoding='utf-8') as f:
        json.dump(aceptados, f, ensure_ascii=False, indent=2)
    with open('triciclos_descartados.json', 'w', encoding='utf-8') as f:
        json.dump(descartados, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}\n📊 RESUMEN\n{'='*50}")
    print(f"Triciclos procesados:  {len(triciclos)}")
    print(f"Aceptados:             {len(aceptados)}")
    print(f"Descartados:           {len(descartados)}")
    print(f"Descargas nuevas:      {descargas_nuevas}")
    print(f"\nDescartes por criterio:")
    c = Counter()
    for d in descartados:
        for m in d['motivos_descarte']:
            c[m] += 1
    for m, n in c.most_common():
        print(f"  {m}: {n}")

if __name__ == "__main__":
    main()
