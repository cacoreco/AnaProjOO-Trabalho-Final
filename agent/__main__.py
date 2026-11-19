# Ponto de entrada:
#
# python -m agent "pergunta"
# OU
# python -m agent (modo conversa)

import logging
import sys

from .sistema import SistemaTutor
from .aux import coletar_argumentos

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