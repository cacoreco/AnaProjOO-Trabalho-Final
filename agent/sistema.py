"""Orquestração da crew com modelo local (Ollama).

Fluxo de um turno:
  0. guardrails em Python: pedido inválido -> resposta fixa, sem chamar o modelo
  1. estudante fez uma pergunta/pedido:        Tutor -> Inquiridor -> Guardião
  2. estudante respondeu a uma pergunta nossa: Inquiridor -> Guardião
  3. o sistema garante que a resposta final termine com uma pergunta
"""

#Orquestração da crew: Tutor -> Inquiridor -> Guardião, com modelo local (Ollama).

import logging
import re

from crewai import LLM, Agent, Crew, Process, Task

from .guardrails import verificar_pedido
from .prompts import carregar_fatos, carregar_prompt

# --- Limites para não estourar a janela de 8k ------------------------------
TURNOS_NO_HISTORICO = 3                # quantos pares pergunta/resposta entram no prompt
MAX_CHARS_ENTRADA = 1500               # tamanho máximo da pergunta do estudante
MAX_CHARS_POR_MENSAGEM = 600           # corte de cada mensagem guardada no histórico

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

    def __init__(self, model, base_url, temperature, context_window_size) -> None:
        fatos = carregar_fatos()
        self._llm = LLM(
            model=model,
            base_url=base_url,
            temperature=temperature,
            context_window_size=context_window_size,
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

    def _estudante_esta_respondendo(self) -> bool:
        """True se a última resposta do sistema terminou com uma pergunta (logo, a nova mensagem a responde)."""
        return bool(self._historico) and self._historico[-1][1].rstrip().endswith("?")

    def _executar_crew(self, pergunta: str, avaliar: bool) -> str:
        # O texto é montado em Python (f-string), sem variáveis do CrewAI.
        contexto = (
            f"HISTÓRICO RECENTE:\n{self._texto_historico()}\n\n"
            f"MENSAGEM DO ESTUDANTE:\n{pergunta}\n"
        )
        if avaliar:
            t_inquiridor = Task(
                description=contexto
                + "\nMODO AVALIAR: a mensagem do estudante é a resposta dele à última pergunta do "
                "Sistema (veja o histórico). Avalie-a conforme suas regras e termine com a próxima pergunta curta.",
                expected_output="Feedback de até 2 linhas e UMA pergunta curta no final.",
                agent=self._inquiridor,
            )
            t_guardiao = Task(
                description=contexto
                + "\nSua tarefa: revise o rascunho do Inquiridor e entregue a resposta final, mantendo a pergunta final.",
                expected_output="A resposta final ao estudante, em português, com no máximo 12 linhas.",
                agent=self._guardiao,
                context=[t_inquiridor],
            )
            nomeadas = [("inquiridor", t_inquiridor), ("guardiao", t_guardiao)]
        else:
            t_tutor = Task(
                description=contexto + "\nSua tarefa: responda como Tutor, seguindo suas regras.",
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
                description=contexto
                + "\nSua tarefa: revise o rascunho do Tutor e entregue a resposta final.",
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
    def _saida_da_tarefa(tarefa) -> str:
        saida = getattr(tarefa, "output", None)
        return str(getattr(saida, "raw", "") or "").strip()

    @staticmethod
    def _extrair_pergunta(texto: str) -> str:
        """Devolve a última frase terminada em '?' (curta e que não seja 'entendeu?'), ou ''."""
        for frase in reversed(re.findall(r"[^.!?\n]*\?", texto)):
            frase = frase.strip(" *_-\t")
            if 10 <= len(frase) <= 250 and "entendeu" not in frase.lower():
                return frase
        return ""

    def _garantir_pergunta_final(self, texto: str) -> str:
        """Contrato de saída: a resposta termina com uma pergunta (mantém o diálogo socrático)."""
        if texto.rstrip().endswith("?"):
            return texto
        pergunta = self._extrair_pergunta(self.ultimos_rascunhos.get("inquiridor", ""))
        return f"{texto}\n\n{pergunta}" if pergunta else texto

    @staticmethod
    def _saida_valida(texto: str) -> bool:
        return len(texto) >= 15  # descarta saída vazia ou truncada demais

    def resposta(self, pergunta: str) -> str:
        """Ponto de entrada: recebe a mensagem do estudante e devolve a resposta final."""
        pergunta = (pergunta or "").strip()
        if not pergunta:                          # tratamento: entrada vazia
            return MSG_VAZIA
        pergunta = pergunta[:MAX_CHARS_ENTRADA]   # tratamento: entrada longa demais
        self.ultimos_rascunhos = {}

        bloqueio = verificar_pedido(pergunta)     # guardrail: padrão inexistente ou solução pronta
        if bloqueio:
            self.ultimos_rascunhos = {"guardrail": "pedido tratado em Python, sem chamar o modelo"}
            self._historico.append((pergunta, bloqueio))
            return bloqueio

        avaliar = self._estudante_esta_respondendo()
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
