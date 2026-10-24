import pandas as pd

def limpar_numero(valor):
    if pd.isna(valor) or valor == "-":
        return 0

    valor = str(valor).replace(".", "").replace(",", ".")

    try:
        return float(valor)
    except:
        return 0

def analisar_excel(arquivo):
    df = pd.read_excel(
        arquivo,
        sheet_name="Jogadores de Linha",
        header=1
    )

    # Ajuste caso seu arquivo tenha mais colunas
    df = df.iloc[:, :17]

    # Renomeie aqui caso a coluna de jogos tenha outro nome
    coluna_jogos = "Partidas\nJogadas"

    colunas_numericas = [
        coluna_jogos,
        "Gols",
        "Assist.",
        "Amarelo",
        "Exp.\n2 Amar.",
        "Vermelho"
    ]

    for col in colunas_numericas:
        df[col] = df[col].apply(limpar_numero)

    jogadores = (
        df.groupby("Jogador", as_index=False)
        .agg({
            coluna_jogos: "sum",
            "Gols": "sum",
            "Assist.": "sum",
            "Amarelo": "sum",
            "Exp.\n2 Amar.": "sum",
            "Vermelho": "sum"
        })
    )

    jogadores["Cartoes"] = (
        jogadores["Amarelo"]
        + jogadores["Exp.\n2 Amar."]
        + jogadores["Vermelho"]
    )

    top_gols = jogadores.nlargest(4, "Gols")[
        ["Jogador", coluna_jogos, "Gols"]
    ]

    top_assist = jogadores.nlargest(3, "Assist.")[
        ["Jogador", coluna_jogos, "Assist."]
    ]

    top_cartoes = jogadores.nlargest(3, "Cartoes")[
        ["Jogador", coluna_jogos, "Cartoes"]
    ]

    print("\n=== TOP 3 GOLS ===")
    print(top_gols.to_string(index=False))

    print("\n=== TOP 3 ASSISTÊNCIAS ===")
    print(top_assist.to_string(index=False))

    print("\n=== TOP 3 CARTÕES ===")
    print(top_cartoes.to_string(index=False))

# Exemplo
analisar_excel("turquia.xlsx")