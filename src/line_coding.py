# src/line_coding.py
# Etapa 2 do sistema: codificação de linha (Manchester e AMI).
#
# CODIFICAÇÃO DE LINHA x CODIFICAÇÃO DE CORREÇÃO DE ERROS
#  - Linha: escolhe COMO os bits viram níveis/transições de sinal (sincronismo,
#    ausência de nível DC). Não adiciona redundância para corrigir erros.
#  - Correção de erros (Hamming, Reed-Solomon...): ADICIONA bits de redundância
#    para detectar e corrigir bits errados.
#
# Como cada código entra no sistema:
#  - Manchester: a saída é binária (chips 0/1) e segue para os moduladores
#    (BPSK, QPSK, 16-QAM). Cada bit vira 2 chips, então a taxa útil cai pela metade.
#    A SNR (Eb/N0) é definida por chip transmitido, e a BER é medida nos bits
#    decodificados.
#  - AMI: a saída é ternária (+1, 0, -1) e NÃO passa pelos moduladores. Ela é
#    avaliada em banda base: codificar -> somar ruído AWGN -> decidir -> decodificar.

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


# ---------- AMI ----------

def ami_codificar(bits):
    """bit 0 -> nível 0 | bit 1 -> alterna entre +1 e -1."""
    niveis = []
    ultimo = -1          # começa em -1 para o primeiro '1' sair +1
    for b in bits:
        if b == 0:
            niveis.append(0)
        else:
            ultimo = -ultimo      # inverte a polaridade
            niveis.append(ultimo)
    return np.array(niveis, dtype=int)


def ami_decidir(sinal, limiar=0.5):
    """Decisão por limiares: transforma o sinal ruidoso (números reais)
    em níveis -1, 0 ou +1.
        sinal >  limiar  -> +1
        sinal < -limiar  -> -1
        caso contrário   ->  0
    Usada depois do canal AWGN em banda base, antes de ami_decodificar()."""
    niveis = []
    for valor in sinal:
        if valor > limiar:
            niveis.append(1)
        elif valor < -limiar:
            niveis.append(-1)
        else:
            niveis.append(0)
    return np.array(niveis, dtype=int)


def ami_decodificar(niveis):
    """Nível 0 -> bit 0 | nível +1 ou -1 -> bit 1.
    Também detecta violações: dois '1' seguidos com a mesma polaridade.
    Devolve (bits, violacoes), onde 'violacoes' é a lista de posições."""
    bits = []
    violacoes = []
    ultimo = 0           # última polaridade vista (0 = ainda nenhuma)
    for i in range(len(niveis)):
        n = niveis[i]
        if n == 0:
            bits.append(0)
        else:
            bits.append(1)
            if n == ultimo:
                violacoes.append(i)
            ultimo = n
    return np.array(bits, dtype=int), violacoes
