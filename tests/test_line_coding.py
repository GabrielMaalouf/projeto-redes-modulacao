# tests/test_line_coding.py
# Testes simples para o módulo line_coding.py

import numpy as np
from src.message import gerar_bits_aleatorios
from src.line_coding import (manchester_codificar, manchester_decodificar,
                             nrzi_codificar, nrzi_decodificar)


# ---------- Manchester ----------

def test_manchester_valores():
    chips = manchester_codificar(np.array([0, 1]))
    assert list(chips) == [1, 0, 0, 1]


def test_manchester_tamanho():
    chips = manchester_codificar(np.array([1, 0, 1, 1]))
    assert len(chips) == 8


def test_manchester_ida_e_volta():
    bits = np.array([1, 0, 1, 1, 0, 0, 1, 0])
    chips = manchester_codificar(bits)
    recuperado, erros = manchester_decodificar(chips)
    assert list(recuperado) == list(bits)
    assert erros == []


def test_manchester_ida_e_volta_aleatorio():
    bits = gerar_bits_aleatorios(1000, seed=3)
    recuperado, erros = manchester_decodificar(manchester_codificar(bits))
    assert list(recuperado) == list(bits)
    assert erros == []


def test_manchester_detecta_erro():
    chips = manchester_codificar(np.array([0, 1, 0]))
    chips[1] = 1                       # [1,0] vira [1,1]: par inválido
    recuperado, erros = manchester_decodificar(chips)
    assert erros == [0]


# ---------- NRZ-I ----------

def test_nrzi_valores():
    # bits 1,1,0,1,0,0 -> inverte, inverte, mantém, inverte, mantém, mantém
    niveis = nrzi_codificar(np.array([1, 1, 0, 1, 0, 0]))
    assert list(niveis) == [1, 0, 0, 1, 1, 1]


def test_nrzi_tamanho():
    # 1 chip por bit: a saída tem o mesmo tamanho da entrada
    niveis = nrzi_codificar(np.array([1, 0, 1, 1]))
    assert len(niveis) == 4


def test_nrzi_ida_e_volta():
    bits = np.array([1, 1, 0, 0, 1, 0, 1, 1])
    recuperado = nrzi_decodificar(nrzi_codificar(bits))
    assert list(recuperado) == list(bits)


def test_nrzi_ida_e_volta_aleatorio():
    bits = gerar_bits_aleatorios(1000, seed=4)
    recuperado = nrzi_decodificar(nrzi_codificar(bits))
    assert list(recuperado) == list(bits)


def test_nrzi_erro_de_chip_vira_dois_erros_de_bit():
    # um chip errado no meio da sequência afeta o bit atual e o seguinte
    bits = np.array([1, 0, 0, 1, 0])
    niveis = nrzi_codificar(bits)      # [1, 1, 1, 0, 0]
    niveis[2] = 0                      # chip errado
    recuperado = nrzi_decodificar(niveis)
    erros = int(np.sum(recuperado != bits))
    assert erros == 2
