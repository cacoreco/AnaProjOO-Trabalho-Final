# Abre um servidor web local que provém uma interface para o agente

import logging
import gradio
import sys

from agent import SistemaTutor, coletar_argumentos, porta_local

def main() -> None:
    logging.getLogger("crewai").setLevel(logging.ERROR)

    args = coletar_argumentos()
    url= porta_local(args.porta)

    try:
        sistema = SistemaTutor(args.modelo, url, args.temperatura, args.janela)
    except (OSError, ValueError) as erro:
        print(f"Erro ao iniciar o sistema: {erro}")
        sys.exit(1)

    interface = gradio.Interface(
        fn=sistema.resposta,
        title="Agente Tutor Padrão Memento",
        description="Sistema multiagente em Python que ensina o padrão de projeto *Memento* (GoF) a um estudante iniciante.",
        examples=[
            "Explique o que é o padrão Memento",
            "Dê exemplo de situações para usar o padrão Memento",
            "Como o padrão Memento costuma ser aplicado de forma errada?"
        ],
        inputs=[gradio.Textbox(lines=4, label="Prompt", placeholder="Digite seu prompt aqui")],
        outputs=gradio.Textbox(lines=16, label="Resposta", placeholder="A resposta pode demorar alguns minutos")
    )

    interface.launch(theme=gradio.themes.Base())

if __name__ == "__main__":
    main()