import sys
sys.path.append('./metodos')
import mp3, video

def exibir_opcoes():
    print('''BEM VINDO AO DOWLOADER!!!
ESTE PROJETO TEM COMO PROPÓSITO BAIXAR VIDEOS E FOTOS!!
      
1 - mp3 (audio)
2 - mp4 (vídeo)
0 - Sair
''')

escolha = None
exibir_opcoes()

while escolha != 0:
    try:
        escolha = int(input('Qual opção desejada?: '))
        
        if escolha == 1:
            mp3.download()
        elif escolha == 2:
            video.download()
        elif escolha == 0:
            print("Encerrando a aplicação.")
            break
        else:
            print("Opção inválida. Por favor, escolha uma das opções listadas.")
        exibir_opcoes()
        
    except ValueError:
        print("Por favor, insira um número válido.")
