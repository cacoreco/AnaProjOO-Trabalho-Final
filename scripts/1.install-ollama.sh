#!/bin/sh
set -eu

# Script auxiliar para facilitar a configuração do ollama
# REQUISITOS: archlinux, systemctl, curl

# Constantes
modelo="qwen2.5:0.5b"
modelfile=".modelfile"

# Função auxiliar
sair_com_erro() {
    printf 'ERRO: %s\n' "$*"
    exit 1
}

# Verifica se o sistema é arch linux 
[ -f /etc/arch-release ] || sair_com_erro "É necessário o Arch Linux para rodar esse script."
command -v systemctl >/dev/null || sair_com_erro "comando \"systemctl\" não encontrado."

# PASSO 1: Instalar o Ollama (se já não estiver instalado)
sudo pacman -Sy --needed ollama

# PASSO 2: Iniciar o ollama
sudo systemctl enable --now ollama || sair_com_erro "Falha ao iniciar o ollama."

# PASSO 3: Instalar o modelo
ollama pull "$modelo" || sair_com_erro "Falha ao instalar o modelo $modelo."
ollama create "$modelo-8k" -f "$modelfile"  || sair_com_erro "Falha ao criar o modelo $modelo."

# PASSO 4: Testar se está funcionando
if command -v curl > /dev/null; then
    curl http://localhost:11434/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"model":"qwen2.5-0.5b-8k","messages":[{"role":"user","content":"Diga olá em uma frase."}]}' \
    || sair_com_erro "Erro ao testar o modelo"
else
    sair_com_erro "Commando \"curl\" não encontrado."
fi

# FIM
printf '\n%s\n' "Ollama e modelo instalados e funcionando."