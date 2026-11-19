import logging
import gradio as gr
import argparse

from agent.sistema import SistemaTutor
from agent.__main__ import coletar_argumentos

def resposta(prompt):
    logging.getLogger("crewai").setLevel(logging.ERROR)

    args = coletar_argumentos()
    url= f"http://localhost:{args.porta}"

    try:
        sistema = SistemaTutor(args.modelo, url, args.temperatura, args.janela)
    except (OSError, ValueError) as erro:
        print(f"Erro ao iniciar o sistema: {erro}")
        sys.exit(1)

    return sistema.resposta(prompt)

interface = gr.Interface(
    fn=resposta,
    title="Agente Tutor Padrão Memento",
    description="Sistema multiagente em Python que ensina o padrão de projeto *Memento* (GoF) a um estudante iniciante.",
    examples=[
        "Explique o que é o padrão Memento",
        "Dê exemplo de situações para usar o padrão Memento",
        "Como o padrão Memento costuma ser aplicado de forma errada?"
    ],
    inputs=[gr.Textbox(lines=4, label="Prompt", placeholder="Digite seu prompt aqui")],
    outputs=gr.Textbox(lines=16, label="Resposta", placeholder="A resposta pode demorar alguns minutos")
)

if __name__ == "__main__":
    interface.launch()