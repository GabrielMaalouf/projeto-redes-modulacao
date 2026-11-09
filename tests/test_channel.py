# tests/test_channel.py
# Testes do módulo channel.py.
#  Camada 2: calibração do ruído (variância, SNR alta e SNR muito baixa).
#  Rajadas: proporção de símbolos ruins, erros agrupados e comparação com o AWGN.

import numpy as np
from src.message import (texto_para_bits, bits_para_texto, gerar_bits_aleatorios)
from src.line_coding import manchester_codificar, manchester_decodificar
from src.modulation import modular, demodular, bits_por_simbolo
from src.channel import (desvio_do_ruido, canal_awgn, canal_rajadas, aplicar_canal,
                         PROB_BOM_PARA_RUIM, PROB_RUIM_PARA_BOM)


def ber(modulacao, canal, ebn0_db, n_bits, seed):
    """Transmite bits aleatórios pelo canal e devolve a BER."""
    k = bits_por_simbolo(modulacao)
    bits = gerar_bits_aleatorios(n_bits, seed)
    simbolos = modular(bits, modulacao)
    recebidos, _ = aplicar_canal(simbolos, canal, ebn0_db, k, seed)
    bits_recebidos = demodular(recebidos, modulacao)[:n_bits]
    return np.sum(bits_recebidos != bits) / n_bits


# ---------- AWGN: calibração ----------

def test_desvio_do_ruido_formula():
    # Eb/N0 = 0 dB (=1) e 1 bit por símbolo: variância = 1 / (2 * 1) = 0,5
    assert abs(desvio_do_ruido(0, 1) ** 2 - 0.5) < 1e-9
    # com 4 bits por símbolo a variância é 4 vezes menor
    assert abs(desvio_do_ruido(0, 4) ** 2 - 0.125) < 1e-9


def test_variancia_do_ruido_awgn():
    # a variância medida deve ficar perto da esperada (tolerância de 2%)
    simbolos = np.ones(200000, dtype=complex)
    for k in [1, 2, 4]:
        recebidos, _ = canal_awgn(simbolos, 6, k, seed=1)
        ruido = recebidos - simbolos
        esperada = desvio_do_ruido(6, k) ** 2
        assert abs(np.var(ruido.real) - esperada) / esperada < 0.02
        assert abs(np.var(ruido.imag) - esperada) / esperada < 0.02


def test_awgn_tamanho_e_estados():
    simbolos = np.ones(1000, dtype=complex)
    recebidos, estados = canal_awgn(simbolos, 6, 2, seed=1)
    assert len(recebidos) == 1000
    assert np.sum(estados) == 0              # no AWGN o estado é sempre bom


def test_reprodutibilidade():
    # mesma seed -> mesmo resultado; seed diferente -> resultado diferente
    simbolos = np.ones(1000, dtype=complex)
    a, _ = canal_awgn(simbolos, 6, 2, seed=7)
    b, _ = canal_awgn(simbolos, 6, 2, seed=7)
    c, _ = canal_awgn(simbolos, 6, 2, seed=8)
    assert np.allclose(a, b)
    assert not np.allclose(a, c)


def test_snr_alta_sem_erros():
    # com SNR altíssima, a BER deve ser 0 nas três modulações
    for nome in ["BPSK", "QPSK", "16QAM"]:
        assert ber(nome, "AWGN", 40, 100000, seed=2) == 0


def test_snr_muito_baixa_ber_perto_de_meio():
    # com SNR muito baixa (-30 dB), o ruído domina e os bits recebidos são
    # praticamente aleatórios. (Em -10 dB a BER ainda é ~0,33, não 0,5.)
    for nome in ["BPSK", "QPSK", "16QAM"]:
        valor = ber(nome, "AWGN", -30, 100000, seed=3)
        assert 0.45 < valor < 0.52


def test_ber_diminui_com_a_snr():
    valores = []
    for ebn0_db in [0, 4, 8]:
        valores.append(ber("QPSK", "AWGN", ebn0_db, 100000, seed=4))
    assert valores[0] > valores[1] > valores[2]


# ---------- Teste de consistência: mensagem ASCII de ponta a ponta ----------

def test_mensagem_ascii_com_snr_alta():
    # texto -> bits -> Manchester -> modulação -> canal -> demodulação -> decodificação -> texto
    mensagem = "Redes de Computadores - UNISINOS"
    bits = texto_para_bits(mensagem)
    chips = manchester_codificar(bits)
    for nome in ["BPSK", "QPSK", "16QAM"]:
        k = bits_por_simbolo(nome)
        simbolos = modular(chips, nome)
        recebidos, _ = canal_awgn(simbolos, 40, k, seed=5)
        chips_recebidos = demodular(recebidos, nome)[:len(chips)]
        bits_recebidos, erros = manchester_decodificar(chips_recebidos)
        assert bits_para_texto(bits_recebidos) == mensagem
        assert erros == []


# ---------- Rajadas ----------

def test_proporcao_de_simbolos_ruins():
    # proporção esperada = p_bom_ruim / (p_bom_ruim + p_ruim_bom) = 0,01 / 0,11 = 9,1%
    simbolos = np.ones(300000, dtype=complex)
    _, estados = canal_rajadas(simbolos, 6, 2, seed=6)
    esperada = PROB_BOM_PARA_RUIM / (PROB_BOM_PARA_RUIM + PROB_RUIM_PARA_BOM)
    proporcao = np.mean(estados)
    assert abs(proporcao - esperada) < 0.02


def test_rajadas_sao_agrupadas():
    # o estado ruim dura em média 1 / p_ruim_bom = 10 símbolos seguidos
    simbolos = np.ones(300000, dtype=complex)
    _, estados = canal_rajadas(simbolos, 6, 2, seed=7)
    duracoes = []
    atual = 0
    for e in estados:
        if e == 1:
            atual += 1
        elif atual > 0:
            duracoes.append(atual)
            atual = 0
    media = np.mean(duracoes)
    assert 7 < media < 14


def test_ruido_no_estado_ruim_e_10db_mais_forte():
    # 10 dB a mais de ruído = variância 10 vezes maior
    simbolos = np.ones(300000, dtype=complex)
    recebidos, estados = canal_rajadas(simbolos, 6, 2, seed=8)
    ruido = recebidos - simbolos
    var_bom = np.var(ruido[estados == 0].real)
    var_ruim = np.var(ruido[estados == 1].real)
    assert abs(var_ruim / var_bom - 10) < 1.0
    # e o estado bom tem a variância nominal do AWGN
    esperada = desvio_do_ruido(6, 2) ** 2
    assert abs(var_bom - esperada) / esperada < 0.03


def test_rajadas_pioram_a_ber():
    # na mesma SNR nominal, as rajadas devem ter mais erros que o AWGN
    for nome in ["BPSK", "QPSK", "16QAM"]:
        awgn = ber(nome, "AWGN", 8, 200000, seed=9)
        rajadas = ber(nome, "RAJADAS", 8, 200000, seed=9)
        assert rajadas > awgn


def test_erros_agrupados_nas_rajadas():
    # nas rajadas, os erros se concentram nos símbolos do estado ruim
    n_bits = 200000
    bits = gerar_bits_aleatorios(n_bits, 10)
    simbolos = modular(bits, "BPSK")
    recebidos, estados = canal_rajadas(simbolos, 8, 1, seed=10)
    bits_recebidos = demodular(recebidos, "BPSK")[:n_bits]
    erro = bits_recebidos != bits
    taxa_ruim = np.mean(erro[estados == 1])
    taxa_bom = np.mean(erro[estados == 0])
    assert taxa_ruim > 10 * taxa_bom


def test_aplicar_canal_nome_invalido():
    simbolos = np.ones(10, dtype=complex)
    try:
        aplicar_canal(simbolos, "OUTRO", 6, 1, seed=1)
        assert False
    except ValueError:
        assert True
