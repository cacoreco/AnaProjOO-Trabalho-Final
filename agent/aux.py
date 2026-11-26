# Esse é um módulo apenas para funções auxiliares para uso em outros locais

import argparse
import os

def coletar_argumentos() -> None:
    """
    coleta as argumentos passados pelo usuário na CLI
    """

    parser = argparse.ArgumentParser(
        prog='Agente Memento',
        description='Sistema multiagente em Python que ensina o padrão de projeto *Memento* (GoF) a um estudante iniciante.'
    )

    parser.add_argument("prompt", nargs="?", default=None)
    parser.add_argument('-m', '--modelo', default="ollama/qwen2.5:0.5b-8k", help="modelo de linguagem a ser usado")
    parser.add_argument('-t', '--temperatura', type=float, default=0.2, help="baixa: menos criatividade, menos invenção")
    parser.add_argument('-j', '--janela', type=int, default=8192, help="tamanho da janela de contexto")
    parser.add_argument('-p', '--porta', type=int, default=11434, help="porta em que o ollama está rodando")

    return parser.parse_args()

def porta_local(porta: int) -> str:
    """
    retorna uma URL local referente à porta especificada
    """

    return f"http://localhost:{porta}"

def limpa_tela() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")