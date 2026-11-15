# Política de Segurança

## Recursos de Segurança Ativos neste Repositório

Este repositório usa os seguintes mecanismos automáticos:

- **Dependabot** — monitora dependências vulneráveis e abre PRs de atualização automaticamente (ver `.github/dependabot.yml`)
- **GitHub Secret Scanning** — nativo para repositórios públicos, detecta chaves de API vazadas
- **Gitleaks CI** — camada extra que roda em todo push, procurando padrões de segredo (ver `.github/workflows/secret-scan.yml`)
- **pip-audit** — auditoria de dependências Python a cada commit (ver `.github/workflows/ci.yml`)

## Reportando uma Vulnerabilidade

**Se você encontrou uma vulnerabilidade neste projeto:**

1. **NÃO abra uma issue pública** — vulnerabilidades reportadas em issues ficam visíveis para todos, incluindo potenciais atacantes
2. **Comunique diretamente ao professor** por e-mail institucional
3. Se preferir, use o mecanismo do GitHub: aba **Security → Report a vulnerability**
4. Aguarde retorno em até 48 horas úteis

## O que Fazer se Commitar um Segredo por Engano

**Aconteceu a maioria de nós pelo menos uma vez.** Não entre em pânico, mas aja rápido:

1. **Revogue o segredo imediatamente** no serviço de origem (AWS console, painel da API, etc.). Trocar o segredo é a única mitigação real — remover do Git NÃO basta, pois o histórico permanece.
2. **Avise o professor** para registrar o incidente (aprendizado do time, sem penalidade se reportado honestamente)
3. **Remova do histórico do Git:**
   ```bash
   # Se foi no último commit
   git reset HEAD~1
   # Edite o arquivo, remova o segredo, adicione ao .gitignore
   git add .
   git commit -m "fix: remove segredo commitado por engano"
   git push --force-with-lease
   ```
4. **Se já foi para o main compartilhado**, avise o time antes de fazer force push
5. **Adicione o padrão ao `.gitignore`** para não repetir

## Boas Práticas do Time

- **Nunca escreva segredo no código.** Use `.env` + `python-decouple` ou `django-environ`
- **Nunca commite arquivos `.env`** (já está no `.gitignore`, mas confira)
- **Antes de cada `git push`, olhe o `git diff --staged`** — desenvolveu o reflexo, reduz 90% dos incidentes
- **Rotacione segredos periodicamente** — mesmo sem incidente
- **Configure senhas fortes e 2FA** na sua conta GitHub pessoal
