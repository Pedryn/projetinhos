import subprocess
import sys
import os
import mysql.connector

# =====================================================
# CONFIGURAÇÃO
# =====================================================

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "betizador"

BASE = os.path.dirname(os.path.abspath(__file__))

# =====================================================
# HELPERS
# =====================================================

def conectar():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

def rodar_script(script, args=[]):
    caminho = os.path.join(BASE, script)
    if not os.path.exists(caminho):
        print(f"\n[ERRO] Arquivo não encontrado: {caminho}")
        return False
    print(f"\n{'='*50}")
    resultado = subprocess.run([sys.executable, caminho] + args)
    return resultado.returncode == 0

def time_no_banco(nome):
    """
    Verifica se o time tem dados coletados no banco.
    Não basta estar na tabela times — precisa ter tabela de stats
    com pelo menos 1 registro E tabela de jogadores com jogadores.
    """
    try:
        con = conectar()
        cur = con.cursor()

        # Busca o slug do time
        cur.execute("""
            SELECT id, slug FROM times
            WHERE LOWER(nome) LIKE %s OR LOWER(slug) LIKE %s
            LIMIT 1
        """, (f"%{nome.lower()}%", f"%{nome.lower().replace(' ', '-')}%"))
        res = cur.fetchone()
        if not res:
            con.close()
            return False

        _, slug = res
        if not slug:
            con.close()
            return False

        slug_db = slug.replace("-", "_")

        # Verifica se tabela de stats existe e tem dados
        cur.execute(f"SHOW TABLES LIKE '{slug_db}'")
        if not cur.fetchone():
            con.close()
            return False

        cur.execute(f"SELECT COUNT(*) FROM `{slug_db}`")
        count = cur.fetchone()[0]
        if count == 0:
            con.close()
            return False

        # Verifica se tabela de jogadores existe
        cur.execute(f"SHOW TABLES LIKE '{slug_db}_jogadores'")
        if not cur.fetchone():
            con.close()
            return False

        con.close()
        return True
    except:
        return False

def pedir_parametros_coleta(nome):
    """Pede parâmetros de coleta uma única vez."""
    print(f"\n  Parâmetros para '{nome}':")
    escolha      = input("  Número da escolha do time [1]: ").strip() or "1"
    data_ini_str = input("  Data início [01/01/2025]: ").strip() or "01/01/2025"
    data_fim_str = input("  Data fim    [hoje]:       ").strip() or "17/07/2026"
    return [nome, escolha, data_ini_str, data_fim_str]

def coletar_time(nome, args=None):
    """Roda sofascore_coletor + coletor_jogadores para um time."""
    print(f"\n  Coletando dados de '{nome}'...")

    if args is None:
        args = pedir_parametros_coleta(nome)
    else:
        # Atualiza o nome no args mas mantém os demais parâmetros
        args = [nome] + args[1:]

    print("\n  [1/2] Coletando stats do time...")
    ok1 = rodar_script("sofascore_coletor.py", args)
    if not ok1:
        print("  [ERRO] Falha ao coletar stats do time.")
        return False

    print("\n  [2/2] Coletando stats dos jogadores...")
    ok2 = rodar_script("coletor_jogadores.py", args)
    if not ok2:
        print("  [ERRO] Falha ao coletar stats dos jogadores.")
        return False

    return True

# =====================================================
# OPÇÕES DO MENU
# =====================================================

def opcao_adicionar_time():
    print("\n" + "="*50)
    print("  ADICIONAR TIME")
    print("="*50)
    nome = input("\nNome do time: ").strip()
    coletar_time(nome)

def opcao_atualizar_time():
    print("\n" + "="*50)
    print("  ATUALIZAR STATS DE TIME")
    print("="*50)

    # Lista times disponíveis no banco
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute("SELECT id, nome FROM times ORDER BY nome")
        times = cur.fetchall()
        con.close()
    except:
        times = []

    if times:
        print("\nTimes no banco:")
        for t in times:
            print(f"  {t[1]}")

    nome = input("\nNome do time para atualizar: ").strip()
    coletar_time(nome)

def opcao_odds():
    print("\n" + "="*50)
    print("  COLETAR ODDS DE UM JOGO")
    print("="*50)

    time_casa      = input("\nTime da casa: ").strip()
    time_visitante = input("Time visitante: ").strip()
    data_jogo      = input("Data/hora do jogo [DD/MM/YYYY HH:MM]: ").strip()
    liga           = input("Liga (ex: LaLiga): ").strip()

    # Verifica se os times estão no banco
    casa_ok = time_no_banco(time_casa)
    vis_ok  = time_no_banco(time_visitante)

    if not casa_ok or not vis_ok:
        print("\n[AVISO] Times sem dados no banco:")
        if not casa_ok:
            print(f"  - {time_casa}")
        if not vis_ok:
            print(f"  - {time_visitante}")

        print("\nPreciso coletar os dados antes de gerar o bilhete.")
        print("Parâmetros de coleta (valem para os dois times):")
        escolha      = input("  Número da escolha [1]: ").strip() or "1"
        data_ini_str = input("  Data início [01/01/2025]: ").strip() or "01/01/2025"
        data_fim_str = input("  Data fim    [hoje]:       ").strip()
        if not data_fim_str:
            import datetime
            data_fim_str = datetime.date.today().strftime("%d/%m/%Y")
        args_base = [None, escolha, data_ini_str, data_fim_str]

        if not casa_ok:
            print(f"\n--- Coletando {time_casa} ---")
            ok = coletar_time(time_casa, args_base)
            if not ok:
                print(f"  [AVISO] Falha ao coletar {time_casa}.")

        if not vis_ok:
            print(f"\n--- Coletando {time_visitante} ---")
            ok = coletar_time(time_visitante, args_base)
            if not ok:
                print(f"  [AVISO] Falha ao coletar {time_visitante}.")

        # Calcula pontos dos times recém coletados
        print("\n--- Calculando pontuações ---")
        rodar_script("calcular_pontos.py")

    # Coleta as odds
    print("\n--- Coletando odds ---")
    ok_odds = rodar_script("coletor_odds.py", [time_casa, time_visitante, data_jogo, liga])

    # Gera bilhete automaticamente
    if ok_odds:
        print("\n--- Gerando bilhete ---")
        rodar_script("gerar_bilhete.py", [time_casa, time_visitante, data_jogo, liga])

def opcao_calcular_pontos():
    print("\n" + "="*50)
    print("  CALCULAR PONTUAÇÕES")
    print("="*50)
    rodar_script("calcular_pontos.py")

def opcao_bilhete():
    print("\n" + "="*50)
    print("  GERAR BILHETE")
    print("="*50)
    time_casa      = input("\nTime da casa: ").strip()
    time_visitante = input("Time visitante: ").strip()
    data_jogo      = input("Data/hora do jogo [DD/MM/YYYY HH:MM]: ").strip()
    liga           = input("Liga (ex: LaLiga): ").strip()
    rodar_script("gerar_bilhete.py", [time_casa, time_visitante, data_jogo, liga])

def opcao_bilhete():
    print("\n" + "="*50)
    print("  GERAR BILHETE")
    print("="*50)
    time_casa      = input("\nTime da casa: ").strip()
    time_visitante = input("Time visitante: ").strip()
    data_jogo      = input("Data/hora do jogo [DD/MM/YYYY HH:MM]: ").strip()
    liga           = input("Liga (ex: LaLiga): ").strip()
    rodar_script("gerar_bilhete.py", [time_casa, time_visitante, data_jogo, liga])

# =====================================================
# MENU PRINCIPAL
# =====================================================

def menu():
    while True:
        print("\n" + "="*50)
        print("  BETIZADOR — MENU PRINCIPAL")
        print("="*50)
        print("\n  [1] Adicionar novo time")
        print("  [2] Atualizar stats de um time")
        print("  [3] Coletar odds + gerar bilhete")
        print("  [4] Recalcular pontuações")
        print("  [5] Gerar bilhete (times já no banco)")
        print("  [0] Sair")

        opcao = input("\nEscolha: ").strip()

        if opcao == "1":
            opcao_adicionar_time()
        elif opcao == "2":
            opcao_atualizar_time()
        elif opcao == "3":
            opcao_odds()
        elif opcao == "4":
            opcao_calcular_pontos()
        elif opcao == "5":
            opcao_bilhete()
        elif opcao == "0":
            print("\nAté mais!")
            break
        else:
            print("  Opção inválida.")

if __name__ == "__main__":
    menu()