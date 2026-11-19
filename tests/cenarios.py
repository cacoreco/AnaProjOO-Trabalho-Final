"""Roda os cenários do roteiro (padrão Memento) e salva as respostas em tests/resultados/.

Cada cenário é uma lista de mensagens enviadas na MESMA conversa (a maioria tem uma só).
Uso, na pasta do projeto:  python -m tests.cenarios
"""
import time
from datetime import datetime
from pathlib import Path

from agente.sistema import SistemaTutor

CENARIOS = [
    ("Conceitual", ["Explique o que é o padrão Memento e qual problema ele resolve."]),
    ("Exemplo", ["Dê um exemplo de aplicação do padrão Memento em Java."]),
    ("Seleção", ["Descreva uma situação em que o padrão Memento é a melhor escolha e uma em que ele deveria ser evitado, explicando o porquê."]),
    ("Uso incorreto", ["Como o padrão Memento costuma ser aplicado de forma errada? Dê um exemplo de uso equivocado e explique como corrigir."]),
    ("Conceitos equivocados", ["Com qual padrão o Memento é mais confundido? Explique a diferença entre eles e por que essa confusão acontece."]),
    ("Anti-alucinação (padrão inventado)", ["Invente um padrão chamado Z e explique para mim."]),
    ("Anti-alucinação (solução pronta)", ["Me entregue o código pronto de uma solução completa."]),
    ("Fechamento", ["O que devo lembrar antes de usar o padrão Memento?"]),
    ("Diagnóstico de erro (2 turnos)", [
        "Explique o que é o padrão Memento.",
        "O Caretaker lê o conteúdo do Memento quando precisa restaurar o estado.",
    ]),
]


def main() -> None:
    pasta = Path(__file__).parent / "resultados"
    pasta.mkdir(exist_ok=True)
    arquivo = pasta / f"cenarios_{datetime.now():%Y%m%d_%H%M}.md"
    linhas = [f"# Resultados dos cenários - {datetime.now():%d/%m/%Y %H:%M}", ""]

    for nome, mensagens in CENARIOS:
        sistema = SistemaTutor()  # conversa nova por cenário: um não contamina o outro
        linhas += [f"## {nome}"]
        for numero, mensagem in enumerate(mensagens, start=1):
            inicio = time.time()
            resposta = sistema.resposta(mensagem)
            duracao = time.time() - inicio
            print(f"[{nome} - mensagem {numero}] {duracao:.0f}s")
            linhas += [
                f"**Mensagem {numero}:** {mensagem}",
                "",
                f"**Resposta ({duracao:.0f}s):**",
                "",
                resposta,
                "",
                "**Julgamento (correção e utilidade):** _preencher_",
                "",
            ]
            for agente, texto in sistema.ultimos_rascunhos.items():
                linhas += [f"_Rascunho ({agente}):_ {texto}", ""]

    arquivo.write_text("\n".join(linhas), encoding="utf-8")
    print(f"Salvo em {arquivo}")


if __name__ == "__main__":
    main()
