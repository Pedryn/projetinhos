import undetected_chromedriver as uc
import sys
import mysql.connector
import datetime
import time

# =====================================================
# CONFIGURAÇÃO — edite com suas credenciais
# =====================================================

DB_HOST   = "localhost"
DB_USER   = "root"
DB_PASS   = "root"
DB_NAME   = "betizador"
# Temporadas aceitas — preenchidas dinamicamente pelo usuário
TEMPORADAS_VALIDAS = {"25/26", "2025", "2026"}  # padrão, sobrescrito no main

# =====================================================
# BANCO
# =====================================================

def conectar(com_banco=True):
    cfg = dict(host=DB_HOST, user=DB_USER, password=DB_PASS)
    if com_banco:
        cfg["database"] = DB_NAME
    return mysql.connector.connect(**cfg)

def setup_banco():
    con = conectar(com_banco=False)
    cur = con.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    con.close()

    con = conectar()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ligas (
            id        INT PRIMARY KEY,
            nome      VARCHAR(150),
            slug      VARCHAR(150),
            categoria VARCHAR(100),
            pais      VARCHAR(100)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS temporadas (
            id      INT PRIMARY KEY,
            liga_id INT,
            nome    VARCHAR(150),
            ano     VARCHAR(10),
            FOREIGN KEY (liga_id) REFERENCES ligas(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS times (
            id             INT PRIMARY KEY,
            nome           VARCHAR(150),
            nome_curto     VARCHAR(100),
            slug           VARCHAR(150),
            pais           VARCHAR(100),
            cor_primaria   VARCHAR(10),
            cor_secundaria VARCHAR(10)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jogos (
            id                INT PRIMARY KEY,
            liga_id           INT,
            temporada_id      INT,
            fase              VARCHAR(100),
            data              DATE,
            time_casa_id      INT,
            time_visitante_id INT,
            gols_casa         INT,
            gols_visitante    INT,
            vencedor          INT,
            estadio           VARCHAR(150),
            cidade            VARCHAR(100),
            arbitro           VARCHAR(100),
            publico           INT,
            FOREIGN KEY (liga_id)           REFERENCES ligas(id),
            FOREIGN KEY (temporada_id)      REFERENCES temporadas(id),
            FOREIGN KEY (time_casa_id)      REFERENCES times(id),
            FOREIGN KEY (time_visitante_id) REFERENCES times(id)
        )
    """)

    con.commit()
    con.close()
    print("Banco e tabelas base prontos.")

def criar_tabela_time(cur, slug):
    """Cria tabela de stats com o nome do slug do time."""
    tabela = slug.replace("-", "_")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS `{tabela}` (
            id                       INT AUTO_INCREMENT PRIMARY KEY,
            jogo_id                  INT,
            time_id                  INT,
            periodo                  VARCHAR(5),
            -- Identificação do jogo
            data                     DATE,
            liga                     VARCHAR(150),
            fase                     VARCHAR(100),
            time_casa                VARCHAR(150),
            time_visitante           VARCHAR(150),
            gols_casa                INT,
            gols_visitante           INT,
            posse_bola               FLOAT,
            xg                       FLOAT,
            grandes_chances          INT,
            total_chutes             INT,
            defesas_goleiro          INT,
            escanteios               INT,
            faltas                   INT,
            passes                   INT,
            desarmes                 INT,
            cartoes_amarelos         INT,
            cartoes_vermelhos        INT,
            distancia_coberta        FLOAT,
            sprints                  INT,
            chutes_no_gol            INT,
            chutes_fora              INT,
            chutes_bloqueados        INT,
            chutes_dentro_area       INT,
            chutes_fora_area         INT,
            trave                    INT,
            grandes_chances_marcadas INT,
            grandes_chances_perdidas INT,
            toques_area_penalti      INT,
            impedimentos             INT,
            passes_profundidade      INT,
            faltas_sofridas_terco    INT,
            passes_certos            INT,
            entradas_terco_final     INT,
            bolas_longas_certas      INT,
            bolas_longas_total       INT,
            cruzamentos_certos       INT,
            cruzamentos_total        INT,
            arremessos_lateral       INT,
            duelos_vencidos          FLOAT,
            duelos_terrestres_venc   INT,
            duelos_terrestres_total  INT,
            duelos_aereos_venc       INT,
            duelos_aereos_total      INT,
            dribles_venc             INT,
            dribles_total            INT,
            perdas_bola              INT,
            desarmes_vencidos        INT,
            desarmes_total           INT,
            interceptacoes           INT,
            recuperacoes             INT,
            cortes                   INT,
            erros_que_geraram_chute  INT,
            erros_que_geraram_gol    INT,
            defesas_total            INT,
            gols_evitados            FLOAT,
            defesas_grandes          INT,
            bolas_altas              INT,
            socos                    INT,
            tiros_de_meta            INT,
            UNIQUE KEY uq_jogo_periodo (jogo_id, periodo),
            FOREIGN KEY (jogo_id) REFERENCES jogos(id),
            FOREIGN KEY (time_id) REFERENCES times(id)
        )
    """)
    return tabela

# =====================================================
# SOFASCORE
# =====================================================

BASE = "https://api.sofascore.com/api/v1"

def ultima_data_salva(team_slug):
    """Retorna a data do último jogo salvo no banco para esse time."""
    try:
        con = conectar()
        cur = con.cursor()
        tabela = team_slug.replace("-", "_")
        cur.execute(f"SHOW TABLES LIKE '{tabela}'")
        if not cur.fetchone():
            con.close()
            return None
        cur.execute(f"SELECT MAX(data) FROM `{tabela}`")
        res = cur.fetchone()
        con.close()
        return res[0] if res and res[0] else None
    except:
        return None

def api_get(driver, endpoint, tentativas=3):
    script = f"""
        const r = await fetch('{BASE}{endpoint}', {{
            headers: {{
                'Accept': 'application/json',
                'Referer': 'https://www.sofascore.com/'
            }}
        }});
        return await r.json();
    """
    for i in range(tentativas):
        try:
            return driver.execute_script(f"return (async () => {{ {script} }})()")
        except Exception as e:
            if i < tentativas - 1:
                print(f"    [retry {i+1}/{tentativas}] {str(e)[:60]}")
                # Recarrega a página para restaurar o contexto
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

def ultima_data_salva(cur, time_slug):
    """Retorna a data do último jogo salvo no banco para esse time."""
    tabela = time_slug.replace("-", "_")
    try:
        cur.execute(f"SHOW TABLES LIKE '{tabela}'")
        if not cur.fetchone():
            return None
        cur.execute(f"SELECT MAX(data) FROM `{tabela}`")
        res = cur.fetchone()
        return res[0] if res and res[0] else None
    except:
        return None

def todos_jogos_temporada(driver, team_id, data_minima=None):
    todos = []
    pagina = 0
    while True:
        data = api_get(driver, f"/team/{team_id}/events/last/{pagina}")
        if not data:
            break
        eventos = data.get("events", [])
        if not eventos:
            break
        da_temp = []
        fora    = []
        for e in eventos:
            season_year = e.get("season", {}).get("year", "")
            ts = e.get("startTimestamp", 0)
            data_jogo = datetime.datetime.fromtimestamp(ts).date() if ts else None
            if season_year in TEMPORADAS_VALIDAS and data_jogo and DATA_INICIO <= data_jogo <= DATA_FIM:
                # Modo incremental: ignora jogos anteriores ao último salvo
                if data_minima and data_jogo <= data_minima:
                    fora.append(e)
                else:
                    da_temp.append(e)
            else:
                fora.append(e)
        todos = da_temp + todos
        print(f"  Página {pagina}: {len(da_temp)} da temporada | {len(fora)} fora")
        if fora and not da_temp:
            break
        if len(eventos) < 10:
            break
        pagina += 1
        time.sleep(0.5)
    return todos

# =====================================================
# PARSER DE STATS
# =====================================================

def get_val(groups, key, side):
    field = f"{side}Value"
    for g in groups:
        for item in g.get("statisticsItems", []):
            if item.get("key") == key:
                return item.get(field)
    return None

def get_total(groups, key, side):
    field = f"{side}Total"
    for g in groups:
        for item in g.get("statisticsItems", []):
            if item.get("key") == key:
                return item.get(field)
    return None

def extrair_stats(stats_json, side):
    linhas = []
    for period in stats_json.get("statistics", []):
        periodo = period.get("period", "ALL").upper()
        if periodo != "ALL":
            continue   # ignora 1ST e 2ND
        g = period.get("groups", [])
        def v(k): return get_val(g, k, side)
        def t(k): return get_total(g, k, side)
        linhas.append({
            "periodo":                   periodo,
            "posse_bola":                v("ballPossession"),
            "xg":                        v("expectedGoals"),
            "grandes_chances":           v("bigChanceCreated"),
            "total_chutes":              v("totalShotsOnGoal"),
            "defesas_goleiro":           v("goalkeeperSaves"),
            "escanteios":                v("cornerKicks"),
            "faltas":                    v("fouls"),
            "passes":                    v("passes"),
            "desarmes":                  v("totalTackle"),
            "cartoes_amarelos":          v("yellowCards"),
            "cartoes_vermelhos":         v("redCards"),
            "distancia_coberta":         v("kilometersCovered"),
            "sprints":                   v("numberOfSprints"),
            "chutes_no_gol":             v("shotsOnGoal"),
            "chutes_fora":               v("shotsOffGoal"),
            "chutes_bloqueados":         v("blockedScoringAttempt"),
            "chutes_dentro_area":        v("totalShotsInsideBox"),
            "chutes_fora_area":          v("totalShotsOutsideBox"),
            "trave":                     v("hitWoodwork"),
            "grandes_chances_marcadas":  v("bigChanceScored"),
            "grandes_chances_perdidas":  v("bigChanceMissed"),
            "toques_area_penalti":       v("touchesInPenaltyBox"),
            "impedimentos":              v("offsides"),
            "passes_profundidade":       v("throughBalls"),
            "faltas_sofridas_terco":     v("fouledFinalThird"),
            "passes_certos":             v("accuratePasses"),
            "entradas_terco_final":      v("finalThirdEntries"),
            "bolas_longas_certas":       v("accurateLongBalls"),
            "bolas_longas_total":        t("accurateLongBalls"),
            "cruzamentos_certos":        v("accurateCross"),
            "cruzamentos_total":         t("accurateCross"),
            "arremessos_lateral":        v("throwIns"),
            "duelos_vencidos":           v("duelWonPercent"),
            "duelos_terrestres_venc":    v("groundDuelsPercentage"),
            "duelos_terrestres_total":   t("groundDuelsPercentage"),
            "duelos_aereos_venc":        v("aerialDuelsPercentage"),
            "duelos_aereos_total":       t("aerialDuelsPercentage"),
            "dribles_venc":              v("dribblesPercentage"),
            "dribles_total":             t("dribblesPercentage"),
            "perdas_bola":               v("dispossessed"),
            "desarmes_vencidos":         v("wonTacklePercent"),
            "desarmes_total":            t("wonTacklePercent"),
            "interceptacoes":            v("interceptionWon"),
            "recuperacoes":              v("ballRecovery"),
            "cortes":                    v("totalClearance"),
            "erros_que_geraram_chute":   v("errorLeadToShot"),
            "erros_que_geraram_gol":     v("errorLeadToGoal"),
            "defesas_total":             v("goalkeeperSaves"),
            "gols_evitados":             v("goalsPrevented"),
            "defesas_grandes":           v("bigSaves"),
            "bolas_altas":               v("highClaims"),
            "socos":                     v("punches"),
            "tiros_de_meta":             v("goalKicks"),
        })
    return linhas

# =====================================================
# UPSERTS
# =====================================================

def upsert_liga(cur, ev):
    ut  = ev.get("tournament", {}).get("uniqueTournament", {})
    cat = ut.get("category", {})
    cur.execute("""
        INSERT INTO ligas (id, nome, slug, categoria, pais)
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE nome=VALUES(nome)
    """, (ut.get("id"), ut.get("name"), ut.get("slug"),
          cat.get("name"), cat.get("country", {}).get("name")))
    return ut.get("id")

def upsert_temporada(cur, ev, liga_id):
    s = ev.get("season", {})
    cur.execute("""
        INSERT INTO temporadas (id, liga_id, nome, ano)
        VALUES (%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE nome=VALUES(nome)
    """, (s.get("id"), liga_id, s.get("name"), s.get("year")))
    return s.get("id")

def upsert_time(cur, team):
    c = team.get("teamColors", {})
    cur.execute("""
        INSERT INTO times (id, nome, nome_curto, slug, pais, cor_primaria, cor_secundaria)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE nome=VALUES(nome)
    """, (team.get("id"), team.get("name"), team.get("shortName"),
          team.get("slug"), team.get("country", {}).get("name"),
          c.get("primary"), c.get("secondary")))

def upsert_jogo(cur, ev, liga_id, temporada_id):
    venue  = ev.get("venue", {})
    ri     = ev.get("roundInfo", {})
    ts     = ev.get("startTimestamp", 0)
    data   = datetime.datetime.fromtimestamp(ts).date() if ts else None
    cur.execute("""
        INSERT INTO jogos (id, liga_id, temporada_id, fase, data,
            time_casa_id, time_visitante_id, gols_casa, gols_visitante,
            vencedor, estadio, cidade, arbitro, publico)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE gols_casa=VALUES(gols_casa), gols_visitante=VALUES(gols_visitante)
    """, (
        ev.get("id"), liga_id, temporada_id, ri.get("name"), data,
        ev.get("homeTeam", {}).get("id"), ev.get("awayTeam", {}).get("id"),
        ev.get("homeScore", {}).get("current"), ev.get("awayScore", {}).get("current"),
        ev.get("winnerCode"),
        venue.get("name"), venue.get("city", {}).get("name"),
        ev.get("referee", {}).get("name"), ev.get("attendance"),
    ))
    return ev.get("id")

def salvar_stats(cur, tabela, jogo_id, time_id, linhas):
    ins = ign = 0
    for l in linhas:
        try:
            cols         = ", ".join(l.keys())
            placeholders = ", ".join(["%s"] * len(l))
            cur.execute(f"""
                INSERT INTO `{tabela}` (jogo_id, time_id, {cols})
                VALUES (%s, %s, {placeholders})
            """, [jogo_id, time_id] + list(l.values()))
            ins += 1
        except mysql.connector.errors.IntegrityError:
            ign += 1
    return ins, ign

# =====================================================
# MAIN
# =====================================================

# =====================================================
# ARGUMENTOS: python sofascore_coletor.py "nome" escolha "dd/mm/yyyy" "dd/mm/yyyy"
# Quando chamado pelo rodar.py os args são passados direto
# Quando chamado manualmente, pede interativamente
# =====================================================

print("="*50)
print("  SOFASCORE COLETOR")
print("="*50)

args = sys.argv[1:]  # [nome, escolha, data_ini, data_fim]

if len(args) >= 1:
    nome = args[0].strip()
else:
    nome = input("\nDigite o nome do time: ").strip()

if len(args) >= 2:
    _escolha_arg = args[1].strip()
else:
    _escolha_arg = None

if len(args) >= 3:
    data_ini_str = args[2].strip()
else:
    data_ini_str = input("Data início [01/01/2026]: ").strip() or "01/01/2026"

if len(args) >= 4:
    data_fim_str = args[3].strip()
else:
    data_fim_str = input("Data fim    [hoje]:       ").strip()

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
print(f"  Temporadas aceitas: {TEMPORADAS_VALIDAS}")

print("\nConectando ao banco...")
setup_banco()

print("Abrindo navegador...")
options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors")
options.add_argument("--allow-insecure-localhost")
driver = uc.Chrome(options=options, version_main=153)
driver.get("https://www.sofascore.com/")

# Espera a página carregar completamente antes de fazer fetch
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
try:
    WebDriverWait(driver, 20).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
except:
    pass
time.sleep(5)  # extra para JS terminar de inicializar

print(f"\nBuscando: {nome}")
time_obj = buscar_time(driver, nome, _escolha_arg if "_escolha_arg" in dir() else None)
if not time_obj:
    driver.quit()
    exit()

team_id   = time_obj["id"]
team_name = time_obj["name"]
team_slug = time_obj.get("slug", team_name.lower().replace(" ", "-"))
print(f"\nTime: {team_name} (slug={team_slug})")

# Modo incremental — verifica último jogo salvo no banco
con_inc = conectar()
cur_inc = con_inc.cursor()
ULTIMA_DATA = ultima_data_salva(cur_inc, team_slug)
con_inc.close()

if ULTIMA_DATA:
    print(f"Último jogo no banco: {ULTIMA_DATA} — buscando apenas jogos posteriores")
else:
    print("Nenhum jogo no banco — coleta completa")



jogos = todos_jogos_temporada(driver, team_id, data_minima=ULTIMA_DATA)
print(f"Total: {len(jogos)} jogos encontrados")

con = conectar()
cur = con.cursor()

# Cria tabela com nome do time
tabela = criar_tabela_time(cur, team_slug)
con.commit()
print(f"Tabela de stats: `{tabela}`")

total_ins = total_ign = 0

for i, jogo_resumo in enumerate(jogos, 1):
    casa      = jogo_resumo.get("homeTeam", {}).get("name", "?")
    visitante = jogo_resumo.get("awayTeam", {}).get("name", "?")
    sc_h      = jogo_resumo.get("homeScore", {}).get("current", "-")
    sc_a      = jogo_resumo.get("awayScore", {}).get("current", "-")
    ts        = jogo_resumo.get("startTimestamp", 0)
    data_dt   = datetime.datetime.fromtimestamp(ts).date() if ts else None
    data      = data_dt.strftime("%d/%m/%Y") if data_dt else "?"
    liga      = jogo_resumo.get("tournament", {}).get("uniqueTournament", {}).get("name", "?")

    # Modo incremental — pula jogos já salvos
    if ULTIMA_DATA and data_dt and data_dt <= ULTIMA_DATA:
        print(f"\n  [{i}/{len(jogos)}] {data} | {liga} — já no banco, pulando")
        continue

    print(f"\n  [{i}/{len(jogos)}] {data} | {liga}")
    print(f"  {casa} {sc_h} x {sc_a} {visitante}")

    # Detalhes completos do evento
    ev_data = api_get(driver, f"/event/{jogo_resumo['id']}")
    if not ev_data or "event" not in ev_data:
        print("  Sem detalhes — pulando")
        continue
    ev = ev_data["event"]

    liga_id      = upsert_liga(cur, ev)
    temporada_id = upsert_temporada(cur, ev, liga_id)
    upsert_time(cur, ev["homeTeam"])
    upsert_time(cur, ev["awayTeam"])
    jogo_id = upsert_jogo(cur, ev, liga_id, temporada_id)

    side = "home" if ev.get("homeTeam", {}).get("id") == team_id else "away"

    stats_data = api_get(driver, f"/event/{jogo_resumo['id']}/statistics")
    if stats_data and "statistics" in stats_data:
        linhas = extrair_stats(stats_data, side)
        # Enriquece cada linha com info do jogo
        ts   = ev.get("startTimestamp", 0)
        liga_nome = ev.get("tournament", {}).get("uniqueTournament", {}).get("name", "-")
        fase_nome = ev.get("roundInfo", {}).get("name", "-")
        for l in linhas:
            l["data"]           = datetime.datetime.fromtimestamp(ts).date() if ts else None
            l["liga"]           = liga_nome
            l["fase"]           = fase_nome
            l["time_casa"]      = ev.get("homeTeam", {}).get("name", "-")
            l["time_visitante"] = ev.get("awayTeam", {}).get("name", "-")
            l["gols_casa"]      = ev.get("homeScore", {}).get("current")
            l["gols_visitante"] = ev.get("awayScore", {}).get("current")
        ins, ign = salvar_stats(cur, tabela, jogo_id, team_id, linhas)
        total_ins += ins
        total_ign += ign
        print(f"  {ins} período(s) salvos | {ign} já existiam")
    else:
        print("  Sem stats disponíveis")

    con.commit()
    time.sleep(0.4)

con.close()
driver.quit()

print(f"\n{'='*50}")
print(f"  CONCLUÍDO")
print(f"  Time             : {team_name}")
print(f"  Tabela criada    : `{tabela}`")
print(f"  Jogos processados: {len(jogos)}")
print(f"  Registros salvos : {total_ins}")
print(f"  Já existiam      : {total_ign}")
print(f"{'='*50}")