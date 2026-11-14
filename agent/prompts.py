"""Leitura dos prompts e do arquivo de fatos (tudo fica em arquivos de texto na pasta prompts/)."""
from pathlib import Path

PASTA_PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
SECOES = ("ROLE", "GOAL", "BACKSTORY")


def carregar_fatos() -> str:
    """Lê a fonte de verdade sobre o Memento, usada pelos três agentes."""
    return (PASTA_PROMPTS / "memento_fatos.md").read_text(encoding="utf-8").strip()


def carregar_prompt(nome: str, fatos: str) -> dict:
    """Lê prompts/<nome>.md e devolve {'role', 'goal', 'backstory'}.

    O marcador {fatos} é substituído aqui, em Python, e não pelo CrewAI:
    assim, chaves { } em códigos Java não são confundidas com variáveis.
    """
    texto = (PASTA_PROMPTS / f"{nome}.md").read_text(encoding="utf-8")
    texto = texto.replace("{fatos}", fatos)

    secoes = {}
    atual = None
    for linha in texto.splitlines():
        titulo = linha[3:].strip() if linha.startswith("## ") else None
        if titulo in SECOES:            # começou uma seção (ROLE, GOAL ou BACKSTORY)
            atual = titulo.lower()
            secoes[atual] = []
        elif atual is not None:         # linha pertence à seção atual
            secoes[atual].append(linha)

    faltando = [s.lower() for s in SECOES if s.lower() not in secoes]
    if faltando:
        raise ValueError(f"Prompt '{nome}.md' sem as seções: {faltando}")
    return {chave: "\n".join(linhas).strip() for chave, linhas in secoes.items()}
