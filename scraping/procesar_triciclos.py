#!/usr/bin/env python3
"""
Procesa los triciclos de Revolico:
1. Lee los JSON de búsqueda (revolico_state_p1.json, p2.json)
2. Filtra solo triciclos
3. Visita cada detalle para extraer description
4. Aplica los 7 filtros duros
5. Genera triciclos_aceptados.json y triciclos_descartados.json
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import sys

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}
BASE_URL = "https://www.revolico.com"

MARCAS_CONOCIDAS = [
    "VEDCA", "JINPENG", "JIMPENG", "JIMPEG", "MISHOZUKI", "TOPMAQ", "STAR",
    "MVP", "KVITOVA", "ONEHOT", "ONEHOT", "OIM", "MAF", "CAIMAN", "TRAKTION",
    "YAMAKI", "PORTO BELLO", "PORTOBELLO", "JINGHAN", "NAVILAM",
    "LEISURE", "JMD", "VIENTO RAPIDO", "UNIZUKI", "BRYDERK", "PANTHER",
    "JINPEN", "LLC", "POWER RED", "MOTOMANIA", "RAIC", "DAYUN", "TOP MAQ"
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

def descargar_detalle(permalink):
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
                return val
    except Exception as e:
        print(f"    ⚠️  Error descargando {permalink}: {e}")
    return None

def extraer_autonomia(texto):
    if not texto: return None
    patrones = [
        r'[Aa]lcance[:\s]+(\d+(?:[.,]\d+)?)\s*km',
        r'[Aa]utonom[íi]a[:\s]+(?:de\s+|aprox\.?\s*)?(\d+(?:[.,]\d+)?)\s*km',
        r'(\d+(?:[.,]\d+)?)\s*km\s+de\s+[Aa]utonom',
        r'recorre\s+(\d+(?:[.,]\d+)?)\s*km',
        r'(\d+(?:[.,]\d+)?)\s*km\s+sin\s+carga',
        r'(\d+(?:[.,]\d+)?)\s*km\s+con\s+carga',
    ]
    for p in patrones:
        m = re.search(p, texto)
        if m:
            try:
                v = float(m.group(1).replace(',', '.'))
                if v > 0: return v
            except ValueError:
                pass
    return None

def extraer_marca(titulo, descripcion):
    texto = f"{titulo} {descripcion or ''}".upper()
    # Ordenar por longitud descendente para que "PORTO BELLO" gane a "PORTO"
    for marca in sorted(MARCAS_CONOCIDAS, key=len, reverse=True):
        if marca in texto:
            return marca.title()
    m = re.search(r'[Mm]arca\s+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ0-9]{2,20})', f"{titulo} {descripcion or ''}")
    if m: return m.group(1)
    return None

def extraer_tipo(texto):
    t = texto.lower()
    if 'híbrido' in t or 'hibrido' in t or 'hybrid' in t:
        return "híbrido"
    if 'eléctrico' in t or 'electrico' in t or 'electric' in t or 'batería' in t or 'litio' in t:
        return "eléctrico"
    if 'gasolina' in t or 'combustible' in t or 'nafta' in t:
        return "combustible"
    return None

def extraer_voltaje(texto):
    if not texto: return None
    for m in re.finditer(r'(\d{2,3})\s*[Vv]\b', texto):
        v = int(m.group(1))
        if 12 <= v <= 120:
            return f"{v}V"
    return None

def extraer_garantia(texto):
    if not texto: return None
    patrones = [
        r'[Gg]arant[íi]a[:\s]+(\d+)\s*mes',
        r'(\d+)\s*meses?\s+de\s+[Gg]arant',
    ]
    for p in patrones:
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

def procesar_anuncio(ad_busqueda, provincias, municipios):
    """Devuelve (aceptado | None, descartado | None)."""
    permalink = ad_busqueda['permalink']
    ad_detalle = descargar_detalle(permalink)
    if not ad_detalle:
        return None, {
            "enlace": BASE_URL + permalink,
            "titulo_crudo": ad_busqueda.get('title'),
            "motivos_descarte": ["DESCARGA_FALLIDA"],
            "datos_crudos": {"precio_publicado": None, "tipo_triciclo": None,
                             "marca_detectada": None, "ubicacion": None,
                             "fecha_publicacion": None, "autonomia_km": None,
                             "moneda_original": None, "municipio": None,
                             "tipo_uso": None, "garantia_meses": None,
                             "panel_incluido": None, "voltaje_bateria": None}
        }

    titulo = ad_detalle.get('title', '')
    descripcion = ad_detalle.get('description') or ''
    texto_completo = f"{titulo}\n{descripcion}"

    # Campos base
    precio = ad_detalle.get('price')
    moneda = ad_detalle.get('currency')
    provincia_ref = ad_detalle.get('province', {}).get('__ref', '')
    municipio_ref = ad_detalle.get('municipality', {}).get('__ref', '')
    provincia = provincias.get(provincia_ref.split(':', 1)[1]) if provincia_ref else None
    municipio = municipios.get(municipio_ref.split(':', 1)[1]) if municipio_ref else None

    # Fecha (usamos updatedOnByUser)
    fecha_iso = ad_detalle.get('updatedOnByUser', '')
    fecha = fecha_iso[:10] if fecha_iso else None

    # Campos inferidos
    marca = extraer_marca(titulo, descripcion)
    tipo = extraer_tipo(texto_completo)
    autonomia = extraer_autonomia(texto_completo)
    voltaje = extraer_voltaje(texto_completo)
    garantia = extraer_garantia(texto_completo)
    panel = extraer_panel(texto_completo)
    uso = extraer_uso(texto_completo)

    # Datos crudos
    datos = {
        "precio_publicado": precio,
        "tipo_triciclo": tipo,
        "marca_detectada": marca,
        "ubicacion": provincia,
        "fecha_publicacion": fecha,
        "autonomia_km": autonomia,
        "moneda_original": moneda,
        "municipio": municipio,
        "tipo_uso": uso,
        "garantia_meses": garantia,
        "panel_incluido": panel,
        "voltaje_bateria": voltaje,
    }

    # Aplicar filtros
    motivos = []
    if not precio or not isinstance(precio, (int, float)) or precio <= 0:
        motivos.append("PRECIO_INVALIDO")
    if tipo not in ("eléctrico", "combustible", "híbrido"):
        motivos.append("TIPO_NO_DETERMINADO")
    if not marca or marca.lower() in ("desconocida", ""):
        motivos.append("MARCA_NO_DETECTADA")
    if not provincia or provincia.strip() == "":
        motivos.append("UBICACION_VACIA")
    if not fecha or not fecha.startswith("2026-"):
        motivos.append("FECHA_FUERA_DE_2026")
    if not autonomia or autonomia <= 0:
        motivos.append("AUTONOMIA_NO_INDICADA")
    if not moneda or moneda not in ("USD", "CUP", "MN", "EUR", "MLC"):
        motivos.append("MONEDA_NO_DETECTADA")

    if motivos:
        return None, {
            "enlace": BASE_URL + permalink,
            "titulo_crudo": titulo,
            "motivos_descarte": motivos,
            "datos_crudos": datos,
        }
    else:
        aceptado = {**datos, "enlace": BASE_URL + permalink}
        return aceptado, None

def main():
    print("📂 Leyendo JSON de búsqueda...")
    with open('scraping/data/revolico_state_p1.json', encoding='utf-8') as f:
        d1 = json.load(f)
    with open('scraping/data/revolico_state_p2.json', encoding='utf-8') as f:
        d2 = json.load(f)

    ads = extraer_ads(d1) + extraer_ads(d2)
    provincias, municipios = construir_lookups([d1, d2])
    print(f"  → {len(ads)} anuncios totales, {len(provincias)} provincias, {len(municipios)} municipios")

    # Filtrar solo triciclos + deduplicar por id
    vistos = set()
    triciclos = []
    for a in ads:
        if a['id'] in vistos:
            continue
        if 'triciclo' in a['title'].lower() or 'triciclo' in a.get('permalink', '').lower():
            triciclos.append(a)
            vistos.add(a['id'])
    print(f"  → {len(triciclos)} triciclos únicos para procesar\n")

    aceptados, descartados = [], []
    for i, ad in enumerate(triciclos, 1):
        print(f"[{i}/{len(triciclos)}] {ad['title'][:70]}")
        ac, de = procesar_anuncio(ad, provincias, municipios)
        if ac:
            aceptados.append(ac)
            print(f"    ✅ ACEPTADO (autonomía: {ac['autonomia_km']} km, marca: {ac['marca_detectada']})")
        else:
            descartados.append(de)
            print(f"    ❌ Descartado: {', '.join(de['motivos_descarte'])}")
        time.sleep(2)

    print(f"\n💾 Escribiendo archivos...")
    with open('data/raw/triciclos_aceptados.json', 'w', encoding='utf-8') as f:
        json.dump(aceptados, f, ensure_ascii=False, indent=2)
    with open('scraping/data/triciclos_descartados.json', 'w', encoding='utf-8') as f:
        json.dump(descartados, f, ensure_ascii=False, indent=2)

    # Reporte
    from collections import Counter
    print(f"\n{'='*50}")
    print(f"📊 RESUMEN")
    print(f"{'='*50}")
    print(f"Triciclos revisados:  {len(triciclos)}")
    print(f"Aceptados:            {len(aceptados)}")
    print(f"Descartados:          {len(descartados)}")
    print(f"\nDescartes por criterio:")
    contador = Counter()
    for d in descartados:
        for m in d['motivos_descarte']:
            contador[m] += 1
    for motivo, n in contador.most_common():
        print(f"  {motivo}: {n}")
    print(f"\n✅ Archivos generados:")
    print(f"   - triciclos_aceptados.json")
    print(f"   - triciclos_descartados.json")

if __name__ == "__main__":
    main()
