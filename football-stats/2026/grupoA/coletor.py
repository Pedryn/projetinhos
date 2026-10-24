import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import time
import json

# =====================================================
# JOGADORES
# =====================================================

# =====================================================
# Seleção do arquivo JSON de jogadores
# Liste todos os .json da pasta e escolha pelo número
# =====================================================
import glob, os

jsons = sorted(glob.glob("*.json"))

if not jsons:
    raise FileNotFoundError("Nenhum arquivo .json encontrado na pasta atual.")

print("\n=== Arquivos JSON disponíveis ===")
for i, f in enumerate(jsons, 1):
    print(f"  [{i}] {f}")

while True:
    try:
        escolha = int(input("\nEscolha o número do arquivo: "))
        if 1 <= escolha <= len(jsons):
            arquivo = jsons[escolha - 1]
            break
        print(f"  Digite um número entre 1 e {len(jsons)}.")
    except ValueError:
        print("  Digite apenas o número.")

print(f"\nCarregando: {arquivo}")
with open(arquivo, "r", encoding="utf-8") as f:
    _data = json.load(f)

goleiros = _data["goleiros"]
linha    = _data["linha"]

# =====================================================
# HELPERS
# =====================================================

def ct(cell):
    """Extrai texto limpo de qualquer célula."""
    t = cell.get_text(separator=" ", strip=True)
    return t if t else "-"

def scrape(driver, player):
    driver.get(player["url"])
    time.sleep(5)
    for _ in range(6):
        driver.execute_script("window.scrollBy(0, 900);")
        time.sleep(1.5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(3)
    return BeautifulSoup(driver.page_source, "html.parser")

def get_times(row):
    """
    Time Casa e Time Visitante usam div.grid__cell (SEM tm-grid__cell).
    Pegamos pelo atributo title da tag <a> dentro desses divs.
    """
    divs = row.select("div.grid__cell")
    times = []
    for d in divs:
        a = d.find("a", title=True)
        if a:
            times.append(a["title"])
    # sempre retorna 2 valores
    casa      = times[0] if len(times) > 0 else "-"
    visitante = times[1] if len(times) > 1 else "-"
    return casa, visitante

def is_jogo(row):
    """Linha de jogo individual: tem placar tipo 1:2 ou -:- no resultado."""
    res = row.select_one("a.tm-grid__cell[href*='spielbericht'], a.tm-grid__cell.tm-grid__cell--win, a.tm-grid__cell.tm-grid__cell--loss, a.tm-grid__cell.tm-grid__cell--draw, a.tm-grid__cell.tm-grid__cell--no-report")
    return res is not None

# =====================================================
# PARSERS — RESUMO
# Índices confirmados pelo HTML (div[role='row'] sem placar):
#   [0] Competição  [1] Jogos Relacionados  [2] Partidas Jogadas (link)  [3] PPJ
#
# GOLEIRO:
#   [4] Gols  [5] Gols Contra  [6] Entrou  [7] Saiu
#   [8] Amarelo  [9] 2 Amarelos  [10] Vermelho
#   [11] Gols Sofridos  [12] Sem Gols Sofridos  [13] Minutos
#
# LINHA:
#   [4] Gols  [5] Assistências  [6] Gols Contra
#   [7] Amarelo  [8] 2 Amarelos  [9] Vermelho
#   [10] Entrou  [11] Saiu  [12] Gols Pênalti  [13] Min/Gol  [14] Minutos
# =====================================================

def parse_resumo_gol(row, name):
    if is_jogo(row):
        return None
    t = [ct(c) for c in row.select(".tm-grid__cell")]
    if len(t) < 10:
        return None
    return {
        "Jogador":             name,
        "Competicao":          t[0],
        "Jogos Relacionados":  t[1],
        "Partidas Jogadas":    t[2],
        "PPJ":                 t[3],
        "Gols":                t[4]  if len(t) > 4  else "-",
        "Gols Contra":         t[5]  if len(t) > 5  else "-",
        "Entrou":              t[6]  if len(t) > 6  else "-",
        "Saiu":                t[7]  if len(t) > 7  else "-",
        "Amarelo":             t[8]  if len(t) > 8  else "-",
        "Expulso 2 Amarelos":  t[9]  if len(t) > 9  else "-",
        "Vermelho":            t[10] if len(t) > 10 else "-",
        "Gols Sofridos":       t[11] if len(t) > 11 else "-",
        "Sem Gols Sofridos":   t[12] if len(t) > 12 else "-",
        "Minutos":             t[13] if len(t) > 13 else t[-1],
    }

def parse_resumo_lin(row, name):
    if is_jogo(row):
        return None
    t = [ct(c) for c in row.select(".tm-grid__cell")]
    if len(t) < 10:
        return None
    return {
        "Jogador":             name,
        "Competicao":          t[0],
        "Jogos Relacionados":  t[1],
        "Partidas Jogadas":    t[2],
        "PPJ":                 t[3],
        "Gols":                t[4]  if len(t) > 4  else "-",
        "Assistencias":        t[5]  if len(t) > 5  else "-",
        "Gols Contra":         t[6]  if len(t) > 6  else "-",
        "Amarelo":             t[7]  if len(t) > 7  else "-",
        "Expulso 2 Amarelos":  t[8]  if len(t) > 8  else "-",
        "Vermelho":            t[9]  if len(t) > 9  else "-",
        "Entrou":              t[10] if len(t) > 10 else "-",
        "Saiu":                t[11] if len(t) > 11 else "-",
        "Gols Penalti":        t[12] if len(t) > 12 else "-",
        "Min por Gol":         t[13] if len(t) > 13 else "-",
        "Minutos":             t[14] if len(t) > 14 else t[-1],
    }

# =====================================================
# PARSERS — JOGOS INDIVIDUAIS
# Índices confirmados pelo HTML (linhas COM placar):
#   tm-grid__cell: [0] Rodada  [1] Data  [2] Cidade  [3] Resultado
#                  [4] Posição  [5] Gols  [6] Assist  [7] Gols Contra
#                  [8] Amarelo  [9] 2 Amarelos  [10] Vermelho
#                  [11] Entrou  [12] Saiu  [13] Minutos
#   grid__cell (sem tm-): Time Casa e Time Visitante (via title)
# =====================================================

def parse_jogo(row, name):
    if not is_jogo(row):
        return None
    t = [ct(c) for c in row.select(".tm-grid__cell")]
    if len(t) < 5:
        return None

    # resultado fica numa <a> especial — pega diretamente
    res_tag = row.select_one("a.tm-grid__cell")
    resultado = ct(res_tag) if res_tag else t[3]

    casa, visitante = get_times(row)

    return {
        "Jogador":            name,
        "Rodada":             t[0],
        "Data":               t[1],
        "Cidade":             t[2],
        "Time Casa":          casa,
        "Time Visitante":     visitante,
        "Resultado":          resultado,
        "Posicao":            t[4]  if len(t) > 4  else "-",
        "Gols":               t[5]  if len(t) > 5  else "-",
        "Assistencias":       t[6]  if len(t) > 6  else "-",
        "Gols Contra":        t[7]  if len(t) > 7  else "-",
        "Amarelo":            t[8]  if len(t) > 8  else "-",
        "Expulso 2 Amarelos": t[9]  if len(t) > 9  else "-",
        "Vermelho":           t[10] if len(t) > 10 else "-",
        "Entrou":             t[11] if len(t) > 11 else "-",
        "Saiu":               t[12] if len(t) > 12 else "-",
        "Minutos":            t[13] if len(t) > 13 else t[-1],
    }

# =====================================================
# MAIN LOOP
# =====================================================

options = uc.ChromeOptions()
options.add_argument("--start-maximized")
driver = uc.Chrome(options=options, version_main=148)

resumo_gol, jogos_gol = [], []
resumo_lin, jogos_lin = [], []

for player in goleiros:
    print(f"\n{'='*45}\n  [GOL] {player['name']}\n{'='*45}")
    try:
        soup = scrape(driver, player)
        for row in soup.select('div[role="row"][aria-rowindex]'):
            r = parse_resumo_gol(row, player["name"])
            j = parse_jogo(row, player["name"])
            if r: resumo_gol.append(r)
            if j: jogos_gol.append(j)
        rn = sum(1 for x in resumo_gol if x["Jogador"] == player["name"])
        jn = sum(1 for x in jogos_gol  if x["Jogador"] == player["name"])
        print(f"  resumo: {rn} | jogos: {jn}")
    except Exception as e:
        print(f"  ERRO: {e}")

for player in linha:
    print(f"\n{'='*45}\n  [LIN] {player['name']}\n{'='*45}")
    try:
        soup = scrape(driver, player)
        for row in soup.select('div[role="row"][aria-rowindex]'):
            r = parse_resumo_lin(row, player["name"])
            j = parse_jogo(row, player["name"])
            if r: resumo_lin.append(r)
            if j: jogos_lin.append(j)
        rn = sum(1 for x in resumo_lin if x["Jogador"] == player["name"])
        jn = sum(1 for x in jogos_lin  if x["Jogador"] == player["name"])
        print(f"  resumo: {rn} | jogos: {jn}")
    except Exception as e:
        print(f"  ERRO: {e}")

driver.quit()

# =====================================================
# DATAFRAMES
# =====================================================

COLS_RG = ["Jogador","Competicao","Jogos Relacionados","Partidas Jogadas","PPJ",
           "Gols","Gols Contra","Entrou","Saiu",
           "Amarelo","Expulso 2 Amarelos","Vermelho",
           "Gols Sofridos","Sem Gols Sofridos","Minutos"]

COLS_JG = ["Jogador","Rodada","Data","Cidade","Time Casa","Time Visitante","Resultado",
           "Posicao","Gols","Assistencias","Gols Contra",
           "Amarelo","Expulso 2 Amarelos","Vermelho",
           "Entrou","Saiu","Minutos"]

COLS_RL = ["Jogador","Competicao","Jogos Relacionados","Partidas Jogadas","PPJ",
           "Gols","Assistencias","Gols Contra",
           "Amarelo","Expulso 2 Amarelos","Vermelho",
           "Entrou","Saiu","Gols Penalti","Min por Gol","Minutos"]

COLS_JL = ["Jogador","Rodada","Data","Cidade","Time Casa","Time Visitante","Resultado",
           "Posicao","Gols","Assistencias","Gols Contra",
           "Amarelo","Expulso 2 Amarelos","Vermelho",
           "Entrou","Saiu","Minutos"]

def make_df(rows, cols):
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = "-"
    return df[cols].reset_index(drop=True)

df_rg = make_df(resumo_gol, COLS_RG)
df_jg = make_df(jogos_gol,  COLS_JG)
df_rl = make_df(resumo_lin, COLS_RL)
df_jl = make_df(jogos_lin,  COLS_JL)

for df in [df_rg, df_rl]:
    df.drop_duplicates(subset=["Jogador","Competicao"], inplace=True)
    df.reset_index(drop=True, inplace=True)

print(f"\nResumo Gol:{len(df_rg)} | Jogos Gol:{len(df_jg)}")
print(f"Resumo Lin:{len(df_rl)} | Jogos Lin:{len(df_jl)}")

# =====================================================
# EXCEL — helpers
# =====================================================

NAVY="1B3251"; WHITE="FFFFFF"; LIGHT_BG="F0F4FA"; LIGHT_GOL="FFF8E7"

def hdr_font(color=WHITE): return Font(name="Arial",bold=True,color=color,size=8)
def body_font(bold=False):  return Font(name="Arial",bold=bold,color="1A1A1A",size=9)
def fill(h): return PatternFill("solid",fgColor=h)
def center(wrap=False): return Alignment(horizontal="center",vertical="center",wrap_text=wrap)
def left(): return Alignment(horizontal="left",vertical="center")

thin  = Side(style="thin",  color="C0CCE0")
thick = Side(style="medium",color=NAVY)
b_all = Border(left=thin,right=thin,top=thin,bottom=thin)
b_hdr = Border(left=thin,right=thin,top=thin,bottom=thick)

def write_header(ws, grupos, headers, offset):
    for grp in grupos:
        cs,ce = grp["cols"][0]+offset, grp["cols"][-1]+offset
        ws.merge_cells(start_row=1,start_column=cs,end_row=1,end_column=ce)
        c = ws.cell(row=1,column=cs,value=grp["label"])
        c.font=hdr_font(); c.fill=fill(grp["cor"])
        c.alignment=center(); c.border=b_all
    for i,h in enumerate(headers,1):
        c = ws.cell(row=2,column=i+offset,value=h)
        c.font=hdr_font(); c.fill=fill(NAVY)
        c.alignment=center(wrap=True); c.border=b_hdr
    ws.row_dimensions[1].height=18
    ws.row_dimensions[2].height=32

def write_rows(ws, df, cols, offset, bg_alt, result_col=None):
    jogador_atual=None; flip=False
    for row_i,(_,row) in enumerate(df.iterrows(),start=3):
        if row["Jogador"]!=jogador_atual:
            jogador_atual=row["Jogador"]; flip=not flip
        bg = bg_alt if flip else WHITE
        for ci,cn in enumerate(cols,1):
            val=row.get(cn,"-")
            val="-" if (val!=val or str(val).strip()=="") else val
            c=ws.cell(row=row_i,column=ci+offset,value=val)
            c.fill=fill(bg); c.border=b_all
            c.font=body_font(bold=(ci==1))
            if cn==result_col:
                s=str(val)
                if ":" in s:
                    try:
                        a,b=int(s.split(":")[0]),int(s.split(":")[1])
                        cor="145A32" if a>b else ("7B241C" if a<b else "784212")
                        c.font=Font(name="Arial",bold=True,color=cor,size=9)
                    except: pass
                c.alignment=center()
            else:
                c.alignment=left() if ci<=2 else center()
        ws.row_dimensions[row_i].height=15

def set_widths(ws, widths, offset):
    for i,w in enumerate(widths,1):
        ws.column_dimensions[get_column_letter(i+offset)].width=w

def sep(ws, col):
    ws.column_dimensions[get_column_letter(col)].width=3

# =====================================================
# ABA GOLEIROS
# =====================================================

wb = openpyxl.Workbook()
ws_g = wb.active
ws_g.title = "Goleiros"
ws_g.freeze_panes = "A3"

N_RG = len(COLS_RG)  # 15

grp_rg = [
    {"cols":[1,2,3,4,5], "cor":NAVY,    "label":"IDENTIFICAÇÃO"},
    {"cols":[6,7],       "cor":"1A5276", "label":"ATAQUE"},
    {"cols":[8,9],       "cor":"145A32", "label":"PARTICIPAÇÃO"},
    {"cols":[10,11,12],  "cor":"7B241C", "label":"CARTÕES"},
    {"cols":[13,14],     "cor":"784212", "label":"GOLEIRO"},
    {"cols":[15],        "cor":"2C3E50", "label":"TEMPO"},
]
hdr_rg = ["Jogador","Competição","Jogos\nRelac.","Partidas\nJogadas","PPJ",
          "Gols","Gols\nContra",
          "Entrou","Saiu",
          "Amarelo","Exp.\n2 Amar.","Vermelho",
          "Gols\nSofridos","Sem Gols\nSofridos",
          "Minutos"]

write_header(ws_g, grp_rg, hdr_rg, offset=0)
write_rows(ws_g, df_rg, COLS_RG, offset=0, bg_alt=LIGHT_GOL)
set_widths(ws_g, [20,22,9,10,7, 7,9, 8,7, 9,10,9, 10,13, 10], offset=0)
sep(ws_g, N_RG+1)

OFF_JG = N_RG+1
grp_jg = [
    {"cols":[1,2,3,4,5,6,7], "cor":NAVY,    "label":"IDENTIFICAÇÃO DO JOGO"},
    {"cols":[8],              "cor":"145A32", "label":"POS."},
    {"cols":[9,10,11],        "cor":"1A5276", "label":"CONTRIBUIÇÃO"},
    {"cols":[12,13,14],       "cor":"7B241C", "label":"CARTÕES"},
    {"cols":[15,16,17],       "cor":"2C3E50", "label":"TEMPO"},
]
hdr_jg = ["Jogador","Rodada","Data","Cidade","Time Casa","T. Visitante","Resultado",
          "Posição",
          "Gols","Assist.","Gols\nContra",
          "Amarelo","Exp.\n2 Amar.","Vermelho",
          "Entrou\n(min)","Saiu\n(min)","Minutos"]

write_header(ws_g, grp_jg, hdr_jg, offset=OFF_JG)
write_rows(ws_g, df_jg, COLS_JG, offset=OFF_JG, bg_alt=LIGHT_GOL, result_col="Resultado")
set_widths(ws_g, [20,9,11,10,16,16,10, 9, 7,8,9, 8,10,8, 9,9,10], offset=OFF_JG)

# =====================================================
# ABA JOGADORES DE LINHA
# =====================================================

ws_l = wb.create_sheet("Jogadores de Linha")
ws_l.freeze_panes = "A3"

N_RL = len(COLS_RL)  # 16

grp_rl = [
    {"cols":[1,2,3,4,5],  "cor":NAVY,    "label":"IDENTIFICAÇÃO"},
    {"cols":[6,7,8],      "cor":"1A5276", "label":"ATAQUE"},
    {"cols":[9,10,11],    "cor":"7B241C", "label":"CARTÕES"},
    {"cols":[12,13],      "cor":"145A32", "label":"PARTICIPAÇÃO"},
    {"cols":[14,15,16],   "cor":"2C3E50", "label":"TEMPO / BÔNUS"},
]
hdr_rl = ["Jogador","Competição","Jogos\nRelac.","Partidas\nJogadas","PPJ",
          "Gols","Assist.","Gols\nContra",
          "Amarelo","Exp.\n2 Amar.","Vermelho",
          "Entrou","Saiu",
          "Gols\nPênalti","Min/\nGol","Minutos"]

write_header(ws_l, grp_rl, hdr_rl, offset=0)
write_rows(ws_l, df_rl, COLS_RL, offset=0, bg_alt=LIGHT_BG)
set_widths(ws_l, [20,22,9,10,7, 7,8,9, 9,10,9, 8,7, 9,9,10], offset=0)
sep(ws_l, N_RL+1)

OFF_JL = N_RL+1
grp_jl = [
    {"cols":[1,2,3,4,5,6,7], "cor":NAVY,    "label":"IDENTIFICAÇÃO DO JOGO"},
    {"cols":[8],              "cor":"145A32", "label":"POS."},
    {"cols":[9,10,11],        "cor":"1A5276", "label":"CONTRIBUIÇÃO"},
    {"cols":[12,13,14],       "cor":"7B241C", "label":"CARTÕES"},
    {"cols":[15,16,17],       "cor":"2C3E50", "label":"TEMPO"},
]
hdr_jl = ["Jogador","Rodada","Data","Cidade","Time Casa","T. Visitante","Resultado",
          "Posição",
          "Gols","Assist.","Gols\nContra",
          "Amarelo","Exp.\n2 Amar.","Vermelho",
          "Entrou\n(min)","Saiu\n(min)","Minutos"]

write_header(ws_l, grp_jl, hdr_jl, offset=OFF_JL)
write_rows(ws_l, df_jl, COLS_JL, offset=OFF_JL, bg_alt=LIGHT_BG, result_col="Resultado")
set_widths(ws_l, [20,9,11,10,16,16,10, 9, 7,8,9, 8,10,8, 9,9,10], offset=OFF_JL)

# =====================================================
# SALVAR
# =====================================================

nome_saida = os.path.splitext(arquivo)[0] + ".xlsx"
wb.save(nome_saida)
print("\n============================================")
print("EXCEL SALVO: football_stats_limpo.xlsx")
print("Aba 'Goleiros':           Resumo | Jogos")
print("Aba 'Jogadores de Linha': Resumo | Jogos")
print("============================================")