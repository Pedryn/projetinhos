import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
import json
import time

BASE = "https://api.sofascore.com/api/v1"

def api_get(driver, endpoint):
    script = f"""
        const r = await fetch('{BASE}{endpoint}', {{
            headers: {{
                'Accept': 'application/json',
                'Referer': 'https://www.sofascore.com/'
            }}
        }});
        return await r.json();
    """
    try:
        return driver.execute_script(f"return (async () => {{ {script} }})()")
    except:
        return None

print("Abrindo navegador...")
options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors")
driver = uc.Chrome(options=options, version_main=153)
driver.get("https://www.sofascore.com/")
WebDriverWait(driver, 20).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)
time.sleep(5)

nome = input("\nNome do campeonato: ").strip()
print(f"\nBuscando: {nome}")

# Testa vários endpoints para achar o certo
endpoints = [
    f"/search/query/{nome}",
    f"/search/{nome}",
    f"/unique-tournament/search/{nome}",
]

data = None
for ep in endpoints:
    print(f"  Tentando: {ep}")
    data = api_get(driver, ep)
    if data:
        print(f"  Chaves retornadas: {list(data.keys())}")
        # Mostra primeiros 300 chars
        print(f"  Preview: {json.dumps(data, ensure_ascii=False)[:300]}")
        break

# Independente do resultado, testa buscar por ID direto
print("\n\nTestando busca de times por ID de torneio conhecido:")
print("  LaLiga = 8, Brasileirao = 325, Premier League = 17")
tid = int(input("Cole um ID para testar: ").strip())

data2 = api_get(driver, f"/unique-tournament/{tid}/seasons")
print(f"\nTemporadas: {json.dumps(data2, ensure_ascii=False)[:400] if data2 else 'erro'}")

if data2 and "seasons" in data2:
    sid = data2["seasons"][0]["id"]
    data3 = api_get(driver, f"/unique-tournament/{tid}/season/{sid}/teams")
    print(f"\nTimes: {json.dumps(data3, ensure_ascii=False)[:500] if data3 else 'erro'}")

driver.quit()