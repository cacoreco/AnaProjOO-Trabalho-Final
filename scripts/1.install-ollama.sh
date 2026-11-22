#!/bin/sh
set -eu

modelo="qwen2.5:0.5b"
modelfile=".modelfile"

# Script auxiliar para facilitar a configuração do ollama
#   Requisitos: archlinux com systemd

sair_com_erro() {
    printf '%s\n' "$*"
    exit 1
}

# Para o script só funcionar no arch (já que requer os comandos do arch)
# O comando systemctl também é necessário
[ -f /etc/arch-release ] || sair_com_erro "É necessário o Arch Linux para rodar esse script."
command -v systemctl >/dev/null || sair_com_erro "comando \"systemctl\" não encontrado."

# Instala o Ollama (se já não estiver instalado)
sudo pacman -S --needed ollama

# Inicia o ollama
sudo systemctl enable --now ollama || sair_com_erro "Falha ao iniciar o ollama."

# Instala o modelo
ollama pull "$modelo" || sair_com_erro "Falha ao instalar o modelo $modelo."
ollama create "$modelo-8k" -f "$modelfile"  || sair_com_erro "Falha ao criar o modelo $modelo."

# Conferir a instalação
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-0.5b-8k","messages":[{"role":"user","content":"Diga olá em uma frase."}]}' \
  || sair_com_erro "Erro ao testar o modelo"

printf '\n%s\n' "Ollama e modelo instalados e funcionando."