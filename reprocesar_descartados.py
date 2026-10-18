#!/usr/bin/env python3
"""
Reprocesa los descartados con extractores mejorados.
NO hace scraping: solo re-evalúa datos ya extraídos en datos_crudos.
Para autonomía y tipo necesita el texto, así que guardamos también el
texto completo de la descripción en un archivo de caché.
"""

import json
import re
import os
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}
BASE_URL = "https://www.revolico.com"
CACHE_FILE = "cache_descripciones.json"

def limpiar_texto(t):
    """Normaliza el texto: quita caracteres invisibles, normaliza espacios."""
    if not t: return ""
    t = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060\ufeff]', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def extraer_autonomia(texto):
    """Extractor mejorado: soporta mayúsculas, rangos, plurales."""
    if not texto: return None
    t = limpiar_texto(texto)
    patrones = [
        # "Autonomía de 80-100 KM" / "Autonomía: 80 km" / "Autonomía 120KM"
        r'[Aa]utonom[íi]a\s*[:\-]?\s*(?:de\s+|aprox\.?\s*)?(\d+(?:[.,]\d+)?)(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?\s*k?m',
        # "Alcance: 120 km" / "Alcance de 80 km"
        r'[Aa]lcance\s*[:\-]?\s*(?:de\s+)?(\d+(?:[.,]\d+)?)(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?\s*k?m',
        # "80 km de autonomía"
        r'(\d+(?:[.,]\d+)?)(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?\s*k?m\s+de\s+[Aa]utonom',
        # "recorre 100 km"
        r'recorre\s+(\d+(?:[.,]\d+)?)\s*k?m',
        # "90-100 km con carga" / "120 km sin carga"
        r'(\d+(?:[.,]\d+)?)(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?\s*k?m\s+(?:sin|con)\s+carga',
        # "Kilometraje: 100"
        r'[Kk]ilometraje\s*[:\-]?\s*(\d+(?:[.,]\d+)?)',
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

def extraer_tipo(texto):
    """Extractor mejorado: infiere eléctrico de palabras técnicas."""
    if not texto: return None
    t = texto.lower()
    if 'híbrido' in t or 'hibrido' in t or 'hybrid' in t:
        return "híbrido"
    # Eléctrico explícito o por términos técnicos
    señales_electricas = [
        'eléctrico', 'electrico', 'electric',
        'batería', 'bateria', 'baterías', 'baterias',
        'litio', 'lifepo', 'gel',
        'autonomía', 'autonomia',
        'cargador inteligente',
    ]
    if any(s in t for s in señales_electricas):
        return "eléctrico"
    # Voltaje explícito: 60V, 72V, 48V
    if re.search(r'\b(48|60|72|84|96)\s*[Vv]\b', texto):
        return "eléctrico"
    # Combustible
    if any(s in t for s in ['gasolina', 'combustible', 'nafta', 'motor 2t', 'motor 4t']):
        return "combustible"
    if re.search(r'\b\d{2,3}\s*cc\b', t):
        return "combustible"
    return None

def descargar_detalle(permalink):
    """Descarga la descripción completa de un anuncio (con caché)."""
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            cache = json.load(f)
    if permalink in cache:
        return cache[permalink]
    
    try:
        r = requests.get(BASE_URL + permalink, headers=HEADERS, timeout=30)
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
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
                return resultado
    except Exception as e:
        print(f"    ⚠️  {e}")
    return None

def evaluar(datos, titulo, descripcion):
    """Re-evalúa los filtros con extractores mejorados."""
    texto = f"{titulo}\n{descripcion}"
    
    # Re-extraer
    tipo = extraer_tipo(texto)
    autonomia = extraer_autonomia(texto)
    
    # Actualizar datos_crudos
    datos['tipo_triciclo'] = tipo or datos.get('tipo_triciclo')
    datos['autonomia_km'] = autonomia if autonomia is not None else datos.get('autonomia_km')
    
    # Aplicar filtros
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
    # Cargar aceptados actuales
    with open('triciclos_aceptados.json', encoding='utf-8') as f:
        aceptados = json.load(f)
    with open('triciclos_descartados.json', encoding='utf-8') as f:
        descartados = json.load(f)
    
    print(f"📂 Estado inicial:")
    print(f"   Aceptados:   {len(aceptados)}")
    print(f"   Descartados: {len(descartados)}\n")
    
    # Cargar caché de descripciones si existe
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            cache = json.load(f)
        print(f"   Descripciones en caché: {len(cache)}\n")
    
    nuevos_aceptados = []
    siguen_descartados = []
    
    for i, d in enumerate(descartados, 1):
        permalink = d['enlace'].replace(BASE_URL, '')
        titulo = d['titulo_crudo']
        
        # Intentar obtener descripción (caché o descarga)
        detalle = descargar_detalle(permalink)
        if not detalle:
            # Si no se puede, mantener descartado
            siguen_descartados.append(d)
            print(f"[{i}/{len(descartados)}] ❌ Sin descripción: {titulo[:50]}")
            time.sleep(1)
            continue
        
        motivos, datos_actualizados = evaluar(d['datos_crudos'].copy(), detalle['title'], detalle['description'])
        
        if motivos:
            d['datos_crudos'] = datos_actualizados
            d['motivos_descarte'] = motivos
            siguen_descartados.append(d)
            print(f"[{i}/{len(descartados)}] ❌ {', '.join(motivos)} | {titulo[:50]}")
        else:
            nuevo = {**datos_actualizados, "enlace": d['enlace']}
            nuevos_aceptados.append(nuevo)
            print(f"[{i}/{len(descartados)}] ✅ RECUPERADO: {titulo[:50]}")
        
        time.sleep(1)  # 1s porque muchos vienen de caché
    
    # Guardar todo
    aceptados_final = aceptados + nuevos_aceptados
    with open('triciclos_aceptados.json', 'w', encoding='utf-8') as f:
        json.dump(aceptados_final, f, ensure_ascii=False, indent=2)
    with open('triciclos_descartados.json', 'w', encoding='utf-8') as f:
        json.dump(siguen_descartados, f, ensure_ascii=False, indent=2)
    
    from collections import Counter
    print(f"\n{'='*50}\n📊 RESUMEN DEL REPROCESAMIENTO\n{'='*50}")
    print(f"Aceptados antes:      {len(aceptados)}")
    print(f"Aceptados recuperados: {len(nuevos_aceptados)}")
    print(f"Aceptados ahora:      {len(aceptados_final)}")
    print(f"Descartados antes:    {len(descartados)}")
    print(f"Descartados ahora:    {len(siguen_descartados)}")
    print(f"\nDescartes que quedan:")
    c = Counter()
    for d in siguen_descartados:
        for m in d['motivos_descarte']:
            c[m] += 1
    for m, n in c.most_common():
        print(f"  {m}: {n}")

if __name__ == "__main__":
    main()
