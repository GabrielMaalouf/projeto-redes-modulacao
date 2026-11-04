# src/message.py
# Etapa 1 do sistema: gerar a mensagem ASCII e convertê-la em bits (e o caminho inverso).

import numpy as np


def texto_para_bits(texto):
    """Converte um texto em uma lista de bits (0 e 1).
    Cada caractere vira 8 bits, usando a tabela ASCII."""
    bits = []
    for caractere in texto:
        codigo = ord(caractere)           # número do caractere na tabela ASCII ('A' -> 65)
        binario = format(codigo, "08b")   # 65 -> '01000001' (sempre 8 dígitos)
        for digito in binario:
            bits.append(int(digito))      # '0' -> 0 e '1' -> 1
    return np.array(bits, dtype=int)


def bits_para_texto(bits):
    """Converte uma lista de bits de volta para texto.
    Pega os bits de 8 em 8 e transforma cada grupo em um caractere."""
    texto = ""
    for inicio in range(0, len(bits) - 7, 8):
        grupo = bits[inicio:inicio + 8]
        codigo = 0
        for b in grupo:
            codigo = codigo * 2 + int(b)  # monta o número a partir dos bits
        # Se houve erro de bit, o código pode cair fora dos caracteres imprimíveis.
        # Nesse caso mostramos '?' para não quebrar a exibição.
        if 32 <= codigo <= 126:
            texto += chr(codigo)
        else:
            texto += "?"
    return texto


def repetir_bits(bits, quantidade):
    """Repete a mensagem até ter 'quantidade' bits.
    Serve para chegar nos 100.000 bits exigidos nos experimentos."""
    resultado = []
    while len(resultado) < quantidade:
        resultado.extend(bits)
    return np.array(resultado[:quantidade], dtype=int)