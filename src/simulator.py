# src/simulator.py
# Cadeia completa do sistema (ponta a ponta):
#
#   bits -> codificação de linha -> modulação -> CANAL -> demodulação
#        -> decodificação de linha -> bits recebidos -> métricas
#
# Todas as etapas usam os módulos já existentes. Este arquivo só "liga os fios".
#
# Seeds:
#  - a seed do ensaio gera os BITS (mesmos bits para todas as modulações,
#    codificações, canais e SNRs -> comparação justa);
#  - o RUÍDO usa uma seed derivada (seed + DESLOCAMENTO_SEED_RUIDO), para que
#    bits e ruído não venham da mesma sequência aleatória.

import numpy as np

from src.line_coding import (manchester_codificar, manchester_decodificar,
                             nrzi_codificar, nrzi_decodificar)
from src.modulation import modular, demodular, bits_por_simbolo
from src.channel import aplicar_canal
from src.metrics import contar_erros, posicoes_dos_erros


DESLOCAMENTO_SEED_RUIDO = 100000


def seed_do_ruido(seed):
    """Seed usada pelo canal a partir da seed do ensaio."""
    return seed + DESLOCAMENTO_SEED_RUIDO


# ---------- Codificação de linha pelo nome ----------

def codificar_linha(bits, codificacao):
    """codificacao: "MANCHESTER" ou "NRZI". Devolve os chips (0/1)."""
    if codificacao == "MANCHESTER":
        return manchester_codificar(bits)
    elif codificacao == "NRZI":
        return nrzi_codificar(bits)
    else:
        raise ValueError("Codificação desconhecida: " + str(codificacao))


def decodificar_linha(chips, codificacao):
    """Devolve (bits, pares_invalidos). Só o Manchester detecta pares inválidos;
    no NRZ-I a lista é sempre vazia."""
    if codificacao == "MANCHESTER":
        return manchester_decodificar(chips)
    elif codificacao == "NRZI":
        return nrzi_decodificar(chips), []
    else:
        raise ValueError("Codificação desconhecida: " + str(codificacao))


# ---------- Transmissão ----------

def transmitir(bits, codificacao, modulacao, canal, snr_db, seed):
    """Passa os bits por todo o sistema.

    canal: "AWGN", "RAJADAS" ou "IDEAL" (sem ruído, usado no teste de consistência).
    snr_db: Eb/N0 por chip, em dB (ignorado no canal IDEAL).

    Devolve um dicionário com todas as etapas, para permitir inspeção e gráficos."""
    bits = np.array(bits, dtype=int)
    k = bits_por_simbolo(modulacao)

    chips = codificar_linha(bits, codificacao)
    simbolos = modular(chips, modulacao)

    if canal == "IDEAL":
        recebidos = simbolos.copy()
        estados = np.zeros(len(simbolos), dtype=int)
    else:
        recebidos, estados = aplicar_canal(simbolos, canal, snr_db, k, seed_do_ruido(seed))

    # a modulação pode ter completado com zeros: cortamos de volta
    chips_recebidos = demodular(recebidos, modulacao)[:len(chips)]
    bits_recebidos, pares_invalidos = decodificar_linha(chips_recebidos, codificacao)
    bits_recebidos = bits_recebidos[:len(bits)]

    return {
        "bits": bits,
        "chips": chips,
        "simbolos": simbolos,
        "recebidos": recebidos,
        "estados": estados,
        "chips_recebidos": chips_recebidos,
        "bits_recebidos": bits_recebidos,
        "pares_invalidos": pares_invalidos,
        "erros_de_chip": contar_erros(chips, chips_recebidos),
        "n_erros": contar_erros(bits, bits_recebidos),
    }


def posicoes_incorretas(resultado):
    """Atalho: posições dos bits incorretos de uma transmissão."""
    return posicoes_dos_erros(resultado["bits"], resultado["bits_recebidos"])
