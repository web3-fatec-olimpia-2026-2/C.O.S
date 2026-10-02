# Guia de Contribuição do Grupo

Este documento define como o grupo trabalha em conjunto. É contrato interno — todo integrante lê e segue.

---

## Fluxo Git

### Branches

- **`main`** — branch de produção, sempre estável, protegida (só recebe merge via PR revisado)
- **`develop`** (opcional) — branch de integração de features antes de subir para `main`
- **`feature/nome-descritivo`** — cada nova funcionalidade em branch própria
- **`fix/nome-descritivo`** — correções de bug
- **`docs/nome-descritivo`** — mudanças só de documentação

### Nomeando branches

```
feature/api-de-reservas
feature/tela-de-login-htmx
fix/paginacao-quebrada
docs/atualizar-readme
```

### Nomeando commits (Conventional Commits)

Formato: `<tipo>(<escopo opcional>): <descrição curta>`

Tipos válidos:
- `feat` — nova funcionalidade
- `fix` — correção de bug
- `docs` — mudança em documentação
- `style` — formatação, ponto e vírgula (sem mudança de lógica)
- `refactor` — refatoração sem mudar comportamento
- `test` — adicionar ou corrigir testes
- `chore` — tarefa de manutenção (dependências, config)

Exemplos:
```
feat(api): adiciona endpoint POST /reservas/
fix(login): corrige erro 500 quando e-mail contém acento
docs(readme): atualiza instruções de setup
refactor(models): extrai lógica de validação para método próprio
test(reservas): adiciona teste de conflito de datas
```

---

## Pull Requests

### Antes de abrir PR

- [ ] Código funciona localmente (rodei e testei)
- [ ] Testes passando (`pytest`)
- [ ] Sem segredos no diff (`git diff --staged` conferido)
- [ ] Commits com mensagem descritiva
- [ ] Branch atualizada com `main` (`git pull origin main --rebase`)

### Ao abrir PR

- **Título:** conventional commit + descrição (ex: `feat(api): endpoint de reservas`)
- **Descrição:** o que muda, por que, como testar
- **Link da User Story do Taiga**
- **Screenshots** se houver mudança visual
- **Marcar reviewers:** mínimo 1 colega + o Scrum Master

### Regras de merge

- **Precisa de 1 aprovação** de outro integrante
- **CI verde** (todos os checks passando)
- **Sem conflitos** com main
- **Squash and merge** (preserva histórico limpo em main)

---

## Padrões de Código

### Python

- **Formatação:** [Ruff](https://docs.astral.sh/ruff/) (rodar antes de commit: `ruff format .`)
- **Linting:** Ruff também (`ruff check .`)
- **Imports:** ordenados (Ruff cuida)
- **Nomes:**
  - Variáveis e funções: `snake_case`
  - Classes: `PascalCase`
  - Constantes: `UPPER_SNAKE_CASE`
  - Privadas: prefixo `_`
- **Docstrings:** em funções com lógica não trivial, no formato Google

### Django

- **Models:** sempre com `__str__` implementado e `Meta.ordering`
- **Views:** preferir CBV quando cabível
- **URLs:** com `name=` obrigatório, para poder usar `reverse()`
- **Templates:** herdar de `base.html`; blocos nomeados

---

## Uso de IA Generativa

Este projeto segue a **Política de IA da disciplina em 4 níveis** (ver contrato pedagógico):

- **Nível 1 (livre):** dúvidas conceituais, traduzir erros, nomear variáveis, revisar gramática
- **Nível 2 (com declaração):** código gerado por IA com mais de 5 linhas → comentário obrigatório:
  ```python
  # Assistido por IA (Claude): "prompt resumido em uma linha"
  ```
  E menção no README do PR
- **Nível 3 (proibido):** avaliação individual, prova prática, sprint review oral
- **Nível 4 (metacompetência):** prompt engineering é ensinado formalmente na aula 2

Aluno deve conseguir **explicar linha a linha** o código do próprio PR. Sprint Review é oral e o professor pode pedir explicação de qualquer trecho aleatoriamente.

---

## Papéis Scrum do Grupo

Os papéis são **rotativos a cada sprint** para todo integrante experimentar cada responsabilidade:

- **Product Owner interno** (1 pessoa) — traduz requisitos, prioriza backlog, aprova entregas parciais
- **Scrum Master interno** (1 pessoa) — facilita cerimônias, remove impedimentos, cuida do Taiga
- **Time de Desenvolvimento** (3 pessoas) — desenvolvedores; entre eles rotacionam pares

## Cerimônias

- **Sprint Planning** — início de cada sprint, ~30 min
- **Daily assíncrona** — segunda a segunda, registrada no Taiga
- **Sprint Review** — fim de cada sprint, apresentação para o professor
- **Retrospective** — fim de cada sprint, formato "manter/melhorar/começar/parar"

---

## Definition of Done

Uma User Story só é considerada "Done" quando:

- [ ] Código na `main` (mergeado via PR)
- [ ] Testes automatizados passando (cobertura mínima geral: 40%)
- [ ] Revisado em code review (mínimo 1 aprovação)
- [ ] Documentado no README ou `docs/`
- [ ] Deploy verificado (a partir da Sprint 3)
- [ ] Sem regressão em outras features
- [ ] Acessibilidade WCAG 2.1 AA quando envolve UI
