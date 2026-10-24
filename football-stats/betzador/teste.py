import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time

print("Abrindo navegador...")
options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors")
driver = uc.Chrome(options=options, version_main=150)

# Jogo de teste — The Strongest x Oriente Petrolero
# Troque pelo ID de um jogo de amanhã quando testar
JOGO_ID = "lvhNV8sC"

# =====================================================
# 1) Abre página de comparação de odds
# =====================================================
url_odds = f"https://www.flashscore.com.br/jogo/{JOGO_ID}/#/comparacao-de-odds/odds-de-futebol/resultado-final/1"
print(f"\nAbrindo: {url_odds}")
driver.get(url_odds)

WebDriverWait(driver, 20).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)
time.sleep(5)

soup = BeautifulSoup(driver.page_source, "html.parser")

# =====================================================
# 2) Tenta capturar odds de resultado final (1X2)
# =====================================================
print("\n--- ODDS RESULTADO FINAL (1X2) ---")

# Procura tabela de odds
odds_rows = soup.select("[class*='oddsRow'], [class*='odds__row'], [class*='ui-table__row']")
print(f"Linhas de odds encontradas: {len(odds_rows)}")

for row in odds_rows[:10]:
    cells = row.select("[class*='oddsCell'], [class*='odds__odd'], span")
    valores = [c.get_text(strip=True) for c in cells if c.get_text(strip=True)]
    if valores:
        print(f"  {valores}")

# =====================================================
# 3) Salva HTML para análise
# =====================================================
with open("odds_debug.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
print("\nHTML salvo em odds_debug.html")

# =====================================================
# 4) Lista abas de mercados disponíveis
# =====================================================
print("\n--- MERCADOS DISPONÍVEIS ---")
mercados = soup.select("[class*='filterOver'], [class*='tabs__tab'], [class*='subNav']")
for m in mercados[:15]:
    txt = m.get_text(strip=True)
    if txt:
        print(f"  {txt}")

input("\nPressione Enter para fechar...")
driver.quit()