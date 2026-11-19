# src/modulation.py

# Modular = transformar grupos de bits em SÍMBOLOS (números complexos I + jQ).
#   BPSK   : 1 bit por símbolo   (2 símbolos)
#   QPSK   : 2 bits por símbolo  (4 símbolos)
#   16-QAM : 4 bits por símbolo  (16 símbolos)


import numpy as np


BITS_POR_SIMBOLO = {"BPSK": 1, "QPSK": 2, "16QAM": 4}


def bits_por_simbolo(modulacao):
    return BITS_POR_SIMBOLO[modulacao]


def completar_bits(bits, k):
    sobra = len(bits) % k
    if sobra == 0:
        return np.array(bits, dtype=int)
    faltam = k - sobra
    return np.concatenate([np.array(bits, dtype=int), np.zeros(faltam, dtype=int)])


# ---------- BPSK ----------

def modular_bpsk(bits):
    """bit 0 -> -1 | bit 1 -> +1 (símbolos reais, energia 1)."""
    bits = np.array(bits, dtype=int)
    simbolos = 2 * bits - 1
    return simbolos.astype(complex)


def demodular_bpsk(simbolos):
    """Decide pelo sinal da parte real: positivo -> 1, negativo -> 0."""
    bits = np.real(simbolos) > 0
    return bits.astype(int)


# ---------- QPSK ----------

def modular_qpsk(bits):
    bits = completar_bits(bits, 2)
    grupos = bits.reshape(-1, 2)              # uma linha por símbolo
    parte_i = 2 * grupos[:, 0] - 1
    parte_q = 2 * grupos[:, 1] - 1
    return (parte_i + 1j * parte_q) / np.sqrt(2)


def demodular_qpsk(simbolos):
    """Decide cada eixo pelo sinal: I dá o 1º bit e Q dá o 2º bit."""
    bit_i = (np.real(simbolos) > 0).astype(int)
    bit_q = (np.imag(simbolos) > 0).astype(int)
    grupos = np.column_stack([bit_i, bit_q])  # uma linha por símbolo
    return grupos.flatten()


# ---------- 16-QAM ----------

def _bits_para_nivel(bit_a, bit_b):
    sinal = 2 * bit_a - 1                     # bit 0 -> -1 e bit 1 -> +1
    modulo = 3 - 2 * bit_b                    # bit 0 -> 3 e bit 1 -> 1
    return sinal * modulo


def modular_16qam(bits):
    """Cada grupo de 4 bits vira 1 símbolo: 2 bits para I e 2 bits para Q.
    Os níveis (-3, -1, +1, +3) são divididos por raiz de 10 para a energia ficar 1."""
    bits = completar_bits(bits, 4)
    grupos = bits.reshape(-1, 4)
    parte_i = _bits_para_nivel(grupos[:, 0], grupos[:, 1])
    parte_q = _bits_para_nivel(grupos[:, 2], grupos[:, 3])
    return (parte_i + 1j * parte_q) / np.sqrt(10)


def _nivel_para_bits(valor):
    bit_a = (valor > 0).astype(int)           # sinal
    bit_b = (np.abs(valor) < 2).astype(int)   # perto do centro -> 1; longe -> 0
    return bit_a, bit_b


def demodular_16qam(simbolos):
    """Volta à escala original (multiplica por raiz de 10) e decide cada eixo."""
    parte_i = np.real(simbolos) * np.sqrt(10)
    parte_q = np.imag(simbolos) * np.sqrt(10)
    b0, b1 = _nivel_para_bits(parte_i)
    b2, b3 = _nivel_para_bits(parte_q)
    grupos = np.column_stack([b0, b1, b2, b3])
    return grupos.flatten()


# ---------- Funções gerais (escolhem a modulação pelo nome) ----------

def modular(bits, modulacao):
    """modulacao pode ser "BPSK", "QPSK" ou "16QAM"."""
    if modulacao == "BPSK":
        return modular_bpsk(bits)
    elif modulacao == "QPSK":
        return modular_qpsk(bits)
    elif modulacao == "16QAM":
        return modular_16qam(bits)
    else:
        raise ValueError("Modulação desconhecida: " + str(modulacao))


def demodular(simbolos, modulacao):
    """Devolve os bits recebidos (podem ter zeros extras no final, se houve complemento)."""
    if modulacao == "BPSK":
        return demodular_bpsk(simbolos)
    elif modulacao == "QPSK":
        return demodular_qpsk(simbolos)
    elif modulacao == "16QAM":
        return demodular_16qam(simbolos)
    else:
        raise ValueError("Modulação desconhecida: " + str(modulacao))


def constelacao(modulacao):
    """Devolve todos os símbolos ideais e os bits de cada um.        
    Serve para testes e para desenhar o diagrama de constelação.""" # CONFERIR SE ESTÁ FAZENDO SENTIDO NO CÓDIGO FINAL!
    k = bits_por_simbolo(modulacao)
    lista_bits = []
    for numero in range(2 ** k):
        binario = format(numero, "0" + str(k) + "b")   # ex.: 5 -> '0101'
        linha = []
        for digito in binario:
            linha.append(int(digito))
        lista_bits.append(linha)
    todos_os_bits = np.array(lista_bits, dtype=int)
    simbolos = modular(todos_os_bits.flatten(), modulacao)
    return simbolos, todos_os_bits
