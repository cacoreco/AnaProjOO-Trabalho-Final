# Banco de perguntas de verificação do Inquiridor (usado quando o modelo não produz uma pergunta válida).
#
# Por quê: nos cenários reais, o modelo local às vezes não escreveu nenhuma pergunta, ou devolveu o
# próprio pedido do estudante como "pergunta". Sem pergunta, o diálogo socrático para: a próxima
# mensagem do estudante deixa de ser avaliada como resposta. Cada entrada abaixo tem:
#   - texto:    a pergunta (termina com '?', usa SOMENTE o exemplo do Editor);
#   - gabarito: a resposta esperada, tirada dos FATOS, entregue ao Inquiridor para ele comparar;
#   - dica:     a pista que o Inquiridor dá se o estudante errar (sem revelar o gabarito).

from dataclasses import dataclass

from .guardrails import _normalizar

PREFIXO = "Aqui vai uma pergunta para testar seu conhecimento: "


@dataclass(frozen=True)
class Pergunta:
    tema: str
    texto: str
    gabarito: str
    dica: str
    palavras: tuple = ()  # trechos (sem acento) que, se aparecerem na mensagem, escolhem esta pergunta


BANCO = (
    Pergunta(
        tema="participantes",
        texto=PREFIXO + "no Editor com desfazer, com suas próprias palavras, quem guarda o snapshot do "
        "texto, quem só guarda e devolve esses snapshots e quem é o único que lê o conteúdo de um snapshot?",
        gabarito="O Memento (EstadoEditor) guarda o snapshot; o Caretaker (Historico) só guarda e devolve "
        "mementos; o Originator (Editor) é o único que lê o conteúdo do Memento.",
        dica="Pense em quem é dono do texto private do Editor e em quem só enxerga uma interface vazia.",
        palavras=("o que e", "participante"),
    ),
    Pergunta(
        tema="caretaker",
        texto=PREFIXO + "o que o Caretaker (Historico) pode fazer com um Memento e o que ele NÃO pode fazer?",
        gabarito="Ele só guarda e devolve mementos (por exemplo, numa pilha de undo); nunca lê nem altera o "
        "conteúdo, porque a interface do Memento que ele enxerga é vazia.",
        dica="Olhe a interface Memento dentro do Editor: ela tem algum método?",
        palavras=("caretaker", "historico", "zelador"),
    ),
    Pergunta(
        tema="originator",
        texto=PREFIXO + "quem é o único que lê o conteúdo do Memento e em qual método do Editor isso acontece?",
        gabarito="O Originator (Editor), no método restaurar, onde faz o cast para EstadoEditor para ler o texto.",
        dica="Procure no código do Editor onde aparece o cast ((EstadoEditor) m).",
        palavras=("originator", "originador"),
    ),
    Pergunta(
        tema="traco",
        texto=PREFIXO + "execute à mão o trecho abaixo, usando o Editor e o Historico do exemplo.\n\n"
        "```java\n"
        "Editor editor = new Editor();\n"
        "Historico historico = new Historico();\n"
        'editor.escrever("Oi");\n'
        "historico.guardar(editor.salvar());\n"
        'editor.escrever(" mundo");\n'
        "editor.restaurar(historico.recuperar());\n"
        "```\n\n"
        "Qual é o valor do atributo texto do Editor depois da última linha?",
        gabarito='"Oi". O texto começa vazio e vira "Oi"; salvar() guarda o snapshot "Oi" no Historico; '
        'escrever(" mundo") muda o texto para "Oi mundo"; recuperar() devolve o snapshot e restaurar() '
        'volta o texto para "Oi".',
        dica='Acompanhe o valor de texto linha a linha e repare que salvar() foi chamado ANTES de escrever(" mundo").',
        palavras=("exemplo", "java", "codigo"),
    ),
    Pergunta(
        tema="command",
        texto=PREFIXO + "com suas palavras, qual é a diferença entre o que o Memento guarda e o que o Command guarda?",
        gabarito="O Memento guarda o ESTADO; o Command guarda a OPERAÇÃO (e precisa conhecer a operação inversa).",
        dica="Pense no que cada um precisa guardar para desfazer: o estado anterior, ou a operação e a sua inversa?",
        palavras=("command", "comando", "confund", "diferenca"),
    ),
    Pergunta(
        tema="mutavel",
        texto=PREFIXO + "se o Editor guardasse o texto numa List em vez de uma String, o que poderia dar "
        "errado ao salvar sem copiar a lista?",
        gabarito="Memento e Originator compartilhariam a MESMA referência ao objeto mutável; se o Originator "
        "alterasse a lista depois, o snapshot mudaria junto. Correção: copiar ao salvar E ao restaurar.",
        dica="Pense em duas variáveis apontando para o mesmo objeto mutável: o que acontece se uma delas o alterar?",
        palavras=("errad", "incorret", "equivoc", "mutav", "copi"),
    ),
    Pergunta(
        tema="evitar",
        texto=PREFIXO + "em que situação o Memento deve ser evitado e qual padrão pode ser considerado no lugar?",
        gabarito="Quando o estado é muito grande e salvo com muita frequência (custo de memória e de cópia); "
        "considerar o Command, que guarda só a operação e a inversa.",
        dica="Pense no que acontece com a memória se o texto inteiro de um arquivo grande for salvo a cada tecla.",
        palavras=("evitar", "quando usar", "melhor escolha", "memoria", "lembrar", "antes de usar"),
    ),
)


def escolher_pergunta(mensagem: str, feitas: set) -> Pergunta:
    """Escolhe a pergunta cujo tema combina com a mensagem; prefere as que ainda não foram feitas."""
    n = _normalizar(mensagem)
    disponiveis = [p for p in BANCO if p.tema not in feitas] or list(BANCO)
    for p in disponiveis:
        if any(palavra in n for palavra in p.palavras):
            return p
    return disponiveis[0]
