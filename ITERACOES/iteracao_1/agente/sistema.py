"""Orquestração da crew: Tutor -> Inquiridor -> Guardião, com modelo local (Ollama)."""
import logging

from crewai import LLM, Agent, Crew, Process, Task

from .prompts import carregar_fatos, carregar_prompt

# --- Configuração do modelo local (nada de API paga ou chave) -------------
MODELO = "ollama/qwen2.5-3b-8k"        # variante criada com o Modelfile (num_ctx 8192)
URL_OLLAMA = "http://localhost:11434"  # servidor local do Ollama
JANELA_CONTEXTO = 8192                 # deve coincidir com o num_ctx do Modelfile
TEMPERATURA = 0.2                      # baixa: menos criatividade, menos invenção

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
    """Tutor multiagente do padrão Memento. Uma instância = uma conversa."""

    def __init__(self) -> None:
        fatos = carregar_fatos()
        self._llm = LLM(
            model=MODELO,
            base_url=URL_OLLAMA,
            temperature=TEMPERATURA,
            context_window_size=JANELA_CONTEXTO,
        )
        self._tutor = self._criar_agente("tutor", fatos)
        self._inquiridor = self._criar_agente("inquiridor", fatos)
        self._guardiao = self._criar_agente("guardiao", fatos)
        self._historico = []  # memória da conversa: lista de (pergunta, resposta)

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

    def _executar_crew(self, pergunta: str) -> str:
        # As três tarefas veem o mesmo contexto: histórico recente + mensagem original.
        # O texto é montado em Python (f-string), sem variáveis do CrewAI.
        contexto = (
            f"HISTÓRICO RECENTE:\n{self._texto_historico()}\n\n"
            f"MENSAGEM DO ESTUDANTE:\n{pergunta}\n"
        )
        t_tutor = Task(
            description=contexto + "\nSua tarefa: responda como Tutor, seguindo suas regras.",
            expected_output="Explicação curta em português, sem pergunta no final.",
            agent=self._tutor,
        )
        t_inquiridor = Task(
            description=contexto
            + "\nSua tarefa: se a mensagem responde a uma pergunta anterior, avalie-a; "
            "senão, proponha UM exercício. Use o rascunho do Tutor só como contexto.",
            expected_output="Feedback curto e UMA pergunta ou exercício.",
            agent=self._inquiridor,
            context=[t_tutor],
        )
        t_guardiao = Task(
            description=contexto
            + "\nSua tarefa: revise os rascunhos do Tutor e do Inquiridor e entregue a resposta final.",
            expected_output="A resposta final ao estudante, em português.",
            agent=self._guardiao,
            context=[t_tutor, t_inquiridor],
        )
        crew = Crew(
            agents=[self._tutor, self._inquiridor, self._guardiao],
            tasks=[t_tutor, t_inquiridor, t_guardiao],
            process=Process.sequential,  # um agente por vez, na ordem das tarefas
            verbose=False,
        )
        resultado = crew.kickoff()
        return str(getattr(resultado, "raw", resultado)).strip()

    @staticmethod
    def _saida_valida(texto: str) -> bool:
        return len(texto) >= 15  # descarta saída vazia ou truncada demais

    def resposta(self, pergunta: str) -> str:
        """Ponto de entrada: recebe a mensagem do estudante e devolve a resposta final."""
        pergunta = (pergunta or "").strip()
        if not pergunta:                        # tratamento: entrada vazia
            return MSG_VAZIA
        pergunta = pergunta[:MAX_CHARS_ENTRADA]  # tratamento: entrada longa demais

        try:
            texto = self._executar_crew(pergunta)
        except Exception as erro:               # tratamento: falha do modelo (Ollama fora do ar etc.)
            log.warning("Falha na crew: %s", erro)
            return f"{MSG_FALHA_MODELO}\n(Detalhe técnico: {str(erro)[:200]})"

        if not self._saida_valida(texto):       # tratamento: saída inesperada
            return MSG_SAIDA_INVALIDA

        self._historico.append((pergunta, texto))  # só guarda na memória respostas válidas
        return texto
