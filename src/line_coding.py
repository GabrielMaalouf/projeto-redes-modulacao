# src/line_coding.py
# Etapa 2 do sistema: codificação de linha (Manchester e NRZ-I).
#
# CODIFICAÇÃO DE LINHA x CODIFICAÇÃO DE CORREÇÃO DE ERROS
#  - Linha: escolhe COMO os bits viram níveis/transições de sinal (sincronismo,
#    ausência de nível DC). Não adiciona redundância para corrigir erros.
#  - Correção de erros (Hamming, Reed-Solomon...): ADICIONA bits de redundância
#    para detectar e corrigir bits errados.
#
# As duas codificações usadas no trabalho têm saída binária (chips 0/1) e seguem
# para os moduladores (BPSK, QPSK, 16-QAM):
#  - Manchester: cada bit vira 2 chips (a taxa útil cai pela metade).
#    Sempre há transição no meio do bit, o que ajuda o sincronismo.
#  - NRZ-I: cada bit vira 1 chip (não aumenta a banda). O bit 1 inverte o nível
#    e o bit 0 mantém. Sequências longas de zeros não têm transição.
#
# A SNR (Eb/N0) é definida por chip transmitido, e a BER é medida nos bits
# decodificados, depois da decodificação de linha.

import numpy as np


# ---------- MANCHESTER ----------

def manchester_codificar(bits):
    """Cada bit vira 2 chips: 0 -> [1, 0] e 1 -> [0, 1].
    A saída tem o dobro do tamanho da entrada."""
    chips = []
    for b in bits:
        if b == 0:
            chips.append(1)
            chips.append(0)
        else:
            chips.append(0)
            chips.append(1)
    return np.array(chips, dtype=int)


def manchester_decodificar(chips):
    """Olha os chips de 2 em 2: [1,0] -> 0 e [0,1] -> 1.
    Se chegar [0,0] ou [1,1], houve erro no canal: guardamos a posição do bit
    e decidimos pelo primeiro chip.
    Devolve (bits, erros), onde 'erros' é a lista de posições (em bits) inválidas."""
    bits = []
    erros = []
    for i in range(0, len(chips) - 1, 2):
        primeiro = chips[i]
        segundo = chips[i + 1]
        if primeiro == 1 and segundo == 0:
            bits.append(0)
        elif primeiro == 0 and segundo == 1:
            bits.append(1)
        else:
            erros.append(i // 2)
            if primeiro == 1:
                bits.append(0)
            else:
                bits.append(1)
    return np.array(bits, dtype=int), erros


# ---------- NRZ-I ----------

def nrzi_codificar(bits):
    """bit 1 -> inverte o nível | bit 0 -> mantém o nível.
    A saída tem o mesmo tamanho da entrada. O nível inicial é 0."""
    niveis = []
    nivel = 0
    for b in bits:
        if b == 1:
            nivel = 1 - nivel      # inverte (0 vira 1 e 1 vira 0)
        niveis.append(nivel)
    return np.array(niveis, dtype=int)


def nrzi_decodificar(niveis):
    """Compara cada nível com o anterior: mudou -> bit 1; igual -> bit 0.
    Como a decodificação é diferencial, um chip errado pode causar até
    2 bits errados (o bit atual e o seguinte)."""
    bits = []
    anterior = 0                   # mesmo nível inicial do codificador
    for n in niveis:
        if n != anterior:
            bits.append(1)
        else:
            bits.append(0)
        anterior = n
    return np.array(bits, dtype=int)
