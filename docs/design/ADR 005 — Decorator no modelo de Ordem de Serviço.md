# ADR 005 — Decorator no modelo de Ordem de Serviço

## Contexto
O sistema gerencia Ordens de Serviço (caminho: `ordens/models.py`) que possuem diferentes categorias (Sinalização Horizontal, Vertical, Semafórica), prioridades e status. Avaliamos se caberia o uso do padrão Decorator (GoF) para encadear regras de negócio adicionais, calcular prazos dinâmicos ou formatar a exibição/exportação dessas OS combinando suas características.

## Decisão
Não aplicamos o padrão Decorator (GoF) na camada de modelo ou nas regras de negócio das Ordens de Serviço.

## Justificativa
As variações presentes na nossa `OrdemServico` não representam responsabilidades opcionais que precisam ser empilhadas dinamicamente. Elas são características estruturais da entidade bem resolvidas por enumerações nativas do Django (as classes internas de `TextChoices`, como `Categoria.choices` e `Prioridade.choices`). 

O padrão Decorator (GoF) seria arquiteturalmente justificado se precisássemos envolver o objeto para somar comportamentos aditivos durante a execução — por exemplo, calcular o custo de uma OS Base, empilhando um Decorator de Adicional Noturno, depois um Decorator de Taxa de Urgência, e outro de Desconto. No escopo atual, nossa necessidade é apenas classificar a ordem, o que torna uma lista fixa de opções perfeitamente suficiente. Implementar um Decorator estrutural (GoF) aqui seria excesso de cerimônia (overengineering) para um problema que não existe.

Adicionalmente, mantemos a estrita separação conceitual: os decorators de função sintáticos do Python (`@login_required`, `@require_POST`) que já utilizamos amplamente em `ordens/views.py` para controle de acesso e requisições HTTP não têm relação com a decisão de rejeitar o padrão de projeto estrutural GoF.

## Consequências
A estrutura de dados permanece limpa e alinhada às convenções do ORM do Django. Mantemos as validações no método `save()` e `clean()`, evitando hierarquias complexas de wrappers (classes embrulhando classes). A complexidade do sistema não foi aumentada artificialmente, facilitando a manutenção futura do código e a avaliação do projeto.