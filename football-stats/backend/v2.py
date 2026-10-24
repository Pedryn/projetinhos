import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time

players = [
    {
        "name": "Mike Maignan",
        "url": "https://www.transfermarkt.com.br/mike-maignan/leistungsdatendetails/spieler/182906/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Brice Samba",
        "url": "https://www.transfermarkt.com.br/brice-samba/leistungsdatendetails/spieler/191056/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Robin Risser",
        "url": "https://www.transfermarkt.com.br/robin-risser/leistungsdatendetails/spieler/743515/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Lucas Digne",
        "url": "https://www.transfermarkt.com.br/lucas-digne/leistungsdatendetails/spieler/126664/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Jules Kounde",
        "url": "https://www.transfermarkt.com.br/jules-kounde/leistungsdatendetails/spieler/412517/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "William Saliba",
        "url": "https://www.transfermarkt.com.br/william-saliba/leistungsdatendetails/spieler/495666/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Ibrahima Konate",
        "url": "https://www.transfermarkt.com.br/ibrahima-konate/leistungsdatendetails/spieler/357119/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Dayot Upamecano",
        "url": "https://www.transfermarkt.com.br/dayot-upamecano/leistungsdatendetails/spieler/344695/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Aurelien Tchouameni",
        "url": "https://www.transfermarkt.com.br/aurelien-tchouameni/leistungsdatendetails/spieler/413112/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Eduardo Camavinga",
        "url": "https://www.transfermarkt.com.br/eduardo-camavinga/leistungsdatendetails/spieler/640428/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Warren Zaire Emery",
        "url": "https://www.transfermarkt.com.br/warren-zaire-emery/leistungsdatendetails/spieler/810092/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Kylian Mbappe",
        "url": "https://www.transfermarkt.com.br/kylian-mbappe/leistungsdatendetails/spieler/342229/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Ousmane Dembele",
        "url": "https://www.transfermarkt.com.br/ousmane-dembele/leistungsdatendetails/spieler/288230/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Marcus Thuram",
        "url": "https://www.transfermarkt.com.br/marcus-thuram/leistungsdatendetails/spieler/318528/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Randal Kolo Muani",
        "url": "https://www.transfermarkt.com.br/randal-kolo-muani/leistungsdatendetails/spieler/487969/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Bradley Barcola",
        "url": "https://www.transfermarkt.com.br/bradley-barcola/leistungsdatendetails/spieler/708265/saison/2025/wettbewerb/0/plus/1"
    },
    {
        "name": "Kingsley Coman",
        "url": "https://www.transfermarkt.com.br/kingsley-coman/leistungsdatendetails/spieler/243714/saison/2025/wettbewerb/0/plus/1"
    }
]

options = uc.ChromeOptions()

options.add_argument("--start-maximized")

driver = uc.Chrome(
    options=options,
    version_main=148
)

all_data = []

for player in players:

    print("\n===================================")
    print(f"Buscando {player['name']}")
    print("===================================\n")

    try:

        driver.get(player["url"])

        # espera inicial
        time.sleep(5)

        # scrolla lentamente
        for i in range(6):

            driver.execute_script(
                "window.scrollBy(0, 900);"
            )

            print(f"Scroll {i+1}/6")

            time.sleep(1.5)

        # sobe um pouco
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight / 2);"
        )

        time.sleep(3)

        print(driver.title)

        soup = BeautifulSoup(
            driver.page_source,
            "html.parser"
        )

        # nova tabela do transfermarkt
        rows = soup.select(
            'div[role="row"][aria-rowindex]'
        )

        print(f"\nTOTAL ROWS: {len(rows)}")

        if len(rows) == 0:
            print("Tabela real não carregou")
            continue

        for row in rows:

            try:

                cells = row.select(
                    ".tm-grid__cell"
                )

                texts = []

                for c in cells:

                    value = c.text.strip()

                    if value == "":
                        value = "-"

                    texts.append(value)

                print("\nROW:")
                print(texts)

                if len(texts) < 10:
                    continue

                # detecta goleiro
                is_goalkeeper = (
                    "Maignan" in player["name"]
                    or "Samba" in player["name"]
                    or "Risser" in player["name"]
                )

                # =================================================
                # TABELA PRINCIPAL
                # =================================================

                data = {
                    "Jogador": player["name"],
                    "Competicao": texts[0],
                    "Partidas": texts[2],
                    "PPJ": texts[3],

                    # linha
                    "Gols": "-",
                    "Assistencias": "-",

                    # gerais
                    "Entrou": "-",
                    "Substituido": "-",
                    "Cartao Amarelo": "-",
                    "2 Amarelos": "-",
                    "Cartao Vermelho": "-",

                    # goleiro
                    "Gols Sofridos": "-",
                    "Partidas sem sofrer gol": "-",

                    "Minutos Jogados": texts[-1]
                }

                # =================================================
                # GOLEIROS
                # =================================================

                if is_goalkeeper:

                    data["Entrou"] = texts[6]
                    data["Substituido"] = texts[7]
                    data["Cartao Amarelo"] = texts[8]
                    data["2 Amarelos"] = texts[9]
                    data["Cartao Vermelho"] = texts[10]
                    data["Gols Sofridos"] = texts[11]
                    data["Partidas sem sofrer gol"] = texts[12]

                # =================================================
                # JOGADORES DE LINHA
                # =================================================

                else:

                    data["Gols"] = texts[4]
                    data["Assistencias"] = texts[5]
                    data["Entrou"] = texts[6]
                    data["Substituido"] = texts[7]
                    data["Cartao Amarelo"] = texts[8]
                    data["2 Amarelos"] = texts[9]
                    data["Cartao Vermelho"] = texts[10]

                # =================================================
                # ÚLTIMOS 5 JOGOS
                # =================================================

                ultimos_jogos = row.select("td")

                if len(ultimos_jogos) >= 15:

                    data["Rodada"] = ultimos_jogos[0].text.strip()
                    data["Data"] = ultimos_jogos[1].text.strip()
                    data["Casa/Fora"] = ultimos_jogos[2].text.strip()
                    data["Time Casa"] = ultimos_jogos[3].text.strip()
                    data["Resultado"] = ultimos_jogos[4].text.strip()
                    data["Time Visitante"] = ultimos_jogos[5].text.strip()
                    data["Posicao"] = ultimos_jogos[6].text.strip()

                print("\nDADOS:")
                print(data)

                all_data.append(data)

            except Exception as e:
                print("\nERRO NA ROW:")
                print(e)

    except Exception as e:

        print("\nERRO GERAL:")
        print(e)

df = pd.DataFrame(all_data)

df.to_excel(
    "football_stats.xlsx",
    index=False
)

print("\n========================")
print("PLANILHA SALVA")
print("========================")

driver.quit()