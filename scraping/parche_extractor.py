#!/usr/bin/env python3
"""
Parche: solo actualiza el patrón de autonomía en los scripts existentes
y reprocesa usando el caché de descripciones (no vuelve a descargar).
"""
import json
import re
import os
from collections import Counter

CACHE_FILE = "scraping/data/cache_descripciones.json"

def limpiar_texto(t):
    if not t: return ""
    t = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060\ufeff]', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def extraer_autonomia_v2(texto):
    """Extractor de autonomía con soporte para 'hasta', 'máx', rangos, etc."""
    if not texto: return None
    t = limpiar_texto(texto)
    
    # Prefijos opcionales entre la palabra clave y el número
    pre = r'(?:de\s+|hasta\s+|de\s+hasta\s+|aprox\.?\s*|aproximadamente\s+|m[áa]x\.?\s*|m[áa]ximo\s+|unos\s+|~)?'
    num = r'(\d+(?:[.,]\d+)?)'
    rango = r'(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?'
    km = r'\s*k?m\b'
    
    patrones = [
        rf'[Aa]utonom[íi]a\s*[:\-]?\s*{pre}{num}{rango}{km}',
        rf'[Aa]lcance\s*[:\-]?\s*{pre}{num}{rango}{km}',
        rf'{num}{rango}{km}\s+de\s+[Aa]utonom',
        rf'recorre\s+{pre}{num}\s*k?m',
        rf'{num}{rango}{km}\s+(?:sin|con)\s+carga',
        rf'[Kk]ilometraje\s*[:\-]?\s*{pre}{num}',
        rf'hasta\s+{num}\s*k?m',
    ]
    
    for p in patrones:
        m = re.search(p, t, re.IGNORECASE)
        if m:
            try:
                v = float(m.group(1).replace(',', '.'))
                if 0 < v < 1000:
                    return v
            except ValueError:
                pass
    return None

def extraer_tipo_v2(texto):
    if not texto: return None
    t = texto.lower()
    if 'híbrido' in t or 'hibrido' in t or 'hybrid' in t:
        return "híbrido"
    señales_electricas = ['eléctrico', 'electrico', 'electric', 'batería', 'bateria',
                          'baterías', 'baterias', 'litio', 'lifepo', 'gel',
                          'autonomía', 'autonomia', 'cargador inteligente']
    if any(s in t for s in señales_electricas):
        return "eléctrico"
    if re.search(r'\b(48|60|72|84|96)\s*[Vv]\b', texto):
        return "eléctrico"
    if any(s in t for s in ['gasolina', 'combustible', 'nafta', 'motor 2t', 'motor 4t']):
        return "combustible"
    if re.search(r'\b\d{2,3}\s*cc\b', t):
        return "combustible"
    return None

def evaluar(datos, titulo, descripcion):
    texto = f"{titulo}\n{descripcion}"
    tipo = extraer_tipo_v2(texto)
    autonomia = extraer_autonomia_v2(texto)
    datos['tipo_triciclo'] = tipo or datos.get('tipo_triciclo')
    datos['autonomia_km'] = autonomia if autonomia is not None else datos.get('autonomia_km')
    
    motivos = []
    precio = datos.get('precio_publicado')
    if not precio or not isinstance(precio, (int, float)) or precio <= 0:
        motivos.append("PRECIO_INVALIDO")
    if datos['tipo_triciclo'] not in ("eléctrico", "combustible", "híbrido"):
        motivos.append("TIPO_NO_DETERMINADO")
    marca = datos.get('marca_detectada')
    if not marca or marca.lower() == "desconocida":
        motivos.append("MARCA_NO_DETECTADA")
    ubic = datos.get('ubicacion')
    if not ubic or str(ubic).strip() == "":
        motivos.append("UBICACION_VACIA")
    fecha = datos.get('fecha_publicacion')
    if not fecha or not str(fecha).startswith("2026-"):
        motivos.append("FECHA_FUERA_DE_2026")
    if not datos['autonomia_km'] or datos['autonomia_km'] <= 0:
        motivos.append("AUTONOMIA_NO_INDICADA")
    moneda = datos.get('moneda_original')
    if not moneda or moneda not in ("USD", "CUP", "MN", "EUR", "MLC"):
        motivos.append("MONEDA_NO_DETECTADA")
    return motivos, datos

def main():
    # Cargar caché
    if not os.path.exists(CACHE_FILE):
        print("❌ No hay cache_descripciones.json. Ejecuta primero reprocesar_descartados.py")
        return
    with open(CACHE_FILE, encoding='utf-8') as f:
        cache = json.load(f)
    print(f"📂 Caché cargada: {len(cache)} descripciones\n")
    
    with open('data/raw/triciclos_aceptados.json', encoding='utf-8') as f:
        aceptados = json.load(f)
    with open('scraping/data/triciclos_descartados.json', encoding='utf-8') as f:
        descartados = json.load(f)
    
    print(f"Estado inicial: {len(aceptados)} aceptados, {len(descartados)} descartados\n")
    
    nuevos = []
    siguen = []
    sin_cache = []
    
    for i, d in enumerate(descartados, 1):
        permalink = d['enlace'].replace("https://www.revolico.com", "")
        detalle = cache.get(permalink)
        if not detalle:
            sin_cache.append(d)
            siguen.append(d)
            continue
        
        motivos, datos_act = evaluar(d['datos_crudos'].copy(), detalle['title'], detalle['description'])
        if motivos:
            d['datos_crudos'] = datos_act
            d['motivos_descarte'] = motivos
            siguen.append(d)
        else:
            nuevos.append({**datos_act, "enlace": d['enlace']})
            print(f"[{i}] ✅ RECUPERADO: {d['titulo_crudo'][:60]}")
    
    aceptados_final = aceptados + nuevos
    with open('data/raw/triciclos_aceptados.json', 'w', encoding='utf-8') as f:
        json.dump(aceptados_final, f, ensure_ascii=False, indent=2)
    with open('scraping/data/triciclos_descartados.json', 'w', encoding='utf-8') as f:
        json.dump(siguen, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}\n📊 RESULTADO FINAL\n{'='*50}")
    print(f"Aceptados:   {len(aceptados)} → {len(aceptados_final)}")
    print(f"Descartados: {len(descartados)} → {len(siguen)}")
    print(f"\nDescartes restantes:")
    c = Counter()
    for d in siguen:
        for m in d['motivos_descarte']:
            c[m] += 1
    for m, n in c.most_common():
        print(f"  {m}: {n}")

if __name__ == "__main__":
    main()
