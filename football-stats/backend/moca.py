import requests
from bs4 import BeautifulSoup
import pandas as pd

"""
Para realizar a solicitação à página temos que informar ao site que somos um navegador
e é para isso que usamos a variável headers
"""
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

# endereco_da_pagina representa o link que direciona a página com os dados
endereco_da_pagina = "https://www.transfermarkt.co.uk/ajax-amsterdam/transferrekorde/verein/610/plus/1/galerie/0?saison_id=&pos=&detailpos=&altersklasse=&w_s="

# no objeto_response iremos realizar o download da página da web 
objeto_response = requests.get(endereco_da_pagina, headers=headers)

"""
Agora criaremos um objeto BeautifulSoup a partir do nosso objeto_response.
O parâmetro 'html.parser' representa qual parser usaremos na criação do nosso objeto,
um parser é um software responsável por realizar a conversão de uma entrada para uma estrutura de dados.
"""
pagina_bs = BeautifulSoup(objeto_response.content, 'html.parser')


# Primeiro conseguiremos os nomes de cada jogador
nomes_jogadores = [] # Lista ordenada dos nomes de todos os jogadores

# O método find_all() consegue retornar todas as tags que cumprem as restrições dentro dos parênteses
tags_jogadores = pagina_bs.find_all("a", {"class": "spielprofil_tooltip"})
# No nosso caso estamos encontrando todas as âncoras com a classe "spielprofil_tooltip"

# Agora iremos conseguir somente os nomes de todos os jogadores
for tag_jogador in tags_jogadores:
    nomes_jogadores.append(tag_jogador.text)


# Agora partiremos para o país da liga de origem de cada jogador
pais_jogadores = [] # Lista ordenada dos nomes do país da liga de origem de todos os jogadores

tags_ligas = pagina_bs.find_all("td",{"class": None})
# Agora iremos receber todas as células da tabela que não possuem classe

for tag_liga in tags_ligas:
    # A função find irá encontrar a primeira imagem cuja classe é "flaggenrahmen" e possui um título
    imagem_pais = tag_liga.find("img", {"class": "flaggenrahmen"}, {"title":True})
    # A variável imagem_país será uma estrutura com todas as informações da imagem,
    # uma delas é o title que contem o nome do país da bandeira
    if(imagem_pais != None): # Testaremos se o método encontrou alguma correspondência
        pais_jogadores.append(imagem_pais['title'])
    

# Por fim iremos conseguir as informacões de custo dos jogadores
custos_jogadores = []

tags_custos = pagina_bs.find_all("td", {"class": "rechts hauptlink"})

for tag_custo in tags_custos:
    texto_preco = tag_custo.text
    # O texto do preço contém caracteres que não precisamos como £ (euros) e m (milhão) então iremos retirá-los
    texto_preco = texto_preco.replace("£", "").replace("m","")
    # Converteremos agora o valor para uma variável numérica
    preco_numerico = float(texto_preco)
    custos_jogadores.append(preco_numerico)

# Criando um DataFrame a partir de nossos dados
df = pd.DataFrame({"Jogador":nomes_jogadores,"Preço (milhão de euro)":custos_jogadores,"País de Origem":pais_jogadores})

# Imprimindo os dados que obtemos
print(df)