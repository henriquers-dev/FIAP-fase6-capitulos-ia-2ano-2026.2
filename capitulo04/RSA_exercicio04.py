import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt

# --- 1. Configuração ---
np.random.seed(42)
num_bits = 16

# --- Geração de sequências aleatórias para Alice ---
alice_bits = np.random.randint(2, size=num_bits)
alice_bases = np.random.randint(2, size=num_bits) # 0 para base Z (+), 1 para base X (x)

# --- Geração de bases aleatórias para Bob ---
bob_bases = np.random.randint(2, size=num_bits)

print(f"Bits de Alice:   {alice_bits}")
print(f"Bases de Alice:  {alice_bases} (0=Z, 1=X)")
print(f"Bases de Bob:    {bob_bases} (0=Z, 1=X)")
