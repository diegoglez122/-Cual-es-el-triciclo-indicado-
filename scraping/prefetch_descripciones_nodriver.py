# prefetch_descripciones_nodriver.py
# Baja descripciones de anuncios con nodriver y actualiza cache_descripciones.json
import asyncio
import glob
import json
import os
import time
import nodriver as uc
from bs4 import BeautifulSoup

BASE_URL = "https://www.revolico.com"
CACHE_FILE = "scraping/data/cache_descripciones.json"
PROFILE_DIR = "./chrome_profile_revolico"
GUARDAR_CADA = 10
SLEEP_ENTRE = 6

def cargar_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def extraer_ads(d):
    apollo = d.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})
    for k, v in apollo.items():
        if k.startswith('AdType:') and isinstance(v, dict):
            yield v

def recolectar_permalinks():
    permalinks = set()
    for path in sorted(glob.glob('scraping/data/revolico_state_p*.json')):
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
        for ad in extraer_ads(d):
            title = (ad.get('title') or '').lower()
            permalink = ad.get('permalink') or ''
            if 'triciclo' in title or 'triciclo' in permalink.lower():
                permalinks.add(permalink)
    return sorted(permalinks)

async def obtener_detalle(browser, permalink):
    url = BASE_URL + permalink
    try:
        page = await browser.get(url)
        for intento in range(1, 5):
            await page.sleep(2)
            html = await page.get_content()
            if "__NEXT_DATA__" in html and len(html) > 50_000:
                break
        else:
            return None

        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script:
            return None
        data = json.loads(script.string)
        apollo = data['props']['pageProps'].get('__APOLLO_STATE__', {})
        for key, val in apollo.items():
            if key.startswith('AdType:') and isinstance(val, dict) and 'description' in val:
                return {"title": val.get('title', ''), "description": val.get('description') or ''}
    except Exception as e:
        print(f"   WARN {permalink}: {e}")
    return None

async def main():
    cache = cargar_cache()
    print(f"CACHE actual: {len(cache)} entradas")

    todos = recolectar_permalinks()
    print(f"PERMALINKS unicos de triciclos: {len(todos)}")

    faltan = [p for p in todos if p not in cache]
    print(f"FALTAN por descargar: {len(faltan)}")

    if not faltan:
        print("Nada que hacer.")
        return

    browser = await uc.start(
        browser_executable_path="/usr/bin/google-chrome",
        sandbox=False,
        headless=False,
        user_data_dir=PROFILE_DIR,
    )

    descargadas = 0
    fallidas = 0
    t0 = time.time()

    try:
        for i, permalink in enumerate(faltan, 1):
            detalle = await obtener_detalle(browser, permalink)
            if detalle:
                cache[permalink] = detalle
                descargadas += 1
                print(f"[{i}/{len(faltan)}] OK {detalle['title'][:60]}")
            else:
                fallidas += 1
                print(f"[{i}/{len(faltan)}] FAIL {permalink}")

            if descargadas and descargadas % GUARDAR_CADA == 0:
                guardar_cache(cache)
                print(f"   SAVE cache ({len(cache)} entradas)")

            await asyncio.sleep(SLEEP_ENTRE)
    except KeyboardInterrupt:
        print("\nInterrumpido. Guardando...")
    finally:
        guardar_cache(cache)
        print(f"\nCACHE final: {len(cache)} entradas")
        print(f"   descargadas nuevas: {descargadas}")
        print(f"   fallidas:           {fallidas}")
        print(f"   tiempo: {time.time()-t0:.1f}s")
        browser.stop()

if __name__ == "__main__":
    uc.loop().run_until_complete(main())
