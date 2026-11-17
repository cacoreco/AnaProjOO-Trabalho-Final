# Ponto de entrada:
#
# python -m agent "pergunta"
# OU
# python -m agent (modo conversa)

import logging
import sys

from .sistema import SistemaTutor

def inicializa_sistema():
    
    try:
        sistema = SistemaTutor()
        return sistema
    except (OSError, ValueError) as erro:  # prompt ou arquivo de fatos ausente/inválido
        return None

def main() -> None:
    logging.getLogger("crewai").setLevel(logging.ERROR)  # silencia avisos repetitivos do CrewAI

    try:
        sistema = SistemaTutor()
    except (OSError, ValueError) as erro:
        print(f"Erro ao iniciar o sistema: {erro}")
        sys.exit(1)
        
    
    prompt = "".join(sys.argv[1:])

    # Modo prompt pela CLI 
    if len(sys.argv) > 1:
        print(sistema.resposta(prompt))
    # Modo conversa
    else:
        print("===================================")
        print("Sistema pedagógico: padrão Memento.")
        print("===================================")
        print()
        print("Aperte 'Q' para sair.")
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
