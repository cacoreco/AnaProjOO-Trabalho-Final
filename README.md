# Tutor multiagente do padrão Memento

Sistema multiagente em Python que ensina o padrão de projeto **Memento** (GoF) a um estudante iniciante.
Trabalho final de ELC1070 – Análise e Projeto de Sistemas OO (UFSM).

- **Custo zero:** roda 100% local, com um modelo de linguagem executado pelo Ollama. Não usa API paga nem chave de API. A internet só é necessária para baixar o modelo e as bibliotecas.
- **Framework:** [CrewAI](https://docs.crewai.com/).
- **Três agentes em sequência:** Tutor (explica) → Inquiridor (pergunta e avalia) → Guardião (revisa e aplica as regras anti-alucinação).
- **Fonte de verdade:** `prompts/memento_fatos.md`. É o único conteúdo sobre o Memento que os agentes podem usar.

> Este README é preliminar e serve para preparar o ambiente. A versão final da entrega será ampliada a partir dele.

## Requisitos

| Item | Detalhe |
|---|---|
| Sistema | Arch Linux (ou derivada, como EndeavourOS) |
| Python | **3.12** (o CrewAI não suporta o 3.14, que é a versão padrão do Arch hoje) |
| Ollama | serviço local em `localhost:11434` |
| Modelo | `qwen2.5:3b` (cerca de 1,9 GB em disco) |
| Memória | testado com 15 GiB de RAM, em CPU |
| Tempo | cada resposta leva de 1 a 3 minutos em CPU, porque cada pergunta faz 3 chamadas ao modelo |

## Preparar o ambiente

### 1. Preparar o Ollama

```shell
setup/install-ollama.sh
```

`uv` é o gerenciador que instala o Python 3.12 sem mexer no Python do sistema. Com placa de vídeo existem variantes do pacote do Ollama (por exemplo, `ollama-cuda` para NVIDIA); sem GPU, o pacote `ollama` basta.

Por que a variante: o Ollama usa por padrão uma janela de contexto pequena (4096 tokens) e **corta o prompt em silêncio** quando ela estoura, o que apagaria as regras dos agentes. O `Modelfile` fixa `num_ctx 8192`. O CrewAI fala com o Ollama por um endereço que não permite ajustar esse valor por requisição, então a configuração precisa estar no modelo.

### 2. Ambiente Python 3.12

```shell
setup/configure-python.sh
```

### 3. Ativar o ambiente virtual python

```shell
source .venv/bin/activate            # no fish: source .venv/bin/activate.fish
```

Todo terminal novo precisa repetir o `source .venv/bin/activate`. O prompt passa a mostrar `(.venv)`.

## Executar

```bash
python -m agente "Explique o que é o padrão Memento"   # uma pergunta, imprime a resposta e encerra
python -m agente                                       # modo conversa (digite 'sair' para encerrar)
python -m tests.cenarios                               # roda os cenários do roteiro e salva em tests/resultados/
```

Os cenários levam cerca de 20 minutos. Feche programas pesados e **não edite arquivos** enquanto eles rodam, porque cada cenário relê os prompts.

## Estrutura do projeto

```
├── Modelfile                 # variante do modelo com contexto de 8192
├── requirements.txt          # dependências com versões fixadas
├── agente/
│   ├── __main__.py           # CLI: python -m agente
│   ├── sistema.py            # os três agentes, as tarefas e o tratamento de erros
│   └── prompts.py            # lê os prompts e o arquivo de fatos
├── prompts/
│   ├── memento_fatos.md      # fonte de verdade sobre o Memento
│   ├── tutor.md
│   ├── inquiridor.md
│   └── guardiao.md
├── setup/                    # scripts de configuração
│   ├── configure-python.sh
│   └── install-ollama.sh
└── tests/
    ├── cenarios.py           # roteiro de cenários de teste
    └── resultados/           # uma rodada por arquivo (iteracao1.md, iteracao2.md...)
```

## Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `failed to run custom build command for pyo3-ffi` ao instalar | Você está no Python 3.14. Recrie o ambiente com `uv venv --python 3.12 .venv`. |
| "Não consegui falar com o modelo local" | O Ollama está parado (`sudo systemctl start ollama`) ou a variante não existe (`ollama list`). A linha "Detalhe técnico" da mensagem mostra a causa real. |
| `model not found` | Falta rodar o `ollama create qwen2.5-3b-8k -f Modelfile`. |
| `No module named agente` | Você não está na pasta raiz do projeto. Rode os comandos a partir dela. |
| Respostas muito lentas | Esperado em CPU. Feche o navegador e outros programas pesados. |

## Trabalhando em dupla

- Rode `git pull` antes de começar e faça commits pequenos, com mensagem clara.
- **Evite editar o mesmo arquivo ao mesmo tempo**, principalmente os de `prompts/`. Combinem quem mexe em qual.
- Depois de cada mudança nos prompts ou no código, rode os cenários e salve o resultado em `tests/resultados/` com um nome novo. É a evidência para o relatório.
- Nunca coloque chave de API, senha ou token no repositório. O projeto não precisa de nenhum.
