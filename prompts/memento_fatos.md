FATOS SOBRE O PADRÃO MEMENTO (GoF)

PADRÃO MEMENTO: comportamental, de objeto.
Intenção: sem violar o encapsulamento, capturar e externalizar o estado interno de um objeto para que ele possa ser restaurado depois.
Participantes:
- Originator (nos slides da disciplina, "Fonte"): tem acesso total ao próprio estado. Cria o Memento com um snapshot desse estado e o usa para restaurá-lo. É o ÚNICO que lê o conteúdo do Memento.
- Memento: guarda o snapshot do estado. Tem interface estreita (narrow) para o Caretaker, que é VAZIA (sem métodos para ler, salvar ou restaurar), e interface larga (wide) para o Originator. Salvar e restaurar são métodos do Originator, não do Memento.
- Caretaker: guarda e devolve mementos (por exemplo, uma pilha de undo). NUNCA lê nem altera o conteúdo do Memento.
Quando usar: é preciso restaurar um estado anterior E o acesso direto ao estado (getters e setters) violaria o encapsulamento.
Consequências positivas: preserva o encapsulamento; simplifica o Originator, que não precisa gerenciar o histórico.
Consequências negativas: custo de memória e de cópia se o estado é grande ou os snapshots são frequentes; o Caretaker precisa de uma política de descarte dos mementos antigos.
Quando evitar: estado muito grande salvo com muita frequência; ou quando basta uma operação inversa simples (considerar Command).
Exemplo de quando usar: editor de texto com desfazer, em que o texto do Editor é private.
Exemplo de quando evitar: salvar o texto inteiro de um arquivo muito grande a cada tecla digitada gasta muita memória; alternativa: Command, guardando só a operação e a inversa.
Erros comuns:
- Expor getters ou setters do estado no Memento (por exemplo, um getTexto() público): o Caretaker passa a ler o estado e o encapsulamento é violado. Correção: o Memento não tem métodos públicos de leitura; só o Originator lê.
- Memento e Originator compartilharem a MESMA referência a um objeto mutável (por exemplo, uma lista), sem copiar: se o Originator alterar a lista depois, o snapshot muda junto. Correção: copiar ao salvar E ao restaurar. Com String não há esse problema, porque String é imutável.
- Guardar snapshots sem limite.
Confusão frequente com Command: os dois são usados para implementar desfazer (undo), e por isso se confundem. Command guarda a OPERAÇÃO e precisa saber a operação inversa; Memento guarda o ESTADO. Podem ser combinados: quando a inversa é impossível (por exemplo, converter um texto para maiúsculas perde informação), o Command guarda um Memento do estado anterior para desfazer.
Checklist antes de usar o Memento:
1. O estado é privado e precisa poder voltar atrás?
2. O Memento é opaco para o Caretaker (interface vazia)?
3. Objetos mutáveis são copiados ao salvar e ao restaurar?
4. Existe um limite para a quantidade de snapshots?
5. Uma operação inversa simples bastaria? Então considere Command.

Exemplo canônico em Java (Editor = Originator, EstadoEditor = Memento, Historico = Caretaker):
public class Editor {
    private String texto = "";
    public void escrever(String s) { texto += s; }
    public Memento salvar() { return new EstadoEditor(texto); }       // cria o snapshot
    public void restaurar(Memento m) { texto = ((EstadoEditor) m).texto; }  // só o Editor abre o Memento
    public interface Memento { }                                      // interface VAZIA: é o que o Caretaker enxerga
    private static class EstadoEditor implements Memento {           // o Memento de verdade, escondido
        private final String texto;
        private EstadoEditor(String texto) { this.texto = texto; }
    }
}
class Historico {                                                     // Caretaker: só guarda e devolve
    private final Deque<Editor.Memento> estados = new ArrayDeque<>();
    public void guardar(Editor.Memento m) { estados.push(m); }
    public Editor.Memento recuperar() { return estados.pop(); }
}
Uso: historico.guardar(editor.salvar()); editor.escrever("Olá"); editor.restaurar(historico.recuperar());

CATÁLOGO GoF (23 padrões; estes são os únicos que existem no catálogo):
Criação: Abstract Factory, Builder, Factory Method, Prototype, Singleton.
Estrutura: Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy.
Comportamento: Chain of Responsibility, Command, Interpreter, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor.
