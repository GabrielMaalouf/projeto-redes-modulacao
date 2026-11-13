# tests/test_metrics.py
# Testes simples para o módulo metrics.py

import numpy as np
from src.message import texto_para_bits, bits_para_texto
from src.line_coding import manchester_codificar, manchester_decodificar
from src.modulation import modular, demodular, bits_por_simbolo
from src.channel import canal_awgn
from src.metrics import (contar_erros, calcular_ber, posicoes_dos_erros,
                         letras_erradas, eficiencia_espectral)


def test_sem_erros():
    bits = np.array([1, 0, 1, 1, 0])
    assert contar_erros(bits, bits) == 0
    assert calcular_ber(bits, bits) == 0
    assert posicoes_dos_erros(bits, bits) == []


def test_contagem_e_posicoes():
    enviados = np.array([1, 0, 1, 1, 0, 0, 1, 0])
    recebidos = np.array([1, 1, 1, 1, 0, 1, 1, 0])    # errados nas posições 1 e 5
    assert contar_erros(enviados, recebidos) == 2
    assert posicoes_dos_erros(enviados, recebidos) == [1, 5]


def test_ber_valores_conhecidos():
    enviados = np.array([0, 0, 0, 0])
    assert calcular_ber(enviados, np.array([1, 0, 0, 0])) == 0.25
    assert calcular_ber(enviados, np.array([1, 1, 0, 0])) == 0.5
    assert calcular_ber(enviados, np.array([1, 1, 1, 1])) == 1.0


def test_tamanhos_diferentes_dao_erro():
    try:
        calcular_ber(np.array([1, 0, 1]), np.array([1, 0]))
        assert False
    except ValueError:
        assert True


def test_quantidade_de_posicoes_igual_ao_numero_de_erros():
    enviados = np.random.default_rng(1).integers(0, 2, size=1000)
    recebidos = np.random.default_rng(2).integers(0, 2, size=1000)
    assert len(posicoes_dos_erros(enviados, recebidos)) == contar_erros(enviados, recebidos)


def test_letras_erradas():
    assert letras_erradas("Redes", "Redes") == []
    assert letras_erradas("Redes", "Rxdes") == [1]
    assert letras_erradas("abc", "a?c") == [1]


def test_eficiencia_sem_manchester_igual_a_bits_por_simbolo():
    # NRZ-I usa 1 chip por bit: a eficiência é igual aos bits por símbolo
    assert eficiencia_espectral("BPSK", "NRZI") == 1
    assert eficiencia_espectral("QPSK", "NRZI") == 2
    assert eficiencia_espectral("16QAM", "NRZI") == 4


def test_eficiencia_com_manchester_cai_pela_metade():
    assert eficiencia_espectral("BPSK", "MANCHESTER") == 0.5
    assert eficiencia_espectral("QPSK", "MANCHESTER") == 1
    assert eficiencia_espectral("16QAM", "MANCHESTER") == 2


def test_eficiencia_codificacao_invalida():
    try:
        eficiencia_espectral("BPSK", "OUTRA")
        assert False
    except ValueError:
        assert True


def test_ponta_a_ponta_com_ruido():
    # texto -> bits -> Manchester -> 16-QAM -> canal ruidoso -> volta -> métricas
    mensagem = "Redes de Computadores - UNISINOS " * 20
    bits = texto_para_bits(mensagem)
    chips = manchester_codificar(bits)
    simbolos = modular(chips, "16QAM")
    recebidos, _ = canal_awgn(simbolos, 4, bits_por_simbolo("16QAM"), seed=3)
    chips_recebidos = demodular(recebidos, "16QAM")[:len(chips)]
    bits_recebidos, _ = manchester_decodificar(chips_recebidos)

    erros = contar_erros(bits, bits_recebidos)
    assert erros > 0                                          # com SNR baixa, há erros
    assert len(posicoes_dos_erros(bits, bits_recebidos)) == erros
    assert abs(calcular_ber(bits, bits_recebidos) - erros / len(bits)) < 1e-12
    texto_recebido = bits_para_texto(bits_recebidos)
    assert len(letras_erradas(mensagem, texto_recebido)) > 0  # a mensagem foi estragada
