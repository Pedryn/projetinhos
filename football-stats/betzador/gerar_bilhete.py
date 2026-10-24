import mysql.connector
import sys

# =====================================================
# CONFIGURAÇÃO
# =====================================================

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "betizador"

N       = 10    # últimos N jogos para análise
ALTA    = 0.70  # 7/10
MEDIA   = 0.60  # 6/10
TITULAR = 0.70  # jogou em 70%+ dos jogos

# =====================================================
# BANCO
# =====================================================

def conectar():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

def buscar_time(cur, nome):
    """Busca o time de forma flexível — nome parcial, slug com - ou _."""
    termos = [
        f"%{nome.lower()}%",
        f"%{nome.lower().replace(' ','-')}%",
        f"%{nome.lower().replace(' ','_')}%",
        f"%{nome.lower().replace('-',' ')}%",
        f"%{nome.lower().split('-')[0].strip()}%",  # antes do hífen: "Athletico" de "Athletico-PR"
        f"%{nome.lower().split()[0]}%",              # primeira palavra
    ]
    for termo in termos:
        cur.execute("""
            SELECT id, nome, slug FROM times
            WHERE LOWER(nome) LIKE %s OR LOWER(slug) LIKE %s
            LIMIT 1
        """, (termo, termo))
        r = cur.fetchone()
        if r:
            return r
    return None

# =====================================================
# ANÁLISE DO TIME
# =====================================================

def analisar_time(cur, time_id, time_slug, time_nome):
    """
    Pega os últimos N jogos do time e calcula frequência
    de cada padrão estatístico.
    Retorna lista de padrões com confiança.
    """
    tabela = time_slug.replace("-", "_")
    cur.execute(f"SHOW TABLES LIKE '{tabela}'")
    if not cur.fetchone():
        return []

    cur.execute(f"""
        SELECT
            gols_casa, gols_visitante,
            time_casa, time_visitante,
            escanteios, total_chutes, chutes_no_gol,
            posse_bola, faltas, cartoes_amarelos, cartoes_vermelhos,
            xg, grandes_chances, passes_certos, passes,
            data
        FROM `{tabela}`
        ORDER BY data DESC
        LIMIT {N}
    """)
    cols = [d[0] for d in cur.description]
    jogos = [dict(zip(cols, r)) for r in cur.fetchall()]

    if not jogos:
        return []

    total = len(jogos)
    padroes = []

    def freq(condicao, label, mercado=None, opcao=None):
        count = sum(1 for j in jogos if condicao(j))
        pct   = count / total
        if pct >= ALTA:
            conf = "Alta"
        elif pct >= MEDIA:
            conf = "Média"
        else:
            return
        padroes.append({
            "time":      time_nome,
            "label":     label,
            "freq":      f"{count}/{total}",
            "pct":       pct,
            "confianca": conf,
            "mercado":   mercado,
            "opcao":     opcao,
            "tipo":      "time",
        })

    # Gols marcados
    def gols_marcados(j):
        if j["time_casa"] and time_nome.lower() in j["time_casa"].lower():
            return (j["gols_casa"] or 0)
        return (j["gols_visitante"] or 0)

    def gols_sofridos(j):
        if j["time_casa"] and time_nome.lower() in j["time_casa"].lower():
            return (j["gols_visitante"] or 0)
        return (j["gols_casa"] or 0)

    freq(lambda j: gols_marcados(j) >= 1,   f"{time_nome} marcou pelo menos 1 gol",        "ambos_marcam", "Sim")
    freq(lambda j: gols_marcados(j) >= 2,   f"{time_nome} marcou 2+ gols")
    freq(lambda j: gols_sofridos(j) >= 1,   f"{time_nome} sofreu pelo menos 1 gol")
    freq(lambda j: gols_sofridos(j) == 0,   f"{time_nome} não sofreu gols (clean sheet)")
    freq(lambda j: (gols_marcados(j) + gols_sofridos(j)) >= 3, f"Jogos do {time_nome} tiveram 3+ gols", "over_under", "Over")
    freq(lambda j: gols_marcados(j) >= 1 and gols_sofridos(j) >= 1, f"Ambos marcaram em jogos do {time_nome}", "ambos_marcam", "Sim")

    # Escanteios
    freq(lambda j: (j["escanteios"] or 0) >= 3,  f"{time_nome} teve 3+ escanteios")
    freq(lambda j: (j["escanteios"] or 0) >= 5,  f"{time_nome} teve 5+ escanteios")
    freq(lambda j: (j["escanteios"] or 0) >= 7,  f"{time_nome} teve 7+ escanteios")

    # Chutes
    freq(lambda j: (j["total_chutes"] or 0) >= 10, f"{time_nome} teve 10+ chutes")
    freq(lambda j: (j["chutes_no_gol"] or 0) >= 3, f"{time_nome} teve 3+ finalizações certas")
    freq(lambda j: (j["chutes_no_gol"] or 0) >= 5, f"{time_nome} teve 5+ finalizações certas")

    # Cartões
    freq(lambda j: (j["cartoes_amarelos"] or 0) >= 1, f"{time_nome} recebeu cartão amarelo")
    freq(lambda j: (j["cartoes_amarelos"] or 0) >= 2,  f"{time_nome} recebeu 2+ cartões")

    # Posse
    freq(lambda j: (j["posse_bola"] or 0) >= 50, f"{time_nome} ficou com a posse (50%+)")

    # xG
    freq(lambda j: (j["xg"] or 0) >= 1.5, f"{time_nome} gerou 1.5+ xG")
    freq(lambda j: (j["xg"] or 0) >= 2.0, f"{time_nome} gerou 2.0+ xG")

    return padroes

# =====================================================
# ANÁLISE COMBINADA (CASA + VISITANTE)
# =====================================================

def analisar_combinado(cur, id_casa, slug_casa, nome_casa,
                            id_vis,  slug_vis,  nome_vis):
    """Padrões que dependem dos dois times juntos."""
    tab_c = slug_casa.replace("-", "_")
    tab_v = slug_vis.replace("-", "_")

    cur.execute(f"SHOW TABLES LIKE '{tab_c}'")
    if not cur.fetchone(): return []
    cur.execute(f"SHOW TABLES LIKE '{tab_v}'")
    if not cur.fetchone(): return []

    def ultimos(tabela, n):
        cur.execute(f"""
            SELECT escanteios, cartoes_amarelos, total_chutes, xg,
                   gols_casa, gols_visitante, time_casa
            FROM `{tabela}` ORDER BY data DESC LIMIT {n}
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    jc = ultimos(tab_c, N)
    jv = ultimos(tab_v, N)

    if not jc or not jv:
        return []

    padroes = []
    total = min(len(jc), len(jv))

    def media(jogos, campo):
        vals = [j.get(campo) or 0 for j in jogos]
        return sum(vals) / len(vals) if vals else 0

    # Média combinada de escanteios
    med_esc_c = media(jc, "escanteios")
    med_esc_v = media(jv, "escanteios")
    med_esc   = round(med_esc_c + med_esc_v, 1)

    for limite in [8, 10, 12]:
        count_c = sum(1 for j in jc if (j["escanteios"] or 0) >= limite // 2)
        count_v = sum(1 for j in jv if (j["escanteios"] or 0) >= limite // 2)
        pct = min(count_c, count_v) / total
        if pct >= MEDIA:
            conf = "Alta" if pct >= ALTA else "Média"
            padroes.append({
                "time":      f"{nome_casa} + {nome_vis}",
                "label":     f"Total de escanteios Over {limite - 0.5} (média combinada: {med_esc})",
                "freq":      f"{min(count_c,count_v)}/{total}",
                "pct":       pct,
                "confianca": conf,
                "mercado":   "escanteios",
                "opcao":     f"Over {limite - 0.5}",
                "tipo":      "combinado",
            })
            break  # só o mais provável

    # Média combinada de cartões
    med_cart_c = media(jc, "cartoes_amarelos")
    med_cart_v = media(jv, "cartoes_amarelos")
    med_cart   = round(med_cart_c + med_cart_v, 1)

    for limite in [3, 4, 5]:
        count_c = sum(1 for j in jc if (j["cartoes_amarelos"] or 0) >= limite // 2)
        count_v = sum(1 for j in jv if (j["cartoes_amarelos"] or 0) >= limite // 2)
        pct = min(count_c, count_v) / total
        if pct >= MEDIA:
            conf = "Alta" if pct >= ALTA else "Média"
            padroes.append({
                "time":      f"{nome_casa} + {nome_vis}",
                "label":     f"Total de cartões Over {limite - 0.5} (média combinada: {med_cart})",
                "freq":      f"{min(count_c,count_v)}/{total}",
                "pct":       pct,
                "confianca": conf,
                "mercado":   "cartoes",
                "opcao":     f"Over {limite - 0.5}",
                "tipo":      "combinado",
            })
            break

    return padroes

# =====================================================
# ANÁLISE DOS JOGADORES
# =====================================================

def analisar_jogadores(cur, time_slug, time_nome, n_jogos_time):
    """
    Para cada titular (jogou 70%+ dos jogos),
    analisa padrões de chutes, gols, cartões.
    """
    tabela_tj = f"{time_slug.replace('-','_')}_jogadores"
    cur.execute(f"SHOW TABLES LIKE '{tabela_tj}'")
    if not cur.fetchone():
        return []

    cur.execute(f"""
        SELECT j.nome, j.slug, j.posicao
        FROM `{tabela_tj}` tjt
        JOIN jogadores j ON j.id = tjt.jogador_id
        WHERE j.posicao != 'G'
    """)
    jogadores = cur.fetchall()

    padroes = []
    min_jogos = int(n_jogos_time * TITULAR)

    for nome_j, slug_j, posicao in jogadores:
        if not slug_j:
            continue
        tabela_j = slug_j.replace("-", "_")
        cur.execute(f"SHOW TABLES LIKE '{tabela_j}'")
        if not cur.fetchone():
            continue

        cur.execute(f"""
            SELECT
                minutos_jogados, gols, assistencias,
                chutes_no_gol, total_chutes,
                cartao_amarelo, cartao_vermelho,
                dribles_vencidos, duelos_vencidos
            FROM `{tabela_j}`
            WHERE minutos_jogados > 0
            ORDER BY data DESC
            LIMIT {N}
        """)
        cols = [d[0] for d in cur.description]
        jogos = [dict(zip(cols, r)) for r in cur.fetchall()]

        if len(jogos) < min_jogos:
            continue  # não é titular

        total = len(jogos)

        def freq_j(condicao, label, mercado=None, opcao=None):
            count = sum(1 for j in jogos if condicao(j))
            pct   = count / total
            if pct >= ALTA:
                conf = "Alta"
            elif pct >= MEDIA:
                conf = "Média"
            else:
                return
            padroes.append({
                "time":      time_nome,
                "jogador":   nome_j,
                "posicao":   posicao,
                "label":     f"{nome_j} ({posicao}): {label}",
                "freq":      f"{count}/{total}",
                "pct":       pct,
                "confianca": conf,
                "mercado":   mercado,
                "opcao":     opcao,
                "tipo":      "jogador",
            })

        # Chutes e gols
        freq_j(lambda j: (j["chutes_no_gol"] or 0) >= 1,
               "finalizou a gol em pelo menos 1x")
        freq_j(lambda j: (j["total_chutes"] or 0) >= 2,
               "teve 2+ chutes no jogo")
        freq_j(lambda j: (j["gols"] or 0) >= 1,
               "marcou gol",
               mercado="gols_jogador", opcao=f"{nome_j} marca")
        freq_j(lambda j: (j["assistencias"] or 0) >= 1,
               "deu assistência")

        # Cartões
        freq_j(lambda j: (j["cartao_amarelo"] or 0) >= 1,
               "recebeu cartão amarelo",
               mercado="cartoes_jogador", opcao=f"{nome_j} amarelo")

    return padroes

# =====================================================
# BUSCA ODDS RELEVANTES
# =====================================================

def odds_jogo(cur, time_casa, time_visitante):
    cur.execute("""
        SELECT jogo_id_fs FROM odds
        WHERE LOWER(time_casa) LIKE %s AND LOWER(time_visitante) LIKE %s
        ORDER BY coletado_em DESC LIMIT 1
    """, (f"%{time_casa.lower()}%", f"%{time_visitante.lower()}%"))
    r = cur.fetchone()
    if not r:
        return {}
    jogo_id = r[0]

    cur.execute("""
        SELECT mercado, opcao, odd FROM odds
        WHERE jogo_id_fs = %s
        ORDER BY mercado, opcao
    """, (jogo_id,))
    resultado = {}
    for mercado, opcao, odd in cur.fetchall():
        if mercado not in resultado:
            resultado[mercado] = {}
        resultado[mercado][opcao] = odd
    return resultado

# =====================================================
# CRUZAR PADRÕES COM ODDS
# =====================================================

def cruzar_com_odds(padroes, odds):
    """
    Mapeia cada padrão para a odd correta no banco.
    Só associa quando o mercado E a opção batem exatamente.
    """
    for p in padroes:
        mercado = p.get("mercado")
        opcao   = p.get("opcao")

        if not mercado or not opcao:
            continue

        # Mapeamento direto mercado→opção→odd
        mercado_odds = odds.get(mercado, {})
        if not mercado_odds:
            continue

        # Tenta match exato primeiro
        if opcao in mercado_odds:
            p["odd"] = mercado_odds[opcao]
            continue

        # Tenta match parcial (ex: "Over" bate com "Over 2.5")
        for k, v in mercado_odds.items():
            if opcao.lower() in k.lower():
                p["odd"] = v
                break

    return padroes

# =====================================================
# IMPRIMIR BILHETE
# =====================================================

def imprimir_bilhete(nome_casa, nome_vis, data_jogo, liga,
                     padroes_casa, padroes_vis, padroes_comb,
                     padroes_jog_casa, padroes_jog_vis, odds):

    linha = "=" * 60

    print(f"\n{linha}")
    print(f"  🎯  BETIZADOR — ANÁLISE ESTATÍSTICA")
    print(linha)
    print(f"  {liga}")
    print(f"  {data_jogo}")
    print(f"\n  {nome_casa.upper()}  x  {nome_vis.upper()}")
    print(f"  Baseado nos últimos {N} jogos de cada time")
    print(linha)

    def imprimir_grupo(titulo, padroes):
        if not padroes:
            return
        print(f"\n  {titulo}")
        print(f"  {'-'*56}")
        for p in sorted(padroes, key=lambda x: x["pct"], reverse=True):
            odd_str = f"  →  odd {p['odd']}" if p.get("odd") else ""
            print(f"  [{p['confianca']:5}] {p['freq']:>5}  {p['label']}{odd_str}")

    imprimir_grupo(f"📊 PADRÕES — {nome_casa}", padroes_casa)
    imprimir_grupo(f"📊 PADRÕES — {nome_vis}",  padroes_vis)
    imprimir_grupo(f"🔀 PADRÕES COMBINADOS",     padroes_comb)
    imprimir_grupo(f"⚽ TITULARES — {nome_casa}", padroes_jog_casa)
    imprimir_grupo(f"⚽ TITULARES — {nome_vis}",  padroes_jog_vis)

    # Sugestões consolidadas — só Alta confiança de padrões com odd
    sugestoes = [p for p in (padroes_casa + padroes_vis + padroes_comb +
                              padroes_jog_casa + padroes_jog_vis)
                 if p["confianca"] == "Alta" and p.get("odd")]

    if sugestoes:
        print(f"\n  ✅ SUGESTÕES COM MAIOR CONFIANÇA E ODD DISPONÍVEL")
        print(f"  {'-'*56}")
        for s in sorted(sugestoes, key=lambda x: x["pct"], reverse=True):
            print(f"  [{s['freq']:>5}]  {s['label']}")
            print(f"           Odd: {s['odd']}  |  Confiança: {s['confianca']}")

    if not odds:
        print(f"\n  ⚠️  Odds não encontradas no banco para este jogo.")
        print(f"       Use a opção 3 do menu para coletar as odds primeiro.")

    print(f"\n{linha}")
    print(f"  ⚠️  Jogue com responsabilidade.")
    print(linha)

# =====================================================
# MAIN
# =====================================================

args           = sys.argv[1:]
time_casa_inp  = args[0].strip() if len(args) > 0 else input("Time da casa: ").strip()
time_vis_inp   = args[1].strip() if len(args) > 1 else input("Time visitante: ").strip()
data_jogo      = args[2].strip() if len(args) > 2 else input("Data/hora: ").strip()
liga           = args[3].strip() if len(args) > 3 else input("Liga: ").strip()

con = conectar()
cur = con.cursor()

t_casa = buscar_time(cur, time_casa_inp)
t_vis  = buscar_time(cur, time_vis_inp)

if not t_casa:
    print(f"\n[ERRO] '{time_casa_inp}' não encontrado no banco.")
    con.close(); sys.exit(1)
if not t_vis:
    print(f"\n[ERRO] '{time_vis_inp}' não encontrado no banco.")
    con.close(); sys.exit(1)

id_casa,  nome_casa, slug_casa = t_casa
id_vis,   nome_vis,  slug_vis  = t_vis

print(f"\nAnalisando {nome_casa} x {nome_vis}...")

# Conta jogos disponíveis para definir titular
def contar_jogos(slug):
    tabela = slug.replace("-", "_")
    try:
        cur.execute(f"SELECT COUNT(*) FROM `{tabela}`")
        return cur.fetchone()[0]
    except:
        return 0

n_casa = min(contar_jogos(slug_casa), N)
n_vis  = min(contar_jogos(slug_vis),  N)

padroes_casa     = analisar_time(cur, id_casa, slug_casa, nome_casa)
padroes_vis      = analisar_time(cur, id_vis,  slug_vis,  nome_vis)
padroes_comb     = analisar_combinado(cur, id_casa, slug_casa, nome_casa,
                                           id_vis,  slug_vis,  nome_vis)
padroes_jog_casa = analisar_jogadores(cur, slug_casa, nome_casa, n_casa)
padroes_jog_vis  = analisar_jogadores(cur, slug_vis,  nome_vis,  n_vis)

odds = odds_jogo(cur, time_casa_inp, time_vis_inp)

# Cruza padrões com odds disponíveis
todos = padroes_casa + padroes_vis + padroes_comb + padroes_jog_casa + padroes_jog_vis
cruzar_com_odds(todos, odds)

imprimir_bilhete(nome_casa, nome_vis, data_jogo, liga,
                 padroes_casa, padroes_vis, padroes_comb,
                 padroes_jog_casa, padroes_jog_vis, odds)

con.close()