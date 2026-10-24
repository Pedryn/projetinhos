def calcular_apostas(odd1, odd2, valor_total):
    inv1 = 1 / odd1
    inv2 = 1 / odd2
    soma_inversos = inv1 + inv2

    aposta1 = (inv1 / soma_inversos) * valor_total
    aposta2 = (inv2 / soma_inversos) * valor_total

    retorno1 = aposta1 * odd1
    retorno2 = aposta2 * odd2

    print("\n===== Resultado =====")
    print(f"Odd 1: {odd1}")
    print(f"Odd 2: {odd2}")
    print(f"Total apostado: R$ {valor_total:.2f}")
    print(f"Aposte R$ {aposta1:.2f} na odd {odd1}")
    print(f"Aposte R$ {aposta2:.2f} na odd {odd2}")
    print(f"Retorno se ganhar a aposta 1: R$ {retorno1:.2f}")
    print(f"Retorno se ganhar a aposta 2: R$ {retorno2:.2f}")
    print(f"Lucro garantido (mínimo): R$ {min(retorno1, retorno2) - valor_total:.2f}")

# Entradas do usuário
try:
    odd1 = float(input("Digite a primeira odd: "))
    odd2 = float(input("Digite a segunda odd: "))
    valor_total = float(input("Digite o valor total que deseja apostar: "))
    calcular_apostas(odd1, odd2, valor_total)
except ValueError:
    print("Por favor, digite números válidos para as odds e o valor.")
