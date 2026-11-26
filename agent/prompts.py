# Leitura dos prompts e do arquivo de fatos (tudo fica em arquivos de texto na pasta `prompts/`).

from pathlib import Path

PASTA_PROMPTS = Path("prompts")
ARQUIVO_FATOS = "memento_fatos.md"
SECOES = ("ROLE", "GOAL", "BACKSTORY")

def carregar_fatos() -> str:
    """
    Lê a fonte de verdade sobre o Memento, usada pelos três agentes.

    Retorna:
        texto do arquivo em string
    """

    return (PASTA_PROMPTS / ARQUIVO_FATOS).read_text(encoding="utf-8").strip()
 
def carregar_prompt(nome: str, fatos: str, limite_linhas: int = 14) -> dict:
    """
    Lê prompts/<nome>.md e devolve o role, goal e backstory.

    Args:
        nome (str):             nome do arquivo md
        fatos (str):            string com fatos extraídos do arquivo de fatos
        limite_linhas (int):    limite de linhas da resposta

    Retorna:
        dict:                   {"ROLE", "GOAL", "BACKSTORY"}
    """

    # lê o texto do arquivo
    texto: str = (PASTA_PROMPTS / f"{nome}.md").read_text(encoding="utf-8")

    # Os marcadores {limite_linhas} e {fatos} são substituídos aqui, em Python, e não pelo CrewAI:
    # assim, chaves { } em códigos Java não são confundidas com variáveis.
    # {limite_linhas} vem de sistema.py (LIMITE_LINHAS): o tamanho da resposta é definido num lugar só.
    # Ele é trocado ANTES de {fatos}, para não mexer no texto dos FATOS.
    texto = texto.replace("{limite_linhas}", str(limite_linhas))
    texto = texto.replace("{fatos}", fatos)

    # variáveis auxiliares para o loop
    secoes = {}
    atual = None

    # percorre o arquivo linha por linha
    for linha in texto.splitlines():
        titulo = linha[3:].strip() if linha.startswith("## ") else None
        # se começou uma seção (ROLE, GOAL ou BACKSTORY)
        if titulo in SECOES:
            atual = titulo.lower()
            secoes[atual] = []
        # se linha pertence à seção atual
        elif atual is not None:
            secoes[atual].append(linha)

    # verifica se falta seções no arquivo
    faltando = [s.lower() for s in SECOES if s.lower() not in secoes]
    if faltando:
        raise ValueError(f"Prompt '{nome}.md' sem as seções: {faltando}")

    return {chave: "\n".join(linhas).strip() for chave, linhas in secoes.items()}