"""
Orquestração da crew com modelo local (Ollama).

Fluxo de um turno:
  0. guardrails em Python: pedido inválido, cumprimento ou assunto fora do tema
     -> resposta fixa, sem chamar o modelo
  1. estudante fez uma pergunta/pedido novo:   Tutor -> Inquiridor -> Guardião
  2. estudante respondeu a uma pergunta nossa: Inquiridor -> Guardião
     (uma pergunta nova feita logo depois de uma pergunta nossa volta para o fluxo 1)
  3. o sistema garante que a resposta final termine com uma pergunta
"""

# Orquestração da crew: Tutor -> Inquiridor -> Guardião, com modelo local (Ollama).

import logging
import re

from crewai import LLM, Agent, Crew, Process, Task

from .guardrails import eh_novo_pedido, verificar_pedido, verificar_tema
from .prompts import carregar_fatos, carregar_prompt

# --- Limites para não estourar a janela de 8k ------------------------------
TURNOS_NO_HISTORICO = 3                # quantos pares pergunta/resposta entram no prompt
MAX_CHARS_ENTRADA = 1500               # tamanho máximo da pergunta do estudante
MAX_CHARS_POR_MENSAGEM = 600           # corte de cada mensagem guardada no histórico
# Teto de tokens por resposta de agente. Sem ele, modelos pequenos podem entrar em repetição
# e gerar milhares de tokens sem parar (visto com o qwen2.5:0.5b: mais de 13 mil numa resposta).
MAX_TOKENS_POR_AGENTE = 800

# --- Mensagens de erro amigáveis -------------------------------------------
MSG_VAZIA = "Digite uma pergunta sobre o padrão Memento."
MSG_FALHA_MODELO = (
    "Não consegui falar com o modelo local. Verifique se o Ollama está em "
    "execução (por exemplo: systemctl status ollama) e tente novamente."
)
MSG_SAIDA_INVALIDA = "Não consegui gerar uma resposta confiável agora. Tente reformular a pergunta."

log = logging.getLogger(__name__)

class SistemaTutor:
    #Tutor multiagente do padrão Memento. Uma instância = uma conversa.

    def __init__(self, model: str, base_url: str, temperature: float, context_window_size: int) -> None:
        fatos = carregar_fatos()
        self._llm = LLM(
            model=model,
            base_url=base_url,
            temperature=float(temperature),
            context_window_size=int(context_window_size),
            max_tokens=MAX_TOKENS_POR_AGENTE,
        )
        self._tutor = self._criar_agente("tutor", fatos)
        self._inquiridor = self._criar_agente("inquiridor", fatos)
        self._guardiao = self._criar_agente("guardiao", fatos)
        self._historico = []         # memória da conversa: lista de (pergunta, resposta)
        self.ultimos_rascunhos = {}  # saída de cada agente no último turno (depuração e testes)

    def _criar_agente(self, nome: str, fatos: str) -> Agent:
        p = carregar_prompt(nome, fatos)
        return Agent(
            role=p["role"],
            goal=p["goal"],
            backstory=p["backstory"],
            llm=self._llm,
            allow_delegation=False,  # os papéis são fixos: ninguém delega para outro agente
            verbose=False,
        )

    def _texto_historico(self) -> str:
        if not self._historico:
            return "(conversa nova, sem histórico)"
        linhas = []
        for pergunta, resposta in self._historico[-TURNOS_NO_HISTORICO:]:
            linhas.append(f"Estudante: {pergunta[:MAX_CHARS_POR_MENSAGEM]}")
            linhas.append(f"Sistema: {resposta[:MAX_CHARS_POR_MENSAGEM]}")
        return "\n".join(linhas)

    def _sistema_fez_pergunta(self) -> bool:
        # True se a última resposta do sistema terminou com uma pergunta ao estudante.
        return bool(self._historico) and self._historico[-1][1].rstrip().endswith("?")

    """
        True se a mensagem é a resposta do estudante à nossa última pergunta.

        Uma pergunta ou pedido novo (termina com '?' ou começa com "explique", "dê um exemplo"...)
        não é resposta: antes, qualquer mensagem depois de uma pergunta nossa ia para o modo
        AVALIAR, o Tutor nunca mais era chamado e o sistema repetia a mesma pergunta em loop.
    """
    def _estudante_esta_respondendo(self, mensagem: str) -> bool:   
        return self._sistema_fez_pergunta() and not eh_novo_pedido(mensagem)

    def _executar_crew(self, pergunta: str, avaliar: bool) -> str:
        # O texto é montado em Python (f-string), sem variáveis do CrewAI.
        contexto = (
            f"HISTÓRICO RECENTE:\n{self._texto_historico()}\n\n"
            f"MENSAGEM DO ESTUDANTE:\n{pergunta}\n"
        )
        # O Guardião não recebe o histórico: com ele, o modelo trocava o rascunho a revisar
        # por uma cópia de uma resposta anterior do Sistema.
        contexto_guardiao = f"MENSAGEM DO ESTUDANTE:\n{pergunta}\n"
        contexto_guardiao += "\nEscreva para o estudante (\"você\"), sem falar do rascunho nem \"do estudante\".\n"
        if avaliar:
            # Só a última pergunta e a resposta: com o histórico inteiro, o modelo avaliava uma
            # mensagem antiga do estudante (chegou a dizer que uma resposta certa estava errada).
            ultima_pergunta = self._extrair_pergunta(self._historico[-1][1]) or self._historico[-1][1]
            t_inquiridor = Task(
                description=f"PERGUNTA DO SISTEMA:\n{ultima_pergunta}\n\n"
                f"RESPOSTA DO ESTUDANTE (é esta que você avalia):\n{pergunta}\n"
                "\nMODO AVALIAR: avalie SOMENTE a RESPOSTA DO ESTUDANTE acima, comparando-a com os FATOS, "
                "conforme suas regras, e termine com a próxima pergunta curta.",
                expected_output="Feedback de até 2 linhas e UMA pergunta curta no final.",
                agent=self._inquiridor,
            )
            t_guardiao = Task(
                description=contexto_guardiao
                + "\nSua tarefa: revise o rascunho do Inquiridor (no contexto) e entregue a resposta final, "
                "mantendo o feedback curto e a pergunta final. Não acrescente uma explicação nova do padrão: "
                "só corrija o que contradiz os FATOS.",
                expected_output="O feedback do rascunho (no máximo 3 linhas) e a pergunta final do rascunho. Nada além disso.",
                agent=self._guardiao,
                context=[t_inquiridor],
            )
            nomeadas = [("inquiridor", t_inquiridor), ("guardiao", t_guardiao)]
        else:
            t_tutor = Task(
                description=contexto
                + "\nSua tarefa: responda como Tutor, seguindo suas regras, à MENSAGEM DO ESTUDANTE acima. "
                "O histórico serve só de contexto: não repita respostas anteriores do Sistema.",
                expected_output="Explicação curta em português, sem pergunta no final.",
                agent=self._tutor,
            )
            t_inquiridor = Task(
                description=contexto
                + "\nMODO PERGUNTAR: não há resposta do estudante para avaliar. NÃO escreva 'Feedback'. "
                "O rascunho do Tutor (no contexto) NÃO é resposta do estudante: use-o só para saber o assunto. "
                "Escreva SOMENTE uma pergunta curta sobre esse assunto.",
                expected_output="Uma única pergunta curta, terminada em '?'.",
                agent=self._inquiridor,
                context=[t_tutor],
            )
            t_guardiao = Task(
                description=contexto_guardiao
                + "\nSua tarefa: revise o rascunho do Tutor (no contexto) e entregue a resposta final. "
                "Mantenha os blocos de código do rascunho.",
                expected_output="A resposta final ao estudante, em português, com no máximo 12 linhas.",
                agent=self._guardiao,
                context=[t_tutor],  # o Guardião revisa só a explicação; a pergunta é acrescentada pelo sistema
            )
            nomeadas = [("tutor", t_tutor), ("inquiridor", t_inquiridor), ("guardiao", t_guardiao)]

        crew = Crew(
            agents=[tarefa.agent for _, tarefa in nomeadas],
            tasks=[tarefa for _, tarefa in nomeadas],
            process=Process.sequential,  # um agente por vez, na ordem das tarefas
            verbose=False,
        )
        resultado = crew.kickoff()
        # Guarda a saída de cada agente, para ver onde uma resposta ruim nasceu
        self.ultimos_rascunhos = {nome: self._saida_da_tarefa(t) for nome, t in nomeadas}
        return str(getattr(resultado, "raw", resultado)).strip()

    @staticmethod
    def _saida_da_tarefa(tarefa: Task) -> str:
        saida = getattr(tarefa, "output", None)
        return str(getattr(saida, "raw", "") or "").strip()

    @staticmethod
    def _extrair_pergunta(texto: str) -> str:
        #Devolve a última frase terminada em '?' (curta e que não seja 'entendeu?'), ou ''.

        for frase in reversed(re.findall(r"[^.!?\n]*\?", texto)):
            frase = frase.strip(" *_-\t")
            frase = re.sub(r"(?i)^pergunta( curta)?\s*:\s*", "", frase)  # rótulo que o modelo às vezes escreve
            if 10 <= len(frase) <= 250 and "entendeu" not in frase.lower():
                return frase
        return ""

    def _garantir_pergunta_final(self, texto: str) -> str:
        #Contrato de saída: a resposta termina com uma pergunta (mantém o diálogo socrático).

        if texto.rstrip().endswith("?"):
            return texto
        pergunta = self._extrair_pergunta(self.ultimos_rascunhos.get("inquiridor", ""))
        return f"{texto}\n\n{pergunta}" if pergunta else texto

    @staticmethod
    def _saida_valida(texto: str) -> bool:
        return len(texto) >= 16  # descarta saída vazia ou truncada demais

    # Ponto de entrada: recebe a mensagem do estudante e devolve a resposta final.
    def resposta(self, pergunta: str) -> str:
        try:
            pergunta = (pergunta or "").strip()
            if not pergunta:                          # tratamento: entrada vazia
                return MSG_VAZIA
            pergunta = pergunta[:MAX_CHARS_ENTRADA]   # tratamento: entrada longa demais
            self.ultimos_rascunhos = {}

            bloqueio = verificar_pedido(pergunta)     # guardrail: padrão inexistente ou solução pronta
            if bloqueio:
                self.ultimos_rascunhos = {"guardrail": "pedido tratado em Python, sem chamar o modelo"}
                return bloqueio

            avaliar = self._estudante_esta_respondendo(pergunta)

            # guardrail: cumprimento ou assunto fora do tema. Não entra no histórico, para não
            # poluir o contexto do modelo e para que uma pergunta nossa ainda pendente continue valendo.
            fora_do_tema = verificar_tema(pergunta, respondendo=avaliar)
            if fora_do_tema:
                self.ultimos_rascunhos = {"guardrail": "cumprimento ou fora do tema, tratado em Python"}
                return fora_do_tema

            try:
                texto = self._executar_crew(pergunta, avaliar)
            except Exception as erro:                 # tratamento: falha do modelo (Ollama fora do ar etc.)
                log.warning("Falha na crew: %s", erro)
                return f"{MSG_FALHA_MODELO}\n(Detalhe técnico: {str(erro)[:200]})"

            if not self._saida_valida(texto):         # tratamento: saída inesperada
                return MSG_SAIDA_INVALIDA

            texto = self._garantir_pergunta_final(texto)
            self._historico.append((pergunta, texto))  # só guarda na memória respostas válidas
            return texto
        except (EOFError, KeyboardInterrupt):
            return "AÇÃO INTERROMPIDA"
