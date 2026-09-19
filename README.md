# [Nome do Projeto]

> Projeto desenvolvido pelo **Grupo XX** na disciplina de Desenvolvimento Web III  
> **FATEC Olímpia** — CST em Desenvolvimento de Software Multiplataforma — 2026/2  
> Professor: [Nome do Professor]

---

## Sobre o Projeto

**Problema que resolve:** [Descreva em 1-2 parágrafos qual é o problema que seu projeto ataca]

**Público-alvo:** [Quem vai usar isso?]

**Organização parceira:** [Nome da organização real com quem vocês fizeram contato]

---

## Equipe

| Nome | Papel principal | GitHub |
|---|---|---|
| [Nome Completo] | Product Owner | [@usuario](https://github.com/usuario) |
| [Nome Completo] | Scrum Master | [@usuario](https://github.com/usuario) |
| [Nome Completo] | Dev Full-stack | [@usuario](https://github.com/usuario) |
| [Nome Completo] | Dev Back-end | [@usuario](https://github.com/usuario) |
| [Nome Completo] | Dev Front-end | [@usuario](https://github.com/usuario) |

---

## Tecnologias

- **Back-end:** Django 5.x + Django REST Framework
- **Front-end:** HTMX + Alpine.js (base) + React (etapa final)
- **Banco de Dados:** SQLite (dev) / PostgreSQL (prod) + MongoDB Atlas
- **Testes:** pytest + pytest-django
- **CI/CD:** GitHub Actions
- **Deploy:** [Railway / Render / Fly.io]

---

## Como Rodar Localmente

### Pré-requisitos
- Python 3.11+
- Git

### Passos

```bash
# 1. Clone o repositório
git clone https://github.com/web3-fatec-olimpia-2026-2/grupo-XX-nome-projeto.git
cd grupo-XX-nome-projeto

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/WSL/Mac
# venv\Scripts\activate    # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com seus valores locais

# 5. Aplique as migrations
python manage.py migrate

# 6. Crie um superusuário para o admin
python manage.py createsuperuser

# 7. Rode o servidor de desenvolvimento
python manage.py runserver
```

Acesse: http://localhost:8000

---

## Como Rodar os Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=. --cov-report=html
# Abrir htmlcov/index.html no navegador
```

---

## Documentação

- [Arquitetura do Sistema](docs/arquitetura.md)
- [Requisitos e User Stories](docs/requisitos.md)
- [Decisões Técnicas (ADRs)](docs/decisoes.md)
- [Manual do Usuário](docs/manual-usuario.md)
- [Guia de Contribuição](CONTRIBUTING.md)
- [Política de Segurança](SECURITY.md)

---

## Sprints

| Sprint | Período | Objetivo | Status |
|---|---|---|---|
| Sprint 1 | 17/08 - 14/09 | Django MTV + CRUD SQLite | [ver Taiga](link) |
| Sprint 2 | 15/09 - 10/10 | NoSQL + Frontend Interativo | [ver Taiga](link) |
| Sprint 3 | 11/10 - 22/11 | APIs + Testes + Arquitetura | [ver Taiga](link) |
| Sprint 4 | 23/11 - 13/12 | Deploy + Polimento + Feira | [ver Taiga](link) |

---

## Demo em Produção

- **URL:** [https://seu-projeto.railway.app](#)
- **Documentação da API (Swagger):** [https://seu-projeto.railway.app/api/docs/](#)
- **Vídeo demo (5 min):** [YouTube](#)

---

## Licença

MIT License — veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## Agradecimentos

- Professor responsável pela disciplina
- Organização parceira que colaborou como stakeholder
- Colegas de outros grupos que fizeram code review
