N = 15
# Escolha de 'a'. a=7 é uma boa escolha para N=15, pois tem período 4.
# Outras boas escolhas são 11, 13. 'a' não pode ter fatores em comum com N.
a = 7

print(f"--- Algoritmo de Shor para Fatorar N = {N} ---")

# --- Parte 1: Checagem Clássica ---
if mdc(a, N) != 1:
    print(f"Sorte! O mdc(a, N) não é 1. Um fator é {mdc(a, N)}.")
else:
    print(f"Escolhido a = {a}. mdc(a, N) = 1. Prosseguindo para a parte quântica.")

    # --- Parte 2: Construção e Simulação do Circuito Quântico ---
    circuito_shor, n_contagem = criar_circuito_shor(a, N)

    # Opcional: Desenhar o circuito
    # print("\nCircuito Quântico de Shor (N=15, a=7):")
    # display(circuito_shor.draw(output='mpl', fold=-1))

    print("\nIniciando a simulação com o Sampler do Qiskit Aer...")
    sampler = Sampler()
    job = sampler.run(circuito_shor, shots=1024)
    result = job.result()

    # --- Parte 3: Pós-processamento ---
    fator1, fator2 = post_processar_resultados(result, n_contagem, N, a)

    if fator1 and fator2:
        print("\n--- SUCESSO! ---")
        print(f"Os fatores de {N} são: {fator1} e {fator2}")
        print(f"Verificação: {fator1} * {fator2} = {fator1 * fator2}")
    else:
        print("\n--- FALHA ---")
        print("Não foi possível encontrar os fatores com a medição obtida. Tente executar novamente ou escolher outro 'a'.")
