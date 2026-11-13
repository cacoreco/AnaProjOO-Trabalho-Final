#!/usr/bin/env sh

# Script auxiliar para facilitar a configuração do ollama
#   Requisitos: archlinux com systemd
#   Autor: github.com/Adrian351lang

# Para o script só funcionar no arch (já que requer os comandos do arch)
[ -f /etc/arch-release ] || {
    echo "É necessário o arch linux para rodar esse script."
    exit 1
}

# systemd é o daemon do sistema necessário
command -v systemctl > /dev/null || {
    echo "É necessário o systemd para rodar esse script."
}

# Instala os pacotes necessários
#   UV = gerenciar versões python
#   Ollama = IA local
sudo pacman -S --needed uv ollama

# Inicia o ollama
sudo systemctl enable --now ollama || {
    echo "Falha ao iniciar o ollama."
    exit 1
}

# Conferir a instalação
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-3b-8k","messages":[{"role":"user","content":"Diga olá em uma frase."}]}'
