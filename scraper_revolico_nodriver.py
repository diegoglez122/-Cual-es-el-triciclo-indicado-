# scraper_revolico_nodriver.py — v2 con perfil persistente y detección robusta
import asyncio
import os
import json
import nodriver as uc
from bs4 import BeautifulSoup

PAG_INI = int(os.environ.get('PAG_INI', 1))
PAG_FIN = int(os.environ.get('PAG_FIN', 15))
PROFILE_DIR = os.environ.get('PROFILE_DIR', './chrome_profile_revolico')
SLEEP_ENTRE_PAGS = float(os.environ.get('SLEEP_PAGS', 10))
MAX_INTENTOS = 6  # x 5s = 30s max por página

print(f"📄 Rango: {PAG_INI} → {PAG_FIN} | perfil: {PROFILE_DIR} | sleep: {SLEEP_ENTRE_PAGS}s")

BASE = "https://www.revolico.com/search?category=vehiculos&subcategory=vehiculos-motos-electricas-y-triciclos"

async def obtener_datos(browser, pagina):
    url = f"{BASE}&page={pagina}"
    print(f"🌐 p{pagina}: {url}")
    try:
        page = await browser.get(url)
        html = ""
        for intento in range(1, MAX_INTENTOS + 1):
            await page.sleep(5)
            html = await page.get_content()
            if "__NEXT_DATA__" in html and len(html) > 100_000:
                print(f"  ✅ HTML listo en intento {intento} ({len(html)} chars)")
                break
            print(f"  ⏳ intento {intento}: {len(html)} chars sin __NEXT_DATA__")
        else:
            print(f"  ❌ challenge no resuelto tras {MAX_INTENTOS} intentos")

        with open(f"revolico_raw_p{pagina}.html", "w", encoding="utf-8") as f:
            f.write(html)

        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script:
            print("  ❌ sin __NEXT_DATA__")
            return None

        data = json.loads(script.string)
        with open(f"revolico_state_p{pagina}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 revolico_state_p{pagina}.json")
        return data

    except Exception as e:
        print(f"  ❌ error p{pagina}: {e}")
        return None

async def main():
    browser = await uc.start(
        browser_executable_path="/usr/bin/google-chrome",
        sandbox=False,
        headless=False,
        user_data_dir=PROFILE_DIR,
    )
    for p in range(PAG_INI, PAG_FIN + 1):
        await obtener_datos(browser, p)
        if p < PAG_FIN:
            await asyncio.sleep(SLEEP_ENTRE_PAGS)
    browser.stop()

if __name__ == "__main__":
    uc.loop().run_until_complete(main())
