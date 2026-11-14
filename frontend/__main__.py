import gradio as gr

import agente

def resposta(prompt):
    sistema = agente.inicializa_sistema()
    if sistema is None:
        return "Erro ao iniciar o sistema"

    return agente.resposta(prompt, sistema)

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

interface.launch()