# Ponto de entrada:
#
# python -m cli "pergunta"
# OU
# python -m cli (modo conversa)

import logging
import sys

from colorama import Fore

from agent import SistemaTutor, coletar_argumentos, porta_local, limpa_tela

def main() -> None:
    logging.getLogger("crewai").setLevel(logging.ERROR)  # silencia avisos repetitivos do CrewAI

    args = coletar_argumentos()
    prompt = args.prompt
    url= porta_local(args.porta)

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
        limpa_tela()

        print(Fore.YELLOW + "===================================" + Fore.RESET)
        print(Fore.YELLOW + "Sistema pedagógico: padrão Memento." + Fore.RESET)
        print(Fore.YELLOW + "===================================" + Fore.RESET)
        print()
        print(Fore.LIGHTBLACK_EX + "`CTRL + C` para sair." + Fore.RESET)
        print()
        while True:
            try:
                prompt = input(Fore.BLUE + "Você: " + Fore.RESET)
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if prompt.strip().lower() in ("sair", "exit", "quit", "q"):
                break

            resposta = sistema.resposta(prompt)
            if resposta == "AÇÃO INTERROMPIDA":
                break

            print(Fore.RED + "Sistema: " + Fore.RESET + resposta)
        
        print()
        print(Fore.LIGHTBLACK_EX + "Saindo do sistema..." + Fore.RESET)

if __name__ == "__main__":
    main()