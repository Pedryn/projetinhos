import pandas as pd

# =====================================================
# ABRIR EXCEL
# =====================================================

df = pd.read_excel("football_stats.xlsx")

print(df.head())

# =====================================================
# IDENTIFICAR LINHAS DE JOGOS
# =====================================================

# jogos possuem placar tipo 1:2 ou -:-
mask_jogos = (
    df["PPJ"]
    .astype(str)
    .str.contains(":", na=False)
)

jogos = df[mask_jogos].copy()

# resumo = resto
resumo = df[~mask_jogos].copy()

# =====================================================
# LIMPAR RESUMO
# =====================================================

# remove duplicados
resumo = resumo.drop_duplicates(
    subset=["Jogador", "Competicao"]
)

# remove linhas inválidas
resumo = resumo[
    resumo["Competicao"].notna()
]

resumo = resumo[
    resumo["Competicao"] != "-"
]

# =====================================================
# PEGAR APENAS 5 JOGOS POR JOGADOR
# =====================================================

jogos = jogos.groupby(
    "Jogador"
).head(5)

# =====================================================
# RESETAR INDEX
# =====================================================

resumo.reset_index(
    drop=True,
    inplace=True
)

jogos.reset_index(
    drop=True,
    inplace=True
)

# =====================================================
# GARANTIR COLUNAS
# =====================================================

colunas_resumo = [

    "Jogador",
    "Competicao",
    "Partidas",
    "PPJ",

    "Gols",
    "Assistencias",

    "Entrou",
    "Substituido",

    "Cartao Amarelo",
    "Cartao Vermelho",

    "Gols Sofridos",
    "Partidas sem sofrer gol",

    "Minutos Jogados"

]

for col in colunas_resumo:

    if col not in resumo.columns:
        resumo[col] = "-"

# =====================================================
# ORGANIZAR RESUMO
# =====================================================

resumo = resumo[colunas_resumo]

# =====================================================
# ORGANIZAR JOGOS
# =====================================================

# cria dataframe novo de jogos
jogos_formatado = pd.DataFrame()

jogos_formatado["Jogador"] = jogos["Jogador"]

# estrutura da tabela do transfermarkt
jogos_formatado["Rodada"] = jogos["Competicao"]
jogos_formatado["Data"] = jogos["Partidas"]
jogos_formatado["Cidade"] = jogos["PPJ"]

jogos_formatado["Time Casa"] = jogos["Gols"]
jogos_formatado["Time Visitante"] = jogos["Assistencias"]

jogos_formatado["Resultado"] = jogos["Entrou"]
jogos_formatado["Posicao"] = jogos["Substituido"]

jogos_formatado["Gols"] = jogos["Cartao Amarelo"]
jogos_formatado["Assistencias"] = jogos["Cartao Vermelho"]

jogos_formatado["Gols Contra"] = jogos["Gols Sofridos"]

jogos_formatado["Amarelo"] = jogos["Partidas sem sofrer gol"]

jogos_formatado["2 Amarelos"] = "-"

jogos_formatado["Vermelho"] = "-"

jogos_formatado["Entrou"] = "-"
jogos_formatado["Saiu"] = "-"

jogos_formatado["Info"] = "-"

jogos_formatado["Minutos"] = jogos["Minutos Jogados"]

# =====================================================
# SALVAR
# =====================================================

with pd.ExcelWriter(
    "football_stats_limpo.xlsx",
    engine="openpyxl"
) as writer:

    # =========================================
    # RESUMO
    # =========================================

    resumo.to_excel(
        writer,
        sheet_name="Dados",
        startrow=0,
        startcol=0,
        index=False
    )

    # =========================================
    # JOGOS
    # =========================================

    jogos_formatado.to_excel(
        writer,
        sheet_name="Dados",
        startrow=0,
        startcol=len(resumo.columns) + 3,
        index=False
    )

print("\n======================")
print("EXCEL LIMPO SALVO")
print("======================")