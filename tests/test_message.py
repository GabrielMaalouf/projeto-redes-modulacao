# tests/test_message.py
# Testes simples para o módulo message.py

from src.message import (texto_para_bits, bits_para_texto,
                         gerar_bits_aleatorios, repetir_bits)


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


def test_caractere_invalido_vira_interrogacao():
    # 'A' com o bit mais significativo trocado vira código 193 (não imprimível)
    bits = texto_para_bits("A")
    bits[0] = 1
    assert bits_para_texto(bits) == "?"


def test_bits_aleatorios_tamanho_e_valores():
    bits = gerar_bits_aleatorios(100000, seed=1)
    assert len(bits) == 100000
    assert set(bits) == {0, 1}


def test_bits_aleatorios_equiprovaveis():
    # a proporção de 1s deve ficar perto de 50%
    bits = gerar_bits_aleatorios(100000, seed=1)
    proporcao = bits.mean()
    assert 0.49 < proporcao < 0.51


def test_bits_aleatorios_reproduzivel():
    # mesma seed -> mesmos bits; seed diferente -> bits diferentes
    a = gerar_bits_aleatorios(1000, seed=7)
    b = gerar_bits_aleatorios(1000, seed=7)
    c = gerar_bits_aleatorios(1000, seed=8)
    assert list(a) == list(b)
    assert list(a) != list(c)


def test_repetir_bits():
    bits = texto_para_bits("Oi")           # 16 bits
    muitos = repetir_bits(bits, 100000)
    assert len(muitos) == 100000
