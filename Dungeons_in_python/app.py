from historia_padrao import contar_historia
import mysql.connector

# Conectar com o banco
conexao = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root',
    database='jogo'
)
cursor = conexao.cursor(dictionary=True)

# Função para listar os tipos de personagem disponíveis
def listar_tipos():
    cursor.execute("SELECT * FROM tipos_personagem")
    tipos = cursor.fetchall()

    print("\nEscolha seu personagem:")
    print("-" * 50)
    for t in tipos:
        print(f"{t['id']} - {t['nome']:<10} | For: {t['forca']} Int: {t['inteligencia']} Des: {t['destreza']} "
              f"Def: {t['defesa']} Vida: {t['vida']} Mana: {t['mana']} Vel: {t['velocidade']}")
    return tipos

# Função para criar novo jogador com história
def novo_jogo():
    nome_jogador = input("Digite o nome do seu personagem: ")

    # Mostrar história com base no nome
    historia = contar_historia(nome_jogador)
    print(historia)

    # Jogador escolhe o tipo
    tipos = listar_tipos()
    try:
        escolha = int(input("\nDigite o número do personagem escolhido: "))
    except ValueError:
        print("❌ Entrada inválida. Digite um número.")
        return

    tipo = next((t for t in tipos if t['id'] == escolha), None)

    if tipo:
        sql = """
        INSERT INTO jogadores (
            nome_jogador, personagem_id, nome_personagem,
            forca, inteligencia, destreza, defesa,
            vida, mana, velocidade, nivel, experiencia
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            nome_jogador,
            tipo['id'],
            tipo['nome'],
            tipo['forca'],
            tipo['inteligencia'],
            tipo['destreza'],
            tipo['defesa'],
            tipo['vida'],
            tipo['mana'],
            tipo['velocidade'],
            1,  # nível inicial
            0   # experiência inicial
        )
        cursor.execute(sql, valores)
        conexao.commit()

        print(f"\n✅ Personagem '{nome_jogador}' criado com sucesso como um {tipo['nome']}!")
    else:
        print("❌ Tipo inválido.")

# Função para continuar jogo com personagens já salvos
def continuar_jogo():
    cursor.execute("""
        SELECT j.id, j.nome_jogador, j.nome_personagem, j.nivel,
               j.vida, j.mana, j.forca, j.inteligencia, j.destreza, j.defesa, j.velocidade, j.experiencia
        FROM jogadores j
    """)
    jogadores = cursor.fetchall()

    if not jogadores:
        print("\nNenhum jogador salvo ainda.")
        return

    print("\nJogadores salvos:")
    print(f"{'ID':<3} | {'Nome':<15} | {'Classe':<12} | {'Nv':<3} | Vida | Mana | For | Int | Des | Def | Vel | XP")
    print("-" * 90)
    for j in jogadores:
        print(f"{j['id']:<3} | {j['nome_jogador']:<15} | {j['nome_personagem']:<12} | {j['nivel']:<3} | "
              f"{j['vida']:<4} | {j['mana']:<4} | {j['forca']:<3} | {j['inteligencia']:<3} | {j['destreza']:<3} | "
              f"{j['defesa']:<3} | {j['velocidade']:<3} | {j['experiencia']}")

    try:
        id_escolhido = int(input("\nDigite o ID do jogador para continuar: "))
    except ValueError:
        print("❌ Entrada inválida.")
        return

    jogador = next((j for j in jogadores if j['id'] == id_escolhido), None)

    if jogador:
        print(f"\n🎮 Continuando jogo com {jogador['nome_jogador']} o {jogador['nome_personagem']} (Nv {jogador['nivel']})!")
        # Aqui você pode continuar a aventura com os dados do jogador
    else:
        print("❌ ID inválido.")

# Menu principal
def menu():
    while True:
        print("\n----- DUNGEONS IN PYTHON -----")
        print("1 - Novo Jogo")
        print("2 - Continuar")
        print("3 - Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == '1':
            novo_jogo()
        elif opcao == '2':
            continuar_jogo()
        elif opcao == '3':
            print("Até logo, aventureiro!")
            break
        else:
            print("❌ Opção inválida.")

# Rodar o menu
menu()

# Fechar conexão ao fim do programa
cursor.close()
conexao.close()
