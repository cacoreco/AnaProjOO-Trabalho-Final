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
 
# Frase de introdução de TODA pergunta final (do banco ou do modelo): a pergunta não aparece solta.
PREFIXO = "Aqui vai uma pergunta para testar seus conhecimentos: "
 
 
@dataclass(frozen=True)
class Pergunta:
    tema: str
    texto: str
    gabarito: str
    dica: str
    palavras: tuple = ()  # trechos (sem acento) que, se aparecerem na mensagem, escolhem esta pergunta
    # Avaliação da resposta do estudante (ver avaliacao.py). Todos os trechos são expressões regulares sobre o texto
    # sem acento, sem aspas e em minúsculas. criterios: grupos de alternativas; cada grupo com uma alternativa
    # presente conta um acerto. erros: padrões que indicam uma resposta errada mesmo que os critérios apareçam.
    criterios: tuple = ()
    erros: tuple = ()
 
    @property
    def corpo(self) -> str:
        """A pergunta sem a frase de introdução (usada quando o estudante tenta de novo)."""
        return self.texto[len(PREFIXO):] if self.texto.startswith(PREFIXO) else self.texto
 
 
BANCO = (
    Pergunta(
        tema="participantes",
        texto=PREFIXO + "no Editor com desfazer, com suas próprias palavras, quem guarda o snapshot do "
        "texto, quem só guarda e devolve esses snapshots e quem é o único que lê o conteúdo de um snapshot?",
        gabarito="O Memento (EstadoEditor) guarda o snapshot; o Caretaker (Historico) só guarda e devolve "
        "mementos; o Originator (Editor) é o único que lê o conteúdo do Memento.",
        dica="Pense em quem é dono do texto private do Editor e em quem só enxerga uma interface vazia.",
        palavras=("o que e", "participante"),
        criterios=(('originator', 'editor'), ('caretaker', 'historico'), ('memento', 'estadoeditor', 'snapshot')),
        erros=(),
    ),
    Pergunta(
        tema="caretaker",
        texto=PREFIXO + "o que o Caretaker (Historico) pode fazer com um Memento e o que ele NÃO pode fazer?",
        gabarito="Ele só guarda e devolve mementos (por exemplo, numa pilha de undo); nunca lê nem altera o "
        "conteúdo, porque a interface do Memento que ele enxerga é vazia.",
        dica="Olhe a interface Memento dentro do Editor: ela tem algum método?",
        palavras=("caretaker", "historico", "zelador"),
        criterios=(('guarda', 'guardar', 'armazena', 'devolve', 'devolver', 'pilha'), ('nao le', 'nao pode ler', 'nunca le', 'nao altera', 'nao modifica', 'nao acessa', 'nao abre', 'sem ler', 'so guarda', 'apenas guarda', 'vazia', 'opac')),
        erros=(),
    ),
    Pergunta(
        tema="originator",
        texto=PREFIXO + "quem é o único que lê o conteúdo do Memento e em qual método do Editor isso acontece?",
        gabarito="O Originator (Editor), no método restaurar, onde faz o cast para EstadoEditor para ler o texto.",
        dica="Procure no código do Editor onde aparece o cast ((EstadoEditor) m).",
        palavras=("originator", "originador"),
        criterios=(('originator', 'editor'), ('restaur', 'cast')),
        erros=(),
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
        palavras=("java", "codigo"),
        criterios=(('\\boi\\b',),),
        erros=('(?<!nao )(?<!nunca )oi\\s+mundo[\\s.)!]*$',),
    ),
    Pergunta(
        tema="command",
        texto=PREFIXO + "com suas palavras, qual é a diferença entre o que o Memento guarda e o que o Command guarda?",
        gabarito="O Memento guarda o ESTADO; o Command guarda a OPERAÇÃO (e precisa conhecer a operação inversa).",
        dica="Pense no que cada um precisa guardar para desfazer: o estado anterior, ou a operação e a sua inversa?",
        palavras=("command", "comando", "confund", "diferenca"),
        criterios=(('estado', 'snapshot'), ('operac', 'comando', 'inversa', 'acao')),
        erros=(),
    ),
    Pergunta(
        tema="mutavel",
        texto=PREFIXO + "se o Editor guardasse o texto numa List em vez de uma String, o que poderia dar "
        "errado ao salvar sem copiar a lista?",
        gabarito="Memento e Originator compartilhariam a MESMA referência ao objeto mutável; se o Originator "
        "alterasse a lista depois, o snapshot mudaria junto. Correção: copiar ao salvar E ao restaurar.",
        dica="Pense em duas variáveis apontando para o mesmo objeto mutável: o que acontece se uma delas o alterar?",
        palavras=("errad", "incorret", "equivoc", "mutav", "copi", "lembrar", "antes de usar"),
        criterios=(('referencia', 'mesm[oa]\\s+(?:objeto|lista|referencia)', 'compartilh', 'aponta'), ('muda', 'altera', 'modific', 'junto', 'afeta')),
        erros=(),
    ),
    Pergunta(
        tema="evitar",
        texto=PREFIXO + "em que situação o Memento deve ser evitado e qual padrão pode ser considerado no lugar?",
        gabarito="Quando o estado é muito grande e salvo com muita frequência (custo de memória e de cópia); "
        "considerar o Command, que guarda só a operação e a inversa.",
        dica="Pense no que acontece com a memória se o texto inteiro de um arquivo grande for salvo a cada tecla.",
        palavras=("evitar", "quando usar", "melhor escolha", "memoria"),
        criterios=(('grande', 'frequen', 'memoria'), ('command', 'comando')),
        erros=(),
    ),
)
 
 
# Ordem da busca por palavra-chave: do tema mais específico para o mais genérico (um pedido de "uso equivocado" que
# também diz "exemplo" tem de cair em "mutavel", não em "traco"). Sem palavra-chave, vale a ordem do BANCO.
_ORDEM_DE_BUSCA = ("mutavel", "evitar", "command", "caretaker", "originator", "participantes", "traco")
 
 
# A mensagem fixa de "solução pronta" (guardrails.py) termina com esta pergunta. Ela não está no BANCO (não é sorteada),
# mas o sistema a registra como pendente: a próxima mensagem do estudante é a resposta DELA, não da pergunta anterior.
PERGUNTA_SOLUCAO_PRONTA = Pergunta(
    tema="solucao_pronta",
    texto="no Editor com desfazer, quem guarda o estado anterior e quem pode ler o conteúdo guardado?",
    gabarito="O Memento (EstadoEditor) guarda o snapshot do estado anterior (e o Caretaker, o Historico, guarda os "
    "mementos); só o Originator (Editor) pode ler o conteúdo do Memento.",
    dica="Pense em quem recebe o snapshot do texto e em quem é o único que enxerga o que há dentro dele.",
    criterios=(("memento", "estadoeditor", "snapshot", "historico", "caretaker"), ("originator", "editor")),
)
 
 
def proxima_pergunta(feitas: set, atual: str = None, com_codigo: bool = False) -> Pergunta:
    """A próxima pergunta do banco (na ordem do BANCO) que ainda não foi feita.
 
    O rastreio do código ("traco") só entra se o código canônico já apareceu na conversa.
    """
    candidatas = [p for p in BANCO if p.tema != atual and (com_codigo or p.tema != "traco")]
    return next((p for p in candidatas if p.tema not in feitas), candidatas[0])
 
 
def _disponiveis(feitas: set) -> dict:
    """Perguntas ainda não feitas nesta conversa (se todas já foram, recomeça com todas), na ordem do BANCO."""
    return {p.tema: p for p in BANCO if p.tema not in feitas} or {p.tema: p for p in BANCO}
 
 
def pergunta_por_palavra_chave(mensagem: str, feitas: set):
    """Devolve a pergunta do banco cujo tema combina com o pedido do estudante, ou None se nenhuma combina.
 
    Quando combina, o sistema usa esta pergunta (que tem gabarito e dica) em vez de pedir uma ao modelo.
    """
    n = _normalizar(mensagem)
    disponiveis = _disponiveis(feitas)
    for nome in _ORDEM_DE_BUSCA:
        p = disponiveis.get(nome)
        if p and any(palavra in n for palavra in p.palavras):
            return p
    return None
 
 
def pergunta_do_tema(tema: str) -> Pergunta:
    """Devolve a pergunta de um tema (ex.: "traco", o rastreio do código canônico que está na tela)."""
    return next(p for p in BANCO if p.tema == tema)
 
 
def escolher_pergunta(mensagem: str, feitas: set) -> Pergunta:
    """Pergunta do tema do pedido; se nenhum combina, a primeira ainda não feita (usada quando o modelo falha)."""
    return pergunta_por_palavra_chave(mensagem, feitas) or next(iter(_disponiveis(feitas).values()))
 