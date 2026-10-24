import pygame
import time
import random

# Inicializando o pygame
pygame.init()

# Cores
preto = (0, 0, 0)
vermelho = (213, 50, 80)
verde = (0, 255, 0)
verde_1 = (170, 215, 81)
verde_2 = (162, 209, 73)
branco = (255, 255, 255)
azul = (70, 130, 180)

# Tamanho da grade do jogo
tamanho_bloco = 20
blocos_x = 17
blocos_y = 17

grade_largura = blocos_x * tamanho_bloco
grade_altura = blocos_y * tamanho_bloco

# Margem ao redor do campo
margem = 50
largura = grade_largura + margem * 2
altura = grade_altura + margem * 2

# Tela
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption('Jogo da Cobrinha')

# Controle de FPS
clock = pygame.time.Clock()
velocidade = 10

# Fonte
fonte = pygame.font.SysFont("bahnschrift", 25)

def mostrar_pontuacao(pontos):
    texto = fonte.render("Pontos: " + str(pontos), True, verde)
    tela.blit(texto, [10, 10])  # canto superior esquerdo da tela

def desenhar_cobrinha(lista):
    for x in lista:
        pygame.draw.rect(tela, preto, [x[0], x[1], tamanho_bloco, tamanho_bloco])

def desenhar_fundo_xadrez():
    for linha in range(blocos_y):
        for coluna in range(blocos_x):
            x = margem + coluna * tamanho_bloco
            y = margem + linha * tamanho_bloco
            cor = verde_1 if (linha + coluna) % 2 == 0 else verde_2
            pygame.draw.rect(tela, cor, (x, y, tamanho_bloco, tamanho_bloco))

def gerar_posicao_comida():
    col = random.randint(0, blocos_x - 1)
    lin = random.randint(0, blocos_y - 1)
    return margem + col * tamanho_bloco, margem + lin * tamanho_bloco

def game_loop():
    game_over = False
    game_close = False

    x1 = margem + (blocos_x // 2) * tamanho_bloco
    y1 = margem + (blocos_y // 2) * tamanho_bloco

    x1_mudanca = 0
    y1_mudanca = 0

    corpo_cobra = []
    comprimento = 1

    comida_x, comida_y = gerar_posicao_comida()

    while not game_over:

        while game_close:
            tela.fill(azul)
            desenhar_fundo_xadrez()
            msg = fonte.render("Você perdeu! C = continuar | Q = sair", True, vermelho)
            tela.blit(msg, [largura / 10, altura / 2])
            mostrar_pontuacao(comprimento - 1)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    elif event.key == pygame.K_c:
                        game_loop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x1_mudanca = -tamanho_bloco
                    y1_mudanca = 0
                elif event.key == pygame.K_RIGHT:
                    x1_mudanca = tamanho_bloco
                    y1_mudanca = 0
                elif event.key == pygame.K_UP:
                    y1_mudanca = -tamanho_bloco
                    x1_mudanca = 0
                elif event.key == pygame.K_DOWN:
                    y1_mudanca = tamanho_bloco
                    x1_mudanca = 0

        x1 += x1_mudanca
        y1 += y1_mudanca

        # Verifica se bateu na parede (dentro da grade)
        if (x1 < margem or x1 >= margem + grade_largura or
            y1 < margem or y1 >= margem + grade_altura):
            game_close = True

        # Preenche toda a tela com uma cor de fundo
        tela.fill(azul)
        desenhar_fundo_xadrez()
        pygame.draw.rect(tela, vermelho, [comida_x, comida_y, tamanho_bloco, tamanho_bloco])

        cabeca = [x1, y1]
        corpo_cobra.append(cabeca)

        if len(corpo_cobra) > comprimento:
            del corpo_cobra[0]

        for x in corpo_cobra[:-1]:
            if x == cabeca:
                game_close = True

        desenhar_cobrinha(corpo_cobra)
        mostrar_pontuacao(comprimento - 1)

        pygame.display.update()

        if x1 == comida_x and y1 == comida_y:
            comida_x, comida_y = gerar_posicao_comida()
            comprimento += 1

        clock.tick(velocidade)

    pygame.quit()
    quit()

# Iniciar jogo
game_loop()
