# src/theory.py
# Curvas TEÓRICAS de BER em canal AWGN, para comparar com a simulação.
#
# Eb/N0 aqui é por CHIP (mesma definição do channel.py).
#
# 1) Probabilidade de erro de CHIP (antes da decodificação de linha), Gray:
#    BPSK e QPSK : p = Q(sqrt(2 Eb/N0)) = 0.5 erfc(sqrt(Eb/N0))
#    16-QAM      : p ~ (3/8) erfc(sqrt(0.4 Eb/N0))      (aproximação clássica)
#
# 2) Efeito da decodificação de linha sobre a BER dos bits de informação:
#    Manchester (decisão pelo 1º chip quando o par é inválido):
#       o bit sai errado exatamente quando o 1º chip está errado -> BER = p
#       (o 2º chip só serve para DETECTAR o erro, não para corrigi-lo).
#    NRZ-I (decodificação diferencial):
#       o bit sai errado quando exatamente um dos dois chips comparados erra
#       -> BER = 2 p (1 - p)  (aprox. o dobro da BER de chip).
#
# São aproximações: assumem erros de chip independentes. No 16-QAM os 4 bits
# de um símbolo não são totalmente independentes, então pode haver pequena diferença.

import numpy as np
from scipy.special import erfc


def ber_chip_teorica(modulacao, ebn0_db):
    ebn0 = 10 ** (np.array(ebn0_db, dtype=float) / 10)
    if modulacao in ("BPSK", "QPSK"):
        return 0.5 * erfc(np.sqrt(ebn0))
    elif modulacao == "16QAM":
        return (3 / 8) * erfc(np.sqrt(0.4 * ebn0))
    else:
        raise ValueError("Modulação desconhecida: " + str(modulacao))


def ber_teorica(modulacao, codificacao, ebn0_db):
    """BER teórica dos bits de informação, depois da decodificação de linha."""
    p = ber_chip_teorica(modulacao, ebn0_db)
    if codificacao == "MANCHESTER" and modulacao == "16QAM":
        # Caso especial: o Manchester só gera pares complementares (10 ou 01).
        # Cada eixo do 16-QAM recebe (bit de sinal, bit de módulo) = (c, 1-c),
        # então só os níveis -1 e +3 são usados (4 dos 16 pontos!).
        # O bit decodificado depende só do 1º chip (o bit de SINAL):
        #   nível -1 erra se o ruído passar de 1 -> Q(d)
        #   nível +3 erra se o ruído passar de 3 -> Q(3d)
        # com Q(d) = 0.5 erfc(sqrt(0.4 Eb/N0)).
        x = np.sqrt(0.4 * 10 ** (np.array(ebn0_db, dtype=float) / 10))
        return 0.25 * erfc(x) + 0.25 * erfc(3 * x)
    if codificacao == "MANCHESTER":
        return p
    elif codificacao == "NRZI":
        return 2 * p * (1 - p)
    else:
        raise ValueError("Codificação desconhecida: " + str(codificacao))
