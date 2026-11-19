# Tutor multiagente do padrão Memento

Sistema multiagente em Python que ensina o padrão de projeto **Memento** (GoF) a um estudante iniciante.
Trabalho final de ELC1070 – Análise e Projeto de Sistemas OO (UFSM).

## Funcionalidades

- **100% offline:** Modelos de linguagem local são usados pelo `Ollama`. A internet só é necessária para baixar o modelo e as bibliotecas.
- **Custo zero:** Não usa API paga nem chave de API. Pode gerar gastos com energia pelo alto uso da CPU.
- **Framework:** [CrewAI](https://docs.crewai.com/). Usa vários agentes colaborativos.
- **Três agentes em sequência:** Tutor (explica) → Inquiridor (pergunta e avalia) → Guardião (revisa e aplica as regras anti-alucinação).
- **Fonte de verdade:** `prompts/memento_fatos.md`. É o único conteúdo sobre o Memento que os agentes podem usar.
- **CLI configurável:** Capacidade de especificar modelo, temperatura e outros pela linha de comando.
- **Interface Web Simples:** Alternativa à versão por linha de comando.
- **Instalação automatizada:** Scripts prontos para instalação e setup na pasta `scripts`.

## Requisitos

| Item    | Descrição                                                                                 |
|---------|-------------------------------------------------------------------------------------------|
| Sistema | [Arch Linux](https://archlinux.org) (ou derivados)                                        |
| Python  | versão `3.12` (o CrewAI não suporta o 3.14, que é a versão padrão do Arch hoje)           |
| Ollama  | serviço local a ser rodado em `localhost`                                                 |
| Modelo  | `qwen2.5:0.5b` ou similares (cerca de 500 MiB em disco)                                   |
| Memória | testado com 8 GiB de RAM, em CPU                                                          |
| Tempo   | cada resposta leva de 1 a 3 minutos em CPU, porque cada pergunta faz 3 chamadas ao modelo |

## Instalação

### 1. Preparar o Ollama

Rodar o seguinte comando:

```shell
scripts/1.install-ollama.sh
```

> `uv` é o gerenciador que instala o Python 3.12 sem mexer no Python do sistema. Com placa de vídeo existem variantes do pacote do Ollama (por exemplo, `ollama-cuda` para NVIDIA); sem GPU, o pacote `ollama` basta.

> Por que a variante: o Ollama usa por padrão uma janela de contexto pequena (4096 tokens) e **corta o prompt em silêncio** quando ela estoura, o que apagaria as regras dos agentes. O `Modelfile` fixa `num_ctx 8192`. O CrewAI fala com o Ollama por um endereço que não permite ajustar esse valor por requisição, então a configuração precisa estar no modelo.

### 2. Ambiente Python 3.12

Rodar o seguinte comando:

```shell
scripts/2.setup-agente.sh
```

### 3. Ativar o ambiente virtual python

Rodar o seguinte comando:

```shell
source .venv/bin/activate            # no fish: source .venv/bin/activate.fish
```

> NOTA: Todo terminal novo precisa repetir o `source .venv/bin/activate`. O prompt passa a mostrar `(.venv)`.

> DICA: Definir alias de comando para iniciar venv (opcional)

#### Bash e Zsh
Adicionar o seguinte código ao seu `.bashrc` ou `.zshrc`:
```shell
alias venv="source .venv/bin/activate"
```

#### Fish
Adicionar o seguinte código ao seu `.config/fish/config.fish`:
```shell
alias venv "source .venv/bin/activate.fish"
```

## Execução

### Método 1: Pela CLI

```shell
venv
python -m agent "Explique o que é o padrão Memento"    # uma pergunta, imprime a resposta e encerra
python -m agent                                        # modo conversa (digite 'sair' para encerrar)
python -m tests                                        # roda os cenários do roteiro e salva em tests/resultados/
```

#### Opções

| Flag           | Opção Longa               | Descrição                                 |
|----------------|---------------------------|-------------------------------------------|
| -h             | --help                    | mostrar ajuda                             |
| -m MODELO      | --modelo MODELO           | modelo de linguagem a ser usado           |
| -t TEMPERATURA | --temperatura TEMPERATURA | baixa: menos criatividade, menos invenção |
| -j JANELA      | --janela JANELA           | tamanho da janela de contexto             |
| -p PORTA       | --porta PORTA             | porta a ser usada pelo servidor local     |

### Método 2: Pela Interface Web

```shell
venv
python -m gui
```

Acessar http://localhost:7860

Os cenários levam cerca de 20 minutos. Feche programas pesados e **não edite arquivos** enquanto eles rodam, porque cada cenário relê os prompts.

## Estrutura do projeto

```shell
├── Modelfile                   # variante do modelo com contexto de 8192
├── agent/
│   ├── __main__.py             # CLI: python -m agent
│   ├── sistema.py              # os três agentes, as tarefas e o tratamento de erros
│   └── prompts.py              # lê os prompts e o arquivo de fatos
├── docs/
│   └── resultados/             # resultados em markdown dos testes
├── gui/
│   └── __main__.py             # Interface Web
├── lib/
│   └── requirements.txt        # dependências com versões fixadas
├── prompts/
│   ├── memento_fatos.md        # fonte de verdade sobre o Memento
│   ├── tutor.md                # instruções de explicação
│   ├── inquiridor.md           # instruções de pergunta
│   └── guardiao.md             # instruções de revisão
├── scripts/
│   ├── configure-python.sh     # configura  o ambiente virtual
│   └── install-ollama.sh       # instala o ollama e os modelos
└── tests/
    └── __main__.py             # roteiro de cenários de teste
```

## Problemas comuns

| Sintoma                                                       | Causa e solução                                                                                                                                           |
|---------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `failed to run custom build command for pyo3-ffi` ao instalar | Você está no Python 3.14. Recrie o ambiente com `uv venv --python 3.12 .venv`.                                                                            |
| "Não consegui falar com o modelo local"                       | O Ollama está parado (`sudo systemctl start ollama`) ou a variante não existe (`ollama list`). A linha "Detalhe técnico" da mensagem mostra a causa real. |
| `model not found`                                             | Falta rodar o `ollama create qwen2.5-3b-8k -f Modelfile`.                                                                                                 |
| `ModuleNotFoundError: No module named agente`                 | Você não está na pasta raiz do projeto. Rode os comandos a partir dela.                                                                                   |
| `ModuleNotFoundError: No module named 'crewai`                | Você esqueceu de rodar o `activate` para ativar o `venv`                                                                                                  |
| Respostas muito lentas                                        | Esperado em CPU. Feche o navegador e outros programas pesados ou tente trocar o modelo.                                                                   |

## Trabalhando em dupla

- Rode `git pull` **antes de começar**, para evitar conflitos.
- Faça **commits pequenos** com **mesagens claras**.
- **Evite editar o mesmo arquivo ao mesmo tempo**, principalmente os de `prompts/`. Combinem quem mexe em qual.
- Depois de cada mudança nos prompts ou no código, **rode os testes**. O resultado será salvo em `docs/resultados`. É a evidência para o relatório.
- Nunca coloque chave de API, senha ou token no repositório. O projeto não precisa de nenhum.
