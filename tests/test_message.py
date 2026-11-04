# tests/test_message.py
# Testes simples para o módulo message.py

from src.message import texto_para_bits, bits_para_texto, repetir_bits


def test_letra_A():
    # 'A' = 65 em ASCII = 01000001 em binário
    bits = texto_para_bits("A")
    assert list(bits) == [0, 1, 0, 0, 0, 0, 0, 1]


def test_tamanho():
    # cada caractere vira 8 bits
    bits = texto_para_bits("abc")
    assert len(bits) == 24


def test_ida_e_volta():
    # converter para bits e voltar deve dar o mesmo texto
    mensagem = "Redes de Computadores - UNISINOS"
    bits = texto_para_bits(mensagem)
    assert bits_para_texto(bits) == mensagem


def test_bit_errado():
    # trocando 1 bit, a letra muda (A=01000001 vira C=01000011)
    bits = texto_para_bits("A")
    bits[6] = 1
    assert bits_para_texto(bits) == "C"


def test_repetir_bits():
    bits = texto_para_bits("Oi")           # 16 bits
    muitos = repetir_bits(bits, 100000)
    assert len(muitos) == 100000