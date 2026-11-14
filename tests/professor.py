from crewai import Agent, Task, Crew, LLM  # classes principais do CrewAI

# Aponta o CrewAI para o Ollama local. Sem isso, ele tentaria usar a OpenAI (paga)
llm = LLM(
    model="ollama/qwen2.5-3b-8k",          # a variante que criamos
    base_url="http://localhost:11434",
    context_window_size=8192,              # o CrewAI passa a saber a janela e some o aviso
)

# Um agente = persona (role) + objetivo (goal) + contexto (backstory)
professor = Agent(
    role="Professor de POO",
    goal="Explicar conceitos de orientação a objetos de forma simples",
    backstory="Você é um professor paciente que ensina iniciantes.",
    llm=llm,  # este agente usa o modelo local
)

# Uma tarefa = o que o agente deve fazer e o formato esperado da saída
tarefa = Task(
    description="Explique em 3 frases o que é encapsulamento.",
    expected_output="Três frases em português.",
    agent=professor,
)

crew = Crew(agents=[professor], tasks=[tarefa])  # a "equipe" que executa as tarefas
print(crew.kickoff())                            # roda e imprime a resposta
