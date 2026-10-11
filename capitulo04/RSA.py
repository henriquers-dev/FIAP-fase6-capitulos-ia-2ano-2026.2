# A FRAGILIDADE DA CRIPTOGRAFIA CLÁSSICA:

"""
O Dilema da Troca de Chaves:
    Precisamos de um canal seguro
    para trocar chaves em segurança.
    Mas, se já tivermos um canal
    seguro, não é só usá-lo direta-
    mente para comunicação.
"""

"""
RSA e Fatoração de Inteiros:
    Fatoração em números primos:
        N = p * q
    Suponha que a Alice quer enviar uma
    mensagem para Bob.
"""

mensagem = 7
print(f"Mensagem que a Alice quer enviar: {mensagem}")

"""
Geração de Chaves:
    Primeiro, Bob precisa definir suas chaves:
        A chave pública servirá para que Alice
        criptografe a mensagem antes do envio.

        A chave privada servirá para Bob descriptografar
        a mensagem.

    Ele escolhe dois números primos p e q, para
    que calcule o produto N entre eles.
"""

p = 5
q = 11
n = p * q

print(f"Números escolhidos por Bob:\n p = {p};\t q = {q}")
print(f"\nMódulo da chave pública (N): {n}")

"""
Então, ele deve escolher seu expoente público
e, um número primo entre si ao Totiente de Euler.
    φ(N) = (p - 1) * (q - 1)
"""

def totiente(p, q):
    return (p - 1) * (q - 1)

def mdc(a, b):
    while b:
        a, b = b, a % b
    return a

phi = totiente(p, q)

print(f"Totiente de Euler: φ(N) = {phi}")

"""
Expoente público e:
    1 < e < φ(N)
    mdc(e, φ(N)) = 1

Bob precisa escolher e para que
mdc(e, 40) seja igual a 1.
"""

for i in range(2, 10):
    j = mdc(i, phi)
    print(f"e = {i}\t mdc({i}, {phi}) = {j}", "*" if j == 1 else "")

e = 3

"""
Por fim, ele deve escolher um expoente privado d:
    d * e = 1 mod φ(N)

No exemplo:
    3 * d = 1 mod 40

Computacionalmente, procuramos d tal que o resto seja 1:
"""

for i in range(2, 30):
    r = (e * i) % phi
    print(f"d = {i}\t {e} * {i} % {phi} = {r}", "\t*" if r == 1 else "")

d = 27

"""
As chaves serão:
    Pública: (N, e)
    Privada: d
"""
pub = (n, e)

print(f"A chave pública é {pub}")
print(f"A chave privada é {d}")

# Criptografia:
"""
    Alice deve criptografar sua mensagem M
    com a chave pública (N, e).

Mensagem criptografada c:
    c = M^e mod N
"""

c = pow(mensagem, pub[1], pub[0])

print(f"A mensagem criptografada é {c}")

# Descriptografia:
"""
    Bob recebe a mensagem c e utiliza sua chave
    privada d para descriptografá-la:

        c^d mod N = M
"""

mensagem_descriptografada = pow(c, d, n)

print(
    f"A mensagem descriptografada é {mensagem_descriptografada}, que é",
    "diferente" if mensagem_descriptografada != mensagem else "igual",
    "da mensagem original"
)
