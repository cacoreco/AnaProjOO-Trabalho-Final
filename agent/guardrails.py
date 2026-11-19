"""Verificações determinísticas (sem modelo) feitas ANTES de chamar a crew.

Por quê: nos testes, o Guardião (modelo de 3B) escolheu o texto de recusa errado
(chegou a dizer que o Memento não existe). Pedidos inválidos previsíveis são
tratados aqui, com respostas fixas, o que é mais seguro e não gasta tempo de modelo.
Limitação: reconhece apenas formulações comuns; paráfrases incomuns passam para a crew,
onde as regras anti-alucinação dos prompts continuam valendo.
"""
import re
import unicodedata

CATALOGO_GOF = (
    "Abstract Factory", "Builder", "Factory Method", "Prototype", "Singleton",
    "Adapter", "Bridge", "Composite", "Decorator", "Facade", "Flyweight", "Proxy",
    "Chain of Responsibility", "Command", "Interpreter", "Iterator", "Mediator",
    "Memento", "Observer", "State", "Strategy", "Template Method", "Visitor",
)

MSG_PADRAO_INEXISTENTE = (
    "Não conheço um padrão chamado {nome} no catálogo GoF (são 23 padrões oficiais), "
    "então não vou inventar uma explicação. Posso explicar o Memento, que existe no "
    "catálogo. Quer começar pelo problema que ele resolve?"
)
MSG_SOLUCAO_PRONTA = (
    "Prefiro não entregar a solução pronta, porque você aprende mais construindo. "
    "Vamos por partes: no Editor com desfazer, quem guarda o estado anterior e quem "
    "pode ler o conteúdo guardado?"
)

FRASES_SOLUCAO_PRONTA = (
    "codigo pronto", "solucao pronta", "solucao completa", "resposta pronta",
    "resolva para mim", "resolva por mim", "faca por mim", "faca tudo por mim",
    "implemente tudo", "gabarito",
)


def _normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, para comparar sem se preocupar com grafia."""
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn").lower()


_CATALOGO_NORMALIZADO = {_normalizar(nome) for nome in CATALOGO_GOF}

# "padrão chamado Z", "padrão denominado Super Observer", "padrão chamado Chain of Responsibility"
_RE_NOME_PADRAO = re.compile(
    r"(?i:padr[ãa]o\s+(?:chamado|denominado|intitulado|de nome|conhecido como))"
    r"\s+[\"“‘']?(\w[\w\-]*(?:\s+(?:of|[A-ZÀ-Ý]\w*))*)"
)
# "invente um padrão", "invente outro padrão novo" (e não "invente um exemplo do padrão")
_RE_INVENTAR_PADRAO = re.compile(r"\binvent\w*\s+(?:um\s+|uma\s+|o\s+|outro\s+|novo\s+)*padr")


def _nome_existe(nome: str) -> bool:
    n = _normalizar(nome).strip()
    return n in _CATALOGO_NORMALIZADO or (
        len(n) >= 4 and any(c.startswith(n) for c in _CATALOGO_NORMALIZADO)
    )


def verificar_pedido(texto: str):
    """Devolve a resposta fixa se o pedido for inválido; devolve None se pode seguir para a crew."""
    achado = _RE_NOME_PADRAO.search(texto)
    if achado and not _nome_existe(achado.group(1)):
        return MSG_PADRAO_INEXISTENTE.format(nome=achado.group(1).strip())

    norm = _normalizar(texto)
    if not achado and _RE_INVENTAR_PADRAO.search(norm):
        return MSG_PADRAO_INEXISTENTE.format(nome="desse tipo")

    if any(frase in norm for frase in FRASES_SOLUCAO_PRONTA):
        return MSG_SOLUCAO_PRONTA
    return None
