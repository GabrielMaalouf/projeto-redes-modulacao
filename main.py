# main.py
# Ponto de entrada do simulador.
#
#   python main.py demo          -> mensagem ASCII passando pelo sistema (bits incorretos)
#   python main.py consistencia  -> teste de consistência (canal ideal e SNR elevada)
#   python main.py varredura     -> varredura completa de BER (gera results/raw/results.csv)
#   python main.py mensagem      -> recuperação da mensagem nos dois canais (results/raw/mensagem.csv)
#   python main.py graficos      -> figuras e tabela a partir dos CSVs brutos
#   python main.py tudo          -> todos os passos acima, em ordem

import os
import sys

# os caminhos de saída em config.py são relativos à raiz do projeto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src import config, experiments, plots


def cmd_demo():
    print(experiments.demonstracao())


def cmd_consistencia():
    ok, texto = experiments.teste_de_consistencia()
    print(texto)
    print("Salvo em", experiments.ARQUIVO_CONSISTENCIA)
    return ok


def cmd_varredura():
    print("Varredura: %d ensaios (%d bits cada)" % (config.total_de_ensaios(), config.N_BITS))
    arquivo = experiments.executar_varredura()
    print("Resultados brutos em", arquivo, "e configuracao em", config.ARQUIVO_CONFIG)


def cmd_mensagem():
    arquivo = experiments.executar_recuperacao_mensagem()
    print("Recuperacao da mensagem salva em", arquivo)


def cmd_graficos():
    if not os.path.exists(config.ARQUIVO_CSV):
        print("Rode antes: python main.py varredura")
        return
    mensagens = None
    if os.path.exists(experiments.ARQUIVO_MENSAGEM):
        mensagens = experiments.ler_mensagens()
    arquivos = plots.gerar_tudo(experiments.ler_resultados(), mensagens)
    print("Arquivos gerados:")
    for a in arquivos:
        print("  " + a)
    print()
    with open(plots.ARQUIVO_TABELA_MD, encoding="utf-8") as f:
        print(f.read())


def cmd_tudo():
    ok = cmd_consistencia()
    cmd_demo()
    cmd_varredura()
    cmd_mensagem()
    cmd_graficos()
    return ok


COMANDOS = {"demo": cmd_demo, "consistencia": cmd_consistencia, "varredura": cmd_varredura,
            "mensagem": cmd_mensagem, "graficos": cmd_graficos, "tudo": cmd_tudo}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMANDOS:
        print(__doc__ if __doc__ else "")
        print("Uso: python main.py [" + "|".join(COMANDOS) + "]")
        sys.exit(1)
    resultado = COMANDOS[sys.argv[1]]()
    sys.exit(1 if resultado is False else 0)
