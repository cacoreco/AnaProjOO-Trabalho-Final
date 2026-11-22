# Verificações determinísticas (sem modelo) feitas ANTES de chamar a crew.

"""
Por quê: nos testes, o Guardião (modelo de 3B) escolheu o texto de recusa errado
(chegou a dizer que o Memento não existe). Pedidos inválidos previsíveis são
tratados aqui, com respostas fixas, o que é mais seguro e não gasta tempo de modelo.
Mais tarde, cumprimentos ("teste", "olá") e assuntos fora do tema ("receita de miojo") também
passaram a ser tratados aqui: o modelo respondia a eles repetindo a explicação anterior.
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

# As mensagens fixas que não fazem uma pergunta ao estudante terminam sem "?": assim, a próxima
# mensagem não é confundida com uma resposta a ser avaliada pelo Inquiridor.
MSG_PADRAO_INEXISTENTE = (
    "Não conheço um padrão chamado {nome} no catálogo GoF (são 23 padrões oficiais), "
    "então não vou inventar uma explicação. Posso explicar o Memento, que existe no "
    "catálogo. Se quiser, pergunte: \"Qual problema o Memento resolve?\""
)
MSG_SAUDACAO = (
    "Olá! Sou um tutor do padrão de projeto Memento (GoF). Você pode perguntar, por exemplo: "
    "\"O que é o padrão Memento?\" ou \"Dê um exemplo do Memento em Java.\""
)
MSG_FORA_DO_TEMA = (
    "Esse assunto está fora do que eu ensino: só consigo ajudar com o padrão de projeto "
    "Memento (GoF). Você pode perguntar, por exemplo: \"Qual problema o Memento resolve?\""
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

# Mensagens que são só cumprimento ou teste (comparadas com o texto inteiro, sem pontuação).
SAUDACOES = {
    "oi", "ola", "opa", "eai", "e ai", "hey", "hello", "hi", "teste", "testando", "test",
    "bom dia", "boa tarde", "boa noite", "tudo bem", "oi tudo bem", "ola tudo bem",
    "tudo bom", "oi tudo bom", "ola tudo bom", "alo",
}

# Prefixos de palavras do assunto (padrões de projeto, OO e o exemplo do Editor).
# Basta UMA palavra da mensagem começar com um deles para ela ser considerada do tema.
RADICAIS_DO_TEMA = (
    "memento", "padr", "pattern", "gof", "gang", "originator", "originador", "caretaker",
    "zelador", "snapshot", "estado", "state", "desfaz", "undo", "redo", "refaz", "encapsul",
    "editor", "histor", "command", "comando", "restaur", "salv", "guard", "java", "codigo",
    "classe", "objeto", "interface", "metodo", "atribut", "orientad", "heranc", "polimorf",
    "participant", "consequenc", "copi", "mutave", "imutave", "getter", "setter", "get",
    "set", "privad", "private", "public", "implement", "pilha", "stack", "lista", "string",
    "texto", "memoria", "uml", "diagrama", "software", "programa", "sistema",
    "projeto", "design", "observer", "singleton", "strategy", "factory", "catalogo",
    "intencao", "estrutura", "narrow", "wide", "estreita", "larga", "opaco", "checkpoint",
    "versao", "backup", "rollback", "transac", "ctrl",
)

# Palavras genéricas, que aparecem em pedidos de continuação ("dê um exemplo", "não entendi")
# e em respostas curtas ("não sei"). Sozinhas, não indicam que a mensagem é de outro assunto.
PALAVRAS_GENERICAS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos", "e",
    "em", "no", "na", "nos", "nas", "por", "para", "pra", "pro", "com", "sem", "sobre", "que",
    "se", "me", "mim", "eu", "voce", "vc", "ele", "ela", "isso", "isto", "esse", "essa",
    "este", "esta", "aquilo", "aqui", "ai", "la", "mais", "menos", "muito", "pouco", "melhor",
    "pior", "outro", "outra", "outros", "novamente", "denovo", "de novo", "ainda", "agora",
    "entao", "tambem", "so", "ja", "nao", "sim", "talvez", "acho", "certo", "errado",
    "correto", "verdade", "ok", "okay", "beleza", "valeu", "obrigado", "obrigada", "por favor",
    "favor", "explique", "explica", "explicar", "explicacao", "exemplo", "exemplos",
    "exemplifique", "mostre", "mostra", "mostrar", "de", "da", "dar", "fale", "fala",
    "falar", "descreva", "descrever", "resuma", "resumo", "resumir", "continue", "continua",
    "continuar", "detalhe", "detalhes", "detalhar", "entendi", "entender", "entendo",
    "sei", "sabe", "saber", "duvida", "duvidas", "pergunta", "perguntas", "resposta",
    "responda", "como", "qual", "quais", "quando", "onde", "quem", "porque", "pq", "por que",
    "quero", "queria", "gostaria", "pode", "poderia", "consegue", "ajuda", "ajude",
    "ajudar", "preciso", "tenho", "tem", "ter", "e", "eh", "ser", "sao", "sera", "foi",
    "esta", "estou", "fica", "ficou", "faz", "fazer", "feito", "funciona", "funcionar",
    "serve", "servir", "usar", "usa", "uso", "usado", "aplicar", "aplica", "coisa", "tudo",
    "nada", "algo", "algum", "alguma", "simples", "facil", "dificil", "basico", "ideia",
    "parte", "primeira", "segunda", "ultima", "anterior", "proxima", "diferenca", "erro",
    "erros", "errada", "certa", "ponto", "pontos", "vantagem", "vantagens", "desvantagem",
    "desvantagens", "problema", "problemas", "resolve", "resolver", "pratica", "real",
    "caso", "casos", "situacao", "situacoes", "ensine", "ensina", "conceito", "teoria",
}

# Começos típicos de uma pergunta ou pedido NOVO (e não da resposta a uma pergunta do Sistema).
_RE_NOVO_PEDIDO = re.compile(
    r"^(?:e\s+|mas\s+|agora\s+|entao\s+)?(?:me\s+|nos\s+)?"
    r"(?:(?:de|da|dar)\s+(?:um|uma|exemplo|exemplos|mais|outro|outra)|explique|explica|explicar|mostre|mostra|fale|fala|descreva|compare|"
    r"defina|cite|liste|resuma|exemplifique|ensine|ensina|crie|escreva|faca|gere|"
    r"implemente|como|o que|oque|qual|quais|quando|onde|quem|por que|porque|pq|"
    r"quero|queria|gostaria|pode|poderia|voce pode|vc pode|preciso|tem como)\b"
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


def _palavras(texto: str) -> list:
    return re.findall(r"[a-z0-9]+", _normalizar(texto))


def eh_novo_pedido(texto: str) -> bool:
    """True se a mensagem é uma pergunta ou pedido novo (termina com '?' ou começa como pedido)."""
    if texto.rstrip().endswith("?"):
        return True
    return bool(_RE_NOVO_PEDIDO.match(" ".join(_palavras(texto))))


def verificar_tema(texto: str, respondendo: bool):
    """Devolve a resposta fixa para cumprimentos e assuntos fora do tema; None se pode seguir.

    respondendo: o estudante está respondendo a uma pergunta do Sistema. Nesse caso, uma resposta
    (que não seja um pedido novo) sempre vai para o Inquiridor, mesmo sem palavras do tema
    ("não sei", "acho que a pilha"), porque avaliar respostas fracas faz parte do diálogo.
    """
    palavras = _palavras(texto)
    if " ".join(palavras) in SAUDACOES:
        return MSG_SAUDACAO
    if respondendo and not eh_novo_pedido(texto):
        return None
    if any(p.startswith(RADICAIS_DO_TEMA) for p in palavras):
        return None
    if all(p in PALAVRAS_GENERICAS or len(p) <= 2 for p in palavras):
        return None  # pedido de continuação ("dê um exemplo", "não entendi"): depende do histórico
    return MSG_FORA_DO_TEMA
