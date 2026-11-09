# tests/test_modulation.py
# Testes do módulo modulation.py.
#  Camada 1: testes sem ruído (ida e volta, energia, Gray, tamanhos).
#  Camada 3: comparação da BER simulada com a teoria (AWGN).

import math
import numpy as np
from src.message import gerar_bits_aleatorios
from src.modulation import (modular, demodular, bits_por_simbolo,
                            constelacao, modular_16qam)

MODULACOES = ["BPSK", "QPSK", "16QAM"]


# ---------- sem ruído ----------

def test_bits_por_simbolo():
    assert bits_por_simbolo("BPSK") == 1
    assert bits_por_simbolo("QPSK") == 2
    assert bits_por_simbolo("16QAM") == 4


def test_ida_e_volta():
    # sem ruído, demodular(modular(bits)) deve devolver os mesmos bits
    bits = gerar_bits_aleatorios(1000, seed=1)
    for nome in MODULACOES:
        simbolos = modular(bits, nome)
        recuperado = demodular(simbolos, nome)
        assert list(recuperado) == list(bits)


def test_energia_media_igual_a_um():
    # com bits equiprováveis, a energia média dos símbolos deve ser 1
    bits = gerar_bits_aleatorios(100000, seed=2)
    for nome in MODULACOES:
        simbolos = modular(bits, nome)
        energia = np.mean(np.abs(simbolos) ** 2)
        assert abs(energia - 1) < 0.02


def test_quantidade_de_simbolos():
    bits = gerar_bits_aleatorios(1000, seed=3)
    assert len(modular(bits, "BPSK")) == 1000
    assert len(modular(bits, "QPSK")) == 500
    assert len(modular(bits, "16QAM")) == 250


def test_numero_de_simbolos_diferentes():
    # BPSK tem 2 símbolos, QPSK tem 4 e 16-QAM tem 16
    esperado = {"BPSK": 2, "QPSK": 4, "16QAM": 16}
    for nome in MODULACOES:
        simbolos, _ = constelacao(nome)
        diferentes = set(np.round(simbolos, 6))
        assert len(diferentes) == esperado[nome]


def test_complemento_quando_bits_nao_sao_multiplos():
    # 10 bits em 16-QAM: faltam 2 bits, então são 3 símbolos
    bits = gerar_bits_aleatorios(10, seed=4)
    simbolos = modular(bits, "16QAM")
    assert len(simbolos) == 3
    recuperado = demodular(simbolos, "16QAM")
    assert list(recuperado[:10]) == list(bits)


def test_16qam_valores_conhecidos():
    # 0000 -> (-3, -3) | 1010 -> (+3, +3) | 0111 -> (-1, +1)
    simbolos = modular_16qam(np.array([0, 0, 0, 0,  1, 0, 1, 0,  0, 1, 1, 1]))
    esperado = np.array([-3 - 3j, 3 + 3j, -1 + 1j]) / np.sqrt(10)
    assert np.allclose(simbolos, esperado)


def test_gray():
    # símbolos vizinhos (distância mínima) devem diferir em exatamente 1 bit
    for nome in MODULACOES:
        simbolos, bits = constelacao(nome)
        menor = 1000
        for i in range(len(simbolos)):
            for j in range(i + 1, len(simbolos)):
                dist = abs(simbolos[i] - simbolos[j])
                if dist < menor:
                    menor = dist
        for i in range(len(simbolos)):
            for j in range(i + 1, len(simbolos)):
                dist = abs(simbolos[i] - simbolos[j])
                if abs(dist - menor) < 1e-9:
                    diferentes = int(np.sum(bits[i] != bits[j]))
                    assert diferentes == 1


# ---------- comparação com a teoria ----------

def ber_simulada(modulacao, ebn0_db, n_bits, seed):
    """Simula AWGN direto no teste (sem usar o channel.py) e devolve a BER."""
    k = bits_por_simbolo(modulacao)
    bits = gerar_bits_aleatorios(n_bits, seed)
    simbolos = modular(bits, modulacao)
    es_n0 = (10 ** (ebn0_db / 10)) * k                # Es/N0 = Eb/N0 * k
    desvio = math.sqrt(1 / (2 * es_n0))               # por eixo (energia de símbolo = 1)
    gerador = np.random.default_rng(seed + 1000)
    ruido = desvio * (gerador.standard_normal(len(simbolos))
                      + 1j * gerador.standard_normal(len(simbolos)))
    recebidos = demodular(simbolos + ruido, modulacao)[:n_bits]
    erros = np.sum(recebidos != bits)
    return erros / n_bits


def ber_teorica(modulacao, ebn0_db):
    ebn0 = 10 ** (ebn0_db / 10)
    if modulacao == "16QAM":
        return (3 / 8) * math.erfc(math.sqrt(0.4 * ebn0))   # aproximação (Gray)
    return 0.5 * math.erfc(math.sqrt(ebn0))                 # BPSK e QPSK


def test_bpsk_pontos_de_referencia_da_teoria():
    # valores conhecidos da BER teórica do BPSK
    assert abs(ber_teorica("BPSK", 0) - 0.0786) < 0.001
    assert abs(ber_teorica("BPSK", 4) - 0.0125) < 0.0005


def test_ber_simulada_bate_com_a_teoria():
    # em SNR média, a simulação deve ficar perto da curva teórica
    for nome in MODULACOES:
        for ebn0_db in [4, 8]:
            simulada = ber_simulada(nome, ebn0_db, 400000, seed=5)
            teorica = ber_teorica(nome, ebn0_db)
            erro_relativo = abs(simulada - teorica) / teorica
            assert erro_relativo < 0.15, (nome, ebn0_db, simulada, teorica)


def test_ordem_das_ber():
    # na mesma Eb/N0: BPSK ~ QPSK < 16-QAM
    bpsk = ber_simulada("BPSK", 6, 200000, seed=6)
    qpsk = ber_simulada("QPSK", 6, 200000, seed=6)
    qam = ber_simulada("16QAM", 6, 200000, seed=6)
    assert abs(bpsk - qpsk) / bpsk < 0.15
    assert qam > 2 * bpsk
