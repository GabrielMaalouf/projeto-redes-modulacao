# src/channel.py
# Etapa 4 do sistema: canal ruidoso.
#
# Dois cenários:
#  1) AWGN: ruído gaussiano branco aditivo, com a SNR controlada por Eb/N0 (em dB).
#  2) Rajadas: o canal alterna entre um estado BOM (SNR nominal) e um estado RUIM
#     (SNR nominal menos 10 dB). Isso é uma DEGRADAÇÃO ADICIONAL do canal: os erros
#     aparecem agrupados, como em uma interferência que liga e desliga.
#
# Definição de SNR usada no trabalho:
#  - Eb/N0 é a energia por bit transmitido (por chip, pois o Manchester envia 2 chips
#    por bit) dividida pela densidade de ruído.
#  - Como os símbolos têm energia média 1 (contrato com o modulation.py):
#        Es/N0 = Eb/N0 * bits_por_simbolo
#        variância do ruído por eixo (I e Q) = 1 / (2 * Es/N0)
#
# As duas funções devolvem (recebidos, estados):
#  - recebidos: símbolos com ruído (mesmo tamanho dos símbolos enviados)
#  - estados:   0 = estado bom, 1 = estado ruim (no AWGN é sempre 0)

import math
import numpy as np


# Parâmetros das rajadas (ficam registrados aqui e no README)
PROB_BOM_PARA_RUIM = 0.01     # chance de, a cada símbolo, o canal passar de bom para ruim
PROB_RUIM_PARA_BOM = 0.1      # chance de, a cada símbolo, o canal voltar de ruim para bom
QUEDA_SNR_RUIM_DB = 10        # no estado ruim a SNR cai 10 dB


def desvio_do_ruido(ebn0_db, bits_por_simbolo):
    """Desvio padrão do ruído em cada eixo (I e Q), para símbolos de energia média 1."""
    ebn0 = 10 ** (ebn0_db / 10)             # de dB para escala linear
    es_n0 = ebn0 * bits_por_simbolo         # energia por símbolo / ruído
    variancia = 1 / (2 * es_n0)
    return math.sqrt(variancia)


def gerar_ruido_unitario(quantidade, gerador):
    """Ruído complexo com desvio 1 em cada eixo. Depois é só multiplicar pelo desvio."""
    parte_i = gerador.standard_normal(quantidade)
    parte_q = gerador.standard_normal(quantidade)
    return parte_i + 1j * parte_q


def gerar_estados_rajadas(quantidade, gerador,
                          p_bom_ruim=PROB_BOM_PARA_RUIM,
                          p_ruim_bom=PROB_RUIM_PARA_BOM):
    """Sorteia o estado do canal em cada símbolo (0 = bom, 1 = ruim).
    A cada símbolo, o estado pode mudar com as probabilidades dadas
    (cadeia de Markov de 2 estados). O canal começa no estado bom."""
    sorteios = gerador.random(quantidade)
    estados = np.zeros(quantidade, dtype=int)
    estado = 0
    for i in range(quantidade):
        if estado == 0:
            if sorteios[i] < p_bom_ruim:
                estado = 1
        else:
            if sorteios[i] < p_ruim_bom:
                estado = 0
        estados[i] = estado
    return estados


def canal_awgn(simbolos, ebn0_db, bits_por_simbolo, seed):
    """Canal AWGN: soma ruído gaussiano com a mesma variância em todos os símbolos."""
    gerador = np.random.default_rng(seed)
    desvio = desvio_do_ruido(ebn0_db, bits_por_simbolo)
    ruido = gerar_ruido_unitario(len(simbolos), gerador) * desvio
    recebidos = simbolos + ruido
    estados = np.zeros(len(simbolos), dtype=int)
    return recebidos, estados


def canal_rajadas(simbolos, ebn0_db, bits_por_simbolo, seed):
    """Canal com rajadas: no estado bom o ruído é o do AWGN (SNR nominal);
    no estado ruim a SNR é 10 dB menor, ou seja, o ruído é mais forte.
    Com a mesma seed, o ruído sorteado é o mesmo do canal_awgn: a única
    diferença é que, no estado ruim, ele é amplificado. Isso deixa a comparação justa."""
    gerador = np.random.default_rng(seed)
    ruido_unitario = gerar_ruido_unitario(len(simbolos), gerador)
    estados = gerar_estados_rajadas(len(simbolos), gerador)

    desvio_bom = desvio_do_ruido(ebn0_db, bits_por_simbolo)
    desvio_ruim = desvio_do_ruido(ebn0_db - QUEDA_SNR_RUIM_DB, bits_por_simbolo)

    desvios = np.where(estados == 1, desvio_ruim, desvio_bom)   # um desvio por símbolo
    recebidos = simbolos + ruido_unitario * desvios
    return recebidos, estados


def aplicar_canal(simbolos, canal, ebn0_db, bits_por_simbolo, seed):
    """Escolhe o canal pelo nome: "AWGN" ou "RAJADAS"."""
    if canal == "AWGN":
        return canal_awgn(simbolos, ebn0_db, bits_por_simbolo, seed)
    elif canal == "RAJADAS":
        return canal_rajadas(simbolos, ebn0_db, bits_por_simbolo, seed)
    else:
        raise ValueError("Canal desconhecido: " + str(canal))
