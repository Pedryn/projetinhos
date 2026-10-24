import customtkinter as ctk
import requests
import yfinance as yf
import tkinter.ttk as ttk
import sqlite3
import hashlib
from tkinter import messagebox

# === Configurações iniciais e tema ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DB_PATH = "dados.db"
current_user = None  # será (id, nome, email)

# ---------------------------
# ===== Banco de dados ======
# ---------------------------
def get_conn():
    return sqlite3.connect(DB_PATH)

def criar_tabelas():
    conn = get_conn()
    c = conn.cursor()
    # tabela de usuários
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT UNIQUE,
        senha_hash TEXT
    )""")
    # tabela de ativos por usuário
    c.execute("""CREATE TABLE IF NOT EXISTS ativos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        ticker TEXT,
        quantidade REAL,
        preco_medio REAL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )""")
    conn.commit()
    conn.close()

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def registrar_usuario(nome, email, senha):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                  (nome, email, hash_senha(senha)))
        conn.commit()
        messagebox.showinfo("Sucesso", "Usuário cadastrado! Faça login.")
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "Email já cadastrado.")
    finally:
        conn.close()

def tentar_login(email, senha):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nome, email, senha_hash FROM usuarios WHERE email=?", (email,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    id_, nome, email_db, senha_hash = row
    if senha_hash == hash_senha(senha):
        return (id_, nome, email_db)
    return None

# ---------------------------
# ===== Funções B3 / UI =====
# ---------------------------
def listar_tickers():
    """Busca todos os tickers listados na B3 via Brapi"""
    url = "https://brapi.dev/api/quote/list"
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            stocks = resp.json().get("stocks", [])
            return [
                {
                    "ticker": s["stock"],
                    "name": s.get("name", ""),
                    "close": s.get("close"),
                    "change": s.get("change")
                }
                for s in stocks
            ]
    except Exception as e:
        print("Erro ao listar tickers:", e)
    return []

def filtrar(ordenacao, busca=""):
    """Ordena conforme o filtro selecionado e aplica busca"""
    for row in lista.get_children():
        lista.delete(row)

    filtrados = tickers

    # Aplica busca
    if busca:
        busca = busca.upper()
        filtrados = [x for x in filtrados if busca in x['ticker'] or busca in x['name'].upper()]

    # Ordenação
    if ordenacao == "Mais Caro":
        filtrados.sort(key=lambda x: x.get('close') or 0, reverse=True)
    elif ordenacao == "Mais Barato":
        filtrados.sort(key=lambda x: x.get('close') or 0)
    elif ordenacao == "A-Z":
        filtrados.sort(key=lambda x: x['ticker'])
    elif ordenacao == "Z-A":
        filtrados.sort(key=lambda x: x['ticker'], reverse=True)

    # Preenche a tabela (com preço e cor)
    for item in filtrados:
        preco = f"R$ {item.get('close', 0):.2f}" if item.get('close') else "—"
        mudanca = item.get("change", 0) or 0
        tag = "verde" if mudanca >= 0 else "vermelho"
        lista.insert("", "end", values=(item['ticker'], item['name'], preco), tags=(tag,))

    lista.tag_configure("verde", foreground="#00FF00")
    lista.tag_configure("vermelho", foreground="#FF5555")

def atualizar_lista(event=None):
    filtro = combo_filtro.get()
    texto_busca = entry_busca.get()
    filtrar(filtro, texto_busca)

def mostrar_detalhes(event):
    """Abre uma janela popup com informações detalhadas da ação clicada (via Yahoo Finance)"""
    selecionado = lista.focus()
    if not selecionado:
        return

    valores = lista.item(selecionado, "values")
    ticker = valores[0] + ".SA"  # Yahoo precisa do sufixo .SA

    try:
        acao = yf.Ticker(ticker)
        info = acao.info
    except Exception as e:
        print(f"Erro ao buscar {ticker}: {e}")
        return

    nome = info.get("longName", ticker)
    preco = info.get("currentPrice")
    market_cap = info.get("marketCap")
    volume = info.get("volume")

    # Popup
    popup = ctk.CTkToplevel(root)
    popup.title(f"Detalhes - {ticker}")
    popup.geometry("400x260")

    ctk.CTkLabel(popup, text=f"{nome}", font=("Arial", 18, "bold")).pack(pady=10)
    ctk.CTkLabel(popup, text=f"Preço atual: R$ {preco:.2f}" if preco else "Preço atual: Indisponível").pack(pady=5)
    if market_cap:
        ctk.CTkLabel(popup, text=f"Valor de mercado: R$ {market_cap:,.2f}").pack(pady=5)
    if volume:
        ctk.CTkLabel(popup, text=f"Volume diário: {volume:,}").pack(pady=5)

# ---------------------------
# ====== Janela Meus Ativos =
# ---------------------------
def abrir_meus_ativos():
    if current_user is None:
        messagebox.showerror("Atenção", "Faça login primeiro.")
        return

    user_id = current_user[0]

    janela = ctk.CTkToplevel(root)
    janela.title(f"Meus Ativos - {current_user[1]}")
    janela.geometry("800x500")

    # Treeview de ativos
    cols = ("ID", "Ticker", "Quantidade", "Preço Médio (R$)", "Preço Atual (R$)", "Valor Atual (R$)", "Lucro/Prejuízo (R$)")
    tree = ttk.Treeview(janela, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor="center", width=120 if c != "Ticker" else 100)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def carregar_ativos():
        for r in tree.get_children():
            tree.delete(r)
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, ticker, quantidade, preco_medio FROM ativos WHERE usuario_id=?", (user_id,))
        linhas = c.fetchall()
        conn.close()
        for linha in linhas:
            aid, ticker, qtd, preco_med = linha
            ticker_y = ticker + ".SA"
            preco_atual = None
            valor_atual = None
            lucro = None
            try:
                info = yf.Ticker(ticker_y).info
                preco_atual = info.get("currentPrice")
                if preco_atual is not None:
                    valor_atual = preco_atual * qtd
                    lucro = (preco_atual - preco_med) * qtd
            except Exception as e:
                print("Erro yfinance:", e)
            tree.insert("", "end", values=(
                aid,
                ticker,
                f"{qtd:.4f}",
                f"{preco_med:.2f}",
                f"{preco_atual:.2f}" if preco_atual else "—",
                f"{valor_atual:.2f}" if valor_atual else "—",
                f"{lucro:.2f}" if lucro else "—"
            ))

    # Formulário para adicionar ativo
    frame_form = ctk.CTkFrame(janela)
    frame_form.pack(fill="x", padx=10, pady=(0,10))

    entry_ticker = ctk.CTkEntry(frame_form, placeholder_text="Ticker (ex: PETR4)")
    entry_ticker.pack(side="left", padx=5)
    entry_qtd = ctk.CTkEntry(frame_form, placeholder_text="Quantidade")
    entry_qtd.pack(side="left", padx=5)
    entry_preco = ctk.CTkEntry(frame_form, placeholder_text="Preço médio (R$)")
    entry_preco.pack(side="left", padx=5)

    def adicionar_ativo():
        t = entry_ticker.get().strip().upper().replace(".SA", "")
        try:
            q = float(entry_qtd.get())
            p = float(entry_preco.get())
        except ValueError:
            messagebox.showerror("Erro", "Quantidade e preço devem ser números.")
            return
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO ativos (usuario_id, ticker, quantidade, preco_medio) VALUES (?, ?, ?, ?)",
                  (user_id, t, q, p))
        conn.commit()
        conn.close()
        entry_ticker.delete(0, "end")
        entry_qtd.delete(0, "end")
        entry_preco.delete(0, "end")
        carregar_ativos()

    btn_add = ctk.CTkButton(frame_form, text="Adicionar ativo", command=adicionar_ativo)
    btn_add.pack(side="left", padx=5)

    def remover_selecionado():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um ativo para remover.")
            return
        vals = tree.item(sel, "values")
        aid = vals[0]
        if messagebox.askyesno("Confirmar", "Remover ativo selecionado?"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM ativos WHERE id=? AND usuario_id=?", (aid, user_id))
            conn.commit()
            conn.close()
            carregar_ativos()

    btn_rem = ctk.CTkButton(frame_form, text="Remover selecionado", command=remover_selecionado)
    btn_rem.pack(side="left", padx=5)

    btn_atual = ctk.CTkButton(frame_form, text="Atualizar", command=carregar_ativos)
    btn_atual.pack(side="left", padx=5)

    carregar_ativos()

# ---------------------------
# ====== Login UI ===========
# ---------------------------
def abrir_tela_login():
    login_win = ctk.CTkToplevel(root)
    login_win.title("Login / Cadastro")
    login_win.geometry("420x320")
    login_win.grab_set()

    # Tabs para Login / Cadastro
    tabview = ctk.CTkTabview(login_win, width=400)
    tabview.pack(fill="both", expand=True, padx=10, pady=10)
    tabview.add("Login")
    tabview.add("Cadastro")

    # --- Login ---
    frame_login = tabview.tab("Login")
    ctk.CTkLabel(frame_login, text="Email:").pack(pady=(10, 0))
    login_email = ctk.CTkEntry(frame_login, width=300)
    login_email.pack(pady=5)
    ctk.CTkLabel(frame_login, text="Senha:").pack(pady=(10, 0))
    login_senha = ctk.CTkEntry(frame_login, width=300, show="*")
    login_senha.pack(pady=5)

    def ação_login():
        nonlocal login_win
        email = login_email.get().strip()
        senha = login_senha.get().strip()
        if not email or not senha:
            messagebox.showerror("Erro", "Preencha email e senha.")
            return
        user = tentar_login(email, senha)
        if user:
            global current_user
            current_user = user
            messagebox.showinfo("Bem-vindo", f"Olá, {user[1]}!")
            login_win.destroy()
            atualizar_estado_logado()
        else:
            messagebox.showerror("Erro", "Credenciais inválidas.")

    btn_login = ctk.CTkButton(frame_login, text="Entrar", command=ação_login)
    btn_login.pack(pady=10)

    # --- Cadastro ---
    frame_cad = tabview.tab("Cadastro")
    ctk.CTkLabel(frame_cad, text="Nome:").pack(pady=(8, 0))
    cad_nome = ctk.CTkEntry(frame_cad, width=300)
    cad_nome.pack(pady=5)
    ctk.CTkLabel(frame_cad, text="Email:").pack(pady=(8, 0))
    cad_email = ctk.CTkEntry(frame_cad, width=300)
    cad_email.pack(pady=5)
    ctk.CTkLabel(frame_cad, text="Senha:").pack(pady=(8, 0))
    cad_senha = ctk.CTkEntry(frame_cad, width=300, show="*")
    cad_senha.pack(pady=5)

    def ação_cadastrar():
        nome = cad_nome.get().strip()
        email = cad_email.get().strip()
        senha = cad_senha.get().strip()
        if not (nome and email and senha):
            messagebox.showerror("Erro", "Preencha todos os campos.")
            return
        registrar_usuario(nome, email, senha)
        # opcional: já pular para tab login
        tabview.set("Login")

    btn_cad = ctk.CTkButton(frame_cad, text="Registrar", command=ação_cadastrar)
    btn_cad.pack(pady=10)

# ---------------------------
# ====== Main Window ========
# ---------------------------
def atualizar_estado_logado():
    """Atualiza labels/botoes visíveis no topo de acordo com usuário logado"""
    if current_user:
        label_usuario.configure(text=f"Usuário: {current_user[1]} ({current_user[2]})")
        btn_meus_ativos.configure(state="normal")
        btn_logout.configure(state="normal")
        btn_login.configure(state="disabled")
    else:
        label_usuario.configure(text="Usuário: (não logado)")
        btn_meus_ativos.configure(state="disabled")
        btn_logout.configure(state="disabled")
        btn_login.configure(state="normal")

def deslogar():
    global current_user
    if messagebox.askyesno("Sair", "Deseja deslogar?"):
        current_user = None
        atualizar_estado_logado()

# === Interface principal ===
root = ctk.CTk()
root.title("Monitor B3 - Brapi + Yahoo Finance (com carteira)")
root.geometry("1000x650")

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

# Botões relacionados ao usuário / carteira
btn_login = ctk.CTkButton(frame_topo, text="Login / Cadastro", command=abrir_tela_login)
btn_login.pack(side="right", padx=5)
btn_logout = ctk.CTkButton(frame_topo, text="Logout", command=deslogar, state="disabled")
btn_logout.pack(side="right", padx=5)
btn_meus_ativos = ctk.CTkButton(frame_topo, text="Meus Ativos", command=abrir_meus_ativos, state="disabled")
btn_meus_ativos.pack(side="right", padx=5)
label_usuario = ctk.CTkLabel(frame_topo, text="Usuário: (não logado)")
label_usuario.pack(side="right", padx=10)

# Frame da tabela
frame_tabela = ctk.CTkFrame(root)
frame_tabela.pack(fill="both", expand=True, padx=10, pady=10)

colunas = ("Ticker", "Nome", "Preço")
lista = ttk.Treeview(frame_tabela, columns=colunas, show="headings")
for c in colunas:
    lista.heading(c, text=c)
    lista.column(c, anchor="center", width=350 if c == "Nome" else 150)
lista.pack(fill="both", expand=True)

# Evento de clique
lista.bind("<Double-1>", mostrar_detalhes)

# Rodapé com instruções
frame_rodape = ctk.CTkFrame(root)
frame_rodape.pack(fill="x", padx=10, pady=(0,10))
ctk.CTkLabel(frame_rodape, text="Dica: use 'Meus Ativos' para cadastrar suas posições. Os preços atuais são consultados via Yahoo Finance.").pack(side="left", padx=10)

# Carregar tickers
tickers = listar_tickers()
filtrar("Mais Barato")

# Cria DB e atualiza estado
criar_tabelas()
atualizar_estado_logado()

root.mainloop()
