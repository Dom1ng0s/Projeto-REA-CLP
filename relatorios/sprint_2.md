# Relatório de Desenvolvimento — Sprint 2
**Projeto:** Nexos REA — Backend  
**Branch:** `sprint-2/desenvolvimento`  
**Período:** 26 de maio de 2026  
**Stack:** Python · Flask 3.0.3 · SQLAlchemy 3.1.1 · JWT · PostgreSQL 16 · pytest

---

## Objetivo da Sprint

Construir a fundação do back-end: modelagem relacional completa do banco de dados, autenticação segura via JWT e o primeiro módulo funcional de CRUD — os Recursos Educacionais Abertos (REAs) — com busca e paginação, coberto por testes automatizados.

---

## Commits entregues

| Hash | Data | Descrição |
|------|------|-----------|
| `0d396a8` | 26/05/2026 | Estrutura `src/` e modelagem relacional completa |
| `63db7e9` | 26/05/2026 | Autenticação JWT: register, login, /me |
| `860b1e0` | 26/05/2026 | Docker Compose com PostgreSQL 16 |
| `411842b` | 26/05/2026 | CRUD de REAs com busca e paginação |
| `acd5f70` | 26/05/2026 | Suite de testes automatizados (24 testes) |
| `ae53015` | 26/05/2026 | Bloqueio de URL duplicada + guia de testes `api.http` |

---

## Fase 1 — Modelagem Relacional e Estrutura do Projeto

### Reestruturação do `src/`

O diretório foi reorganizado para o layout em camadas que sustenta toda a aplicação:

```
src/
├── extensions/
│   └── database.py        ← instância única do SQLAlchemy (db)
├── models/
│   └── models.py          ← todas as classes ORM
├── repositories/          ← acesso ao banco de dados
├── services/              ← regras de negócio
├── routes/                ← controladores HTTP (Blueprints)
├── utils/
│   └── responses.py       ← helpers success() / error()
├── schemas/
├── config.py
└── app.py                 ← factory create_app()
```

### Modelos implementados (`src/models/models.py` — 154 linhas)

| Classe | Tabela | Relacionamentos-chave |
|--------|--------|----------------------|
| `User` | `users` | 1:N com Collection, Rating, Report, REA |
| `Tag` | `tags` | N:M com REA (via REATag) e User (via UserTagInterest) |
| `UserTagInterest` | `user_tag_interests` | PK composta (user_id, tag_id) · campo `weight float` |
| `REA` | `reas` | 1:N com Rating, Report, CollectionItem, REATag |
| `REATag` | `rea_tags` | Tabela associativa REA ↔ Tag |
| `Rating` | `ratings` | UniqueConstraint(user_id, rea_id) · CheckConstraint(score 1-5) |
| `Report` | `reports` | UniqueConstraint(user_id, rea_id) |
| `Collection` | `collections` | 1:N com User · 1:N com CollectionItem |
| `CollectionItem` | `collection_items` | Tabela associativa Collection ↔ REA · campo `added_at` |

**Decisões de modelagem:**
- PKs em UUID v4 para `User`, `REA` e `Collection` — evita enumeração e facilita federação futura.
- PKs compostas naturais em todas as tabelas associativas — sem surrogate key desnecessária.
- `cascade="all, delete-orphan"` em todos os relacionamentos pai → filho.
- `ondelete="CASCADE"` e `ondelete="SET NULL"` configurados diretamente nas FKs do banco.
- Timestamps em `DateTime(timezone=True)` com helper `_now()` retornando `datetime.now(timezone.utc)`.

---

## Fase 2 — Autenticação JWT

### Arquivos criados

- `src/repositories/user_repository.py` — `find_by_email`, `find_by_id`, `create`
- `src/services/auth_service.py` — `register`, `login`, `get_me`
- `src/routes/auth_routes.py` — Blueprint `auth_bp`
- `src/utils/responses.py` — helpers `success()` / `error()`

### Endpoints de autenticação

| Método | Rota | Proteção | Comportamento |
|--------|------|----------|---------------|
| `POST` | `/api/auth/register` | pública | Cria usuário; valida e-mail, senha mínima 6 chars, unicidade |
| `POST` | `/api/auth/login` | pública | Retorna `access_token` JWT (2h) + dados do usuário |
| `GET` | `/api/auth/me` | `@jwt_required()` | Retorna perfil do usuário autenticado |

**Configurações JWT (`config.py`):**
- `JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)`
- Segredos via variáveis de ambiente (`SECRET_KEY`, `JWT_SECRET_KEY`)
- Conexão PostgreSQL via `DATABASE_URL` ou fallback local

---

## Fase 3 — CRUD de REAs

### Arquivos criados

- `src/repositories/rea_repository.py` — `list_visible`, `find_by_id`, `find_by_url`, `create`
- `src/services/rea_service.py` — `list_reas`, `get_rea`, `submit_rea`
- `src/routes/rea_routes.py` — Blueprint `rea_bp`

### Endpoints de REAs

| Método | Rota | Proteção | Comportamento |
|--------|------|----------|---------------|
| `GET` | `/api/reas/` | pública | Lista REAs visíveis com busca (`?q=`) e paginação (`?page=&per_page=`) |
| `GET` | `/api/reas/<id>` | pública | Detalhe de um REA específico |
| `POST` | `/api/reas/` | `@jwt_required()` | Submete novo REA; valida campos obrigatórios e URL duplicada |

**Tipos de recurso aceitos:** `video`, `article`, `course`, `ebook`, `exercise`, `other`  
**Limite de paginação:** `per_page` capped em 50 registros  
**Busca:** `ILIKE` case-insensitive em `title` e `description`  
**Proteção extra (commit `ae53015`):** `find_by_url` antes do insert — retorna HTTP 400 se URL já cadastrada

---

## Fase 4 — Infraestrutura e Qualidade

### Docker Compose (`docker-compose.yml`)

```yaml
postgres:
  image: postgres:16-alpine
  ports: "5432:5432"
  volumes: pgdata (persistente)
  environment: POSTGRES_DB=nexos_rea
```

Banco de testes separado: `nexos_rea_test`

### Suite de Testes (`tests/` — 24 testes)

**`conftest.py`:**
- Fixture `app` com escopo de sessão — cria e destrói as tabelas uma vez
- Fixture `clean_db` com `autouse=True` — trunca todas as tabelas entre testes via `metadata.sorted_tables` em ordem reversa (respeita FKs)

**`test_auth.py` — 11 testes:**

| Teste | Cenário |
|-------|---------|
| `test_register_success` | Registro válido retorna 201 e não expõe `password_hash` |
| `test_register_duplicate_email` | Segundo registro com mesmo e-mail → 400 |
| `test_register_missing_name` | Campo obrigatório ausente → 400 |
| `test_register_invalid_email` | Formato de e-mail inválido → 400 |
| `test_register_short_password` | Senha < 6 chars → 400 |
| `test_login_success` | Credenciais corretas → 200 + token |
| `test_login_wrong_password` | Senha errada → 401 |
| `test_login_unknown_email` | E-mail inexistente → 401 |
| `test_login_missing_fields` | Body vazio → 401 |
| `test_me_authenticated` | Token válido → 200 + dados |
| `test_me_without_token` / `test_me_invalid_token` | 401 / 422 |

**`test_reas.py` — 13 testes:**

| Grupo | Testes |
|-------|--------|
| Listagem | empty, with_results, search_by_title, search_no_results, pagination |
| Detalhe | by_id, not_found, invalid_id |
| Submissão | success, without_token, missing_title, invalid_type, duplicate_url |

### Guia de testes manual (`api.http`)

Arquivo com 122 linhas cobrindo todos os endpoints em formato REST Client (VS Code), incluindo variáveis de ambiente para token JWT.

---

## Resumo de métricas

| Categoria | Quantidade |
|-----------|-----------|
| Modelos ORM | 9 classes / 9 tabelas |
| Endpoints HTTP | 6 (3 auth + 3 reas) |
| Testes automatizados | 24 |
| Arquivos criados | ~16 |
| Dependências de produção | 5 (Flask, SQLAlchemy, JWT, psycopg, python-dotenv) |

---

## Padrões estabelecidos na Sprint

1. **Factory pattern** — `create_app(config_class)` para facilitar testes com config diferente
2. **Arquitetura em 3 camadas** — route → service → repository; sem acesso direto ao `db` fora do repositório
3. **Erros como `ValueError`** — propagados do service, capturados na rota e convertidos em JSON com código HTTP adequado
4. **Resposta padronizada** — `{"success": bool, "data"?: ..., "message"?: ...}`
5. **Queries SQLAlchemy 2.x** — `db.select()`, `db.session.get()`, `db.paginate()` (sem legacy `Model.query`)
