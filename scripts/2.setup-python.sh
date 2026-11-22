#!/bin/sh
set -eu

# Script auxiliar para facilitar a configuração do python
# REQUISITOS: archlinux, systemctl, curl

# Constantes
versao_python=3.12
arquivo_requisitos="lib/requirements.txt"

# Função auxiliar
sair_com_erro() {
    printf 'ERRO: %s\n' "$*"
    exit 1
}

# Não deixa o usuário rodar o script como root
[ "$EUID" -ne 0 ] || sair_com_erro "Evite rodar scripts como root."

# Verifica se o sistema é arch linux 
[ -f /etc/arch-release ] || sair_com_erro "É necessário o Arch Linux para rodar esse script."

# PASSO 1: Instala o UV (necessário para criar o ambiente virtual)
read -n 1 -p "NOTA: o comando seguinte precisa de previlégios de administrador. Aceitar (S/n)? " resposta
printf "\n"
[ "$resposta" != "n" -a "$resposta" != "N" ] || {
    echo "Saindo..."
    exit
}

sudo pacman -Sy --needed uv

# Instala python 3.12
uv venv --python "$versao_python" .venv

# ativa o ambiente virtual
source .venv/bin/activate

# instala os requisitos
uv pip install -r "$arquivo_requisitos" || sair_com_erro "Erro ao instalar os requisitos."

# testar se deu certo
python -c "from agente.prompts import carregar_fatos; print(len(carregar_fatos()), 'caracteres')" \
    || sair_com_erro "Erro ao configurar o ambiente."
