FATOS SOBRE O PADRÃO MEMENTO (GoF)

PADRÃO MEMENTO: comportamental, de objeto.
Intenção: sem violar o encapsulamento, capturar e externalizar o estado interno de um objeto para que ele possa ser restaurado depois.
Participantes:
- Originator (nos slides da disciplina, "Fonte"): cria o Memento com um snapshot do seu estado e o usa para restaurá-lo. Só ele lê o conteúdo do Memento.
- Memento: guarda o snapshot do estado. Tem interface estreita (narrow) para o Caretaker (nada para ler) e interface larga (wide) para o Originator.
- Caretaker: guarda e devolve mementos (por exemplo, uma pilha de undo). Nunca examina nem altera o conteúdo do Memento.
Quando usar: é preciso restaurar um estado anterior E o acesso direto ao estado (getters e setters) violaria o encapsulamento.
Consequências positivas: preserva o encapsulamento; simplifica o Originator, que não precisa gerenciar o histórico.
Consequências negativas: custo de memória e de cópia se o estado é grande ou os snapshots são frequentes; o Caretaker precisa de uma política de descarte dos mementos antigos.
Quando evitar: estado muito grande salvo com muita frequência; ou quando basta uma operação inversa simples (considerar Command).
Erros comuns: expor getters ou setters do estado no Memento; compartilhar referência a objeto mutável entre Memento e Originator (é preciso copiar ao salvar E ao restaurar); guardar snapshots sem limite.
Confusão frequente com Command: Command guarda a OPERAÇÃO e precisa saber a operação inversa; Memento guarda o ESTADO. Podem ser combinados: um Command pode usar um Memento para desfazer.
Exemplo canônico (Java): editor de texto com desfazer. Editor é o Originator, EstadoEditor é o Memento (classe privada aninhada que implementa uma interface vazia) e Historico é o Caretaker (pilha de mementos).
Problema que motiva o padrão: guardar o estado anterior dentro do próprio Editor (um atributo texto anterior) só permite um nível de desfazer e mistura edição com gerenciamento de histórico; expor o estado para outra classe guardá-lo quebra o encapsulamento.

CATÁLOGO GoF (23 padrões; estes são os únicos que existem no catálogo):
Criação: Abstract Factory, Builder, Factory Method, Prototype, Singleton.
Estrutura: Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy.
Comportamento: Chain of Responsibility, Command, Interpreter, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor.
