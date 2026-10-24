import time
import os
import sys
import msvcrt  # só funciona no Windows

def limpar_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def digitar_texto(texto, delay=0.03):
    i = 0
    while i < len(texto):
        if msvcrt.kbhit():
            tecla = msvcrt.getch()
            if tecla == b'\r':  # ENTER
                print(texto[i:], end='', flush=True)
                break
        print(texto[i], end='', flush=True)
        time.sleep(delay)
        i += 1
    print()

def contar_historia(nome):
    historia = [
        f"{nome} era um jovem nada convencional. Enquanto todos estavam vivendo suas vidas, ele passava horas — dias inteiros — trancado no quarto, programando em Python.",
        "Um certo dia, teve uma ideia genial (ou nem tanto): criar um jogo que unisse tudo que ele amava. Assim nasceu *Dungeons in Python*.",
        "Mas algo estranho aconteceu...",
        "*FLASH!*",
        f"{nome}: O quê? Onde eu tô?!",
        "Ele abre os olhos e se vê no meio de um campo verdejante. Ao fundo, uma cidade com torres de pedra. Exatamente como a que ele tinha programado.",
        "O nome dela? **Snakeland**.",
        "Mas agora... não era mais só um jogo. Era real.",
        "Ele caminha confuso até os portões da cidade.",
        "Uma placa diz: **Armazém do Bardo — Armas, Poções e Conversa Fiada**.",
        f"{nome}: Acho que vale a pena dar uma olhada...",
        "???: Ora ora, mais um aventureiro perdido? Me chamo Beedle, o Bardo.",
        "**Bardo**: Mas antes de tudo... diga-me, forasteiro, qual é a sua classe?"
    ]

    for paragrafo in historia:
        limpar_terminal()
        print("\n" + "-" * 60 + "\n")
        digitar_texto(paragrafo)
        input("\n(Pressione ENTER para continuar...)")

