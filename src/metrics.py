# src/metrics.py
# Etapa final do sistema: métricas (o "placar" do experimento).
#
#  - BER: fração de bits recebidos com erro = bits errados / bits enviados
#  - posições dos bits incorretos (o enunciado pede para identificá-los)
#  - eficiência espectral nominal, em bits por segundo por Hz (bits/s/Hz)
#
# Eficiência espectral NOMINAL: considera 1 símbolo por segundo para cada Hz de banda
# (caso ideal) e ignora filtros reais. Então vale:
#     eficiência = bits por símbolo / chips por bit
#  - BPSK carrega 1 bit por símbolo, QPSK 2 e 16-QAM 4.
#  - O Manchester usa 2 chips por bit, então a taxa útil cai pela metade.
#  - O NRZ-I usa 1 chip por bit, então a taxa útil não muda.

import numpy as np
from src.modulation import bits_por_simbolo


CHIPS_POR_BIT = {"MANCHESTER": 2, "NRZI": 1}


def contar_erros(bits_enviados, bits_recebidos):
    """Conta em quantas posições o bit recebido é diferente do enviado."""
    enviados = np.array(bits_enviados)
    recebidos = np.array(bits_recebidos)
    if len(enviados) != len(recebidos):
        raise ValueError("Os dois vetores precisam ter o mesmo tamanho")
    return int(np.sum(enviados != recebidos))


def calcular_ber(bits_enviados, bits_recebidos):
    """BER = bits errados / total de bits enviados (um número entre 0 e 1)."""
    erros = contar_erros(bits_enviados, bits_recebidos)
    return erros / len(bits_enviados)


def posicoes_dos_erros(bits_enviados, bits_recebidos):
    """Devolve a lista com as posições (começando em 0) dos bits incorretos."""
    enviados = np.array(bits_enviados)
    recebidos = np.array(bits_recebidos)
    if len(enviados) != len(recebidos):
        raise ValueError("Os dois vetores precisam ter o mesmo tamanho")
    posicoes = []
    for i in range(len(enviados)):
        if enviados[i] != recebidos[i]:
            posicoes.append(i)
    return posicoes


def letras_erradas(texto_original, texto_recebido):
    """Devolve as posições das letras que chegaram diferentes.
    Serve para mostrar na demonstração como o erro de bits estraga a mensagem."""
    posicoes = []
    for i in range(min(len(texto_original), len(texto_recebido))):
        if texto_original[i] != texto_recebido[i]:
            posicoes.append(i)
    return posicoes


def eficiencia_espectral(modulacao, codificacao):
    """Eficiência espectral nominal em bits/s/Hz.
    modulacao: "BPSK", "QPSK" ou "16QAM" | codificacao: "MANCHESTER" ou "NRZI"."""
    if codificacao not in CHIPS_POR_BIT:
        raise ValueError("Codificação desconhecida: " + str(codificacao))
    return bits_por_simbolo(modulacao) / CHIPS_POR_BIT[codificacao]
