# Esse é um módulo apenas para funções auxiliares para uso em outros locais

import argparse
import os

def coletar_argumentos():
    parser = argparse.ArgumentParser(
        prog='Agente Memento',
        description='Sistema multiagente em Python que ensina o padrão de projeto *Memento* (GoF) a um estudante iniciante.'
    )

    parser.add_argument("prompt", nargs="?", default=None)
    parser.add_argument('-m', '--modelo', default="ollama/qwen2.5-0.5b-8k", help="modelo de linguagem a ser usado")
    parser.add_argument('-t', '--temperatura', default=0.2, help="baixa: menos criatividade, menos invenção")
    parser.add_argument('-j', '--janela', default=8192, help="tamanho da janela de contexto")
    parser.add_argument('-p', '--porta', default=11434, help="porta a ser usada pelo servidor local")

    return parser.parse_args()

def porta_local(porta):
    return f"http://localhost:{porta}"

def limpa_tela():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")