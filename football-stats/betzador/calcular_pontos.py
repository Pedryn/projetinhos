import mysql.connector

# =====================================================
# CONFIGURAÇÃO
# =====================================================

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "betizador"

ULTIMOS_N_JOGOS = 10

# =====================================================
# PESOS POR POSIÇÃO
# =====================================================

PESOS = {
    "F": {
        "gols":                   3.0,
        "assistencias":           2.0,
        "chutes_no_gol":          0.5,
        "total_chutes":           0.2,
        "dribles_vencidos":       0.4,
        "passes_certos":          0.03,
        "recuperacoes":           0.2,
        "interceptacoes":         0.2,
        "duelos_vencidos":        0.2,
        "duelos_aereos_vencidos": 0.2,
        "faltas_sofridas":        0.2,
        "faltas_cometidas":      -0.1,
        "posse_perdida":         -0.2,
        "cartao_amarelo":        -1.0,
        "cartao_vermelho":       -3.0,
    },
    "M": {
        "gols":                   4.0,
        "assistencias":           2.5,
        "chutes_no_gol":          0.4,
        "total_chutes":           0.15,
        "dribles_vencidos":       0.3,
        "passes_certos":          0.05,
        "recuperacoes":           0.35,
        "interceptacoes":         0.35,
        "duelos_vencidos":        0.25,
        "duelos_aereos_vencidos": 0.15,
        "faltas_sofridas":        0.15,
        "faltas_cometidas":      -0.15,
        "posse_perdida":         -0.25,
        "cartao_amarelo":        -1.0,
        "cartao_vermelho":       -3.0,
    },
    "D": {
        "gols":                   5.0,
        "assistencias":           3.0,
        "chutes_no_gol":          0.3,
        "total_chutes":           0.1,
        "dribles_vencidos":       0.2,
        "passes_certos":          0.04,
        "recuperacoes":           0.5,
        "interceptacoes":         0.5,
        "duelos_vencidos":        0.4,
        "duelos_aereos_vencidos": 0.4,
        "faltas_sofridas":        0.1,
        "faltas_cometidas":      -0.2,
        "posse_perdida":         -0.3,
        "cartao_amarelo":        -1.0,
        "cartao_vermelho":       -3.0,
    },
    "G": {
        "defesas":                1.5,
        "gols_evitados":          2.0,
        "defesas_dentro_area":    1.0,
        "passes_certos":          0.03,
        "recuperacoes":           0.3,
        "cortes":                 0.3,
        "socos":                  0.1,
        "posse_perdida":         -0.3,
        "cartao_amarelo":        -1.0,
        "cartao_vermelho":       -3.0,
    },
}

# =====================================================
# BANCO
# =====================================================

def conectar():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

def criar_tabela_scores_jogadores(cur, time_slug):
    """
    Cria tabela de scores dos jogadores de um time.
    Ex: barcelona_scores, real_madrid_scores
    """
    tabela = f"{time_slug}_scores"
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS `{tabela}` (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            jogador_id       INT NOT NULL,
            jogador_slug     VARCHAR(150),
            jogo_id          INT NOT NULL,
            data             DATE,
            posicao          VARCHAR(5),
            minutos          INT,
            score_bruto      FLOAT,
            score_norm       FLOAT,
            score_ajustado   FLOAT,
            fator_adv        FLOAT,
            UNIQUE KEY uq (jogador_id, jogo_id),
            INDEX idx_jogador (jogador_id),
            INDEX idx_jogo    (jogo_id),
            INDEX idx_data    (data)
        )
    """)
    return tabela

def criar_tabela_scores_time(cur, time_slug):
    """
    Cria tabela de score agregado do time por jogo.
    Ex: barcelona_time_scores, real_madrid_time_scores
    """
    tabela = f"{time_slug}_time_scores"
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS `{tabela}` (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            time_id          INT NOT NULL,
            jogo_id          INT NOT NULL,
            data             DATE,
            adversario_id    INT,
            score_time       FLOAT,
            fator_adv        FLOAT,
            score_final      FLOAT,
            UNIQUE KEY uq (time_id, jogo_id),
            INDEX idx_data (data)
        )
    """)
    return tabela

# =====================================================
# SCORE DE UM JOGO DO JOGADOR
# =====================================================

def calcular_score(row, posicao):
    pesos = PESOS.get(posicao, PESOS["M"])
    score = 0.0
    for campo, peso in pesos.items():
        val = row.get(campo) or 0
        score += val * peso
    minutos = row.get("minutos_jogados") or 0
    if minutos < 45:
        score *= (minutos / 45)
    return round(score, 4)

def normalizar(valores):
    if not valores:
        return valores
    mn, mx = min(valores), max(valores)
    if mx == mn:
        return [5.0] * len(valores)
    return [round(10 * (v - mn) / (mx - mn), 3) for v in valores]

# =====================================================
# PROCESSAR UM TIME
# =====================================================

def processar_time(cur, time_id, time_slug):
    print(f"\n  Time: {time_slug}")

    tabela_tj       = f"{time_slug}_jogadores"
    tabela_scores_j = criar_tabela_scores_jogadores(cur, time_slug)
    tabela_scores_t = criar_tabela_scores_time(cur, time_slug)

    # Verifica se tabela intermediária existe
    cur.execute(f"SHOW TABLES LIKE '{tabela_tj}'")
    if not cur.fetchone():
        print(f"    [AVISO] {tabela_tj} não existe — rode coletor_jogadores primeiro")
        return 0, 0

    # Busca jogadores do time
    cur.execute(f"""
        SELECT j.id, j.slug, j.posicao
        FROM `{tabela_tj}` tjt
        JOIN jogadores j ON j.id = tjt.jogador_id
    """)
    jogadores = cur.fetchall()
    print(f"    {len(jogadores)} jogadores encontrados")

    total_scores_j = 0

    for jogador_id, slug, posicao_default in jogadores:
        if not slug:
            continue

        tabela_j = slug.replace("-", "_")
        cur.execute(f"SHOW TABLES LIKE '{tabela_j}'")
        if not cur.fetchone():
            continue

        cur.execute(f"SELECT * FROM `{tabela_j}` ORDER BY data")
        cols = [d[0] for d in cur.description]
        jogos = [dict(zip(cols, r)) for r in cur.fetchall()]

        if not jogos:
            continue

        scores_brutos = []
        posicoes      = []
        for j in jogos:
            pos = j.get("posicao_jogo") or posicao_default or "M"
            posicoes.append(pos)
            scores_brutos.append(calcular_score(j, pos))

        scores_norm = normalizar(scores_brutos)

        for i, j in enumerate(jogos):
            try:
                cur.execute(f"""
                    INSERT INTO `{tabela_scores_j}`
                        (jogador_id, jogador_slug, jogo_id, data,
                         posicao, minutos, score_bruto, score_norm)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                        score_bruto = VALUES(score_bruto),
                        score_norm  = VALUES(score_norm)
                """, (
                    jogador_id, slug, j["jogo_id"], j.get("data"),
                    posicoes[i], j.get("minutos_jogados"),
                    scores_brutos[i], scores_norm[i],
                ))
                total_scores_j += 1
            except Exception as e:
                print(f"    Erro {slug}: {e}")

    print(f"    {total_scores_j} scores de jogadores salvos em `{tabela_scores_j}`")

    # ── Score do time por jogo ────────────────────────────────────────────────
    cur.execute(f"""
        SELECT DISTINCT jogo_id, data
        FROM `{tabela_scores_j}`
        ORDER BY data
    """)
    jogos_time = cur.fetchall()

    total_scores_t = 0
    for jogo_id, data in jogos_time:
        cur.execute(f"""
            SELECT score_norm, minutos
            FROM `{tabela_scores_j}`
            WHERE jogo_id = %s AND minutos > 0
        """, (jogo_id,))
        rows = cur.fetchall()
        if not rows:
            continue

        total_min  = sum(r[1] or 0 for r in rows)
        if total_min == 0:
            continue
        score_pond = sum((r[0] or 0) * (r[1] or 0) for r in rows) / total_min

        # Adversário
        cur.execute("""
            SELECT CASE WHEN time_casa_id = %s
                        THEN time_visitante_id
                        ELSE time_casa_id END
            FROM jogos WHERE id = %s
        """, (time_id, jogo_id))
        res    = cur.fetchone()
        adv_id = res[0] if res else None

        try:
            cur.execute(f"""
                INSERT INTO `{tabela_scores_t}`
                    (time_id, jogo_id, data, adversario_id,
                     score_time, fator_adv, score_final)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    score_time  = VALUES(score_time),
                    score_final = VALUES(score_final)
            """, (time_id, jogo_id, data, adv_id,
                  round(score_pond, 3), 1.0, round(score_pond, 3)))
            total_scores_t += 1
        except Exception as e:
            print(f"    Erro time_scores: {e}")

    print(f"    {total_scores_t} scores de jogos salvos em `{tabela_scores_t}`")
    return total_scores_j, total_scores_t

# =====================================================
# FATOR ADVERSÁRIO
# =====================================================

def aplicar_fator_adversario(cur, time_id, time_slug):
    tabela_scores_j = f"{time_slug}_scores"
    tabela_scores_t = f"{time_slug}_time_scores"

    cur.execute(f"""
        SELECT id, jogo_id, data, adversario_id, score_time
        FROM `{tabela_scores_t}`
        ORDER BY data
    """)
    jogos = cur.fetchall()

    for rid, jogo_id, data, adv_id, score_time in jogos:
        if not adv_id:
            continue

        # Descobre slug do adversário
        cur.execute("SELECT slug FROM times WHERE id = %s", (adv_id,))
        res = cur.fetchone()
        if not res:
            continue
        adv_slug = res[0].replace("-", "_") if res[0] else None
        if not adv_slug:
            continue

        tabela_adv = f"{adv_slug}_time_scores"
        cur.execute(f"SHOW TABLES LIKE '{tabela_adv}'")
        if not cur.fetchone():
            # Adversário sem dados — usa neutro
            score_adv = 5.0
        else:
            cur.execute(f"""
                SELECT AVG(score_final) FROM (
                    SELECT score_final FROM `{tabela_adv}`
                    WHERE data < %s
                    ORDER BY data DESC
                    LIMIT %s
                ) sub
            """, (data, ULTIMOS_N_JOGOS))
            res2      = cur.fetchone()
            score_adv = res2[0] if res2 and res2[0] is not None else 5.0

        fator       = round(0.5 + (float(score_adv) / 10.0), 3)
        score_final = round((score_time or 0) * fator, 3)

        cur.execute(f"""
            UPDATE `{tabela_scores_t}`
            SET fator_adv = %s, score_final = %s
            WHERE id = %s
        """, (fator, score_final, rid))

        cur.execute(f"""
            UPDATE `{tabela_scores_j}`
            SET fator_adv      = %s,
                score_ajustado = ROUND(score_norm * %s, 3)
            WHERE jogo_id = %s
        """, (fator, fator, jogo_id))

# =====================================================
# MAIN
# =====================================================

print("="*50)
print("  CALCULADOR DE PONTOS")
print("="*50)

con = conectar()
cur = con.cursor()

# Descobre todos os times com tabelas *_jogadores
cur.execute("SHOW TABLES LIKE '%\\_jogadores'")
tabelas_tj = [r[0] for r in cur.fetchall()]

if not tabelas_tj:
    print("\nNenhuma tabela *_jogadores encontrada.")
    print("Rode coletor_jogadores.py primeiro.")
    con.close()
    exit()

print(f"\n{len(tabelas_tj)} time(s) encontrado(s)\n")

times_processados = []

for tj in tabelas_tj:
    time_slug_db    = tj[:-len("_jogadores")]
    time_slug_busca = time_slug_db.replace("_", "-")

    cur.execute("""
        SELECT id FROM times
        WHERE slug = %s OR REPLACE(slug, '-', '_') = %s
        LIMIT 1
    """, (time_slug_busca, time_slug_db))
    t = cur.fetchone()
    if not t:
        print(f"  [AVISO] Time não encontrado para {tj}")
        continue

    time_id = t[0]
    processar_time(cur, time_id, time_slug_db)
    con.commit()
    times_processados.append((time_id, time_slug_db))

print(f"\n{'='*50}")
print("  APLICANDO FATOR ADVERSÁRIO")
print(f"{'='*50}")

for time_id, time_slug in times_processados:
    print(f"\n  {time_slug}")
    aplicar_fator_adversario(cur, time_id, time_slug)
    con.commit()
    print(f"    Fator adversário aplicado")

print(f"\n{'='*50}")
print(f"  CONCLUÍDO")
print(f"\n  Tabelas criadas por time:")
for _, slug in times_processados:
    print(f"    `{slug}_scores`      — scores dos jogadores")
    print(f"    `{slug}_time_scores` — score do time por jogo")
print(f"\n  Consulta útil — ranking do time nos últimos {ULTIMOS_N_JOGOS} jogos:")
for _, slug in times_processados:
    print(f"\n  -- {slug}:")
    print(f"  SELECT jogador_slug, ROUND(AVG(score_ajustado),2) as media")
    print(f"  FROM `{slug}_scores`")
    print(f"  GROUP BY jogador_slug ORDER BY media DESC LIMIT 10;")
print(f"{'='*50}")