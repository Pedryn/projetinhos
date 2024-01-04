vitorias = 0
empates = 0
derrotas = 0

def play_again():
    return input('Deseja jogar novamente? S/N? ').lower() in ['y', 'yes', 's', 'sim', 'por favor']

while True:
    from random import randint
    from time import sleep

    itens = ('Pedra', 'Papel', 'Tesoura')
    itensvc = (''' 
        _______
    ---'   ____)
          (_____)
          (_____)
          (____)
    ---.__(___)
    ''',
    '''
        _______
    ---'   ____)____
              ______)
              _______)
             _______)
    ---.__________)
    ''',
    '''
        _______
    ---'   ____)____
              ______)
           __________)
          (____)
    ---.__(___)
    ''')

    itenspc = (''' 
      _______
     (____   '---
    (_____)
    (_____)
     (____)
      (___)__.---
    ''',
    '''
           _______
      ____(____   '---
     (_____
    (______
     (______
       (__________.---
    ''',
    '''
           _______
      ____(____   '---
     (______
    (__________
          (____)
           (___)__.---
    ''' )

    def obter_jogada_usuario():
        while True:
            try:
                vc = int(input('Sua Jogada vai ser?: '))
                if 0 <= vc <= 2:
                    return vc
                else:
                    print('Jogada inválida. Digite um número entre 0 e 2.')
            except ValueError:
                print('Entrada inválida. Digite um número válido.')

    pc = randint(0, 2)

    print('''Suas opções:
    [0] Pedra;
    [1] Papel;
    [2] Tesoura''')

    vc = obter_jogada_usuario()

    print('JO')
    sleep(1)
    print('KEN')
    sleep(1)
    print('PO!!!')
    print('-='*11)
    print('Você escolheu {}'.format(itensvc[vc]))
    print('O computador escolheu {}'.format(itenspc[pc]))
    print('-='*11)
    
    if pc == vc:
        print('Empate')
        empates += 1
    elif (pc - vc == 1) or (pc - vc == -2):
        print('Você Ganhou')
        vitorias += 1
    else:
        print('Computador Ganhou')
        derrotas += 1
        
    print(f'\nPLACAR \nVitorias:{vitorias} \nDerrotas:{derrotas} \nEmpates {empates}')

    if not play_again():
        break
