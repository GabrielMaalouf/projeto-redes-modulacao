# src/message.py
# Dois tipos de dados são usados no trabalho:
#  1) Mensagem ASCII real -> usada na DEMONSTRAÇÃO e no TESTE DE CONSISTÊNCIA.
#  2) Bits aleatórios     -> usados na VARREDURA de BER (100.000 bits x várias seeds).


import numpy as np


def texto_para_bits(texto):
    """Converte um texto em um vetor de bits (0 e 1).
    Cada caractere vira 8 bits, usando a tabela ASCII."""
    bits = []
    for caractere in texto:
        codigo = ord(caractere)           # número do caractere na tabela ASCII ('A' -> 65)
        binario = format(codigo, "08b")   # 65 -> '01000001' (sempre 8 dígitos)
        for digito in binario:
            bits.append(int(digito))      # '0' -> 0 e '1' -> 1
    return np.array(bits, dtype=int)


def bits_para_texto(bits):
    """Converte um vetor de bits de volta para texto.
    Pega os bits de 8 em 8 e transforma cada grupo em um caractere.
    Se um erro de bit gerar um caractere não imprimível, mostra '?'."""
    texto = ""
    for inicio in range(0, len(bits) - 7, 8):
        grupo = bits[inicio:inicio + 8]
        codigo = 0
        for b in grupo:
            codigo = codigo * 2 + int(b)  # monta o número a partir dos bits
        if 32 <= codigo <= 126:
            texto += chr(codigo)
        else:
            texto += "?"
    return texto


def gerar_bits_aleatorios(quantidade, seed):
    """Gera 'quantidade' bits aleatórios (0 e 1 com a mesma probabilidade).
    A 'seed' fixa a sequência: a mesma seed sempre gera os mesmos bits,
    o que permite reproduzir o experimento e usar os mesmos bits em todas
    as modulações (comparação justa)."""
    gerador = np.random.default_rng(seed)
    return gerador.integers(0, 2, size=quantidade)


def repetir_bits(bits, quantidade):
    """Repete a mensagem até ter 'quantidade' bits.
    ATENÇÃO: usar apenas em demonstrações (ex.: preencher uma tela).
    NÃO usar na varredura de BER, pois a mensagem ASCII repetida não tem bits
    equiprováveis. Na varredura use gerar_bits_aleatorios()."""
    resultado = []
    while len(resultado) < quantidade:
        resultado.extend(bits)
    return np.array(resultado[:quantidade], dtype=int)
