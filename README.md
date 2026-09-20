# Sistema Web de Controle de Ordens de Serviço (C.O.S.)

> Projeto desenvolvido pelo **Grupo #C.O.S** na disciplina de Desenvolvimento Web III  
> **FATEC Olímpia** — CST em Desenvolvimento de Software Multiplataforma — 2026/2  
> Professor: José Ceron Neto

---

## Sobre o Projeto

**Problema que resolve:** O sistema digitaliza o processo de abertura e acompanhamento de Ordens de Serviço, eliminando a dependência de controles manuais. Resolve a necessidade de comprovação do trabalho realizado ao exigir o envio de provas fotográficas do estado do local "antes" e "depois" da execução. Além disso, centraliza a informação de forma segura para permitir rastreabilidade total e futuras auditorias às operações.

**Público-alvo:** Administradores (controle operacional), Prestadores de Serviço (executantes no terreno), Utilizadores Comuns (consulta) e Utilizadores Premium (consulta avançada e recolha de indicadores).

**Organização parceira:** Secretaria de Trânsito da Prefeitura de Olímpia

---

## Equipa

| Nome | Papel principal | GitHub |
|---|---|---|
| Douglas Pereira | Product Owner | [@Douglas-LP](https://github.com/Douglas-LP) |
| Douglas Pereira | Scrum Master | [@Douglas-LP](https://github.com/Douglas-LP) |
| Claudinei Feliz | Dev Front-end | [@Claudineifeliz](https://github.com/Claudineifeliz) |
| Gleice Constâncio Rodrigues | Dev Back-end | [@geconstancio] (https://github.com/geconstancio) |
| Isabelly Ribeiro | QA | [@isabelly-ribeiro1] (https://github.com/isabelly-ribeiro1) |

---

## Tecnologias

- **Back-end:** Python e Django 5.x (Autenticação, ORM e Grupos/Permissões) + Django REST Framework.
- **Front-end:** HTML, CSS, JavaScript (Interface responsiva para *smartphones*, *tablets* e computadores) + HTMX + Alpine.js.
- **Base de Dados:** SQLite (ambiente de desenvolvimento) e PostgreSQL (ambiente de produção).
- **Gestão de Ficheiros:** Biblioteca Pillow (processamento do registo fotográfico).
- **Testes:** pytest + pytest-django.
- **CI/CD:** GitHub Actions.
- **Deploy:** [Railway / Render / Fly.io]

---

## Como Rodar Localmente

### Pré-requisitos
- Python 3.11+
- Git

### Passos

```bash
# 1. Clone o repositório
git clone https://github.com/geconstancio/C.O.S.git
cd grupo-XX-gestao-os

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/WSL/Mac
# venv\Scripts\activate    # Windows

# 3. Instale as dependências (incluindo Django e Pillow)
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com os seus valores locais

# 5. Aplique as migrations da base de dados SQLite
python manage.py migrate

# 6. Crie um superusuário para o admin (Perfil: Administrador)
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
| Sprint 1 | 17/08 - 14/09 | Configuração base, Utilizadores, Perfis e Permissões. | [ver Taiga](link) |
| Sprint 2 | 15/09 - 10/10 | Fluxo de O.S. e Área do Prestador (Envio de Fotografias). | [ver Taiga](link) |
| Sprint 3 | 11/10 - 22/11 | Conferência Administrativa, Histórico Imutável e Auditoria. | [ver Taiga](link) |
| Sprint 4 | 23/11 - 13/12 | Dashboards, Indicadores e Deploy Final. | [ver Taiga](link) |

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

- José Ceron Neto
- Secretaria de Trânsito da Prefeitura de Olímpia
- Colegas de outros grupos que fizeram code review
