# Plano de Adequação — Backend + Frontend Nexos REA

> Documento gerado em 2026-06-16. Revisitar ao iniciar cada sprint.

---

## Contexto

O frontend (`nexos-rea`) foi gerado via Lovable e conversa **diretamente com o Supabase** — ele não chama a API Flask. O backend (`nexos_rea_backend`) usa Flask + JWT próprio + PostgreSQL local. A integração exige migrar o banco para o Supabase, alinhar o schema e converter a lógica de negócio do Flask em funções PostgreSQL (RPC), além de pequenos ajustes no frontend.

---

## Visão Rápida por Responsável

### Tarefas do Backend
| Sprint | Tarefa |
|---|---|
| A | Provisionar projeto no Supabase e trocar `DATABASE_URL` |
| A | Substituir `flask-jwt-extended` por validação JWT do Supabase (`PyJWT`) |
| A | Atualizar decorators `@jwt_required` e `@admin_required` |
| A | Migrations: renomear/adicionar campos em `reas`, `collections`, `collection_items` |
| A | Migrations: traduzir enum de status para inglês |
| A | Migrations: renomear `ratings→rea_ratings`, `reports→rea_reports` |
| A | Criar tabelas `profiles`, `user_roles`, `subject_areas`, `rea_interactions` |
| B | Criar RPC `get_recommended_feed` (SQL) |
| B | Criar RPC `admin_list_reas` (SQL) |
| B | Criar RPC `admin_set_rea_status` (SQL) |
| B | Criar RPC `admin_resolve_report` (SQL) |
| B | Criar RPC `ensure_favorites_collection` (SQL) |
| C | Habilitar RLS e escrever todas as policies de acesso |
| D | Instalar `flask-cors`, configurar `origins` |
| D | Adicionar `SUPABASE_JWT_SECRET` ao `.env` e `config.py` |
| D | Atualizar `docker-compose.yml` com novas vars |
| E | Atualizar serializers dos services (novos nomes de campo) |
| E | Adicionar filtros ao `GET /api/reas/`: `format`, `education_level`, `subject_area`, `language`, `min_rating` |
| E | Atualizar `api.http` e rodar `pytest` |

### Tarefas do Frontend
| Sprint | Tarefa |
|---|---|
| A | Configurar `.env` com `VITE_SUPABASE_URL` e `VITE_SUPABASE_PUBLISHABLE_KEY` |
| D | Confirmar vars de ambiente em `wrangler.jsonc` / `wrangler.deploy.jsonc` |
| D | Atualizar `.env.example` do repositório frontend |
| E | Teste smoke: verificar `ReaCard` com dados reais do Supabase |
| E | Confirmar renderização dos badges `education_level` e `subject_area` |

---

## Mapa de Diferenças

### Autenticação

| Aspecto | Backend (Flask) | Frontend | Responsável |
|---|---|---|---|
| Sistema | `flask-jwt-extended`, JWT próprio | `supabase.auth.signInWithPassword()` | Backend |
| Usuários | tabela `users` com `password_hash` | `auth.users` (Supabase) + tabela `profiles` | Backend |
| Perfil | campos em `users` | tabela `profiles` (`display_name`, `bio`, `avatar_url`, `skip_external_warning`) | Backend |
| Roles | coluna `role` em `users` | tabela `user_roles` | Backend |

### Tabela `reas` — campo a campo

| Frontend espera | Backend tem | Ação | Responsável |
|---|---|---|---|
| `resource_url` | `url` | Renomear | Backend |
| `format` (enum) | `resource_type` (string) | Renomear + tipar | Backend |
| `rating_avg` | `avg_rating` | Renomear | Backend |
| `subject_area` | não existe | Adicionar coluna | Backend |
| `education_level` (enum) | não existe | Adicionar coluna | Backend |
| `updated_at` | não existe | Adicionar coluna | Backend |
| `status: "active"` | `"ativo"` | Traduzir enum | Backend |
| `status: "blocked_review"` | `"sob_revisao"` | Traduzir enum | Backend |
| `status: "hidden_low_rating"` | `"oculto"` | Traduzir enum | Backend |
| `status: "removed"` | deletado fisicamente | Soft-delete com novo estado | Backend |

### Tabela `collections`

| Frontend espera | Backend tem | Ação | Responsável |
|---|---|---|---|
| `title` | `name` | Renomear | Backend |
| `description` | não existe | Adicionar | Backend |
| `visibility` (enum) | `is_public` (boolean) | Converter | Backend |
| `is_system` | não existe | Adicionar (coleção "Favoritos") | Backend |
| `updated_at` | não existe | Adicionar | Backend |
| `collection_items.position` | não existe | Adicionar | Backend |

### Tabelas ausentes no backend

| Tabela | Equivalente atual | Ação | Responsável |
|---|---|---|---|
| `profiles` | parcial em `users` | Criar + trigger automático | Backend |
| `user_roles` | coluna em `users` | Criar tabela | Backend |
| `subject_areas` | não existe | Criar tabela | Backend |
| `rea_interactions` | não existe | Criar tabela | Backend |
| `rea_ratings` | `ratings` | Renomear + ajustar | Backend |
| `rea_reports` | `reports` | Renomear + ajustar | Backend |

### RPC Functions ausentes (chamadas por `supabase.rpc()`)

| Função | Equivalente Flask | Ação | Responsável |
|---|---|---|---|
| `get_recommended_feed(p_limit)` | `GET /api/recomendacoes/` | Criar SQL function | Backend |
| `admin_list_reas(statuses[])` | `GET /api/admin/revisao` | Criar SQL function | Backend |
| `admin_set_rea_status(rea_id, status)` | `POST /api/admin/aprovar` e `/remover` | Criar SQL function | Backend |
| `admin_resolve_report(...)` | lógica em `admin_service` | Criar SQL function | Backend |
| `ensure_favorites_collection()` | não existe | Criar SQL function | Backend |

### Configuração e Ambiente

| Item | Situação | Ação | Responsável |
|---|---|---|---|
| `VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` | ausente no frontend | Configurar `.env` | **Frontend** |
| `SUPABASE_JWT_SECRET` | ausente no backend | Adicionar `.env` e `config.py` | Backend |
| `flask-cors` | não instalado | Instalar e configurar `origins` | Backend |
| `wrangler.jsonc` vars de produção | a confirmar | Validar e completar | **Frontend** |
| `.env.example` do frontend | desatualizado após integração | Atualizar | **Frontend** |

---

## Sprints

### Sprint A — Migração de Banco e Autenticação
**Estimativa:** 3–4 dias · **Prioridade:** Bloqueante

#### Backend
- [ ] Provisionar projeto no Supabase
- [ ] Trocar `DATABASE_URL` para apontar ao PostgreSQL do Supabase (pooler)
- [ ] Substituir validação JWT do Flask: trocar `flask-jwt-extended` por `PyJWT` validando o JWT público do Supabase
- [ ] Atualizar decorator `@jwt_required` e `@admin_required` para ler claims do token Supabase
- [ ] Executar migrations de schema:
  - Renomear `reas.url` → `resource_url`
  - Renomear `reas.resource_type` → `format` + enum (`video`, `audio`, `text`, `image`, `interactive`, `slides`)
  - Renomear `reas.avg_rating` → `rating_avg`
  - Adicionar `reas.subject_area text`, `reas.education_level` (enum), `reas.updated_at`
  - Traduzir enum de status: `ativo→active`, `oculto→hidden_low_rating`, `sob_revisao→blocked_review`, adicionar `removed`
  - Renomear `ratings` → `rea_ratings`
  - Renomear `reports` → `rea_reports`
  - Renomear `collections.name` → `title`, adicionar `description`, `visibility` (enum), `is_system`, `updated_at`
  - Adicionar `collection_items.position int`
- [ ] Criar tabela `profiles` com trigger `on auth.users insert → insert into profiles`
- [ ] Criar tabela `user_roles`
- [ ] Criar tabela `subject_areas (slug, label)`
- [ ] Criar tabela `rea_interactions (id, user_id, rea_id, event_type, created_at)`

#### Frontend
- [ ] Configurar `.env` com `VITE_SUPABASE_URL` e `VITE_SUPABASE_PUBLISHABLE_KEY` do projeto provisionado

---

### Sprint B — RPC Functions PostgreSQL ✅ CONCLUÍDA
**Estimativa:** 2–3 dias · **Prioridade:** Bloqueante (catálogo e admin não funcionam sem isso)

#### Backend (SQL/Supabase)
- [x] `get_recommended_feed(p_limit int)` — TF-IDF ponderado por peso de interesse + penalidade de itens vistos recentemente. Migration: `20260608232719` (refinado em `20260608233207`)
- [x] `admin_list_reas(p_statuses text[], p_query text, p_limit int, p_offset int)` — filtro por status[], busca textual, paginação, retorna `{ total, items[] }` com denúncias pendentes embutidas. Migration: `20260613191007`
- [x] `admin_set_rea_status(p_rea_id uuid, p_status text)` — unifica aprovar/remover, resolve reports pendentes automaticamente. Migration: `20260613191007`
- [x] `admin_resolve_report(p_rea_id uuid, p_decision text)` — `'restore'` descarta denúncias; `'remove'` aceita e muda status. Migration: `20260609002626`
- [x] `ensure_favorites_collection(_user_id uuid)` — cria coleção `is_system = true` se não existir; trigger automático no signup. Migration: `20260610005428`
- [x] Funções auxiliares: `has_role`, `event_delta`, `decay_user_interests` (cron diário 03h), `get_admin_metrics`, `get_moderation_queue`

#### Frontend
- [x] Nenhuma alteração necessária nesta sprint (o frontend já chama essas RPCs)

> **Atenção:** Confirmar que todas as migrations estão aplicadas ao projeto Supabase com `supabase db push` antes de testar.

---

### Sprint C — Row Level Security (RLS)
**Estimativa:** 2 dias · **Prioridade:** Bloqueante (segurança)

> Esta sprint replica no banco as regras de autorização que hoje vivem no Flask.

#### Backend (Supabase SQL)
- [ ] Habilitar RLS em todas as tabelas
- [ ] `reas`: leitura pública para `status = 'active'`; escrita exige autenticação
- [ ] `rea_ratings` / `rea_reports`: usuário autenticado, um registro por REA por usuário
- [ ] `collections`: dono pode tudo; público lê se `visibility = 'public'`
- [ ] `collection_items`: segue a policy da collection pai
- [ ] `profiles` / `user_interests`: apenas o próprio usuário lê e escreve
- [ ] Funções admin: verificam existência em `user_roles` antes de executar
- [ ] Testar policies com usuário anônimo, usuário comum e admin

#### Frontend
- [ ] Nenhuma alteração necessária nesta sprint

---

### Sprint D — CORS e Variáveis de Ambiente
**Estimativa:** 0,5 dia · **Prioridade:** Bloqueante (sem isso o browser bloqueia as chamadas)

#### Backend (Flask)
- [ ] Instalar `flask-cors` e configurar `origins` para o domínio do Cloudflare Workers
- [ ] Adicionar `SUPABASE_JWT_SECRET` ao `.env` e ao `config.py`
- [ ] Atualizar `docker-compose.yml` para ambiente local com as novas vars

#### Frontend
- [ ] Confirmar que `wrangler.jsonc` / `wrangler.deploy.jsonc` tem as vars de ambiente corretas para produção
- [ ] Atualizar `.env.example` do repositório frontend com todas as vars necessárias

---

### Sprint E — Alinhamento de Payloads (ajuste fino)
**Estimativa:** 1–2 dias · **Prioridade:** Funcional (frontend não renderiza sem os campos corretos)

#### Backend (Flask)
- [ ] Atualizar serializers de todos os services para retornar os novos nomes de campo (`resource_url`, `rating_avg`, `format`, etc.)
- [ ] Garantir que enum de status retorne em inglês (`"active"`, não `"ativo"`)
- [ ] Adicionar suporte aos filtros do catálogo: `format`, `education_level`, `subject_area`, `language`, `min_rating`
- [ ] Atualizar `api.http` com os endpoints e campos revisados
- [ ] Rodar suite de testes (`pytest`) e corrigir falhas causadas pelos renomes

#### Frontend
- [ ] Verificar se `ReaCard` renderiza corretamente com os dados do Supabase real (teste smoke no catálogo)
- [ ] Confirmar que `education_level` e `subject_area` populados aparecem nos badges

---

## O que NÃO precisa mudar

- Estrutura de blueprints e services do Flask — permanece intacta
- Motor de recomendação (`interacao_service.py`) — vira base da RPC `get_recommended_feed`
- Lógica de moderação (gatilho em 3 denúncias) — reexposta como RPC
- `docker-compose.yml` — continua útil para desenvolvimento local

---

## Tabela de Prioridade

| Sprint | Lado | Esforço | Pode subir sem isso? |
|---|---|---|---|
| A — Banco + Auth | Backend + Frontend (env) | Alto | Não |
| B — RPC Functions | Backend (SQL) | Médio | Não |
| C — RLS | Backend (SQL) | Médio | Não — segurança |
| D — CORS + env | Backend + Frontend | Baixo | Não |
| E — Campos finos | Backend + Frontend | Baixo | Parcialmente |
