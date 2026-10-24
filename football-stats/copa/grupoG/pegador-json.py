import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import json
import time

# =====================================================
# CONFIGURAÇÃO
# =====================================================

url_plantel = input("Cole a URL do plantel no Transfermarkt: ").strip()

nome_sugerido = url_plantel.rstrip("/").split("/")[3].replace("-", "_")
nome_arquivo  = input(f"Nome do arquivo JSON [{nome_sugerido}]: ").strip()
if not nome_arquivo:
    nome_arquivo = nome_sugerido
if not nome_arquivo.endswith(".json"):
    nome_arquivo += ".json"

temporada = input("Temporada [2025]: ").strip() or "2025"

# =====================================================
# SCRAPING
# =====================================================

print(f"\nAbrindo: {url_plantel}")

options = uc.ChromeOptions()
options.add_argument("--start-maximized")
# user-agent real para evitar bloqueio
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
driver = uc.Chrome(options=options, version_main=148)

# O TM exige o header Referer/Accept-Language — injeta via CDP
driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
    "headers": {
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.transfermarkt.com.br/"
    }
})

driver.get(url_plantel)
time.sleep(6)

# scroll para garantir carregamento lazy
for _ in range(5):
    driver.execute_script("window.scrollBy(0, 800);")
    time.sleep(1.2)

driver.execute_script("window.scrollTo(0, 0);")
time.sleep(2)

soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# =====================================================
# DEBUG — mostra o que foi encontrado
# =====================================================

tabela = soup.find("table", {"class": "items"})

if not tabela:
    # tenta achar qualquer tabela na página
    todas = soup.find_all("table")
    print(f"\nTabela 'items' não encontrada. Total de tabelas na página: {len(todas)}")
    for i, t in enumerate(todas[:5]):
        print(f"  tabela[{i}] classes: {t.get('class')} | linhas: {len(t.find_all('tr'))}")

    # salva HTML para inspeção
    with open("debug_plantel.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source if hasattr(driver, 'page_source') else soup.prettify())
    print("\nHTML salvo em debug_plantel.html para inspeção.")
    exit()

linhas = tabela.select("tbody tr")
print(f"\nTabela encontrada — {len(linhas)} linhas")

# =====================================================
# EXTRAIR JOGADORES
# =====================================================

goleiros = []
linha    = []

for tr in linhas:

    # posição — tenta duas formas que o TM usa
    td_pos = tr.find("td", {"class": lambda c: c and "rueckennummer" in c})
    if not td_pos:
        continue

    posicao = td_pos.get("title", "").strip()

    # nome e link
    link_tag = tr.select_one("table.inline-table td.hauptlink a")
    if not link_tag:
        continue

    nome = link_tag.get_text(strip=True)
    href = link_tag.get("href", "")

    # /nome-slug/profil/spieler/ID
    partes = href.strip("/").split("/")
    if len(partes) < 4 or "spieler" not in partes:
        print(f"  [SKIP] href inesperado: {href}")
        continue

    idx  = partes.index("spieler")
    slug = partes[0]
    pid  = partes[idx + 1]

    url = (
        f"https://www.transfermarkt.com.br/{slug}"
        f"/leistungsdatendetails/spieler/{pid}"
        f"/saison/{temporada}/wettbewerb/0/plus/1"
    )

    jogador = {"name": nome, "url": url}

    if posicao == "Goleiro":
        goleiros.append(jogador)
        print(f"  [GOL] {nome}")
    else:
        linha.append(jogador)
        print(f"  [LIN] {nome}  ({posicao})")

# =====================================================
# SALVAR JSON
# =====================================================

dados = {"goleiros": goleiros, "linha": linha}

with open(nome_arquivo, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)

print(f"\n{'='*45}")
print(f"JSON salvo: {nome_arquivo}")
print(f"  Goleiros: {len(goleiros)}")
print(f"  Jogadores de linha: {len(linha)}")
print(f"{'='*45}")