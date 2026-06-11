# Relatório de Desenvolvimento — Sprint 3
**Projeto:** Nexos REA — Backend  
**Branch:** `sprint-2/desenvolvimento` (continuação)  
**Data:** 08 de junho de 2026  
**Stack:** Python · Flask 3.0.3 · Flask-SQLAlchemy 3.1.1 · Flask-JWT-Extended 4.6.0 · PostgreSQL 16

---

## Objetivo da Sprint

Implementar o módulo de **Perfil e Interação**: estruturas de banco para gestão de coleções pessoais de REAs e o perfil analítico de interesses do aluno, seguidos dos controladores HTTP protegidos por JWT.

A sprint foi dividida em duas fases executadas em sequência:

---

## Fase 1 — Modelagem de Perfil e Coleções

### Avaliação arquitetural: JSONB vs. tabela relacional

Antes de escrever código, foi analisada a melhor estratégia para armazenar os pesos de interesse do aluno:

**Opção A — JSONB no modelo `User`**  
Coluna `tag_weights JSONB` armazenando `{"matematica": 1.5, "fisica": 0.8}`.

**Opção B — Tabela relacional `user_tag_interests`**  
Linha por (usuário, tag) com coluna `weight FLOAT`.

**Decisão: Opção B (tabela relacional)**, pelos seguintes motivos:

| Critério | JSONB | Relacional |
|----------|-------|------------|
| Integridade referencial (FK → tags) | Impossível | Garantida |
| Query "usuários interessados em tag X" | Lento (scan no JSON) | Índice em (tag_id, weight) |
| Atualização atômica de um peso | Rewrite do documento inteiro | UPDATE em uma linha |
| Preparação para Sprint 4 (recálculo de pesos por evento) | Complexo | Operação simples e indexada |

JSONB seria adequado apenas se os pesos fossem lidos sempre em bloco e nunca consultados individualmente — o oposto do que o sistema de recomendação exigirá.

### Modelos validados em `src/models/models.py`

Os modelos necessários já estavam implementados corretamente desde a Sprint 2. A Fase 1 consistiu em validar os relacionamentos e as decisões de design:

**Perfil analítico:**

```python
class Tag(db.Model):                     # catálogo de tags
    id   = Integer PK
    name = String(100) unique
    slug = String(100) unique + index

class UserTagInterest(db.Model):         # PerfilAnalitico
    user_id    = UUID FK → users          # PK composta
    tag_id     = Integer FK → tags        # PK composta
    weight     = Float  default=1.0       # recalculado na Sprint 4
    updated_at = DateTime (auto-update)
```

**Gestão de coleções:**

```python
class Collection(db.Model):             # 1:N com User
    id         = UUID PK
    user_id    = UUID FK → users (CASCADE)
    name       = String(200)
    is_public  = Boolean default=False
    created_at = DateTime

class CollectionItem(db.Model):         # tabela associativa N:M
    collection_id = UUID FK → collections  # PK composta
    rea_id        = UUID FK → reas         # PK composta
    added_at      = DateTime
```

**Diagrama de relacionamentos:**

```
users ──< collections ──< collection_items >── reas
  │                                              │
  └──< user_tag_interests >── tags ──< rea_tags ─┘
             weight ↑
         (Sprint 4 recalcula)
```

---

## Fase 2 — Controladores e Validação de Dados

### Arquivos criados

| Arquivo | Camada | Linhas |
|---------|--------|--------|
| `src/repositories/colecao_repository.py` | Repositório | 48 |
| `src/repositories/perfil_repository.py` | Repositório | 44 |
| `src/services/colecao_service.py` | Serviço | 119 |
| `src/services/perfil_service.py` | Serviço | 60 |
| `src/routes/colecoes_routes.py` | Rota (Blueprint) | 93 |
| `src/routes/perfil_routes.py` | Rota (Blueprint) | 30 |
| `src/app.py` | Aplicação | atualizado |
| **Total novo** | | **394 linhas** |

---

### Módulo de Coleções

#### Repositório (`colecao_repository.py`)

| Função | Operação |
|--------|----------|
| `find_by_id(collection_id)` | `db.session.get(Collection, uuid)` |
| `list_by_user(user_id)` | SELECT + `selectinload(Collection.items)` + ORDER BY created_at DESC |
| `create(user_id, name, is_public)` | INSERT + commit |
| `delete(collection)` | DELETE + commit (cascade para itens) |
| `find_item(collection_id, rea_id)` | `db.session.get(CollectionItem, (pk1, pk2))` |
| `add_item(collection_id, rea_id)` | INSERT + commit |
| `remove_item(item)` | DELETE + commit |

**N+1 eliminado:** `list_by_user` usa `selectinload(Collection.items)` — SQLAlchemy emite um único `IN` query para carregar todos os itens de todas as coleções retornadas.

#### Serviço (`colecao_service.py`)

Regras de negócio implementadas:

- **Criação:** `name` obrigatório, máximo 200 chars; `is_public` booleano opcional (default `False`)
- **Isolamento por dono:** toda operação que acessa uma coleção específica chama `_assert_owner()` — compara `str(col.user_id)` com o `user_id` do JWT
- **Adicionar REA:** verifica se o REA existe e está visível antes de inserir; bloqueia duplicata com mensagem clara
- **Remover REA:** verifica existência do item antes de deletar
- **Serialização dupla:** `_serialize()` para listas (sem itens, com `item_count`) e `_serialize_with_items()` para detalhe

#### Blueprint (`colecoes_routes.py`)

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `POST` | `/api/colecoes/` | JWT | Criar coleção — body: `{name, is_public?}` |
| `GET` | `/api/colecoes/` | JWT | Listar todas as coleções do usuário logado |
| `GET` | `/api/colecoes/<id>` | JWT | Detalhe com lista de REAs da coleção |
| `DELETE` | `/api/colecoes/<id>` | JWT | Deletar coleção (cascade nos itens) |
| `POST` | `/api/colecoes/<id>/items` | JWT | Adicionar REA — body: `{rea_id}` |
| `DELETE` | `/api/colecoes/<id>/items/<rea_id>` | JWT | Remover REA da coleção |

---

### Módulo de Perfil de Interesses

#### Repositório (`perfil_repository.py`)

| Função | Operação |
|--------|----------|
| `find_tag_by_id(tag_id)` | `db.session.get(Tag, tag_id)` |
| `list_interests(user_id)` | SELECT + `selectinload(UserTagInterest.tag)` + ORDER BY weight DESC |
| `replace_interests(user_id, interesses)` | DELETE existentes → INSERT novos → commit → re-query com eager load |

**Semântica do `replace_interests`:** substitui o perfil inteiro atomicamente em uma única transação. Correto para a semântica de PUT (idempotente: dois PUTs idênticos produzem o mesmo estado).

**Re-query pós-commit:** após o `commit`, os objetos SQLAlchemy ficam com atributos expirados. O repositório faz um segundo SELECT com `selectinload` para retornar objetos com `tag.name` e `tag.slug` já carregados — evita N+1 na serialização.

#### Serviço (`perfil_service.py`)

Regras de validação do payload `PUT /interesses`:

- `interesses` deve ser uma lista (não dict, não string)
- Limite de 50 interesses por perfil
- Cada item: `tag_id` inteiro positivo obrigatório; `weight` float no intervalo `(0.0, 10.0]`
- `tag_id` duplicado na mesma lista é rejeitado antes de qualquer escrita
- `tag_id` inexistente no banco levanta `LookupError` → HTTP 404

#### Blueprint (`perfil_routes.py`)

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `GET` | `/api/perfil/interesses` | JWT | Retorna lista de tags e pesos do usuário, ordenado por peso decrescente |
| `PUT` | `/api/perfil/interesses` | JWT | Substitui perfil completo — body: `{"interesses": [{tag_id, weight}, ...]}` |

**Exemplo de payload (PUT):**
```json
{
  "interesses": [
    {"tag_id": 1, "weight": 2.5},
    {"tag_id": 4, "weight": 1.0},
    {"tag_id": 7, "weight": 0.3}
  ]
}
```

**Exemplo de resposta (GET e PUT):**
```json
{
  "success": true,
  "data": [
    {"tag_id": 1, "tag_name": "Matemática", "tag_slug": "matematica", "weight": 2.5, "updated_at": "2026-06-08T14:00:00+00:00"},
    {"tag_id": 4, "tag_name": "Física",     "tag_slug": "fisica",     "weight": 1.0, "updated_at": "2026-06-08T14:00:00+00:00"}
  ]
}
```

---

### Padrão de mapeamento de exceções

Sprint 3 introduziu um mapeamento mais expressivo que o existente:

| Exceção Python | HTTP | Quando usar |
|----------------|------|-------------|
| `ValueError` | 400 | Validação de entrada — campo faltando, formato inválido, regra de negócio |
| `LookupError` | 404 | Recurso não encontrado — coleção, REA, tag inexistente |
| `PermissionError` | 403 | Recurso existe mas não pertence ao usuário logado |

Esse padrão foi adotado em ambos os blueprints e nos dois serviços.

---

### Atualização do `app.py`

```python
# Imports adicionados
from src.routes.colecoes_routes import colecoes_bp
from src.routes.perfil_routes import perfil_bp

# Blueprints registrados
app.register_blueprint(colecoes_bp, url_prefix="/api/colecoes")
app.register_blueprint(perfil_bp,   url_prefix="/api/perfil")
```

Verificação de integridade executada ao final:

```
python -c "from src.app import create_app; app = create_app(); ..."
OK — 8 novas rotas registradas sem erros de importação
```

---

## Mapa completo de endpoints da API (Sprint 2 + Sprint 3)

| Método | Rota | Auth | Sprint |
|--------|------|------|--------|
| POST | `/api/auth/register` | pública | 2 |
| POST | `/api/auth/login` | pública | 2 |
| GET | `/api/auth/me` | JWT | 2 |
| GET | `/api/reas/` | pública | 2 |
| GET | `/api/reas/<id>` | pública | 2 |
| POST | `/api/reas/` | JWT | 2 |
| POST | `/api/colecoes/` | JWT | **3** |
| GET | `/api/colecoes/` | JWT | **3** |
| GET | `/api/colecoes/<id>` | JWT | **3** |
| DELETE | `/api/colecoes/<id>` | JWT | **3** |
| POST | `/api/colecoes/<id>/items` | JWT | **3** |
| DELETE | `/api/colecoes/<id>/items/<rea_id>` | JWT | **3** |
| GET | `/api/perfil/interesses` | JWT | **3** |
| PUT | `/api/perfil/interesses` | JWT | **3** |

---

## Resumo de métricas da Sprint 3

| Categoria | Quantidade |
|-----------|-----------|
| Novos endpoints HTTP | 8 |
| Arquivos criados | 6 |
| Linhas de código novas | ~394 |
| Camadas cobertas | Repositório + Serviço + Rota |
| Padrões N+1 eliminados | 2 (`selectinload` em lista de coleções e de interesses) |

---

## Pendências para Sprint 4

- **Testes automatizados** dos 8 novos endpoints (Fase 3 da Sprint 3)
- **Recálculo de pesos** em `UserTagInterest` por evento de interação (visualização, rating, adição à coleção)
- **Motor de recomendação** — consulta por `ORDER BY weight DESC` nas tags do usuário cruzando com `rea_tags`
- **Endpoint público de coleções** — `GET /api/colecoes/<id>` para coleções com `is_public=True` sem JWT
