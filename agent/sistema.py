"""
Orquestração da crew com modelo local (Ollama).

Fluxo de um turno:
  0. guardrails em Python: pedido inválido, cumprimento ou assunto fora do tema (guardrails.py)
    -> resposta fixa, sem chamar o modelo
  1. estudante fez uma pergunta/pedido novo:
    -> Tutor -> Inquiridor
  2. estudante respondeu a uma pergunta nossa:
    -> Inquiridor recebe o gabarito e a dica, quando existem (uma pergunta nova feita logo depois de uma pergunta nossa volta para o fluxo 1)
  3. pós-processamento em Python (agent/pos_processamento.py):
       -> limpar a saída (preâmbulo, repetição, corte no meio da frase)
       -> verificar erros conhecidos; o Guardião (modelo) só é chamado se houver algum
       -> no pedido de exemplo, usar o código canônico dos FATOS
       -> garantir que a resposta termine com uma pergunta válida (do Inquiridor ou do banco de perguntas)
"""

import logging

from crewai import LLM, Agent, Crew, Process, Task

from .prompts import carregar_fatos, carregar_prompt
from .guardrails import eh_novo_pedido, verificar_pedido, verificar_tema
from .pos_processamento import (
    anexar_pergunta,
    eh_pedido_de_exemplo,
    eh_recusa,
    extrair_codigo_canonico,
    extrair_pergunta,
    garantir_codigo,
    limpar_saida,
    parece_resposta_do_tema,
    remover_problemas,
    revisao_aceitavel,
    verificar_rascunho,
)
 
# --- Limites para não estourar a janela de 8k ------------------------------
TURNOS_NO_HISTORICO = 3                # quantos pares pergunta/resposta entram no prompt
MAX_CHARS_ENTRADA = 1500               # tamanho máximo da pergunta do estudante
MAX_CHARS_POR_MENSAGEM = 600           # corte de cada mensagem guardada no histórico
# Teto de tokens por resposta de agente. Sem ele, modelos pequenos podem entrar em repetição
# e gerar milhares de tokens sem parar (visto com o qwen2.5:0.5b: mais de 13 mil numa resposta).
MAX_TOKENS_POR_AGENTE = 800
# Tamanho máximo da explicação, em linhas. É a ÚNICA fonte desse limite: entra nos prompts pelo marcador
# {limite_linhas} e na instrução de cada tarefa (antes eram 8, 10, 12 e 15 em lugares diferentes).
LIMITE_LINHAS = 14

# --- Mensagens de erro amigáveis -------------------------------------------
MSG_VAZIA = "Digite uma pergunta sobre o padrão Memento."
MSG_FALHA_MODELO = (
    "Não consegui falar com o modelo local. Verifique se o Ollama está em "
    "execução (por exemplo: systemctl status ollama) e tente novamente."
)
MSG_SAIDA_INVALIDA = "Não consegui gerar uma resposta confiável agora. Tente reformular a pergunta."
# Sem "?" no fim, de propósito: a próxima mensagem não deve ser confundida com a resposta a uma pergunta nossa.
MSG_NAO_SEI = (
    "Não tenho essa informação com segurança; consulte os slides da disciplina ou o livro do GoF. "
    "Posso explicar o Memento. Se quiser, pergunte: \"Qual problema o Memento resolve?\""
)
 
log = logging.getLogger(__name__)
 
class SistemaTutor:
    """
    Tutor multiagente do padrão Memento. Uma instância = uma conversa.
    """
 
    def __init__(self, model: str, base_url: str, temperature: float, context_window_size: int) -> None:
        """
        Inicia o sistema de acordo com as opções especificadas. As opções saem dos argumentos da linha de comando
        """

        fatos = carregar_fatos()
        self._codigo_canonico = extrair_codigo_canonico(fatos)  # exemplo em Java dos FATOS, usado nos pedidos de exemplo
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

        self._historico = []            # memória da conversa: lista de (pergunta, resposta)
        self._pendente = None           # pergunta do banco ainda sem resposta (tem gabarito e dica), ou None
        self._perguntas_feitas = set()  # temas do banco já usados nesta conversa
        self.ultimos_rascunhos = {}     # saída de cada agente no último turno (depuração e testes)
 
    def _criar_agente(self, nome: str, fatos: str) -> Agent:
        """
        Cria um novo agente CrewAI

        Args:
            nome(str): nome do agente
            fatos(str): fatos retirados do arquivo de fatos

        Retorna:
            Agent: objeto do tipo agente
        """

        prompt = carregar_prompt(nome, fatos, LIMITE_LINHAS)
        return Agent(
            role=prompt["role"],
            goal=prompt["goal"],
            backstory=prompt["backstory"],
            llm=self._llm,
            allow_delegation=False,  # os papéis são fixos: ninguém delega para outro agente
            verbose=False,
        )
 
    def _texto_historico(self) -> str:
        """
        Retorna o histórico armazenado, se tiver
        """

        if not self._historico:
            return "(conversa nova, sem histórico)"
        linhas = []
        for pergunta, resposta in self._historico[-TURNOS_NO_HISTORICO:]:
            linhas.append(f"Estudante: {pergunta[:MAX_CHARS_POR_MENSAGEM]}")
            linhas.append(f"Sistema: {resposta[:MAX_CHARS_POR_MENSAGEM]}")
        return "\n".join(linhas)
 
    def _sistema_fez_pergunta(self) -> bool:
        """
        Retorna True se a última resposta do sistema terminou com uma pergunta ao estudante.
        """

        return bool(self._historico) and self._historico[-1][1].rstrip().endswith("?")
 
    def _estudante_esta_respondendo(self, mensagem: str) -> bool:
        """
        Retorna True se a mensagem é a resposta do estudante à nossa última pergunta.
 
        Uma pergunta ou pedido novo (termina com '?' ou começa com "explique", "dê um exemplo"...)
        não é resposta: antes, qualquer mensagem depois de uma pergunta nossa ia para o modo
        AVALIAR, o Tutor nunca mais era chamado e o sistema repetia a mesma pergunta em loop.
        """

        return self._sistema_fez_pergunta() and not eh_novo_pedido(mensagem)
 
    # --- Execução dos agentes -------------------------------------------------
 
    def _rodar(self, nomeadas: list[(str, Task)]) -> None:
        """
        Roda as tarefas em sequência e guarda a saída de cada agente, para ver onde uma resposta ruim nasceu.

        Args:
            nomeadas (list[(str, Task)]): tarefas nomeadas a serem executadas
        """

        crew = Crew(
            agents=[tarefa.agent for _, tarefa in nomeadas],
            tasks=[tarefa for _, tarefa in nomeadas],
            process=Process.sequential,  # um agente por vez, na ordem das tarefas
            verbose=False,
        )
        crew.kickoff()

        for nome, tarefa in nomeadas:
            self.ultimos_rascunhos[nome] = self._saida_da_tarefa(tarefa)
 
    def _explicar(self, pergunta: str) -> str:
        """
        Fluxo 1: Tutor explica; Inquiridor escreve uma pergunta. Devolve o rascunho do Tutor.
        """

        # O texto é montado em Python (f-string), sem variáveis do CrewAI.
        contexto = (
            f"HISTÓRICO RECENTE:\n{self._texto_historico()}\n\n"
            f"MENSAGEM DO ESTUDANTE:\n{pergunta}\n"
        )
        t_tutor = Task(
            description=contexto
            + "\nSua tarefa: responda como Tutor, seguindo suas regras, à MENSAGEM DO ESTUDANTE acima. "
            "O histórico serve só de contexto: não repita respostas anteriores do Sistema.",
            expected_output=f"Explicação clara e completa em português, com no máximo {LIMITE_LINHAS} linhas, "
            "sem pergunta no final.",
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
        self._rodar([("tutor", t_tutor), ("inquiridor", t_inquiridor)])
        return self.ultimos_rascunhos["tutor"]
 
    def _avaliar(self, resposta_do_estudante: str) -> str:
        """
        Fluxo 2: Inquiridor avalia a resposta do estudante. Devolve o feedback com a próxima pergunta.
        """

        if self._pendente is not None:
            # Pergunta do banco: o Inquiridor recebe o gabarito (para comparar) e a dica (para dar se errar).
            ultima_pergunta = self._pendente.texto
            referencia = (
                f"\nRESPOSTA ESPERADA (do material; NÃO revele ao estudante): {self._pendente.gabarito}\n"
                f"DICA (use se a resposta estiver errada ou incompleta, sem revelar a resposta): {self._pendente.dica}\n"
            )
        else:
            # Só a última pergunta e a resposta: com o histórico inteiro, o modelo avaliava uma
            # mensagem antiga do estudante (chegou a dizer que uma resposta certa estava errada).
            ultima_pergunta = extrair_pergunta(self._historico[-1][1]) or self._historico[-1][1]
            referencia = ""
        t_inquiridor = Task(
            description=f"PERGUNTA DO SISTEMA:\n{ultima_pergunta}\n\n"
            f"RESPOSTA DO ESTUDANTE (é esta que você avalia):\n{resposta_do_estudante}\n{referencia}"
            "\nMODO AVALIAR: avalie SOMENTE a RESPOSTA DO ESTUDANTE acima, comparando-a com os FATOS, "
            "conforme suas regras, e termine com a próxima pergunta curta.",
            expected_output="Feedback de até 2 linhas e UMA pergunta curta no final.",
            agent=self._inquiridor,
        )
        self._rodar([("inquiridor", t_inquiridor)])
        return self.ultimos_rascunhos["inquiridor"]
 
    def _revisar(self, texto: str, avaliando: bool) -> str:
        """
        Revisão em duas camadas.

        1) Python procura erros conhecidos (agent/pos_processamento.py).
        2) O Guardião (modelo) só é chamado se achar algum, e corrige SOMENTE o que foi apontado.

        Se ele não corrigir, as frases com erro são removidas: o texto final nunca carrega um erro conhecido.
        """

        problemas = verificar_rascunho(texto, avaliando)
        if not problemas:
            self.ultimos_rascunhos["guardiao"] = "(não chamado: nenhum erro conhecido detectado)"
            return texto
 
        lista = "\n".join(f'- {p.descricao} Trecho: "{p.trecho}"' for p in problemas)
        t_guardiao = Task(
            description=f"RASCUNHO A REVISAR:\n{texto}\n\n"
            f"PROBLEMAS ENCONTRADOS (verificação automática):\n{lista}\n\n"
            "Sua tarefa: reescreva o RASCUNHO corrigindo SOMENTE esses problemas, de acordo com os FATOS. "
            "Mantenha o restante igual, inclusive blocos de código. Escreva para o estudante (\"você\"), "
            "sem comentar a revisão.",
            expected_output="O texto completo do rascunho, com os problemas corrigidos.",
            agent=self._guardiao,
        )
        try:
            self._rodar([("guardiao", t_guardiao)])
            revisado = limpar_saida(self.ultimos_rascunhos["guardiao"])
        except Exception as erro:  # a explicação do Tutor ainda vale: não perde o turno por causa do Guardião
            log.warning("Falha no Guardião: %s", erro)
            revisado = ""
 
        # O Guardião só corrige: se a saída dele não se parece com o rascunho, descarta e mantém o rascunho.
        candidato = revisado if revisao_aceitavel(texto, revisado) else texto
        restantes = verificar_rascunho(candidato, avaliando)
        return remover_problemas(candidato, restantes) if restantes else candidato
 
    @staticmethod
    def _saida_da_tarefa(tarefa: Task) -> str:
        saida = getattr(tarefa, "output", None)
        return str(getattr(saida, "raw", "") or "").strip()
 
    @staticmethod
    def _saida_valida(texto: str) -> bool:
        return len(texto) >= 16  # descarta saída vazia ou truncada demais
 
    def resposta(self, pergunta: str) -> str:
    """
    Ponto de entrada: recebe a mensagem do estudante e devolve a resposta final.

    Args:
        pergunta (str): prompt digitado pelo usuário
    
    Retorna:
        str: resposta gerada pelo modelo
    """

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
                bruto = self._avaliar(pergunta) if avaliar else self._explicar(pergunta)
            except Exception as erro:                 # tratamento: falha do modelo (Ollama fora do ar etc.)
                log.warning("Falha na crew: %s", erro)
                return f"{MSG_FALHA_MODELO}\n(Detalhe técnico: {str(erro)[:200]})"
 
            texto = limpar_saida(bruto)
            if not self._saida_valida(texto):         # tratamento: saída inesperada
                return MSG_SAIDA_INVALIDA
 
            if not avaliar:
                if eh_recusa(texto):                  # o modelo disse que não sabe: usa a recusa padrão, sem pergunta
                    self.ultimos_rascunhos["guardrail"] = "recusa do modelo, trocada pela mensagem padrão"
                    return MSG_NAO_SEI
                if not parece_resposta_do_tema(texto):  # explicação que não fala do assunto: não mostra
                    return MSG_SAIDA_INVALIDA
 
            texto = self._revisar(texto, avaliando=avaliar)
            if not avaliar and eh_pedido_de_exemplo(pergunta):
                texto = garantir_codigo(texto, self._codigo_canonico)
            if not self._saida_valida(texto):         # a revisão pode ter removido frases demais
                return MSG_SAIDA_INVALIDA
 
            texto, do_banco = anexar_pergunta(
                texto, pergunta, self.ultimos_rascunhos.get("inquiridor", ""), self._perguntas_feitas
            )
            self._pendente = do_banco                 # None: pergunta do próprio modelo, sem gabarito
            if do_banco is not None:
                self._perguntas_feitas.add(do_banco.tema)
 
            self._historico.append((pergunta, texto))  # só guarda na memória respostas válidas
            return texto
        except (EOFError, KeyboardInterrupt):
            return "AÇÃO INTERROMPIDA"
 