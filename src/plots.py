# src/plots.py
# Gráficos e tabelas a partir dos RESULTADOS BRUTOS (results/raw/*.csv).
# Nada aqui simula BER: tudo é lido do CSV, então os gráficos podem ser
# regerados a qualquer momento sem rodar a varredura de novo.
#
# Variabilidade entre repetições: para cada ponto (canal, modulação, codificação, SNR)
# calculamos a BER de cada seed e o intervalo de confiança de 95% da média
# (distribuição t de Student com n_seeds - 1 graus de liberdade).

import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")                       # gera PNG sem precisar de tela
import matplotlib.pyplot as plt
from scipy import stats

from src import config
from src.message import gerar_bits_aleatorios
from src.metrics import eficiencia_espectral
from src.modulation import modular, bits_por_simbolo
from src.channel import aplicar_canal
from src.simulator import codificar_linha, seed_do_ruido
from src.theory import ber_teorica


# Cada modulação tem SEMPRE a mesma cor e o mesmo marcador (identidade não depende só da cor)
CORES = {"BPSK": "#2a78d6", "QPSK": "#eb6834", "16QAM": "#1baf7a"}
MARCADORES = {"BPSK": "o", "QPSK": "s", "16QAM": "^"}
TRACOS_CODIFICACAO = {"MANCHESTER": "-", "NRZI": "--"}
TRACOS_CANAL = {"AWGN": "-", "RAJADAS": ":"}
NOMES = {"BPSK": "BPSK", "QPSK": "QPSK", "16QAM": "16-QAM",
         "MANCHESTER": "Manchester", "NRZI": "NRZ-I", "AWGN": "AWGN", "RAJADAS": "Rajadas"}

ARQUIVO_RESUMO = "results/raw/ber_resumo.csv"
ARQUIVO_TABELA_MD = "results/tabela_compromisso.md"
ARQUIVO_TABELA_CSV = "results/tabela_compromisso.csv"
BER_ALVO = 1e-3


def _estilo():
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 150, "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b",
        "xtick.color": "#52514e", "ytick.color": "#52514e",
        "grid.color": "#d9d8d4", "grid.linewidth": 0.6,
        "lines.linewidth": 2, "lines.markersize": 6, "legend.frameon": False,
    })


# ---------- Agregação ----------

def agregar(linhas):
    """Agrupa os ensaios por (canal, modulação, codificação, SNR).
    Devolve um dicionário com BER média, desvio, IC95% e totais."""
    grupos = {}
    for l in linhas:
        chave = (l["canal"], l["modulacao"], l["codificacao"], l["snr_db"])
        grupos.setdefault(chave, []).append(l)

    resumo = {}
    for chave, ensaios in grupos.items():
        bers = np.array([e["ber"] for e in ensaios])
        n = len(bers)
        media = float(np.mean(bers))
        desvio = float(np.std(bers, ddof=1)) if n > 1 else 0.0
        meia_largura = float(stats.t.ppf(0.975, n - 1) * desvio / np.sqrt(n)) if n > 1 else 0.0
        resumo[chave] = {
            "n_seeds": n,
            "n_bits_total": sum(e["n_bits"] for e in ensaios),
            "n_erros_total": sum(e["n_erros"] for e in ensaios),
            "ber_media": media,
            "ber_desvio": desvio,
            "ic95_inf": max(media - meia_largura, 0.0),
            "ic95_sup": media + meia_largura,
            "ber_min": float(np.min(bers)),
            "ber_max": float(np.max(bers)),
        }
    return resumo


def salvar_resumo(resumo, arquivo=ARQUIVO_RESUMO):
    os.makedirs(os.path.dirname(arquivo), exist_ok=True)
    campos = ["n_seeds", "n_bits_total", "n_erros_total", "ber_media", "ber_desvio",
              "ic95_inf", "ic95_sup", "ber_min", "ber_max"]
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["canal", "modulacao", "codificacao", "snr_db"] + campos)
        for chave in sorted(resumo):
            w.writerow(list(chave) + [resumo[chave][c] for c in campos])
    return arquivo


def _serie(resumo, canal, modulacao, codificacao):
    """Arrays (snr, média, erro_inferior, erro_superior) prontos para o errorbar em log.
    BER zero vira o PISO_BER (log de zero não existe)."""
    snrs = sorted(s for (c, m, k, s) in resumo if (c, m, k) == (canal, modulacao, codificacao))
    media, inf, sup = [], [], []
    for s in snrs:
        r = resumo[(canal, modulacao, codificacao, s)]
        mu = max(r["ber_media"], config.PISO_BER)
        media.append(mu)
        inf.append(mu - max(r["ic95_inf"], config.PISO_BER))
        sup.append(max(r["ic95_sup"], config.PISO_BER) - mu)
    return np.array(snrs), np.array(media), np.array(inf), np.array(sup)


def _eixos_ber(ax, titulo):
    ax.set_yscale("log")
    ax.set_ylim(config.PISO_BER / 2, 1)
    ax.set_xlabel("SNR = Eb/N0 por chip (dB)")
    ax.set_ylabel("BER")
    ax.set_title(titulo, loc="left", fontsize=11)
    ax.grid(True, which="major")
    ax.axhline(config.PISO_BER, color="#8a8984", linewidth=0.8, linestyle=(0, (2, 3)))


# ---------- Figuras ----------

def grafico_ber_por_canal(resumo, canal, pasta=config.PASTA_FIGURAS):
    """BER x SNR com IC95% entre seeds; um painel por codificação de linha.
    No AWGN as curvas teóricas aparecem tracejadas finas."""
    fig, eixos = plt.subplots(1, len(config.CODIFICACOES), figsize=(11, 4.4), sharey=True)
    for ax, cod in zip(eixos, config.CODIFICACOES):
        for mod in config.MODULACOES:
            x, y, e_inf, e_sup = _serie(resumo, canal, mod, cod)
            ax.errorbar(x, y, yerr=[e_inf, e_sup], color=CORES[mod], marker=MARCADORES[mod],
                        capsize=3, label=NOMES[mod] + " (simulado, IC95%)")
            if canal == "AWGN":
                xt = np.linspace(min(x), max(x), 200)
                ax.plot(xt, ber_teorica(mod, cod, xt), color=CORES[mod], linewidth=1,
                        linestyle=(0, (4, 3)), alpha=0.8, label=NOMES[mod] + " (teórico)")
        _eixos_ber(ax, "%s · %s" % (NOMES[canal], NOMES[cod]))
    eixos[0].legend(fontsize=8, loc="lower left")
    fig.suptitle("BER × SNR — canal %s (%d seeds × %d bits por ponto)"
                 % (NOMES[canal], len(config.SEEDS), config.N_BITS), x=0.01, ha="left")
    fig.tight_layout()
    arquivo = os.path.join(pasta, "ber_snr_%s.png" % canal.lower())
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


def grafico_awgn_vs_rajadas(resumo, pasta=config.PASTA_FIGURAS):
    """Um painel por modulação: AWGN (linha cheia) x Rajadas (pontilhada)."""
    fig, eixos = plt.subplots(len(config.CODIFICACOES), len(config.MODULACOES),
                              figsize=(13, 7.5), sharey=True, sharex=True)
    for i, cod in enumerate(config.CODIFICACOES):
        for j, mod in enumerate(config.MODULACOES):
            ax = eixos[i][j]
            for canal in config.CANAIS:
                x, y, e_inf, e_sup = _serie(resumo, canal, mod, cod)
                ax.errorbar(x, y, yerr=[e_inf, e_sup], color=CORES[mod],
                            marker=MARCADORES[mod] if canal == "AWGN" else "x",
                            linestyle=TRACOS_CANAL[canal], capsize=3, label=NOMES[canal])
            _eixos_ber(ax, "%s · %s" % (NOMES[mod], NOMES[cod]))
            if i == 0:
                ax.set_xlabel("")
            if j > 0:
                ax.set_ylabel("")
            ax.legend(fontsize=8, loc="lower left")
    fig.suptitle("AWGN × ruído em rajadas (estado ruim: SNR − %d dB)" % config.QUEDA_SNR_RUIM_DB,
                 x=0.01, ha="left")
    fig.tight_layout()
    arquivo = os.path.join(pasta, "awgn_vs_rajadas.png")
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


def grafico_comparativo_codificacoes(resumo, pasta=config.PASTA_FIGURAS):
    """Todas as curvas AWGN juntas: modulação = cor/marcador, codificação = traço."""
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for mod in config.MODULACOES:
        for cod in config.CODIFICACOES:
            x, y, e_inf, e_sup = _serie(resumo, "AWGN", mod, cod)
            ax.errorbar(x, y, yerr=[e_inf, e_sup], color=CORES[mod], marker=MARCADORES[mod],
                        linestyle=TRACOS_CODIFICACAO[cod], capsize=3,
                        label="%s + %s (%.1f b/s/Hz)" % (NOMES[mod], NOMES[cod],
                                                         eficiencia_espectral(mod, cod)))
    _eixos_ber(ax, "AWGN — todas as combinações")
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    arquivo = os.path.join(pasta, "ber_snr_comparativo.png")
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


def grafico_constelacoes(snr=config.SNR_DEMO_DB, n_bits=4000, seed=config.SEEDS[0],
                         pasta=config.PASTA_FIGURAS):
    """Constelações antes e depois do canal, para NRZ-I e Manchester.
    O Manchester restringe os pontos usados (pares de chips sempre complementares)."""
    bits = gerar_bits_aleatorios(n_bits, seed)
    colunas = ["Transmitido", "Após AWGN", "Após rajadas"]
    arquivos = []
    for cod in config.CODIFICACOES:
        fig, eixos = plt.subplots(len(config.MODULACOES), 3, figsize=(10, 10))
        chips = codificar_linha(bits, cod)
        for i, mod in enumerate(config.MODULACOES):
            k = bits_por_simbolo(mod)
            simbolos = modular(chips, mod)
            awgn, _ = aplicar_canal(simbolos, "AWGN", snr, k, seed_do_ruido(seed))
            raj, estados = aplicar_canal(simbolos, "RAJADAS", snr, k, seed_do_ruido(seed))
            for j, dados in enumerate([simbolos, awgn, raj]):
                ax = eixos[i][j]
                if j == 2:
                    bom = estados == 0
                    ax.scatter(dados[bom].real, dados[bom].imag, s=3, alpha=0.35,
                               color=CORES[mod], label="estado bom")
                    ax.scatter(dados[~bom].real, dados[~bom].imag, s=5, alpha=0.7,
                               color="#52514e", label="estado ruim")
                    ax.legend(fontsize=7, loc="upper right", markerscale=2,
                              frameon=True, framealpha=0.9, edgecolor="none")
                else:
                    ax.scatter(dados.real, dados.imag, s=3 if j else 30, alpha=0.35 if j else 1,
                               color=CORES[mod])
                ax.set_xlim(-2, 2)
                ax.set_ylim(-2, 2)
                ax.set_aspect("equal")
                ax.axhline(0, color="#d9d8d4", linewidth=0.6)
                ax.axvline(0, color="#d9d8d4", linewidth=0.6)
                ax.set_title("%s — %s" % (NOMES[mod], colunas[j]), fontsize=9, loc="left")
        fig.suptitle("Constelações (I/Q) com %s, SNR = %s dB" % (NOMES[cod], snr),
                     x=0.01, ha="left")
        fig.tight_layout()
        arquivo = os.path.join(pasta, "constelacoes_%s.png" % cod.lower())
        fig.savefig(arquivo)
        plt.close(fig)
        arquivos.append(arquivo)
    return arquivos


def grafico_recuperacao_mensagem(mensagens, pasta=config.PASTA_FIGURAS):
    """Fração de mensagens ASCII recebidas sem nenhum erro, por SNR."""
    fig, eixos = plt.subplots(1, len(config.CODIFICACOES), figsize=(11, 4.2), sharey=True)
    for ax, cod in zip(eixos, config.CODIFICACOES):
        for mod in config.MODULACOES:
            for canal in config.CANAIS:
                sel = [m for m in mensagens if m["modulacao"] == mod
                       and m["codificacao"] == cod and m["canal"] == canal]
                snrs = sorted(set(m["snr_db"] for m in sel))
                frac = [np.mean([m["mensagem_ok"] for m in sel if m["snr_db"] == s]) for s in snrs]
                ax.plot(snrs, frac, color=CORES[mod],
                        marker=MARCADORES[mod] if canal == "AWGN" else "x",
                        linestyle=TRACOS_CANAL[canal],
                        label="%s · %s" % (NOMES[mod], NOMES[canal]))
        ax.set_ylim(-0.03, 1.03)
        ax.set_xlabel("SNR = Eb/N0 por chip (dB)")
        ax.set_ylabel("Mensagens recebidas sem erro")
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.set_title(NOMES[cod], loc="left", fontsize=11)
        ax.grid(True)
    eixos[0].legend(fontsize=8, loc="upper left")
    fig.suptitle("Recuperação da mensagem %r (%d seeds por ponto)"
                 % (config.MENSAGEM_DEMO, len(config.SEEDS)), x=0.01, ha="left")
    fig.tight_layout()
    arquivo = os.path.join(pasta, "recuperacao_mensagem.png")
    fig.savefig(arquivo)
    plt.close(fig)
    return arquivo


# ---------- Tabela de compromisso BER x eficiência ----------

def snr_necessaria(resumo, canal, mod, cod, alvo=BER_ALVO):
    """Menor SNR (interpolada em log10(BER)) para a BER média ficar <= alvo.
    Devolve None se o alvo não foi atingido na faixa simulada."""
    x, y, _, _ = _serie(resumo, canal, mod, cod)
    if y[0] <= alvo:
        return float(x[0])
    for i in range(1, len(x)):
        if y[i] <= alvo:
            l0, l1, la = np.log10(y[i - 1]), np.log10(y[i]), np.log10(alvo)
            return float(x[i - 1] + (x[i] - x[i - 1]) * (l0 - la) / (l0 - l1))
    return None


def tabela_compromisso(resumo, snrs_tabela=(4, 8, 12)):
    linhas = []
    for mod in config.MODULACOES:
        for cod in config.CODIFICACOES:
            linha = {"modulacao": mod, "codificacao": cod,
                     "eficiencia": eficiencia_espectral(mod, cod)}
            for canal in config.CANAIS:
                for s in snrs_tabela:
                    r = resumo.get((canal, mod, cod, float(s)))
                    linha["ber_%s_%sdB" % (canal, s)] = r["ber_media"] if r else None
                linha["snr_%s_ber1e-3" % canal] = snr_necessaria(resumo, canal, mod, cod)
            linhas.append(linha)
    linhas.sort(key=lambda l: -l["eficiencia"])
    return linhas


def _fmt(v, snr=False):
    if v is None:
        return "> %d dB" % max(config.SNRS_DB) if snr else "-"
    if snr:
        return "%.1f dB" % v
    return "0 (< %.0e)" % config.PISO_BER if v == 0 else "%.2e" % v


def salvar_tabela(linhas, snrs_tabela=(4, 8, 12)):
    os.makedirs(os.path.dirname(ARQUIVO_TABELA_MD), exist_ok=True)
    with open(ARQUIVO_TABELA_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)

    cab = ["Modulação", "Codificação", "Eficiência (bits/s/Hz)"]
    for canal in config.CANAIS:
        cab += ["BER %s @%d dB" % (NOMES[canal], s) for s in snrs_tabela]
    cab += ["SNR p/ BER ≤ 1e-3 (%s)" % NOMES[c] for c in config.CANAIS]
    md = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for l in linhas:
        cel = [NOMES[l["modulacao"]], NOMES[l["codificacao"]], "%.1f" % l["eficiencia"]]
        for canal in config.CANAIS:
            cel += [_fmt(l["ber_%s_%sdB" % (canal, s)]) for s in snrs_tabela]
        cel += [_fmt(l["snr_%s_ber1e-3" % c], snr=True) for c in config.CANAIS]
        md.append("| " + " | ".join(cel) + " |")
    texto = "\n".join(md) + "\n"
    with open(ARQUIVO_TABELA_MD, "w", encoding="utf-8") as f:
        f.write("# Tabela de compromisso BER × eficiência espectral\n\n")
        f.write("SNR = Eb/N0 por chip. BER média de %d seeds × %d bits.\n\n"
                % (len(config.SEEDS), config.N_BITS))
        f.write(texto)
    return texto


def gerar_tudo(linhas, mensagens=None):
    """Gera todas as figuras e tabelas. Devolve a lista de arquivos criados."""
    _estilo()
    os.makedirs(config.PASTA_FIGURAS, exist_ok=True)
    resumo = agregar(linhas)
    arquivos = [salvar_resumo(resumo)]
    for canal in config.CANAIS:
        arquivos.append(grafico_ber_por_canal(resumo, canal))
    arquivos.append(grafico_awgn_vs_rajadas(resumo))
    arquivos.append(grafico_comparativo_codificacoes(resumo))
    arquivos += grafico_constelacoes()
    if mensagens:
        arquivos.append(grafico_recuperacao_mensagem(mensagens))
    salvar_tabela(tabela_compromisso(resumo))
    arquivos += [ARQUIVO_TABELA_MD, ARQUIVO_TABELA_CSV]
    return arquivos
