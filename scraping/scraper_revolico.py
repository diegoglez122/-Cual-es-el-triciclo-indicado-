# scraper_revolico.py
import requests

# ─── Rango de páginas configurable por entorno ───
import os
PAG_INI = int(os.environ.get('PAG_INI', 1))
PAG_FIN = int(os.environ.get('PAG_FIN', 15))
print(f"📄 Rango de páginas: {PAG_INI} → {PAG_FIN}")

from bs4 import BeautifulSoup
import json
import time
import sys

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}

BASE = "https://www.revolico.com/search?category=vehiculos&subcategory=vehiculos-motos-electricas-y-triciclos"

def obtener_datos(pagina):
    url = f"{BASE}&page={pagina}"
    print(f"🌐 Descargando página {pagina}: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        print(f"  → Status: {r.status_code}, Tamaño: {len(r.text)} caracteres")

        with open(f"scraping/data/revolico_raw_p{pagina}.html", "w", encoding="utf-8") as f:
            f.write(r.text)

        soup = BeautifulSoup(r.text, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")

        if not script:
            print("  ❌ No se encontró el bloque __NEXT_DATA__ (posible CAPTCHA o bloqueo)")
            return None

        data = json.loads(script.string)
        print("  ✅ JSON interno extraído correctamente")

        with open(f"scraping/data/revolico_state_p{pagina}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  💾 Guardado en scraping/data/revolico_state_p{pagina}.json")
        return data

    except Exception as e:
        print(f"  ❌ Error en página {pagina}: {e}")
        return None

if __name__ == "__main__":
    for p in range(PAG_INI, PAG_FIN + 1):
        obtener_datos(p)
        time.sleep(2)
    print("\n✅ Proceso terminado. Revisa los archivos generados.")
