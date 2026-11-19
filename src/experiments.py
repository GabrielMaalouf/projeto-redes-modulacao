# src/experiments.py


import csv
import os
import time

from src import config
from src.message import texto_para_bits, bits_para_texto, gerar_bits_aleatorios
from src.metrics import letras_erradas, eficiencia_espectral
from src.simulator import transmitir, posicoes_incorretas


ARQUIVO_MENSAGEM = "results/raw/mensagem.csv"
ARQUIVO_CONSISTENCIA = "results/consistencia.txt"
COLUNAS_MENSAGEM = ["canal", "modulacao", "codificacao", "snr_db", "seed",
                    "n_bits", "n_erros", "n_letras_erradas", "mensagem_ok", "texto_recebido"]


def _garantir_pasta(arquivo):
    pasta = os.path.dirname(arquivo)
    if pasta:
        os.makedirs(pasta, exist_ok=True)


# ---------- 1) Varredura de BER ----------

def executar_varredura(arquivo_csv=config.ARQUIVO_CSV, n_bits=config.N_BITS,
                       seeds=config.SEEDS, snrs=config.SNRS_DB, verbose=True):
    """Roda todos os ensaios e grava uma linha por ensaio no CSV.
    Para cada seed os bits são gerados uma única vez e reutilizados em todas as
    combinações"""
    _garantir_pasta(arquivo_csv)
    with open(config.ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        f.write(config.texto_da_configuracao())

    total = len(config.CANAIS) * len(config.MODULACOES) * len(config.CODIFICACOES) \
        * len(snrs) * len(seeds)
    feitos = 0
    inicio = time.time()

    with open(arquivo_csv, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(config.COLUNAS_CSV)
        for seed in seeds:
            bits = gerar_bits_aleatorios(n_bits, seed)
            for canal in config.CANAIS:
                for modulacao in config.MODULACOES:
                    for codificacao in config.CODIFICACOES:
                        for snr in snrs:
                            r = transmitir(bits, codificacao, modulacao, canal, snr, seed)
                            ber = r["n_erros"] / n_bits
                            escritor.writerow([canal, modulacao, codificacao, snr, seed,
                                               n_bits, r["n_erros"], repr(ber)])
                            feitos += 1
            if verbose:
                print("  seed %d concluida: %d/%d ensaios (%.1f s)"
                      % (seed, feitos, total, time.time() - inicio))
    return arquivo_csv


def ler_resultados(arquivo_csv=config.ARQUIVO_CSV):
    """Lê o CSV bruto e devolve uma lista de dicionários com os tipos corretos."""
    linhas = []
    with open(arquivo_csv, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            linha["snr_db"] = float(linha["snr_db"])
            linha["seed"] = int(linha["seed"])
            linha["n_bits"] = int(linha["n_bits"])
            linha["n_erros"] = int(linha["n_erros"])
            linha["ber"] = float(linha["ber"])
            linhas.append(linha)
    return linhas


# ---------- 2) Recuperação da mensagem ----------

def executar_recuperacao_mensagem(arquivo_csv=ARQUIVO_MENSAGEM, mensagem=config.MENSAGEM_DEMO,
                                  seeds=config.SEEDS, snrs=config.SNRS_DB):
    """Transmite a mensagem ASCII em todas as combinações e registra se ela chegou
    inteira. Mostra como a degradação do canal afeta a mensagem (não só a BER)."""
    _garantir_pasta(arquivo_csv)
    bits = texto_para_bits(mensagem)
    with open(arquivo_csv, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(COLUNAS_MENSAGEM)
        for canal in config.CANAIS:
            for modulacao in config.MODULACOES:
                for codificacao in config.CODIFICACOES:
                    for snr in snrs:
                        for seed in seeds:
                            r = transmitir(bits, codificacao, modulacao, canal, snr, seed)
                            texto = bits_para_texto(r["bits_recebidos"])
                            n_letras = len(letras_erradas(mensagem, texto))
                            escritor.writerow([canal, modulacao, codificacao, snr, seed,
                                               len(bits), r["n_erros"], n_letras,
                                               int(r["n_erros"] == 0), texto])
    return arquivo_csv


def ler_mensagens(arquivo_csv=ARQUIVO_MENSAGEM):
    linhas = []
    with open(arquivo_csv, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            linha["snr_db"] = float(linha["snr_db"])
            linha["n_erros"] = int(linha["n_erros"])
            linha["n_letras_erradas"] = int(linha["n_letras_erradas"])
            linha["mensagem_ok"] = int(linha["mensagem_ok"])
            linhas.append(linha)
    return linhas


# ---------- 3) Teste de consistência ----------

def teste_de_consistencia(mensagem=config.MENSAGEM_DEMO, snr_alta=config.SNR_ALTA_DB,
                          seed=config.SEEDS[0], arquivo=ARQUIVO_CONSISTENCIA):
    linhas = ["TESTE DE CONSISTENCIA",
              "Mensagem: " + repr(mensagem),
              "SNR elevada: %s dB (Eb/N0 por chip)" % snr_alta, ""]
    tudo_ok = True
    casos = [("IDEAL", None), ("AWGN", snr_alta), ("RAJADAS", snr_alta)]
    bits = texto_para_bits(mensagem)
    for canal, snr in casos:
        for modulacao in config.MODULACOES:
            for codificacao in config.CODIFICACOES:
                r = transmitir(bits, codificacao, modulacao, canal, snr, seed)
                texto = bits_para_texto(r["bits_recebidos"])
                ok = (r["n_erros"] == 0 and texto == mensagem
                      and len(r["bits_recebidos"]) == len(bits))
                tudo_ok = tudo_ok and ok
                linhas.append("%-8s %-6s %-11s SNR=%-5s erros=%d pares_invalidos=%d  %s  -> %r"
                              % (canal, modulacao, codificacao, snr if snr is not None else "-",
                                 r["n_erros"], len(r["pares_invalidos"]),
                                 "OK" if ok else "FALHOU", texto))

    # bits que não são múltiplos de 4 (exige padding no QPSK/16-QAM)
    linhas.append("")
    bits_impares = bits[:-3]
    for modulacao in config.MODULACOES:
        for codificacao in config.CODIFICACOES:
            r = transmitir(bits_impares, codificacao, modulacao, "IDEAL", None, seed)
            ok = r["n_erros"] == 0 and len(r["bits_recebidos"]) == len(bits_impares)
            tudo_ok = tudo_ok and ok
            linhas.append("padding: %d bits  %-6s %-11s -> %d bits recebidos, erros=%d  %s"
                          % (len(bits_impares), modulacao, codificacao,
                             len(r["bits_recebidos"]), r["n_erros"], "OK" if ok else "FALHOU"))

    linhas.append("")
    linhas.append("RESULTADO: " + ("TODAS AS COMBINACOES RECUPERARAM A MENSAGEM" if tudo_ok
                                   else "HOUVE DIVERGENCIAS (ver acima)"))
    texto_final = "\n".join(linhas) + "\n"
    _garantir_pasta(arquivo)
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(texto_final)
    return tudo_ok, texto_final


# ---------- 4) Demonstração ----------

def demonstracao(mensagem=config.MENSAGEM_DEMO, snr=config.SNR_DEMO_DB, seed=config.SEEDS[0],
                 max_posicoes=15):
    """Mostra a mensagem passando pelo sistema em cada combinação, com os bits incorretos."""
    bits = texto_para_bits(mensagem)
    saida = ["DEMONSTRACAO  (SNR = %s dB, seed = %d)" % (snr, seed),
             "Mensagem original: %r" % mensagem,
             "Bits (%d): %s..." % (len(bits), "".join(str(b) for b in bits[:48])), ""]
    for canal in config.CANAIS:
        for modulacao in config.MODULACOES:
            for codificacao in config.CODIFICACOES:
                r = transmitir(bits, codificacao, modulacao, canal, snr, seed)
                texto = bits_para_texto(r["bits_recebidos"])
                pos = posicoes_incorretas(r)
                letras = letras_erradas(mensagem, texto)
                marcas = "".join("^" if i in letras else " " for i in range(len(texto)))
                mostra = ", ".join(str(p) for p in pos[:max_posicoes])
                if len(pos) > max_posicoes:
                    mostra += ", ..."
                saida.append("[%s | %s | %s]  eficiencia = %.1f bits/s/Hz"
                              % (canal, modulacao, codificacao,
                                 eficiencia_espectral(modulacao, codificacao)))
                saida.append("  recebida : %r" % texto)
                saida.append("              %s" % marcas)
                saida.append("  bits errados: %d / %d (BER = %.4f)  posicoes: [%s]"
                             % (len(pos), len(bits), len(pos) / len(bits), mostra))
                if codificacao == "MANCHESTER":
                    saida.append("  pares Manchester invalidos (erros detectados): %d"
                                 % len(r["pares_invalidos"]))
                saida.append("")
    return "\n".join(saida)
