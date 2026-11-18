# tests/test_simulator.py
# Testes da cadeia ponta a ponta, das curvas teóricas e da agregação dos resultados.

import numpy as np
import pytest

from src import config
from src.message import texto_para_bits, bits_para_texto, gerar_bits_aleatorios
from src.simulator import transmitir, posicoes_incorretas, codificar_linha, decodificar_linha
from src.theory import ber_teorica
from src.experiments import teste_de_consistencia
from src.plots import agregar, snr_necessaria

COMBINACOES = [(m, c) for m in config.MODULACOES for c in config.CODIFICACOES]


@pytest.mark.parametrize("modulacao,codificacao", COMBINACOES)
def test_canal_ideal_recupera_a_mensagem(modulacao, codificacao):
    bits = texto_para_bits("Teste ponta a ponta!")
    r = transmitir(bits, codificacao, modulacao, "IDEAL", None, 1)
    assert r["n_erros"] == 0
    assert bits_para_texto(r["bits_recebidos"]) == "Teste ponta a ponta!"


@pytest.mark.parametrize("modulacao,codificacao", COMBINACOES)
def test_tamanho_nao_multiplo_volta_com_o_mesmo_tamanho(modulacao, codificacao):
    bits = gerar_bits_aleatorios(101, 3)
    r = transmitir(bits, codificacao, modulacao, "AWGN", 40, 3)
    assert len(r["bits_recebidos"]) == 101
    assert r["n_erros"] == 0


def test_codificacao_de_linha_ida_e_volta():
    bits = gerar_bits_aleatorios(500, 7)
    for cod in config.CODIFICACOES:
        volta, invalidos = decodificar_linha(codificar_linha(bits, cod), cod)
        assert np.array_equal(volta, bits)
        assert invalidos == []


def test_posicoes_incorretas_batem_com_a_contagem():
    bits = gerar_bits_aleatorios(20000, 2)
    r = transmitir(bits, "NRZI", "16QAM", "AWGN", 4, 2)
    pos = posicoes_incorretas(r)
    assert len(pos) == r["n_erros"] > 0
    assert all(r["bits"][p] != r["bits_recebidos"][p] for p in pos)


def test_mesma_seed_mesmo_resultado():
    bits = gerar_bits_aleatorios(5000, 4)
    a = transmitir(bits, "MANCHESTER", "QPSK", "RAJADAS", 6, 4)
    b = transmitir(bits, "MANCHESTER", "QPSK", "RAJADAS", 6, 4)
    assert a["n_erros"] == b["n_erros"]


def test_rajadas_pioram_a_ber():
    bits = gerar_bits_aleatorios(100000, 5)
    awgn = transmitir(bits, "NRZI", "BPSK", "AWGN", 8, 5)["n_erros"]
    raj = transmitir(bits, "NRZI", "BPSK", "RAJADAS", 8, 5)["n_erros"]
    assert raj > awgn


@pytest.mark.parametrize("modulacao,codificacao", COMBINACOES)
def test_simulacao_proxima_da_teoria_no_awgn(modulacao, codificacao):
    bits = gerar_bits_aleatorios(200000, 11)
    r = transmitir(bits, codificacao, modulacao, "AWGN", 4, 11)
    simulada = r["n_erros"] / len(bits)
    teorica = float(ber_teorica(modulacao, codificacao, 4))
    assert abs(simulada - teorica) / teorica < 0.15


def test_teste_de_consistencia_passa(tmp_path):
    ok, texto = teste_de_consistencia(arquivo=str(tmp_path / "c.txt"))
    assert ok
    assert "FALHOU" not in texto


def test_agregacao_e_intervalo():
    linhas = [{"canal": "AWGN", "modulacao": "BPSK", "codificacao": "NRZI", "snr_db": 0.0,
               "seed": s, "n_bits": 100, "n_erros": e, "ber": e / 100}
              for s, e in zip(range(5), [10, 12, 8, 11, 9])]
    r = agregar(linhas)[("AWGN", "BPSK", "NRZI", 0.0)]
    assert r["n_erros_total"] == 50
    assert abs(r["ber_media"] - 0.10) < 1e-12
    assert r["ic95_inf"] < 0.10 < r["ic95_sup"]


def test_snr_necessaria_interpola_em_log():
    resumo = {}
    for snr, ber in [(0.0, 1e-2), (2.0, 1e-4)]:
        resumo[("AWGN", "BPSK", "NRZI", snr)] = {"ber_media": ber, "ic95_inf": ber,
                                                 "ic95_sup": ber}
    assert abs(snr_necessaria(resumo, "AWGN", "BPSK", "NRZI", 1e-3) - 1.0) < 1e-9
    assert snr_necessaria(resumo, "AWGN", "BPSK", "NRZI", 1e-6) is None
