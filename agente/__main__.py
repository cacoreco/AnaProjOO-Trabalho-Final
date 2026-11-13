"""Ponto de entrada: python -m agente "pergunta"   ou   python -m agente (modo conversa)."""
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
    return sistema.resposta(" ".join(prompt))

def main() -> None:
    sistema = inicializa_sistema()
    if sistema is None:
        print(f"Erro ao iniciar o sistema: {erro}")
        sys.exit(1)

    if len(sys.argv) > 1:  # modo comando único: imprime a resposta e encerra
        print(resposta(sys.argv[1:], sistema))
        return

    print("Sistema pedagógico: padrão Memento.")
    print("Digite 'sair' para encerrar.")
    while True:
        try:
            pergunta = input("Você: ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if pergunta.strip().lower() == "sair":
            break
        print(f"Sistema: {sistema.resposta(pergunta)}")


if __name__ == "__main__":
    main()
