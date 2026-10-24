import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import mysql.connector
import datetime
import json
import time
import re

# =====================================================
# CONFIGURAÇÃO
# =====================================================

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "betizador"

# ID da bet365 no Flashscore
BET365_ID = "16"

# Mercados disponíveis e suas URLs no Flashscore
MERCADOS = {
    "1x2":              "resultado-final/1",
    "ambos_marcam":     "ambos-marcam/1",
    "over_under":       "acima-abaixo/1",
    "double_chance":    "double-chance/1",
    "handicap_europeu": "european-handicap/1",
    "placar_exato":     "correct-score/1",
    "ht_ft":            "ht-ft/1",
}

# =====================================================
# BANCO
# =====================================================

def conectar():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

def setup(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS odds (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            jogo_id_fs       VARCHAR(20),   -- ID do Flashscore
            time_casa        VARCHAR(150),
            time_visitante   VARCHAR(150),
            data_jogo        DATETIME,
            liga             VARCHAR(150),
            casa             VARCHAR(30),   -- casa de apostas
            mercado          VARCHAR(50),   -- 1x2, over_under, etc.
            opcao            VARCHAR(50),   -- Casa / Empate / Fora / Over 2.5 / etc.
            odd              FLOAT,
            coletado_em      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq (jogo_id_fs, casa, mercado, opcao)
        )
    """)

# =====================================================
# SCRAPING
# =====================================================

def api_get(driver, endpoint):
    """Chama API do Flashscore dentro do navegador."""
    script = f"""
        const r = await fetch('https://global.ds.lsapp.eu/odds/pq_graphql', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'Referer': 'https://www.flashscore.com.br/'
            }},
            body: JSON.stringify({{ query: `{endpoint}` }})
        }});
        return await r.json();
    """
    try:
        return driver.execute_script(f"return (async () => {{ {script} }})()")
    except:
        return None

# Mapa de IDs de casas de apostas do Flashscore
BOOKMAKER_IDS = {
    "16":  "bet365",
    "574": "Betano",
    "833": "Betfair",
    "933": "Bet365 BR",
    "5":   "William Hill",
    "3":   "Unibet",
}

# Opções por mercado (ordem das colunas no Flashscore)
OPCOES_MERCADO = {
    "1x2":              ["Casa", "Empate", "Fora"],
    "ambos_marcam":     ["Sim", "Não"],
    "over_under":       ["Over", "Under"],
    "double_chance":    ["1X", "12", "X2"],
    "handicap_europeu": ["-1", "Empate", "+1"],
    "placar_exato":     [],   # dinâmico
    "ht_ft":            [],   # dinâmico
}

def parse_odds_pagina(soup, mercado):
    """
    Extrai odds usando os seletores corretos do Flashscore.
    - Linha: div.wclOddsRow
    - ID da casa: button[data-analytics-bookmaker-id]
    - Valores: span.wcl-oddsValue_3e8Cq
    """
    resultado = []
    opcoes = OPCOES_MERCADO.get(mercado, [])

    linhas = soup.select(".wclOddsRow")
    for linha in linhas:
        btn = linha.select_one("button[data-analytics-bookmaker-id]")
        if not btn:
            continue  # linha de cabeçalho

        bm_id     = btn.get("data-analytics-bookmaker-id", "")
        nome_casa = BOOKMAKER_IDS.get(bm_id, f"Casa_{bm_id}")

        valores = [el.get_text(strip=True) for el in linha.select(".wcl-oddsValue_3e8Cq")]
        if not valores:
            continue

        if opcoes:
            for i, v in enumerate(valores):
                if i < len(opcoes):
                    resultado.append({"bm_id": bm_id, "casa": nome_casa,
                                      "opcao": opcoes[i], "odd": v})
        else:
            for i, v in enumerate(valores):
                resultado.append({"bm_id": bm_id, "casa": nome_casa,
                                  "opcao": f"opcao_{i+1}", "odd": v})

    return resultado

def scrape_odds_jogo(driver, jogo_id, time_casa, time_visitante):
    """Scrapa odds de todos os mercados de um jogo."""
    todas_odds = []

    for mercado, url_sufixo in MERCADOS.items():
        url = f"https://www.flashscore.com.br/jogo/{jogo_id}/#/comparacao-de-odds/odds-de-futebol/{url_sufixo}"
        driver.get(url)

        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        odds = parse_odds_pagina(soup, mercado)

        bet365_odds = [o for o in odds if o.get("bm_id") == BET365_ID]
        usar = bet365_odds if bet365_odds else odds

        # Valida: se todas as odds do mercado são iguais, provavelmente são placeholders
        valores = [o["odd"] for o in usar if isinstance(o.get("odd"), (int, float))]
        if len(set(valores)) <= 1 and len(valores) > 1:
            print(f"    {mercado}: odds inválidas (valores repetidos) — ignorando")
            continue

        for o in usar:
            try:
                odd_val = float(str(o["odd"]).replace(",", "."))
            except:
                continue
            todas_odds.append({
                "mercado": mercado,
                "casa":    o["casa"],
                "opcao":   o["opcao"],
                "odd":     odd_val,
            })

        print(f"    {mercado}: {len(usar)} odds")

    return todas_odds

def buscar_jogo_flashscore(driver, time_casa, time_visitante):
    """Busca o ID do jogo no Flashscore pelos nomes dos times."""
    url = "https://www.flashscore.com.br/futebol/"
    driver.get(url)
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    jogos = soup.select("[class*='event__match']")

    tc = time_casa.lower()
    tv = time_visitante.lower()

    for j in jogos:
        texto = j.get_text(separator="|", strip=True).lower()
        if tc in texto and tv in texto:
            jid = j.get("id", "").replace("g_1_", "")
            if jid:
                return jid

    return None

# =====================================================
# MAIN
# =====================================================

import sys as _sys

print("="*50)
print("  COLETOR DE ODDS — FLASHSCORE")
print("="*50)

_args = _sys.argv[1:]
time_casa      = _args[0].strip() if len(_args) > 0 else input("\nTime da casa: ").strip()
time_visitante = _args[1].strip() if len(_args) > 1 else input("Time visitante: ").strip()
data_jogo_str  = _args[2].strip() if len(_args) > 2 else input("Data/hora do jogo [DD/MM/YYYY HH:MM]: ").strip()
liga           = _args[3].strip() if len(_args) > 3 else input("Liga (ex: LaLiga): ").strip()

try:
    data_jogo = datetime.datetime.strptime(data_jogo_str, "%d/%m/%Y %H:%M")
except:
    data_jogo = None

print("\nConectando ao banco...")
con = conectar()
cur = con.cursor()
setup(cur)
con.commit()

print("Abrindo navegador...")
options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors")
driver = uc.Chrome(options=options, version_main=153)
driver.get("https://www.flashscore.com.br/")
WebDriverWait(driver, 20).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)
time.sleep(5)

# Busca ID do jogo automaticamente
print(f"\nProcurando {time_casa} x {time_visitante} no Flashscore...")
jogo_id = buscar_jogo_flashscore(driver, time_casa, time_visitante)

if not jogo_id:
    print("Jogo não encontrado automaticamente.")
    print("Abra o jogo no Flashscore e cole o ID da URL (ex: fiQN1XkR)")
    jogo_id = input("ID do jogo: ").strip()

print(f"ID do jogo: {jogo_id}")
print(f"\nColetando odds de {len(MERCADOS)} mercados...")

odds = scrape_odds_jogo(driver, jogo_id, time_casa, time_visitante)
driver.quit()

print(f"\n{len(odds)} odds coletadas")

# Salva no banco
inseridos = ignorados = 0
for o in odds:
    try:
        cur.execute("""
            INSERT INTO odds
                (jogo_id_fs, time_casa, time_visitante, data_jogo, liga,
                 casa, mercado, opcao, odd)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE odd=VALUES(odd)
        """, (
            jogo_id, time_casa, time_visitante, data_jogo, liga,
            o["casa"], o["mercado"], o["opcao"], o["odd"]
        ))
        inseridos += 1
    except Exception as e:
        ignorados += 1

con.commit()
con.close()

print(f"\n{'='*50}")
print(f"  CONCLUÍDO")
print(f"  Jogo     : {time_casa} x {time_visitante}")
print(f"  ID FS    : {jogo_id}")
print(f"  Salvos   : {inseridos}")
print(f"  Ignorados: {ignorados}")
print(f"\n  Consulta:")
print(f"  SELECT mercado, opcao, odd FROM odds")
print(f"  WHERE jogo_id_fs = '{jogo_id}' AND casa LIKE '%bet365%';")
print(f"{'='*50}")