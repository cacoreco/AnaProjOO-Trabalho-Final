# Avaliação das respostas do estudante às perguntas do Inquiridor: o ACERTO ou ERRO é decidido em Python, sem modelo.
#
# Por quê: o modelo local (3B) não conseguia validar nenhuma resposta. Ele recebia a pergunta e a resposta, não
# tinha certeza de nada e caía na frase de escape ("Não tenho certeza; vamos conferir nos slides..."), mesmo quando
# a resposta estava certa. Agora:
#   1. avaliar_resposta() compara a resposta com os `criterios` da pergunta (banco_perguntas.py) e procura erros
#      conhecidos (pos_processamento.py) -> Veredito: correta, parcial, incorreta ou desconhecida;
#   2. o Inquiridor só ESCREVE o feedback, seguindo o veredito;
#   3. feedback_coerente() descarta o texto do modelo se ele contradiz o veredito (ou cai na frase de escape),
#      e feedback_padrao() entrega um feedback fixo no lugar.
#
# Limitação: critérios são trechos de texto (regex). Uma resposta certa com palavras muito diferentes pode sair como
# "parcial"; por isso o primeiro erro vira dica e nova tentativa, e só o segundo mostra a resposta esperada.
 
import re
from dataclasses import dataclass
 
from .banco_perguntas import Pergunta
from .guardrails import _normalizar as normalizar
from .pos_processamento import verificar_rascunho
 
 
@dataclass(frozen=True)
class Veredito:
    nivel: str            # "correta", "parcial", "incorreta" ou "desconhecida" (pergunta sem critérios)
    acertos: int = 0      # grupos de critérios presentes na resposta
    total: int = 0        # grupos de critérios da pergunta
    equivocos: tuple = () # erros conhecidos do padrão encontrados na resposta (texto do fato correto)
 
 
# Só erros CONCEITUAIS valem contra a resposta do estudante (as outras regras são sobre o estilo do texto do modelo).
_CODIGOS_CONCEITUAIS = {
    "originator_nao_le", "caretaker_le", "caretaker_metodos", "caretaker_salva_restaura",
    "interfaces_invertidas", "memoria_como_violacao", "memento_guarda_operacao",
}
_ASPAS = re.compile(r"[\"'“”‘’]")
 
 
def _texto(resposta: str) -> str:
    """Minúsculas, sem acento, sem aspas ("Oi" e Oi valem o mesmo) e com espaços simples."""
    return re.sub(r"\s+", " ", _ASPAS.sub("", normalizar(resposta))).strip()
 
 
def _equivocos(resposta: str) -> tuple:
    achados = []
    for p in verificar_rascunho(resposta, avaliando=False):
        if p.codigo in _CODIGOS_CONCEITUAIS and p.descricao not in achados:
            achados.append(p.descricao)
    return tuple(achados)
 
 
def avaliar_resposta(resposta: str, pergunta: Pergunta = None) -> Veredito:
    """
    Decide se a resposta do estudante está certa.
 
    Args:
        resposta (str): mensagem do estudante
        pergunta (Pergunta | None): pergunta do banco que ele está respondendo; None se a pergunta foi escrita
            pelo modelo (não há critérios: só se acusa um erro conhecido)
 
    Retorna:
        Veredito: correta (todos os grupos de critérios presentes), parcial (alguns), incorreta (nenhum, ou há um
        erro conhecido) ou desconhecida (nada para comparar)
    """
 
    equivocos = _equivocos(resposta)
    if pergunta is None or not pergunta.criterios:
        return Veredito("incorreta" if equivocos else "desconhecida", equivocos=equivocos)
 
    n = _texto(resposta)
    total = len(pergunta.criterios)
    acertos = sum(1 for grupo in pergunta.criterios if any(re.search(alt, n) for alt in grupo))
    if equivocos or any(re.search(erro, n) for erro in pergunta.erros):
        return Veredito("incorreta", acertos, total, equivocos)
    if acertos == total:
        return Veredito("correta", acertos, total)
    return Veredito("parcial" if acertos else "incorreta", acertos, total)
 
 
# --- Feedback ------------------------------------------------------------------------------------------------
 
_META = re.compile(r"\b(?:fatos|rascunho|estudante|feedback|veredito)\b")
_ESCAPE = re.compile(r"nao tenho certeza")
_POSITIVOS = re.compile(
    r"\b(?:muito bem|isso mesmo|exatamente|exato|perfeito|parabens|acertou|correto|correta|certo|certa|"
    r"esta correta|esta certa|tudo certo)\b"
)
_RESSALVAS = re.compile(r"\b(?:mas|porem|quase|nao|falta|faltou|dica|incompleta|ainda)\b")
_NEGATIVOS = re.compile(r"incorret|errad|\bnao (?:e|esta|estao) (?:isso|certo|correta?)\b|ainda nao e isso|\bnao exatamente\b")
 
 
def feedback_coerente(texto: str, veredito: Veredito) -> bool:
    """False se o feedback do modelo contradiz o veredito, cai na frase de escape, é curto demais ou fala do sistema."""
    t = (texto or "").strip()
    n = normalizar(t)
    if len(t) < 8:
        return False
    if _META.search(n) or verificar_rascunho(t, avaliando=True):
        return False
    if _ESCAPE.search(n):
        return veredito.nivel == "desconhecida"  # só quando não há veredito o modelo pode dizer que não tem certeza
    if veredito.nivel == "correta":
        return not _NEGATIVOS.search(n)  # "Sua resposta está incorreta" para uma resposta certa
    if veredito.nivel in ("parcial", "incorreta"):
        return not (_POSITIVOS.search(n) and not _RESSALVAS.search(n))  # elogio sem ressalva a uma resposta errada
    return True
 
 
def feedback_padrao(veredito: Veredito, pergunta: Pergunta = None, segunda_tentativa: bool = False) -> str:
    """Feedback fixo (sem modelo), usado quando o texto do modelo contradiz o veredito ou na 2ª tentativa errada."""
    if pergunta is None:
        if veredito.equivocos:  # a resposta tem um erro conhecido do padrão: corrige com o fato dos FATOS
            return veredito.equivocos[0]
        return "Obrigado pela resposta."
    if veredito.nivel == "correta":
        return "Isso mesmo! Sua resposta confere com o que o padrão Memento define."
    if segunda_tentativa:
        return f"Vamos olhar a resposta juntos: {pergunta.gabarito}"
    if veredito.nivel == "parcial":
        return f"Quase lá! Falta completar a resposta. Dica: {pergunta.dica}"
    return f"Ainda não é isso. Dica: {pergunta.dica}"
 
 
def sem_pergunta(texto: str) -> str:
    """Tira rótulo ("Feedback:") e perguntas do fim do texto: a próxima pergunta é acrescentada pelo sistema."""
    texto = re.sub(r"(?i)^\**feedback\**\s*:\s*\**\s*", "", (texto or "").strip())
    while texto.endswith("?"):
        achado = re.search(r"[^.!?\n]*\?\s*$", texto)
        if not achado:
            break
        texto = texto[: achado.start()].rstrip()
    return texto
 