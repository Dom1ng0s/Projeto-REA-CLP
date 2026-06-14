# 🎓 Nexos REA — Motor de Recomendação de Recursos Educacionais Abertos

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)](https://jwt.io)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=for-the-badge)](https://sqlalchemy.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-DB-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=for-the-badge)]()

> API REST para curadoria inteligente de REAs: filtra, avalia e recomenda recursos educacionais de forma personalizada com base no perfil e no histórico de interações de cada usuário.

---

## Índice

- [Sobre o projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Requisitos](#-requisitos)
- [Instalação e execução](#-instalação-e-execução)
- [Como usar — Endpoints](#-como-usar--endpoints)
- [Arquitetura](#-arquitetura)
- [Testes](#-testes)
- [Limitações e status atual](#-limitações-e-status-atual)
- [Equipe](#-equipe)
- [Licença](#-licença)

---

## 📖 Sobre o projeto

Professores e estudantes enfrentam sobrecarga de informação ao buscar materiais educacionais abertos: há muitos REAs disponíveis, mas pouca curadoria. O Nexos REA combate isso com um sistema de recomendação personalizado — quanto mais o usuário interage (visualiza, avalia, classifica), mais precisas ficam as sugestões.

O projeto é o backend de um ecossistema maior desenvolvido pelo **Grupo Epsilon** como parte da disciplina de Ciclo de Vida de Projetos na UFAL.

---

## ✨ Funcionalidades

- **Cadastro e autenticação** via JWT (tokens de acesso stateless)
- **Catálogo de REAs** com busca por texto e paginação server-side
- **Submissão de novos REAs** por usuários autenticados
- **Registro de interações:** visualização, avaliação com nota e classificação por tags
- **Coleções pessoais:** criação, listagem, detalhamento, adição e remoção de REAs
- **Perfil de interesses:** leitura e atualização de preferências temáticas do usuário
- **Recomendações personalizadas:** endpoint que retorna REAs rankeados com base no perfil e histórico de interações (`recalcular_pesos`)

---

## 📋 Requisitos

- Python 3.10+
- PostgreSQL (instância local ou na nuvem)
- pip

---

## ⚙️ Instalação e execução

### 1. Clone o repositório

```bash
git clone https://github.com/Dom1ng0s/REA-CLP.git
cd REA-CLP/nexos_rea_backend
```

### 2. Crie e ative o ambiente virtual

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto (`nexos_rea_backend/`):

```env
SECRET_KEY=sua_chave_secreta_aqui
JWT_SECRET_KEY=sua_chave_jwt_secreta_aqui
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nexos_rea
```

### 5. Inicie o servidor

```bash
python src/app.py
```

O servidor estará disponível em `http://localhost:5000`. O SQLAlchemy cria as tabelas automaticamente na primeira execução (`db.create_all()`).

---

## 🔌 Como usar — Endpoints

**URL base:** `http://localhost:5000`

**Autenticação:** endpoints marcados com 🔒 exigem o header:
```
Authorization: Bearer <seu_token_jwt>
```
O token é obtido via `POST /api/auth/login`.

---

### Autenticação (`/api/auth`)

| Método | Endpoint | Auth | Descrição |
|---|---|---|---|
| `POST` | `/api/auth/register` | — | Cadastra novo usuário |
| `POST` | `/api/auth/login` | — | Autentica e retorna o token JWT |
| `GET` | `/api/auth/me` | 🔒 | Retorna os dados do usuário autenticado |

**Exemplo — registro:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Maria", "email": "maria@email.com", "password": "senha123"}'
```

**Exemplo — login:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "maria@email.com", "password": "senha123"}'
# Resposta: { "data": { "access_token": "eyJ..." } }
```

---

### Recursos Educacionais (`/api/reas`)

| Método | Endpoint | Auth | Descrição |
|---|---|---|---|
| `GET` | `/api/reas/` | — | Lista REAs com busca (`?q=`) e paginação (`?page=&per_page=`) |
| `GET` | `/api/reas/<id>` | — | Detalhes de um REA |
| `POST` | `/api/reas/` | 🔒 | Submete um novo REA |
| `POST` | `/api/reas/<id>/visualizacao` | 🔒 | Registra visualização e recalcula pesos de recomendação |
| `POST` | `/api/reas/<id>/avaliacoes` | 🔒 | Avalia um REA com nota |
| `POST` | `/api/reas/<id>/tags` | 🔒 | Classifica um REA com tags |

**Exemplo — busca paginada:**
```bash
curl "http://localhost:5000/api/reas/?q=matematica&page=1&per_page=5"
```

---

### Coleções (`/api/colecoes`)

| Método | Endpoint | Auth | Descrição |
|---|---|---|---|
| `POST` | `/api/colecoes/` | 🔒 | Cria uma nova coleção |
| `GET` | `/api/colecoes/` | 🔒 | Lista as coleções do usuário |
| `GET` | `/api/colecoes/<id>` | 🔒 | Detalhes de uma coleção |
| `DELETE` | `/api/colecoes/<id>` | 🔒 | Remove uma coleção |
| `POST` | `/api/colecoes/<id>/items` | 🔒 | Adiciona um REA à coleção |
| `DELETE` | `/api/colecoes/<id>/items/<rea_id>` | 🔒 | Remove um REA da coleção |

---

### Perfil e Recomendações

| Método | Endpoint | Auth | Descrição |
|---|---|---|---|
| `GET` | `/api/perfil/interesses` | 🔒 | Retorna os interesses do usuário |
| `PUT` | `/api/perfil/interesses` | 🔒 | Atualiza os interesses do usuário |
| `GET` | `/api/recomendacoes/?limit=20` | 🔒 | Retorna REAs recomendados para o usuário |

---

## 🏗️ Arquitetura

O backend segue uma **Arquitetura em Camadas (Layered Architecture)** com separação clara de responsabilidades:

```
nexos_rea_backend/
├── src/
│   ├── app.py                    ← Factory da aplicação + registro de blueprints
│   ├── config.py                 ← Configurações de ambiente
│   │
│   ├── routes/                   ← Camada de Apresentação
│   │   ├── auth_routes.py        ← /api/auth
│   │   ├── rea_routes.py         ← /api/reas
│   │   ├── colecoes_routes.py    ← /api/colecoes
│   │   ├── perfil_routes.py      ← /api/perfil
│   │   └── recomendacao_routes.py← /api/recomendacoes
│   │
│   ├── services/                 ← Camada de Aplicação (lógica de negócio)
│   │   ├── auth_service.py
│   │   ├── rea_service.py
│   │   ├── colecao_service.py
│   │   ├── perfil_service.py
│   │   ├── recomendacao_service.py
│   │   └── interacao_service.py  ← recalcula pesos de recomendação
│   │
│   ├── domain/models/            ← Camada de Domínio (entidades)
│   │   └── models.py
│   │
│   ├── repositories/             ← Acesso a dados (queries SQLAlchemy)
│   │   ├── user_repository.py
│   │   ├── rea_repository.py
│   │   ├── colecao_repository.py
│   │   └── perfil_repository.py
│   │
│   ├── extensions/
│   │   └── database.py           ← Inicialização do SQLAlchemy
│   │
│   └── utils/
│       └── responses.py          ← Helpers success() / error() para respostas JSON
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_reas.py
│   └── test_sprint4.py
│
├── requirements.txt
└── .env
```

**Stack:**

| Responsabilidade | Tecnologia |
|---|---|
| Linguagem | Python 3.10+ |
| Framework | Flask 3.0 |
| ORM | Flask-SQLAlchemy 3.1 |
| Autenticação | Flask-JWT-Extended 4.6 |
| Banco de dados | PostgreSQL (psycopg3) |
| Testes | pytest + pytest-flask |

---

## 🧪 Testes

```bash
cd nexos_rea_backend
pytest tests/
```

Os testes cobrem:
- `test_auth.py` — registro, login, token inválido, `GET /me`
- `test_reas.py` — listagem, busca, submissão, avaliação, tags
- `test_sprint4.py` — funcionalidades da Sprint 4 (coleções e recomendações)

---

## ⚠️ Limitações e status atual

Este projeto está na **Sprint 2** de desenvolvimento ativo. O que já funciona:

- Autenticação JWT completa
- CRUD de REAs com paginação e busca
- Sistema de coleções pessoais
- Registro de interações (visualização, avaliação, classificação)
- Perfil de interesses
- Endpoint de recomendação (implementação inicial do `recalcular_pesos`)

O que ainda não está implementado:
- Deploy em produção (sem URL pública no momento)
- Frontend (este repositório é exclusivamente o backend)
- Algoritmo de recomendação refinado com ML (previsto para sprints futuras)

---

## 👥 Equipe

Projeto desenvolvido pelo **Grupo Epsilon** na disciplina de Ciclo de Vida de Projetos — UFAL.

| Integrante | GitHub |
|---|---|
| Davi Domingos de Oliveira | [@Dom1ng0s](https://github.com/Dom1ng0s) |

---

## 📄 Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.
