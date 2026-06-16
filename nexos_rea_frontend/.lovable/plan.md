
# Sprint 5 — Polimento de UX, Painel Admin e Pendências

Plano consolidando (a) ajustes pontuais que você listou, (b) pendências da Sprint 4 sem UI, e (c) melhorias adicionais que você aprovou.

---

## 1. Início unificada (Home + Auth)

Reformula `src/routes/index.tsx` numa tela de altura `min-h-screen` em **duas colunas**:

- **Esquerda (50%)**: hero atual (badge, headline "O recurso certo, no momento certo.", subtítulo, CTA "Explorar catálogo").
- **Direita (50%)**: painel de autenticação com modos `login | registro | recuperar`, alternados por botões internos sem mudar de rota.

Abaixo do hero, o que era "Pilares" + "CTA final" vira **rodapé** (`<footer>`) compacto da própria página, sem a seção redundante "Comece a explorar agora".

Rotas `/login` e `/registro` passam a redirecionar para `/`. `/recuperar-senha` e `/redefinir-senha` continuam. Usuário já logado vê na coluna direita um card "Bem-vindo de volta" com atalhos (Catálogo, Coleções, Sair) em vez do form.

Arquivos: `src/routes/index.tsx` reescrito; novo `src/components/HomeAuthPanel.tsx` (extrai a lógica de form de `login.tsx`/`registro.tsx`); `login.tsx` e `registro.tsx` viram redirects.

---

## 2. Catálogo — ajustes de filtros e busca

`src/routes/catalogo.tsx`:

- **Search params na URL + debounce**: estado (`q`, `format`, `language`, `subject`, `level`, `minRating`, `page`) migra para `validateSearch` com Zod + `Route.useSearch()` + `navigate({ search })`. Digitação na barra atualiza `q` com **debounce de 300ms** (sem botão "Buscar" — vira ícone decorativo) e reseta `page` para 0.
- **Ícone de filtros vira interruptor**: o `SlidersHorizontal` ao lado do contador alterna visibilidade do bloco de filtros (estado `filtersOpen`, default `true` no desktop, `false` no mobile).
- **Avaliação mínima** — opções reordenadas:
  ```
  Qualquer avaliação
  ⭐⭐☆☆☆ e acima
  ⭐⭐⭐☆☆ e acima
  ⭐⭐⭐⭐☆ e acima
  Sem avaliação (rating_count = 0)
  ```
  O caso "sem avaliação" usa `.eq("rating_count", 0)` em vez de `.gte("rating_avg", ...)`.

---

## 3. ReaCard — clique, favoritar, avaliar, denunciar

`src/components/ReaCard.tsx` ganha 3 novas ações ao lado de "Salvar":

| Botão | Comportamento |
| --- | --- |
| **Favoritar** (`Heart`) | Toggle direto na coleção "Favoritos" do usuário. Estado pré-carregado por query única `useFavoritedSet()` (1 select para todos os reaIds visíveis). |
| **Avaliar** (`Star`) | Popover com 5 estrelas; upsert em `rea_ratings`. Mostra a nota atual do usuário se já avaliou. |
| **Denunciar** (`Flag`) | Dialog com 6 motivos: Conteúdo sexual, Conteúdo violento, Atos perigosos, Spam ou enganoso, Abuso infantil, Outro. "Outro" expande textarea limitada a 100 chars (Zod). Insert em `rea_reports`. |

Também:

- **Clique no card** (qualquer área não-botão) → `ExternalLinkConfirmDialog` com mensagem "Você será redirecionado para um site externo:" + URL renderizada em `<code>` + botões "Cancelar" / "Abrir em nova aba". Se a preferência `skip_external_warning` estiver true (ver §5), abre direto.
- **Indicador "já avaliado"**: badge discreto no canto com a nota do usuário.

Arquivos novos: `src/components/ExternalLinkConfirmDialog.tsx`, `src/components/RateReaPopover.tsx`, `src/components/ReportReaDialog.tsx`, `src/hooks/use-favorites.ts`.

---

## 4. Coleção "Favoritos" automática

**Migration**:

- Adiciona `is_system boolean default false` em `public.collections` + check único `(user_id) where is_system = true`.
- Função `ensure_favorites_collection(uuid)` (SECURITY DEFINER) — cria a coleção "Favoritos" do usuário se não existir.
- Trigger `AFTER INSERT ON auth.users` que chama `ensure_favorites_collection(new.id)` (e backfill 1x para usuários existentes).
- Política RLS: `UPDATE` e `DELETE` em `collections` ficam bloqueados quando `is_system = true` (exceto via função SECURITY DEFINER).
- `cover_url` da coleção Favoritos é **derivado**: na consulta retorna `thumbnail_url` do `collection_items` com menor `position`. Implementado via VIEW `collections_with_cover` ou cálculo no front (mais simples — cálculo no front, ver §nota técnica).

**Front**:

- `src/routes/colecoes.index.tsx` exibe Favoritos sempre primeiro, com ícone `Heart` e sem opção de excluir/editar (botões escondidos quando `is_system`).
- `src/routes/colecoes.$id.tsx` esconde botões de editar/excluir e bloqueia mutações para coleções `is_system`.

---

## 5. Preferência "não perguntar de novo" (link externo)

**Migration**: adiciona `skip_external_warning boolean default false` em `public.profiles`.

**UI**:

- Modal de saída externa tem checkbox "Não perguntar de novo".
- Página `/perfil` ganha switch "Avisar antes de abrir links externos" que reverte a preferência.

---

## 6. Painel Admin (UI das RPCs Sprint 4)

Novas rotas protegidas (pathless layout `_authenticated/_admin`):

- `src/routes/_authenticated/_admin/route.tsx` — `beforeLoad` valida `has_role(uid, 'admin')` via serverFn `requireAdmin` (cria em `src/lib/admin.functions.ts`).
- `src/routes/_authenticated/_admin/admin.index.tsx` (`/admin`) — Dashboard:
  - Cards: REAs ativos, ocultos por baixa nota, sob revisão, removidos.
  - Gráfico de linha (recharts) com CTR dos últimos 30 dias.
- `src/routes/_authenticated/_admin/admin.moderacao.tsx` (`/admin/moderacao`) — Fila:
  - Lista resultados de `get_moderation_queue` com card do REA, denúncias pendentes (motivo, detalhes, data), botões **Restaurar** e **Remover** chamando `admin_resolve_report`.

`Header.tsx` ganha link "Admin" condicional para admins.

---

## 7. Toasts com Undo e Histórico

- **Undo** em ações reversíveis (favoritar/dessfavoritar, salvar em coleção, avaliar): toast com action "Desfazer" usando `sonner` (`toast.success(..., { action: { label: "Desfazer", onClick: undo } })`).
- **Histórico**: nova aba em `/perfil` listando últimos 20 REAs com `event_type='view'` (query em `rea_interactions`, `order by created_at desc`, dedup por `rea_id`).

---

## 8. Ordem das migrations

1. `collections.is_system` + função `ensure_favorites_collection` + trigger em `auth.users` + backfill + RLS update/delete bloqueando system.
2. `profiles.skip_external_warning`.

Nenhuma alteração em `reas`, `rea_ratings`, `rea_reports`, `rea_interactions`, `user_roles`, `has_role`.

---

## Detalhes técnicos relevantes

- **Debounce**: hook `useDebouncedValue(value, 300)` em `src/hooks/use-debounced-value.ts`.
- **Search params**: usar `zodValidator(fallback(...).default(...))` para cada filtro; `loaderDeps` opcional pois usamos `useQuery` com `queryKey` baseado em `Route.useSearch()`.
- **Card clicável**: wrapper `<article onClick>` com `e.stopPropagation()` nos botões internos; `role="button"` + `tabIndex={0}` + handler de `Enter`.
- **Capa derivada de Favoritos**: no front, `collections.index.tsx` faz join com `collection_items(position, reas(thumbnail_url))` ordered by position asc limit 1 — mesma query já usada hoje, só ajustando a coleção Favoritos.
- **Backfill Favoritos**: na migration, `INSERT INTO collections (user_id, title, is_system) SELECT id, 'Favoritos', true FROM auth.users WHERE NOT EXISTS (SELECT 1 FROM collections c WHERE c.user_id = auth.users.id AND c.is_system) ON CONFLICT DO NOTHING`.

---

## Fora de escopo (próximas sprints)

- Notificações em-app para autor do REA quando moderado.
- Compartilhamento social de coleções (OG image dinâmica).
- Edição inline do REA pelo admin.
- Métricas por REA (CTR individual, top reports).
