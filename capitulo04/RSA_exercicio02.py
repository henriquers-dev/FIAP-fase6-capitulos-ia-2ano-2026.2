"""
Algoritmo de Shor (simulado) com estimação de fase iterativa.

Em vez de um registrador de 2n qubits de contagem + QFT inversa, usamos
UM único qubit de controle, reaproveitado 2n vezes:

    para k = m-1, ..., 0:
        reset -> H -> (multiplicação por a^(2^k) mod N controlada)
        -> correção de fase condicionada aos bits já medidos -> H -> medir

Total de qubits: n + 1 (n = bits de N), contra 3n no circuito padrão.
"""

import random
import sys
from fractions import Fraction
from math import gcd, log, pi

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit.library import UnitaryGate
from qiskit_aer import AerSimulator


# ----------------------------------------------------------------------
# Utilidades clássicas
# ----------------------------------------------------------------------
def eh_primo(N):
    if N < 2:
        return False
    i = 2
    while i * i <= N:
        if N % i == 0:
            return False
        i += 1
    return True


def potencia_perfeita(N):
    """Se N = b^e (e >= 2), devolve b; senão None."""
    for e in range(2, N.bit_length() + 1):
        b = round(N ** (1 / e))
        for c in (b - 1, b, b + 1):
            if c > 1 and c ** e == N:
                return c
    return None


# ----------------------------------------------------------------------
# Circuito
# ----------------------------------------------------------------------
def multiplicacao_controlada(m, N, n_alvo):
    """
    Porta de (1 + n_alvo) qubits: se o controle (qubit 0) for 1,
    faz |x> -> |m*x mod N>; senão, identidade. Requer gcd(m, N) = 1.
    """
    dim_alvo = 2 ** n_alvo
    U = np.zeros((2 * dim_alvo, 2 * dim_alvo))
    for x in range(dim_alvo):
        saida = (m * x) % N if x < N else x
        U[2 * x, 2 * x] = 1                  # controle = 0
        U[1 + 2 * saida, 1 + 2 * x] = 1      # controle = 1
    return UnitaryGate(U, label=f"C-x{m} mod {N}")


def criar_circuito_shor(a, N):
    """Circuito de estimação de fase iterativa para a ordem de a mod N."""
    n = N.bit_length()
    m = 2 * n                                 # bits de precisão da fase

    ctrl = QuantumRegister(1, "ctrl")
    alvo = QuantumRegister(n, "alvo")
    bits = ClassicalRegister(m, "bits")
    qc = QuantumCircuit(ctrl, alvo, bits)

    qc.x(alvo[0])                             # alvo = |1>

    for t in range(m):
        k = m - 1 - t                         # potência 2^k desta rodada
        qc.reset(ctrl[0])
        qc.h(ctrl[0])

        mult = pow(a, 2 ** k, N)
        if mult != 1:
            qc.append(multiplicacao_controlada(mult, N, n), [ctrl[0], *alvo])

        for s in range(t):
            with qc.if_test((bits[s], 1)):
                qc.p(-pi / 2 ** (t - s), ctrl[0])

        qc.h(ctrl[0])
        qc.measure(ctrl[0], bits[t])

    # bits[0] é o bit menos significativo de y, então int(string, 2) = y
    return qc, m


# ----------------------------------------------------------------------
# Pós-processamento clássico
# ----------------------------------------------------------------------
def fatores_a_partir_da_fase(y, m, a, N):
    """Tenta obter fatores não triviais de N a partir da medida y."""
    if y == 0:
        return None

    r = Fraction(y, 2 ** m).limit_denominator(N).denominator

    # r pode ser só um divisor da ordem: testa seus múltiplos
    for k in range(1, N // r + 1):
        rk = r * k
        if pow(a, rk, N) != 1 or rk % 2:
            continue
        meio = pow(a, rk // 2, N)
        if meio == N - 1:
            continue
        for f in (gcd(meio - 1, N), gcd(meio + 1, N)):
            if 1 < f < N:
                return f, N // f
    return None


def executar_shor(a, N, shots=256):
    qc, m = criar_circuito_shor(a, N)

    sim = AerSimulator()
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()

    ordenados = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    print(f"  qubits: {qc.num_qubits} | medidas distintas: {len(counts)}")
    print("  mais frequentes:", ", ".join(
        f"y={int(b, 2)} ({c / shots:.2f})" for b, c in ordenados[:4]))

    for bits, _ in ordenados:
        y = int(bits, 2)
        achados = fatores_a_partir_da_fase(y, m, a, N)
        if achados:
            print(f"  y = {y} -> fase {y}/{2 ** m} revelou a ordem de {a} mod {N}")
            return achados
    return None


# ----------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------
def fatorar(N, semente=None):
    print(f"--- Algoritmo de Shor (fase iterativa) para N = {N} ---\n")

    if N < 4:
        print("N deve ser >= 4.")
        return None
    if N % 2 == 0:
        print(f"N é par: {N} = 2 x {N // 2}")
        return 2, N // 2
    if eh_primo(N):
        print(f"{N} é primo: não há o que fatorar.")
        return None
    b = potencia_perfeita(N)
    if b:
        print(f"{N} é potência perfeita: {N} = {b}^{round(log(N, b))}")
        return b, N // b

    candidatos = list(range(2, N))
    random.Random(semente).shuffle(candidatos)

    for a in candidatos:
        g = gcd(a, N)
        if g != 1:
            print(f"Sorte! mdc({a}, {N}) = {g}: {N} = {g} x {N // g}")
            return g, N // g

        print(f">>> a = {a}")
        achados = executar_shor(a, N)
        if achados:
            print(f"\nFatores de {N}: {achados[0]} x {achados[1]}")
            return achados
        print("  não funcionou, tentando outro 'a'...")

    print("Nenhum 'a' funcionou.")
    return None


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    fatorar(N)
