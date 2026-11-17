# Ponto de entrada:
#
# python -m agent "pergunta"
# OU
# python -m agent (modo conversa)

import logging
import sys
import argparse

from .sistema import SistemaTutor

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

def main() -> None:
    logging.getLogger("crewai").setLevel(logging.ERROR)  # silencia avisos repetitivos do CrewAI

    args = coletar_argumentos()
    prompt = args.prompt
    url= f"http://localhost:{args.porta}"

    try:
        sistema = SistemaTutor(args.modelo, url, args.temperatura, args.janela)
    except (OSError, ValueError) as erro:
        print(f"Erro ao iniciar o sistema: {erro}")
        sys.exit(1)

    # Modo prompt pela CLI 
    if prompt is not None:
        print(sistema.resposta(prompt))
    # Modo conversa
    else:
        print("===================================")
        print("Sistema pedagógico: padrão Memento.")
        print("===================================")
        print()
        print("CTRL + C para sair.")
        print()
        while True:
            try:
                prompt = input("Você: ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if prompt.strip().lower() in ["sair", "exit", "quit", "q"]:
                break

            print(f"Sistema: {sistema.resposta(prompt)}")
        
        print()
        print("Saindo do sistema...")


if __name__ == "__main__":
    main()
