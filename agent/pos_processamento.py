# Pós-processamento determinístico das respostas do modelo: tudo aqui é Python puro, sem chamar o modelo.
#
# Por quê: nos cenários reais, o modelo local (a) repetiu parágrafos até estourar o limite de tokens,
# (b) abriu a resposta com frases de preâmbulo ("Certamente, aqui está..."), (c) trocou os papéis de
# Originator e Caretaker, (d) não escreveu um código Java confiável e (e) não terminou com uma pergunta
# (e então a mensagem seguinte do estudante deixava de ser avaliada). Cada função trata um desses casos.
#
# Limitação: a verificação reconhece apenas erros CONHECIDOS (expressões regulares sobre os FATOS);
# um erro novo passa adiante. Por isso ela complementa as regras anti-alucinação dos prompts, não as substitui.
 
import re
from difflib import SequenceMatcher
from typing import NamedTuple
 
from .banco_perguntas import Pergunta, escolher_pergunta
from .guardrails import CATALOGO_GOF
from .guardrails import _normalizar as normalizar  # mesma normalização (minúsculas, sem acento) do guardrails
 
_RE_CERCA = re.compile(r"(```.*?```)", re.S)  # blocos de código cercados por ```
_RE_FIM_DE_FRASE = re.compile(r"(?<=[.!?])\s+")
 
 
# ---------------------------------------------------------------------------------------------
# 1. Limpeza: preâmbulo, repetição e corte no meio da frase
# ---------------------------------------------------------------------------------------------
 
def remover_preambulo(texto: str) -> str:
    """Tira a primeira linha de preâmbulo ("Certamente, aqui está...:", "**Resposta do Tutor:**")."""
    linhas = texto.strip().splitlines()
    if linhas:
        primeira = normalizar(linhas[0]).strip(" *_#")
        termina_em_dois_pontos = re.search(r":\**\s*$", linhas[0].strip())
        if termina_em_dois_pontos and re.match(
            r"(resposta do|certamente|claro|com certeza|aqui esta|responda a seguir)", primeira
        ):
            linhas = linhas[1:]
    return re.sub(r"(?i)^responda:\s*", "", "\n".join(linhas).strip())
 
 
def remover_repeticoes(texto: str) -> str:
    """Remove frases repetidas (loop do modelo). Blocos de código ficam intactos."""
    vistos = set()
    saida = []
    for parte in _RE_CERCA.split(texto):
        if parte.startswith("```"):
            saida.append(parte)
            continue
        linhas = []
        for linha in parte.split("\n"):
            if not linha.strip():
                linhas.append("")
                continue
            mantidas = []
            for frase in _RE_FIM_DE_FRASE.split(linha):
                chave = re.sub(r"\W+", " ", normalizar(frase)).strip()
                if len(chave) >= 20 and chave in vistos:
                    continue  # frase longa já escrita antes: descarta
                vistos.add(chave)
                mantidas.append(frase)
            if mantidas:
                linhas.append(" ".join(mantidas))
        saida.append("\n".join(linhas))
    return re.sub(r"\n{3,}", "\n\n", "".join(saida)).strip()
 
 
def cortar_frase_incompleta(texto: str) -> str:
    """Se o modelo foi cortado no limite de tokens, descarta o bloco de código aberto e a frase pela metade."""
    if texto.count("```") % 2 == 1:  # bloco de código sem fechamento
        texto = texto[: texto.rfind("```")]
    texto = texto.rstrip()
    if not texto or texto[-1] in '.!?:)`*"':
        return texto
    fins = list(re.finditer(r"[.!?](?=\s|$)", texto))
    if fins and fins[-1].end() >= 20:  # só corta se sobrar ao menos uma frase razoável
        return texto[: fins[-1].end()]
    return texto
 
 
def limpar_saida(texto: str) -> str:
    return cortar_frase_incompleta(remover_repeticoes(remover_preambulo(texto or "")))
 
 
# ---------------------------------------------------------------------------------------------
# 2. Verificação de erros conhecidos (contra os FATOS)
# ---------------------------------------------------------------------------------------------
 
class Problema(NamedTuple):
    codigo: str
    descricao: str  # o que está errado e qual é o fato correto (vai para o Guardião)
    trecho: str     # a frase do texto que contém o erro
 
 
class _Regra(NamedTuple):
    codigo: str
    descricao: str
    regex: re.Pattern
    ignora_se_negada: bool    # True: frases com "não/nunca/sem..." são a forma CORRETA e não contam
    cita_o_aluno: bool        # True: o feedback pode repetir a ideia errada do estudante; não vale no modo AVALIAR
 
 
_NEGACAO = re.compile(r"\b(?:nao|nunca|jamais|sem|nem|nenhum\w*)\b")
_PADROES = "|".join(re.escape(normalizar(nome)) for nome in CATALOGO_GOF)
 
_REGRAS = (
    _Regra(
        "originator_nao_le",
        "Está errado: o Originator é o ÚNICO que lê o conteúdo do Memento.",
        re.compile(
            r"originator\b(?:(?!caretaker)[^.!?]){0,60}?\b(?:nao|nunca)\s+(?:\w+\s+){0,2}?"
            r"(?:le|ler|acessa|acessar|abre|abrir|(?:tem|tenha|ter)\s+acesso)\b"
        ),
        False, True,
    ),
    _Regra(
        "caretaker_le",
        "Está errado: o Caretaker NUNCA lê nem altera o conteúdo do Memento; só guarda e devolve.",
        re.compile(
            r"caretaker\b(?:(?!originator)[^.!?]){0,60}?\b(?:le|ler|acessa|acessar|altera|alterar|abre|abrir|modifica|modificar)\b"
        ),
        True, True,
    ),
    _Regra(
        "caretaker_metodos",
        "Está errado: a interface do Memento que o Caretaker enxerga (narrow) é VAZIA, sem métodos para ler, "
        "salvar ou restaurar.",
        re.compile(
            r"caretaker\b[^.!?]{0,80}?(?:acesso a metodos|metodos?\s+(?:de|para)\s+(?:salvar|restaurar|ler|recuperar))"
        ),
        True, True,
    ),
    _Regra(
        "interfaces_invertidas",
        "Está invertido: a interface estreita (narrow, vazia) é a que o Caretaker vê; a larga (wide) é a do Originator.",
        re.compile(
            r"(?:estreita|limitada|narrow)(?:(?!caretaker)[^.!?]){0,50}originator"
            r"|(?:larga|ampla|wide)(?:(?!originator)[^.!?]){0,50}caretaker"
        ),
        False, True,
    ),
    _Regra(
        "memoria_como_violacao",
        "Está errado: gastar memória é um CUSTO do padrão, não uma violação de encapsulamento.",
        re.compile(r"memoria[^.!?]{0,80}viol\w+\s+(?:d?o\s+)?encapsul|viol\w+\s+(?:d?o\s+)?encapsul\w*[^.!?]{0,60}memoria"),
        True, True,
    ),
    _Regra(
        "memento_guarda_operacao",
        "Está errado: o Memento guarda o ESTADO; quem guarda a OPERAÇÃO (e a inversa) é o Command.",
        re.compile(r"\bmemento\b(?:(?!command)[^.!?]){0,40}?\b(?:guarda|armazena|salva)\w*\s+(?:apenas\s+|somente\s+|so\s+)?(?:a\s+)?operac"),
        True, True,
    ),
    _Regra(
        "padrao_existente_negado",
        "Está errado: este padrão EXISTE no catálogo GoF.",
        re.compile(
            rf"(?:nao conheco|nao existe|nao faz parte)[^.!?]{{0,40}}?\b(?:{_PADROES})\b"
            rf"|\b(?:{_PADROES})\b[^.!?]{{0,30}}\bnao (?:existe|esta no catalogo)"
        ),
        False, False,
    ),
    _Regra(
        "vazamento_de_instrucoes",
        'Remova comentários sobre as regras, os FATOS ou o rascunho, e fale com o estudante em segunda pessoa ("você").',
        re.compile(r"\b(?:fatos|rascunho)\b|\bo estudante\b|resposta do (?:tutor|guardiao|inquiridor)|\bregras anti"),
        False, False,
    ),
    _Regra(
        "exemplo_fora_do_editor",
        "Use somente o exemplo do Editor com desfazer; remova exemplos de outros assuntos.",
        re.compile(r"\b(?:banco de dados|transac\w+|gerenciador de estado|videogames?|jogos?|lista de tarefas)\b"),
        False, False,
    ),
)
 
 
def _frases(texto: str):
    """Frases do texto, sem os blocos de código."""
    for parte in _RE_CERCA.split(texto):
        if parte.startswith("```"):
            continue
        for linha in parte.splitlines():
            for frase in _RE_FIM_DE_FRASE.split(linha.strip()):
                if frase:
                    yield frase
 
 
def verificar_rascunho(texto: str, avaliando: bool = False) -> list:
    """Lista os erros conhecidos do texto (uma regra por frase).
 
    avaliando=True: o texto é um feedback ao estudante, que pode citar a ideia errada dele ("você disse que
    o Caretaker lê..."), então as regras que dependem de afirmações sobre o padrão ficam de fora.
    """
    problemas = []
    for frase in _frases(texto):
        n = normalizar(frase)
        for regra in _REGRAS:
            if avaliando and regra.cita_o_aluno:
                continue
            if regra.ignora_se_negada and _NEGACAO.search(n):
                continue
            if regra.regex.search(n):
                problemas.append(Problema(regra.codigo, regra.descricao, frase.strip()))
                break
    return problemas
 
 
def remover_problemas(texto: str, problemas: list) -> str:
    """Último recurso (se o Guardião não corrigir): apaga as frases com erro conhecido."""
    for p in problemas:
        texto = texto.replace(p.trecho, "")
    partes = [
        parte if parte.startswith("```") else re.sub(r"[ \t]{2,}", " ", re.sub(r"[ \t]+\n", "\n", parte))
        for parte in _RE_CERCA.split(texto)
    ]
    return re.sub(r"\n{3,}", "\n\n", "".join(partes)).strip()
 
 
# ---------------------------------------------------------------------------------------------
# 2b. Validação do que o modelo devolveu (antes e depois da revisão)
# ---------------------------------------------------------------------------------------------
 
_TERMOS_DO_TEMA = (
    "memento", "originator", "caretaker", "snapshot", "encapsul", "editor", "command", "desfazer", "undo", "padrao", "estado",
)
_RE_RECUSA = re.compile(r"\bnao (?:tenho|ha|consta|conheco|sei)\b[^.!?]{0,80}\b(?:informac\w*|fatos|padrao|assunto|isso)\b")
 
 
def parece_resposta_do_tema(texto: str) -> bool:
    """False se a explicação não cita nada do assunto (ex.: "Não altere nada mais além disso.")."""
    n = normalizar(texto)
    return any(termo in n for termo in _TERMOS_DO_TEMA)
 
 
def eh_recusa(texto: str) -> bool:
    """True se o modelo curto disse que não sabe ("Não tenho informação sobre X nos FATOS...")."""
    n = normalizar(texto)
    return len(n) <= 400 and bool(_RE_RECUSA.search(n))
 
 
def revisao_aceitavel(original: str, revisado: str) -> bool:
    """O Guardião só CORRIGE: a saída dele tem de parecer o rascunho (tamanho e conteúdo parecidos).
 
    Um modelo pequeno às vezes devolve algo sem relação com o rascunho (já visto: uma frase solta
    de instrução); nesse caso o rascunho original é mantido.
    """
    if not revisado.strip():
        return False
    if not 0.5 <= len(revisado) / max(len(original), 1) <= 1.6:
        return False
    return SequenceMatcher(None, normalizar(original), normalizar(revisado)).ratio() >= 0.5
 
 
# ---------------------------------------------------------------------------------------------
# 3. Código do exemplo: sempre o código canônico dos FATOS
# ---------------------------------------------------------------------------------------------
 
_NAO_PEDE_CODIGO = ("errad", "incorret", "equivoc", "evitar", "quando usar", "confund", "diferenca")
_LEGENDA = "No exemplo, Editor = Originator, EstadoEditor = Memento e Historico = Caretaker."
 
 
def eh_pedido_de_exemplo(mensagem: str) -> bool:
    """True se o estudante pediu um exemplo (de código) do padrão."""
    n = normalizar(mensagem)
    if any(trecho in n for trecho in _NAO_PEDE_CODIGO):
        return False
    return any(palavra in n for palavra in ("exemplo", "java", "codigo"))
 
 
def extrair_codigo_canonico(fatos: str) -> str:
    """Devolve o exemplo em Java dos FATOS (Editor + Historico + uso) já em bloco de código, ou ''."""
    linhas = fatos.splitlines()
    inicio = next((i for i, l in enumerate(linhas) if l.startswith("public class Editor")), None)
    fim = next((i for i, l in enumerate(linhas) if l.startswith("Uso:")), None)
    if inicio is None or fim is None or fim <= inicio:
        return ""
    codigo = "\n".join(linhas[inicio:fim]).rstrip()
    uso = [c.strip() + ";" for c in linhas[fim].removeprefix("Uso:").split(";") if c.strip()]
    return "```java\n" + codigo + "\n\n// Uso:\n" + "\n".join(uso) + "\n```"
 
 
def garantir_codigo(texto: str, codigo: str) -> str:
    """Troca qualquer bloco de código do modelo pelo código canônico (o modelo pequeno costuma errá-lo)."""
    if not codigo:
        return texto
    sem_blocos = re.sub(r"(?:^[^\n]*:[ \t]*\n+)?```.*?```", "", texto, flags=re.S | re.M)
    sem_blocos = re.sub(r"\n{3,}", "\n\n", sem_blocos).strip()
    return f"{sem_blocos}\n\n{_LEGENDA}\n\n{codigo}".strip()
 
 
# ---------------------------------------------------------------------------------------------
# 4. Pergunta final: garantir que o diálogo socrático continue
# ---------------------------------------------------------------------------------------------
 
_RE_META_PERGUNTA = re.compile(r"\b(?:fatos|rascunho|estudante|feedback)\b")
 
 
def extrair_pergunta(texto: str) -> str:
    """Devolve a última frase terminada em '?' (curta e que não seja 'entendeu?'), ou ''."""
    for frase in reversed(re.findall(r"[^.!?\n]*\?", texto)):
        frase = frase.strip(" *_-\t")
        frase = re.sub(r"(?i)^pergunta( curta)?\s*:\s*", "", frase)  # rótulo que o modelo às vezes escreve
        if 10 <= len(frase) <= 250 and "entendeu" not in frase.lower():
            return frase
    return ""
 
 
def pergunta_valida(candidata: str, mensagem: str, texto: str = "") -> bool:
    """Uma pergunta só serve se for uma pergunta de verdade e não um eco do estudante ou do próprio texto."""
    n = normalizar(candidata)
    if not candidata.rstrip().endswith("?") or not 10 <= len(candidata) <= 250:
        return False
    if "entendeu" in n or _RE_META_PERGUNTA.search(n):
        return False
    m = normalizar(mensagem)
    if n in m or SequenceMatcher(None, n, m).ratio() >= 0.75:  # eco da pergunta do estudante
        return False
    return not (texto and n in normalizar(texto))
 
 
def anexar_pergunta(texto: str, mensagem: str, rascunho_inquiridor: str, feitas: set) -> tuple:
    """Garante que o texto termine com uma pergunta válida.
 
    Devolve (texto, pergunta_do_banco). pergunta_do_banco é None quando a pergunta veio do próprio
    modelo; quando veio do banco, traz o gabarito e a dica para a avaliação da próxima resposta.
    """
    ultima = extrair_pergunta(texto) if texto.rstrip().endswith("?") else ""
    if ultima:
        if pergunta_valida(ultima, mensagem):
            return texto, None
        posicao = texto.rfind(ultima)  # termina com '?', mas é um eco: tira
        if posicao >= 0:
            texto = texto[:posicao].rstrip()
 
    candidata = extrair_pergunta(rascunho_inquiridor)
    if candidata and pergunta_valida(candidata, mensagem, texto):
        return f"{texto}\n\n{candidata}".strip(), None
 
    pergunta: Pergunta = escolher_pergunta(mensagem, feitas)
    return f"{texto}\n\n{pergunta.texto}".strip(), pergunta
 