import gradio as gr

def resposta(text):
    return NotImplementedError("Não implementado ainda")

interface = gr.Interface(
    fn=resposta,
    inputs=[gr.Textbox(label="Insira o seu Prompt")],
    outputs=gr.Textbox(label="Resposta (Aguardar alguns minutos)")
)

interface.launch()