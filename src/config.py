# src/config.py
# Configuração do experimento: todos os parâmetros ficam aqui, em um único lugar.
# Os scripts (simulador, varredura, gráficos) e o README usam estes mesmos valores,
# o que garante que qualquer pessoa reproduza exatamente os mesmos resultados.

# Os parâmetros das rajadas ficam definidos no channel.py. Importamos de lá para
# não existirem dois valores diferentes para a mesma coisa.
from src.channel import PROB_BOM_PARA_RUIM, PROB_RUIM_PARA_BOM, QUEDA_SNR_RUIM_DB


# ---------- O que será comparado ----------

MODULACOES = ["BPSK", "QPSK", "16QAM"]          # 16-QAM é a de ordem superior
CODIFICACOES = ["MANCHESTER", "NRZI"]           # as duas codificações de linha
CANAIS = ["AWGN", "RAJADAS"]                    # canal base e segundo cenário


# ---------- Plano experimental ----------

# SNR = Eb/N0 em dB, por chip transmitido (9 valores; o enunciado pede pelo menos 8)
SNRS_DB = [0, 2, 4, 6, 8, 10, 12, 14, 16]

# Bits de INFORMAÇÃO por ensaio (o enunciado pede pelo menos 100.000).
# Com o Manchester, os chips transmitidos são o dobro disso.
N_BITS = 100000

# Cada seed é uma repetição com bits e ruído diferentes (o enunciado pede pelo menos 5).
SEEDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Com 10 seeds x 100.000 bits, cada ponto do gráfico usa 1.000.000 de bits.
# Então a menor BER que dá para medir é cerca de 1e-6. Quando nenhum erro é
# observado, o gráfico mostra este piso (em escala logarítmica o zero não existe).
PISO_BER = 1e-6


# ---------- Mensagem de demonstração e teste de consistência ----------

MENSAGEM_DEMO = "Redes de Computadores - UNISINOS"
SNR_ALTA_DB = 40                                # "SNR elevada" do teste de consistência
SNR_DEMO_DB = 8                                 # SNR da demonstração com a mensagem


# ---------- Arquivos de saída ----------

ARQUIVO_CSV = "results/raw/results.csv"
ARQUIVO_CONFIG = "results/raw/config.txt"
PASTA_FIGURAS = "results/figures"

# Colunas do CSV de resultados brutos (uma linha por ensaio)
COLUNAS_CSV = ["canal", "modulacao", "codificacao", "snr_db", "seed", "n_bits", "n_erros", "ber"]


# ---------- Funções auxiliares ----------

def total_de_ensaios():
    """Quantos ensaios a varredura completa executa."""
    return (len(CANAIS) * len(MODULACOES) * len(CODIFICACOES)
            * len(SNRS_DB) * len(SEEDS))


def texto_da_configuracao():
    """Texto com todos os parâmetros, para salvar junto dos resultados brutos."""
    linhas = []
    linhas.append("CONFIGURACAO DO EXPERIMENTO")
    linhas.append("Modulacoes: " + ", ".join(MODULACOES))
    linhas.append("Codificacoes de linha: " + ", ".join(CODIFICACOES))
    linhas.append("Canais: " + ", ".join(CANAIS))
    linhas.append("SNR (Eb/N0 por chip, em dB): " + ", ".join(str(s) for s in SNRS_DB))
    linhas.append("Bits de informacao por ensaio: " + str(N_BITS))
    linhas.append("Seeds (repeticoes): " + ", ".join(str(s) for s in SEEDS))
    linhas.append("Piso da BER nos graficos: " + str(PISO_BER))
    linhas.append("Rajadas: P(bom->ruim) = " + str(PROB_BOM_PARA_RUIM))
    linhas.append("Rajadas: P(ruim->bom) = " + str(PROB_RUIM_PARA_BOM))
    linhas.append("Rajadas: queda de SNR no estado ruim (dB) = " + str(QUEDA_SNR_RUIM_DB))
    linhas.append("Mensagem de demonstracao: " + MENSAGEM_DEMO)
    linhas.append("SNR alta do teste de consistencia (dB): " + str(SNR_ALTA_DB))
    linhas.append("Total de ensaios: " + str(total_de_ensaios()))
    return "\n".join(linhas) + "\n"
