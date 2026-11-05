# tests/test_line_coding.py
# Testes simples para o módulo line_coding.py

import numpy as np
from src.message import gerar_bits_aleatorios
from src.line_coding import (manchester_codificar, manchester_decodificar,
                             ami_codificar, ami_decidir, ami_decodificar)


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


# ---------- AMI ----------

def test_ami_valores():
    # 1 -> +1, 0 -> 0, 1 -> -1, 1 -> +1
    niveis = ami_codificar(np.array([1, 0, 1, 1]))
    assert list(niveis) == [1, 0, -1, 1]


def test_ami_ida_e_volta():
    bits = np.array([1, 1, 0, 0, 1, 0, 1, 1])
    niveis = ami_codificar(bits)
    recuperado, violacoes = ami_decodificar(niveis)
    assert list(recuperado) == list(bits)
    assert violacoes == []


def test_ami_ida_e_volta_aleatorio():
    bits = gerar_bits_aleatorios(1000, seed=4)
    recuperado, violacoes = ami_decodificar(ami_codificar(bits))
    assert list(recuperado) == list(bits)
    assert violacoes == []


def test_ami_detecta_violacao():
    niveis = np.array([1, 0, 1])       # dois +1 seguidos: viola a alternância
    bits, violacoes = ami_decodificar(niveis)
    assert violacoes == [2]


def test_ami_decidir_limiares():
    sinal = np.array([0.9, 0.4, -0.4, -0.9, 0.0, 1.7, -1.2, 0.5])
    niveis = ami_decidir(sinal)
    assert list(niveis) == [1, 0, 0, -1, 0, 1, -1, 0]


def test_ami_com_ruido_pequeno():
    # ruído bem menor que o limiar (0,5) não deve causar erro
    bits = gerar_bits_aleatorios(1000, seed=5)
    niveis = ami_codificar(bits)
    ruido = np.random.default_rng(0).normal(0, 0.05, size=len(niveis))
    decididos = ami_decidir(niveis + ruido)
    recuperado, violacoes = ami_decodificar(decididos)
    assert list(recuperado) == list(bits)
    assert violacoes == []
