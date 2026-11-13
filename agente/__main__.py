"""Ponto de entrada: python -m agente "pergunta"   ou   python -m agente (modo conversa)."""
import logging
import sys

from .sistema import SistemaTutor


def main() -> None:
    logging.getLogger("crewai").setLevel(logging.ERROR)  # silencia avisos repetitivos do CrewAI
    try:
        sistema = SistemaTutor()
    except (OSError, ValueError) as erro:  # prompt ou arquivo de fatos ausente/inválido
        print(f"Erro ao iniciar o sistema: {erro}")
        sys.exit(1)

    if len(sys.argv) > 1:  # modo comando único: imprime a resposta e encerra
        print(sistema.resposta(" ".join(sys.argv[1:])))
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
