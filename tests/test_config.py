# tests/test_config.py
# Confere se a configuração atende o plano experimental do enunciado.

from src import config
from src.modulation import bits_por_simbolo
from src.metrics import CHIPS_POR_BIT
from src import channel


def test_pelo_menos_8_valores_de_snr():
    assert len(config.SNRS_DB) >= 8
    assert config.SNRS_DB == sorted(config.SNRS_DB)       # em ordem crescente
    assert len(set(config.SNRS_DB)) == len(config.SNRS_DB)  # sem repetição


def test_pelo_menos_100_mil_bits():
    assert config.N_BITS >= 100000


def test_pelo_menos_5_repeticoes_diferentes():
    assert len(config.SEEDS) >= 5
    assert len(set(config.SEEDS)) == len(config.SEEDS)


def test_tres_modulacoes_com_uma_de_ordem_superior():
    assert len(config.MODULACOES) >= 3
    assert "16QAM" in config.MODULACOES
    for nome in config.MODULACOES:
        assert bits_por_simbolo(nome) >= 1                # o modulation.py conhece o nome


def test_duas_codificacoes_de_linha():
    assert len(config.CODIFICACOES) >= 2
    for nome in config.CODIFICACOES:
        assert nome in CHIPS_POR_BIT                      # o metrics.py conhece o nome


def test_dois_canais():
    assert config.CANAIS == ["AWGN", "RAJADAS"]


def test_parametros_das_rajadas_vem_do_channel():
    assert config.PROB_BOM_PARA_RUIM == channel.PROB_BOM_PARA_RUIM
    assert config.PROB_RUIM_PARA_BOM == channel.PROB_RUIM_PARA_BOM
    assert config.QUEDA_SNR_RUIM_DB == channel.QUEDA_SNR_RUIM_DB


def test_total_de_ensaios():
    # 2 canais x 3 modulacoes x 2 codificacoes x 9 SNRs x 10 seeds = 1080
    assert config.total_de_ensaios() == 1080


def test_piso_da_ber_compativel_com_a_amostra():
    # o piso deve ser da ordem de 1 / (bits por ponto)
    bits_por_ponto = config.N_BITS * len(config.SEEDS)
    assert config.PISO_BER == 1 / bits_por_ponto


def test_colunas_do_csv():
    assert config.COLUNAS_CSV == ["canal", "modulacao", "codificacao",
                                  "snr_db", "seed", "n_bits", "n_erros", "ber"]


def test_texto_da_configuracao_registra_tudo():
    texto = config.texto_da_configuracao()
    assert "Seeds" in texto
    assert "Bits de informacao por ensaio: 100000" in texto
    assert "P(bom->ruim)" in texto
    assert "Total de ensaios: 1080" in texto
