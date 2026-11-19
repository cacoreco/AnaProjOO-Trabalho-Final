#!/bin/sh

command -v uv || {
    echo "Erro: `uv` não está instalado."
    exit 1
}

# instala python 3.12
uv venv --python 3.12 .venv

# ativa o ambiente virtual
source .venv/bin/activate

# instala os requisitos
uv pip install -r lib/requirements.txt
uv pip install gradio

# testar se deu certo
python -c "from agente.prompts import carregar_fatos; print(len(carregar_fatos()), 'caracteres')"
