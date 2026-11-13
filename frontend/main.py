import gradio as gr

def reverse_text(text):
    return NotImplementedError("Não implementado ainda")

interface = gr.Interface(
    fn=reverse_text,
    inputs=[gr.Textbox(label="Insira o seu Prompt")],
    outputs=gr.Textbox(label="Resposta (Aguardar alguns minutos)")
)

interface.launch()