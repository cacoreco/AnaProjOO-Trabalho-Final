#!/bin/sh

command -v uv || {
    echo "Erro: `uv` não está instalado."
    exit 1
}

cd frontend

# instala python 3.12
uv venv --python 3.12 .venv

# ativa o ambiente virtual
source .venv/bin/activate

# instala os requisitos
uv pip install gradio