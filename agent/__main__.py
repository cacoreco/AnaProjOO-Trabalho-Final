# Ponto de entrada:
#
# python -m agent "pergunta"
# OU
# python -m agent (modo conversa)

import logging
import sys

from .sistema import SistemaTutor

def inicializa_sistema():
    logging.getLogger("crewai").setLevel(logging.ERROR)  # silencia avisos repetitivos do CrewAI
    try:
        sistema = SistemaTutor()
        return sistema
    except (OSError, ValueError) as erro:  # prompt ou arquivo de fatos ausente/inválido
        return None

def resposta(prompt, sistema):
    return sistema.resposta(prompt)

def main() -> None:
    sistema = inicializa_sistema()
    if sistema is None:
        print("Erro ao iniciar o sistema")
        sys.exit(1)
    
    prompt = sys.argv[1:]

    # Modo prompt pela CLI 
    if len(sys.argv) > 1:
        print(resposta(prompt, sistema))
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
                pergunta = input("Você: ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if pergunta.strip().lower() in ["sair", "exit", "quit", "q"]:
                break

            print(f"Sistema: {sistema.resposta(pergunta)}")
        
        print()
        print("Saindo do sistema...")


if __name__ == "__main__":
    main()
