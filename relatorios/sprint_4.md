# Relatório de Desenvolvimento — Sprint 4
**Projeto:** Nexos REA — Backend
**Branch:** `sprint-4/desenvolvimento`
**Período:** 08 de junho a 12 de junho de 2026
**Stack:** Python · Flask 3.0.3 · Flask-SQLAlchemy 3.1.1 · Flask-JWT-Extended 4.6.0 · PostgreSQL 16

---

## Objetivo da Sprint

Dar vida ao **Motor de Recomendação** — o cérebro do Nexos REA. O algoritmo atua em duas frentes complementares:

1. **Aprendizado (recálculo de pesos):** cada interação do usuário com um REA (visualizar, salvar em coleção, avaliar) dispara uma atualização matemática nos pesos das tags correspondentes no seu perfil de interesses.
2. **Geração (feed recomendado):** o sistema cruza o dicionário de pesos do usuário com as tags do catálogo de REAs, gerando um **Score de Relevância** para cada recurso e retornando uma lista ranqueada.

Meta de qualidade do produto: manter o CTR (Click-Through Rate) do feed acima de 10%.

---

## Decisão arquitetural: onde roda o cruzamento?

O ponto crítico da sprint foi decidir **onde** processar o cruzamento perfil × catálogo. Três opções foram avaliadas:

| Opção | Local de execução | Veredito |
|-------|-------------------|----------|
| Front-end (navegador) | Cliente baixa todo o catálogo e cruza em JS | **Descartado** — destrói a performance e expõe dados |
| Supabase Edge Functions (Deno/TS) | Camada serverless externa | Descartado — duplicaria a lógica fora do nosso back-end |
| **Back-end Flask + PostgreSQL** | Query SQL com join e agregação no banco | **Escolhido** |

**Justificativa:** o motor de recomendação está no escopo da equipe de back-end e já dispomos do modelo relacional completo (`user_tag_interests`, `rea_tags`). Processar o cruzamento como uma única query no PostgreSQL — onde os dados já residem — elimina round-trips de rede, aproveita os índices nativos e devolve à aplicação apenas os N resultados finais já ranqueados. A regra "lógica pesada no servidor" é respeitada na camada mais eficiente possível.

---

## Fase 1 — Aprendizado: recálculo de pesos

### Tabela de pontuação

Cada evento de interação aplica um delta ao peso das tags do REA no perfil do usuário:

| Evento | Delta no peso | Racional |
|--------|---------------|----------|
| Visualizar REA | **+0.5** | Sinal fraco de interesse passivo |
| Adicionar à coleção | **+1.5** | Sinal forte de intenção deliberada |
| Remover da coleção | **−0.5** | Reverte parcialmente o interesse |
| Avaliação 4–5 estrelas | **+2.0** | Endosso explícito de qualidade/relevância |
| Avaliação 1–2 estrelas | **−1.0** | Penalidade por rejeição explícita |

**Regras de contorno:**
- Pesos são limitados ao intervalo **[0.1, 10.0]** para evitar tanto a extinção de uma tag quanto a dominância infinita.
- Quando o usuário interage pela primeira vez com uma tag, ela nasce com **peso base 1.0** e o delta soma em cima (ex.: primeira avaliação 5★ → `1.0 + 2.0 = 3.0`).
- Deltas negativos nunca criam um interesse novo — só reduzem um já existente.

### Implementação

- **`src/services/interacao_service.py`** — núcleo do aprendizado. Mapeia evento → delta e, para cada tag do REA, chama o upsert de peso.
- **`src/repositories/perfil_repository.py`** — `upsert_weight()` aplica o delta com clamp em [0.1, 10.0].
- Os disparos foram integrados de forma transparente nos fluxos existentes:
  - `colecao_service.adicionar_rea` → evento `adicionar_colecao`
  - `colecao_service.remover_rea` → evento `remover_colecao`
  - `rea_service.avaliar_rea` → evento `avaliacao_positiva` ou `avaliacao_negativa` conforme a nota
  - rota de visualização → evento `visualizacao`

---

## Fase 2 — Geração: feed ranqueado

### O cálculo do Score de Relevância

Para cada REA visível:

```
score(REA) = Σ peso_usuario(tag)   para cada tag em comum
                                    entre o REA e o perfil do usuário
```

REAs sem nenhuma tag em comum recebem score 0.0 e caem para o fim da lista, desempatados pela nota média (`avg_rating`).

### A query (uma única ida ao banco)

Implementada em **`src/repositories/rea_repository.py::list_recommended`**:

1. Subquery cruza `rea_tags` com `user_tag_interests` (LEFT JOIN na tag em comum, filtrando pelo usuário atual).
2. `SUM(weight)` agregado por `rea_id` → Score de Relevância.
3. Query externa junta o score a cada REA visível e ordena por `score DESC, avg_rating DESC`, limitada a N resultados.

Todo o join, soma e ordenação acontecem **dentro do PostgreSQL**. A aplicação Python apenas serializa o resultado final.

### Fallback para usuário sem perfil

Se o usuário ainda não tem interesses registrados (perfil vazio), o feed retorna os REAs mais recentes — garantindo que a tela inicial nunca venha vazia para um usuário novo (cold start).

---

## Validação da classificação de REAs

Para o motor funcionar, os REAs precisam estar corretamente classificados por tags. Foi implementado o endpoint de classificação com validação de integridade:

- **`POST /api/reas/<id>/tags`** — associa tags a um REA.
- Rejeita listas vazias, `tag_id` não-inteiro ou não-positivo, e tags inexistentes no catálogo (404).
- Evita duplicação de associações (idempotente sobre tags já presentes).

---

## Demonstração ponta a ponta (chamada real)

Fluxo validado via HTTP no servidor de desenvolvimento:

**Cenário:** usuário novo, 3 REAs classificados (Python, Álgebra, React).

**Feed antes de qualquer interação** (perfil vazio):
```
score=0.0  React na Prática
score=0.0  Álgebra Linear
score=0.0  Python do Zero
```

**Interações do usuário:**
- Salvou "Álgebra Linear" na coleção → +1.5 na tag Álgebra
- Avaliou "React na Prática" com 5 estrelas → +2.0 na tag Frontend

**Feed depois (ranqueado pelo aprendizado):**
```
score=3.0  React na Prática     ← subiu ao topo (1.0 base + 2.0)
score=2.5  Álgebra Linear       ← segundo (1.0 base + 1.5)
score=0.0  Python do Zero       ← sem interação
```

O ciclo completo — interação → recálculo de pesos → cruzamento → feed reordenado — foi confirmado funcionando.

---

## Mapa de novos endpoints (Sprint 4)

| Método | Rota | Auth | Função |
|--------|------|------|--------|
| GET | `/api/recomendacoes/` | JWT | Feed ranqueado por relevância |
| POST | `/api/reas/<id>/visualizacao` | JWT | Registra visualização (+peso) |
| POST | `/api/reas/<id>/avaliacoes` | JWT | Avalia REA (1–5) e recalcula média |
| POST | `/api/reas/<id>/tags` | JWT | Classifica REA com tags |

---

## Testes automatizados

Arquivo **`tests/test_sprint4.py`** — 12 testes cobrindo:

- Avaliação: sucesso, score inválido, recálculo de média entre usuários
- Visualização: registro autenticado e bloqueio sem token
- Classificação: sucesso, tag inexistente, lista vazia
- Recálculo de peso: aumento ao adicionar à coleção
- Recomendação: fallback sem perfil, bloqueio sem token, **ranqueamento por score com perfil populado**

O teste central (`test_recomendacoes_com_perfil_retorna_score`) prova que um usuário com interesse Python=5.0 e Álgebra=1.0 recebe o REA de Python em primeiro lugar.

---

## Arquivos da Sprint 4

| Arquivo | Tipo |
|---------|------|
| `src/services/interacao_service.py` | Novo — motor de recálculo de pesos |
| `src/services/recomendacao_service.py` | Novo — orquestração do feed |
| `src/routes/recomendacao_routes.py` | Novo — endpoint de recomendações |
| `src/repositories/rea_repository.py` | Alterado — `list_recommended`, `find_tags`, `add_tags` |
| `src/repositories/perfil_repository.py` | Alterado — `upsert_weight` |
| `src/services/rea_service.py` | Alterado — `avaliar_rea`, `classificar_rea` |
| `src/services/colecao_service.py` | Alterado — disparo de eventos de interação |
| `src/routes/rea_routes.py` | Alterado — rotas de visualização, avaliação e tags |
| `src/app.py` | Alterado — registro do novo blueprint |
| `tests/test_sprint4.py` | Novo — 12 testes |

---

## Resumo de métricas

| Categoria | Quantidade |
|-----------|-----------|
| Novos endpoints HTTP | 4 |
| Arquivos criados | 4 |
| Testes adicionados | 12 |
| Camadas cobertas | Repositório + Serviço + Rota |
| Cruzamento perfil × catálogo | 1 query SQL (join + agregação no banco) |

---

## Pendências para próximas sprints

- **Medição real de CTR** — instrumentar cliques no feed para validar a meta de >10%.
- **Decaimento temporal** — pesos antigos poderiam perder força ao longo do tempo, refletindo mudança de interesses.
- **Diversidade no feed** — evitar que o ranking fique dominado por uma única tag, introduzindo variedade controlada.
- **Cache do feed** — para usuários com perfil estável, cachear o resultado por curto período reduz carga no banco.
