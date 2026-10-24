import undetected_chromedriver as uc
import sys
import mysql.connector
import datetime
import time

# =====================================================
# CONFIGURAÇÃO
# =====================================================

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "betizador"

# =====================================================
# BANCO
# =====================================================

def conectar():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

def setup_tabelas_base(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jogadores (
            id              INT PRIMARY KEY,
            nome            VARCHAR(150),
            nome_curto      VARCHAR(100),
            slug            VARCHAR(150),
            posicao         VARCHAR(10),
            altura          INT,
            data_nascimento DATE
        )
    """)

    # tabela intermediária criada dinamicamente por time em criar_tabela_time_jogadores()
    pass

def criar_tabela_time_jogadores(cur, team_slug):
    """Cria tabela intermediária time_jogadores com nome do time."""
    tabela = f"{team_slug.replace('-', '_')}_jogadores"
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS `{tabela}` (
            jogador_id  INT,
            PRIMARY KEY (jogador_id),
            FOREIGN KEY (jogador_id) REFERENCES jogadores(id)
        )
    """)
    return tabela

def criar_tabela_jogador(cur, slug):
    tabela = slug.replace("-", "_")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS `{tabela}` (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
            jogo_id                     INT,
            time_id                     INT,
            -- Identificação do jogo
            data                        DATE,
            liga                        VARCHAR(150),
            fase                        VARCHAR(100),
            time_casa                   VARCHAR(150),
            time_visitante              VARCHAR(150),
            gols_casa                   INT,
            gols_visitante              INT,
            -- Performance
            minutos_jogados             INT,
            posicao_jogo                VARCHAR(10),
            rating                      FLOAT,
            -- Gols e assistências
            gols                        INT,
            assistencias                INT,
            gols_esperados              FLOAT,
            assistencias_esperadas      FLOAT,
            -- Finalizações
            total_chutes                INT,
            chutes_no_gol               INT,
            chutes_bloqueados           INT,
            -- Passes
            passes_certos               INT,
            total_passes                INT,
            passes_longos_certos        INT,
            total_passes_longos         INT,
            passes_campo_proprio        INT,
            passes_campo_adversario     INT,
            -- Dribles
            dribles_tentados            INT,
            dribles_vencidos            INT,
            -- Duelos
            duelos_vencidos             INT,
            duelos_aereos_vencidos      INT,
            -- Defesa
            interceptacoes              INT,
            cortes                      INT,
            recuperacoes                INT,
            faltas_cometidas            INT,
            faltas_sofridas             INT,
            -- Posse
            toques                      INT,
            posse_perdida               INT,
            -- Físico
            distancia_km                FLOAT,
            velocidade_max              FLOAT,
            sprints                     INT,
            -- Goleiro
            defesas                     INT,
            gols_evitados               FLOAT,
            defesas_dentro_area         INT,
            socos                       INT,
            -- Cartões
            cartao_amarelo              INT,
            cartao_vermelho             INT,
            UNIQUE KEY uq_jogo (jogo_id),
            FOREIGN KEY (jogo_id) REFERENCES jogos(id),
            FOREIGN KEY (time_id) REFERENCES times(id)
        )
    """)
    return tabela

# =====================================================
# SOFASCORE
# =====================================================

BASE = "https://api.sofascore.com/api/v1"

def api_get(driver, endpoint):
    script = f"""
        const r = await fetch('{BASE}{endpoint}', {{
            headers: {{
                'Accept': 'application/json',
                'Referer': 'https://www.sofascore.com/'
            }}
        }});
        return await r.json();
    """
    driver.set_script_timeout(30)
    for i in range(3):
        try:
            return driver.execute_script(f"return (async () => {{ {script} }})()")
        except Exception as e:
            if i < 2:
                print(f"    [retry {i+1}/3] {str(e)[:60]}")
                try:
                    driver.get("https://www.sofascore.com/")
                    time.sleep(5)
                except:
                    pass
            else:
                raise
    return None

def buscar_time(driver, nome, escolha_fixa=None):
    data = api_get(driver, f"/search/teams/{nome}")
    if not data or "teams" not in data:
        return None
    times = data["teams"]
    for i, t in enumerate(times[:5], 1):
        pais = t.get("country", {}).get("name", "?")
        print(f"  [{i}] {t['name']} (id={t['id']}) — {pais}")
    if escolha_fixa is not None:
        try:
            n = int(escolha_fixa)
            if 1 <= n <= min(5, len(times)):
                print(f"  Escolha automática: {n}")
                return times[n - 1]
        except ValueError:
            pass
    while True:
        try:
            n = int(input("  Escolha: "))
            if 1 <= n <= min(5, len(times)):
                return times[n - 1]
        except ValueError:
            pass

# =====================================================
# UPSERTS
# =====================================================

def upsert_jogador(cur, p):
    ts  = p.get("dateOfBirthTimestamp", 0)
    dn  = datetime.datetime.fromtimestamp(ts).date() if ts else None
    cur.execute("""
        INSERT INTO jogadores (id, nome, nome_curto, slug, posicao, altura, data_nascimento)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE nome=VALUES(nome)
    """, (p.get("id"), p.get("name"), p.get("shortName"), p.get("slug"),
          p.get("position"), p.get("height"), dn))

def upsert_time_jogador(cur, tabela_tj, jogador_id):
    cur.execute(f"""
        INSERT IGNORE INTO `{tabela_tj}` (jogador_id)
        VALUES (%s)
    """, (jogador_id,))

def salvar_stats_jogador(cur, tabela, jogo_id, time_id, jogo_info, stats):
    s = stats.get("statistics", {})
    try:
        cur.execute(f"""
            INSERT INTO `{tabela}` (
                jogo_id, time_id,
                data, liga, fase, time_casa, time_visitante, gols_casa, gols_visitante,
                minutos_jogados, posicao_jogo, rating,
                gols, assistencias, gols_esperados, assistencias_esperadas,
                total_chutes, chutes_no_gol, chutes_bloqueados,
                passes_certos, total_passes, passes_longos_certos, total_passes_longos,
                passes_campo_proprio, passes_campo_adversario,
                dribles_tentados, dribles_vencidos,
                duelos_vencidos, duelos_aereos_vencidos,
                interceptacoes, cortes, recuperacoes, faltas_cometidas, faltas_sofridas,
                toques, posse_perdida,
                distancia_km, velocidade_max, sprints,
                defesas, gols_evitados, defesas_dentro_area, socos,
                cartao_amarelo, cartao_vermelho
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s
            )
        """, (
            jogo_id, time_id,
            jogo_info["data"], jogo_info["liga"], jogo_info["fase"],
            jogo_info["casa"], jogo_info["visitante"],
            jogo_info["gols_casa"], jogo_info["gols_visitante"],
            s.get("minutesPlayed"),
            stats.get("position"),
            s.get("rating") or s.get("ratingVersions", {}).get("original"),
            s.get("goals") or s.get("goalScored") or 0,
            s.get("goalAssist") or 0,
            s.get("expectedGoals"),
            s.get("expectedAssists"),
            s.get("totalShots") if stats.get("position") != "G" else None,
            s.get("shotsOnTarget") if stats.get("position") != "G" else None,
            s.get("blockedScoringAttempt") if stats.get("position") != "G" else None,
            s.get("accuratePass"),
            s.get("totalPass"),
            s.get("accurateLongBalls"),
            s.get("totalLongBalls"),
            s.get("accurateOwnHalfPasses"),
            s.get("totalOppositionHalfPasses"),
            s.get("totalDribbleAttempts", s.get("ballCarriesCount")),
            s.get("successfulDribbles", s.get("progressiveBallCarriesCount")),
            s.get("duelWon"),
            s.get("aerialWon"),
            s.get("interceptionWon"),
            s.get("totalClearance"),
            s.get("ballRecovery"),
            s.get("fouls", s.get("foulCommitted")),
            s.get("wasFouled"),
            s.get("touches"),
            s.get("possessionLostCtrl"),
            s.get("kilometersCovered"),
            s.get("topSpeed"),
            s.get("numberOfSprints"),
            s.get("saves"),
            s.get("goalsPrevented"),
            s.get("savedShotsFromInsideTheBox"),
            s.get("punches"),
            s.get("yellowCard"),
            s.get("redCard"),
        ))
        return True
    except mysql.connector.errors.IntegrityError:
        return False

# =====================================================
# MAIN
# =====================================================

print("="*50)
print("  COLETOR DE JOGADORES")
print("="*50)

args = sys.argv[1:]  # [nome, escolha, data_ini, data_fim]

nome         = args[0].strip() if len(args) >= 1 else input("\nDigite o nome do time: ").strip()
_escolha_arg = args[1].strip() if len(args) >= 2 else None
data_ini_str = args[2].strip() if len(args) >= 3 else (input("Data início [01/01/2026]: ").strip() or "01/01/2026")
data_fim_str = args[3].strip() if len(args) >= 4 else input("Data fim    [hoje]:       ").strip()

try:
    DATA_INICIO = datetime.datetime.strptime(data_ini_str, "%d/%m/%Y").date()
except ValueError:
    DATA_INICIO = datetime.date(2026, 1, 1)

try:
    DATA_FIM = datetime.datetime.strptime(data_fim_str, "%d/%m/%Y").date()
except ValueError:
    DATA_FIM = datetime.date.today()

anos = set(range(DATA_INICIO.year, DATA_FIM.year + 1))
TEMPORADAS_VALIDAS = set()
for ano in anos:
    TEMPORADAS_VALIDAS.add(str(ano))
    TEMPORADAS_VALIDAS.add(f"{str(ano-1)[2:]}/{str(ano)[2:]}")

print(f"  Time    : {nome}")
print(f"  Período : {DATA_INICIO} → {DATA_FIM}")

print("\nConectando ao banco...")
con = conectar()
cur = con.cursor()
setup_tabelas_base(cur)
con.commit()

print("Abrindo navegador...")
options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors")
options.add_argument("--allow-insecure-localhost")

driver = None
for tentativa in range(3):
    try:
        driver = uc.Chrome(options=options, version_main=153)
        driver.get("https://www.sofascore.com/")
        try:
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except:
            pass
        time.sleep(5)
        print("  Navegador pronto.")
        break
    except Exception as e:
        print(f"  Tentativa {tentativa+1}/3 falhou: {e}")
        if driver:
            try: driver.quit()
            except: pass
        time.sleep(5)

if not driver:
    print("[ERRO] Não foi possível abrir o navegador após 3 tentativas.")
    con.close()
    sys.exit(1)

print(f"\nBuscando: {nome}")
time_obj = buscar_time(driver, nome, _escolha_arg)
if not time_obj:
    driver.quit()
    exit()

team_id   = time_obj["id"]
team_name = time_obj["name"]
team_slug = time_obj.get("slug", team_name.lower().replace(" ", "-"))
print(f"\nTime: {team_name} (id={team_id})")

# Cria tabela intermediária do time (ex: paris_saint_germain_jogadores)
tabela_tj = criar_tabela_time_jogadores(cur, team_slug)
con.commit()
print(f"Tabela intermediária: `{tabela_tj}`")

# Verifica último jogo salvo nas tabelas dos jogadores desse time
def ultima_data_jogadores(cur, team_slug):
    """Pega a data mais recente salva em qualquer tabela de jogador do time."""
    tabela_tj = f"{team_slug.replace('-','_')}_jogadores"
    cur.execute(f"SHOW TABLES LIKE '{tabela_tj}'")
    if not cur.fetchone():
        return None
    cur.execute(f"""
        SELECT j.slug FROM `{tabela_tj}` tjt
        JOIN jogadores j ON j.id = tjt.jogador_id
        LIMIT 1
    """)
    r = cur.fetchone()
    if not r:
        return None
    # Pega data mais recente de qualquer jogador do time
    slug = r[0].replace("-", "_") if r[0] else None
    if not slug:
        return None
    try:
        cur.execute(f"SELECT MAX(data) FROM `{slug}`")
        res = cur.fetchone()
        return res[0] if res and res[0] else None
    except:
        return None

ultima_data_jog = ultima_data_jogadores(cur, team_slug)
if ultima_data_jog:
    print(f"Último jogo de jogadores no banco: {ultima_data_jog} — modo incremental ativo")
else:
    print("Sem dados de jogadores no banco — coleta completa")

# Busca jogos do período — só os que já estão no banco (coletados pelo coletor_times)
# No modo incremental, pega apenas jogos após a última data salva
data_inicio_efetiva = ultima_data_jog if ultima_data_jog else DATA_INICIO

cur.execute("""
    SELECT j.id, j.data, l.nome, j.fase,
           tc.nome, tv.nome, j.gols_casa, j.gols_visitante,
           j.time_casa_id
    FROM jogos j
    JOIN ligas l      ON l.id = j.liga_id
    JOIN times tc     ON tc.id = j.time_casa_id
    JOIN times tv     ON tv.id = j.time_visitante_id
    WHERE (j.time_casa_id = %s OR j.time_visitante_id = %s)
      AND j.data > %s
      AND j.data <= %s
    ORDER BY j.data
""", (team_id, team_id, data_inicio_efetiva, DATA_FIM))

jogos = cur.fetchall()
print(f"\n{len(jogos)} jogos encontrados no banco para o período")

total_jogadores = 0
total_stats     = 0

for jogo in jogos:
    jogo_id, data, liga, fase, casa, visitante, gc, gv, casa_id = jogo
    side = "home" if casa_id == team_id else "away"

    print(f"\n  {data} | {liga} | {casa} {gc} x {gv} {visitante}")

    # Busca lineup do jogo
    lineup_data = api_get(driver, f"/event/{jogo_id}/lineups")
    if not lineup_data:
        print("    Sem lineup")
        continue

    players = lineup_data.get(side, {}).get("players", [])
    jogou   = [p for p in players
               if p.get("statistics", {}).get("minutesPlayed", 0) > 0]

    print(f"    {len(jogou)} jogadores em campo")

    jogo_info = {
        "data": data, "liga": liga, "fase": fase,
        "casa": casa, "visitante": visitante,
        "gols_casa": gc, "gols_visitante": gv,
    }

    for p_data in jogou:
        p   = p_data.get("player", {})
        pid = p.get("id")
        if not pid:
            continue

        # Upsert jogador
        upsert_jogador(cur, p)
        upsert_time_jogador(cur, tabela_tj, pid)

        # Cria tabela do jogador
        slug   = p.get("slug", p.get("name", "").lower().replace(" ", "-"))
        tabela = criar_tabela_jogador(cur, slug)
        con.commit()

        # Stats detalhadas
        stats_data = api_get(driver, f"/event/{jogo_id}/player/{pid}/statistics")
        if not stats_data or "statistics" not in stats_data:
            continue

        salvou = salvar_stats_jogador(cur, tabela, jogo_id, team_id, jogo_info, stats_data)
        nome_p = p.get("name", "?")
        mins   = stats_data.get("statistics", {}).get("minutesPlayed", "?")
        if salvou:
            total_stats += 1
            print(f"    ✓ {nome_p} ({mins} min)")
        else:
            print(f"    - {nome_p} já existia ou erro silencioso")

        total_jogadores += 1
        time.sleep(0.2)

    con.commit()

con.close()
driver.quit()

print(f"\n{'='*50}")
print(f"  CONCLUÍDO")
print(f"  Time              : {team_name}")
print(f"  Jogos processados : {len(jogos)}")
print(f"  Stats salvas      : {total_stats}")
print(f"{'='*50}")