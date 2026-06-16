# Relatório de Desenvolvimento — Sprint 5
**Projeto:** Nexos REA — Backend
**Branch:** `sprint-5/desenvolvimento`
**Período:** 13 de junho a 16 de junho de 2026
**Stack:** Python · Flask 3.0.3 · Flask-SQLAlchemy 3.1.1 · Flask-JWT-Extended 4.6.0 · PostgreSQL 16

---

## Objetivo da Sprint

Implementar o **sistema de moderação automatizada** e o **painel administrativo** do Nexos REA. O objetivo foi garantir que conteúdo inadequado saia do catálogo de forma transparente — seja por gatilho automático (nota baixa ou volume de denúncias), seja por julgamento manual de um administrador.

A sprint também incluiu uma rodada de **correções de bugs** identificados durante a auditoria de integração do sistema completo.

---

## Decisão arquitetural: gatilhos no serviço, não no banco

O ponto crítico da sprint foi decidir onde implementar a lógica dos gatilhos de moderação. Duas abordagens foram avaliadas:

| Opção | Local | Veredito |
|-------|-------|----------|
| Triggers PostgreSQL | Banco de dados | Descartado |
| **Gatilhos no `moderacao_service`** | Camada de serviço (Python) | **Escolhido** |

**Justificativa:** triggers no banco são invisíveis para a aplicação, dificultam testes unitários e acoplam a lógica de negócio ao SGBD. Manter os gatilhos no `moderacao_service` permite testá-los de forma isolada, controlar exatamente quando disparam (após commit) e registrá-los nos logs da aplicação. O preço — uma chamada extra a cada avaliação e denúncia — é irrelevante na escala do projeto.

---

## Fase 1 — Modelagem e Serviço de Moderação

### Enum de status

O modelo `REA` passou a usar `StatusREAEnum` no lugar dos campos legados `is_visible` e `is_blocked`:

| Status | Significado | Gatilho |
|--------|-------------|---------|
| `ativo` | Visível no catálogo | Padrão ao criar |
| `oculto` | Removido automaticamente por qualidade | `avg_rating < 2.0` após ao menos 1 avaliação |
| `sob_revisao` | Aguardando julgamento do admin | `report_count >= 3` |

Os campos `is_visible` e `is_blocked` foram mantidos no modelo para compatibilidade com registros legados, mas toda a lógica de visibilidade passou a ler exclusivamente `status`.

### Gatilho de qualidade (`aplicar_gatilho_avaliacao`)

Chamado por `rea_service` após cada recálculo de média. Regras de aplicação:

- Só ativa se `rating_count >= 1` (evita ocultamento por `avg == 0.0` em REAs sem avaliações).
- Só transita para `oculto` se o status atual for `ativo` (não sobrescreve `sob_revisao`).
- Condição: `avg_rating < 2.0` — limite inferior exclusive (nota exatamente 2.0 não oculta).

### Gatilho de denúncias (`registrar_denuncia`)

Persiste o `Report` e avalia o gatilho na mesma operação:

- Valida o `reason` contra uma lista fechada de motivos: `conteudo_inapropriado`, `spam`, `direitos_autorais`, `link_quebrado`, `desinformacao`, `outro`.
- Impede duplicatas (um usuário só pode denunciar cada REA uma vez — `UniqueConstraint`).
- Ao atingir `report_count == 3`, transita o REA para `sob_revisao`.
- Denúncias adicionais após o gatilho são persistidas para rastreabilidade, mas não alteram o status.

---

## Fase 2 — Painel Admin e Rotas

### Decorator `@admin_required`

Verifica em duas etapas: (1) presença e validade do JWT; (2) role `admin` consultada diretamente no banco. Retorna 401 sem token, 422 com token malformado e 403 para usuário comum autenticado.

### `admin_service`

| Função | Comportamento |
|--------|---------------|
| `listar_sob_revisao()` | Retorna REAs com `status = sob_revisao`, ordenados por `report_count DESC`, com array `denuncias` aninhado |
| `aprovar_rea(rea_id)` | Restaura status para `ativo` e marca todas as denúncias pendentes como `reviewed = True` com timestamp |
| `remover_rea(rea_id)` | Hard delete — o `CASCADE` no banco apaga ratings, denúncias e itens de coleção |
| `obter_estatisticas()` | Agrega contagens de usuários, REAs por status, avaliações, denúncias e taxa de engajamento |

**Taxa de engajamento:** proxy calculado como percentual de usuários que possuem ao menos um registro em `user_tag_interests` (gerado pelo motor de recomendação da Sprint 4). Mede indiretamente usuários que interagiram com algum REA.

### Dashboard de estatísticas — estrutura de resposta

```json
{
  "usuarios": {
    "total": 42,
    "com_interacao": 18,
    "taxa_engajamento_pct": 42.9
  },
  "reas": {
    "total": 120,
    "ativos": 115,
    "ocultos_automaticamente": 3,
    "sob_revisao": 2
  },
  "moderacao": {
    "total_avaliacoes": 310,
    "total_denuncias": 27
  }
}
```

---

## Correções de Bugs (Auditoria)

| Arquivo | Bug | Correção |
|---------|-----|----------|
| `auth_service.get_me` | Usuário inativo conseguia obter o próprio perfil após desativação, inconsistente com o bloqueio no login | Adicionada verificação de `is_active` |
| `colecao_service.adicionar_rea` | Usava `is_visible`/`is_blocked` para verificar se REA existia e estava ativo, ignorando o novo campo `status` | Migrado para checar `rea.status == StatusREAEnum.ativo` |
| `tests/conftest.py` | Schema stale entre sessões de teste causava falhas intermitentes ao recriar tabelas | Adicionado `db.drop_all()` antes de `db.create_all()` |
| `test_auth.py` / `test_reas.py` | Assertions verificavam mensagens de erro com acento (ex.: `"inválido"`), quebradas após remoção de acentos da API na sprint anterior | Assertions atualizadas para o texto sem acento |

---

## Mapa de novos endpoints (Sprint 5)

| Método | Rota | Auth | Função |
|--------|------|------|--------|
| POST | `/api/denuncias/` | JWT | Registrar denúncia contra um REA |
| GET | `/api/admin/revisao` | admin | Fila de REAs sob revisão com denúncias detalhadas |
| POST | `/api/admin/aprovar/<id>` | admin | Aprovar REA e restaurar ao catálogo |
| POST | `/api/admin/remover/<id>` | admin | Remover REA definitivamente (irreversível) |
| GET | `/api/admin/estatisticas` | admin | Dashboard de métricas do sistema |

---

## Testes automatizados

Arquivo **`tests/test_sprint5.py`** — 36 testes organizados em 8 grupos:

| Grupo | Testes | O que cobre |
|-------|--------|-------------|
| `@admin_required` | 4 | Sem token (401), usuário comum (403), admin válido (200), token malformado (422) |
| `POST /api/denuncias/` | 6 | Caminho feliz, sem token, REA inexistente, motivo inválido, campos ausentes, duplicata |
| Gatilho de denúncias | 5 | 2 denúncias não alteram status, 3ª aciona `sob_revisao`, REA some da listagem e do GET por ID, denúncias extras são persistidas |
| Gatilho de qualidade | 6 | nota 1 oculta (lista e por ID), nota 2 exata não oculta, nota alta não oculta, não sobrescreve `sob_revisao`, sem avaliações não aciona |
| `GET /api/admin/revisao` | 3 | Fila vazia, retorna REA + denúncias aninhadas, não inclui REAs ativos |
| `POST /api/admin/aprovar` | 5 | Restaura para ativo, REA volta à busca, marca denúncias como revisadas, REA não sob revisão (400), inexistente (404) |
| `POST /api/admin/remover` | 3 | Remove com sucesso, CASCADE apaga reports, inexistente (404) |
| `GET /api/admin/estatisticas` | 4 | Estrutura completa, contagens corretas, `sob_revisao` contabilizado, `oculto` contabilizado |

**Resultado acumulado: 73/73 testes passando** (test_auth + test_reas + test_sprint4 + test_sprint5).

---

## Arquivos da Sprint 5

| Arquivo | Tipo |
|---------|------|
| `src/models/models.py` | Alterado — `StatusREAEnum`, campos `reviewed`/`reviewed_at` em `Report` |
| `src/services/moderacao_service.py` | Novo — gatilhos de qualidade e denúncias |
| `src/services/admin_service.py` | Novo — fila de revisão, aprovação, remoção, estatísticas |
| `src/routes/admin_routes.py` | Novo — 4 endpoints admin |
| `src/routes/denuncia_routes.py` | Novo — endpoint de denúncia |
| `src/utils/decorators.py` | Novo — `@admin_required` |
| `src/repositories/rea_repository.py` | Alterado — filtros migrados de flags para `status` |
| `src/services/rea_service.py` | Alterado — integração com `moderacao_service` |
| `src/services/auth_service.py` | Corrigido — bloqueio de usuário inativo no `get_me` |
| `src/services/colecao_service.py` | Corrigido — verificação de status do REA |
| `src/app.py` | Alterado — registro dos blueprints `denuncias` e `admin` |
| `tests/conftest.py` | Corrigido — `drop_all` antes de `create_all` |
| `tests/test_auth.py` | Corrigido — assertions sem acento |
| `tests/test_reas.py` | Corrigido — assertions sem acento |
| `tests/test_sprint5.py` | Novo — 36 testes |

---

## Resumo de métricas

| Categoria | Quantidade |
|-----------|-----------|
| Novos endpoints HTTP | 5 |
| Arquivos criados | 6 |
| Arquivos corrigidos | 4 |
| Testes adicionados | 36 |
| Testes acumulados | 73 |
| Camadas cobertas | Modelo + Repositório + Serviço + Rota + Decorator |
| Bugs corrigidos | 4 |

---

## Pendências para próximas sprints

- **Integração com frontend** — o schema e o sistema de auth precisam ser alinhados com o repositório `nexos-rea` (ver `PLANO_ADEQUACAO.md`).
- **Soft delete no remover_rea** — atualmente é hard delete; a adequação ao frontend exige um estado `removed` persistido.
- **Auditoria de ações admin** — registrar quem aprovou/removeu e quando, além dos campos já existentes em `Report`.
