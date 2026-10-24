import customtkinter as ctk
import requests
import tkinter.ttk as ttk

# === Configuração de tema ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def carregar_dados():
    """Busca todas as ações/FIIs na B3 via Brapi API"""
    url = "https://brapi.dev/api/quote/list"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json().get('stocks', [])
    return []

def filtrar(ordenacao, busca=""):
    """Ordena conforme o filtro selecionado e aplica busca"""
    for row in lista.get_children():
        lista.delete(row)

    filtrados = dados

    # Aplica busca
    if busca:
        busca = busca.upper()
        filtrados = [x for x in filtrados if busca in x['stock'] or busca in x['name'].upper()]

    # Ordenação
    if ordenacao == "Mais Caro":
        filtrados.sort(key=lambda x: x['close'] or 0, reverse=True)
    elif ordenacao == "Mais Barato":
        filtrados.sort(key=lambda x: x['close'] or 0)
    elif ordenacao == "A-Z":
        filtrados.sort(key=lambda x: x['stock'])
    elif ordenacao == "Z-A":
        filtrados.sort(key=lambda x: x['stock'], reverse=True)

    # Preenche a tabela
    for item in filtrados:
        preco = f"R$ {item['close']:.2f}" if item['close'] else "Preço indisponível"
        mudanca = item.get("change", 0) or 0
        tag = "verde" if mudanca >= 0 else "vermelho"
        lista.insert("", "end", values=(item['stock'], item['name'], preco), tags=(tag,))

    lista.tag_configure("verde", foreground="#00FF00")
    lista.tag_configure("vermelho", foreground="#FF5555")

def atualizar_lista(event=None):
    filtro = combo_filtro.get()
    texto_busca = entry_busca.get()
    filtrar(filtro, texto_busca)

def mostrar_detalhes(event):
    """Abre uma janela popup com informações detalhadas da ação clicada"""
    selecionado = lista.focus()
    if not selecionado:
        return

    valores = lista.item(selecionado, "values")
    ticker = valores[0]

    # Faz a requisição dos detalhes
    url = f"https://brapi.dev/api/quote/{ticker}?fundamental=true"
    resp = requests.get(url)

    popup = ctk.CTkToplevel(root)
    popup.title(f"Detalhes - {ticker}")
    popup.geometry("400x250")

    if resp.status_code != 200:
        ctk.CTkLabel(popup, text=f"{ticker}", font=("Arial", 18, "bold")).pack(pady=10)
        ctk.CTkLabel(popup, text="Não foi possível buscar informações detalhadas.").pack(pady=10)
        return

    data = resp.json()
    results = data.get("results")

    if not results:
        ctk.CTkLabel(popup, text=f"{ticker}", font=("Arial", 18, "bold")).pack(pady=10)
        ctk.CTkLabel(popup, text="Informações indisponíveis.").pack(pady=10)
        return

    res = results[0]
    nome = res.get('longName', ticker)
    preco = res.get('regularMarketPrice')
    market_cap = res.get('marketCap')
    quantidade = (market_cap / preco) if preco and market_cap else None

    # Exibe as informações
    ctk.CTkLabel(popup, text=f"{nome}", font=("Arial", 18, "bold")).pack(pady=10)
    ctk.CTkLabel(popup, text=f"Preço atual: R$ {preco:.2f}" if preco else "Preço atual: Indisponível").pack(pady=5)
    if market_cap:
        ctk.CTkLabel(popup, text=f"Valor de mercado: R$ {market_cap:,.2f}").pack(pady=5)
    if quantidade:
        ctk.CTkLabel(popup, text=f"Quantidade de cotas: {quantidade:,.0f}").pack(pady=5)

# === Interface ===
root = ctk.CTk()
root.title("Monitor B3 - Profissional")
root.geometry("900x600")

# Frame topo
frame_topo = ctk.CTkFrame(root)
frame_topo.pack(fill="x", pady=10, padx=10)

# Filtro
label_filtro = ctk.CTkLabel(frame_topo, text="Ordenar por:")
label_filtro.pack(side="left", padx=5)

combo_filtro = ctk.CTkComboBox(frame_topo, values=["Mais Barato", "Mais Caro", "A-Z", "Z-A"], command=lambda _: atualizar_lista())
combo_filtro.set("Mais Barato")
combo_filtro.pack(side="left", padx=5)

# Busca
label_busca = ctk.CTkLabel(frame_topo, text="Buscar:")
label_busca.pack(side="left", padx=5)

entry_busca = ctk.CTkEntry(frame_topo, placeholder_text="Digite o ticker ou nome...")
entry_busca.pack(side="left", padx=5, fill="x", expand=True)
entry_busca.bind("<KeyRelease>", atualizar_lista)

# Frame da tabela
frame_tabela = ctk.CTkFrame(root)
frame_tabela.pack(fill="both", expand=True, padx=10, pady=10)

colunas = ("Ticker", "Nome", "Preço")
lista = ttk.Treeview(frame_tabela, columns=colunas, show="headings")
for c in colunas:
    lista.heading(c, text=c)
    lista.column(c, anchor="center", width=250 if c == "Nome" else 150)
lista.pack(fill="both", expand=True)

# Evento de clique
lista.bind("<Double-1>", mostrar_detalhes)

# Carregar dados
dados = carregar_dados()
filtrar("Mais Barato")

root.mainloop()
