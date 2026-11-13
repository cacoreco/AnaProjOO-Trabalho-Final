import gradio as gr

def resposta(text):
    return NotImplementedError("Não implementado ainda")

interface = gr.Interface(
    fn=resposta,
    title="Agente Tutor Padrão Memento",
    description="Sistema multiagente em Python que ensina o padrão de projeto *Memento* (GoF) a um estudante iniciante.",
    examples=[
        "Explique o que é o padrão Memento",
        "Como o padrão Memento costuma ser aplicado de forma errada? Dê um exemplo de uso equivocado e explique como corrigir",
        "Com qual padrão o Memento é mais confundido? Explique a diferença entre eles e por que essa confusão acontece."
    ],
    inputs=[gr.Textbox(lines=4, label="Prompt", placeholder="Digite seu prompt aqui")],
    outputs=gr.Textbox(lines=16, label="Resposta", placeholder="A resposta pode demorar alguns minutos")
)

interface.launch()