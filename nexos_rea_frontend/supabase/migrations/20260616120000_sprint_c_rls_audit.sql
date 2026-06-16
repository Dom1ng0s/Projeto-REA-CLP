
-- ============================================================
-- Sprint C — RLS Audit & Cleanup
-- ============================================================
-- Aplica o conteúdo da migration 20260614 que não foi registrada
-- no banco, e consolida todas as correções de RLS da Sprint C.
-- ============================================================

-- ------------------------------------------------------------
-- 1. collections: remover políticas redundantes
--    As de baixo foram criadas antes do campo is_system existir
--    e permitem UPDATE/DELETE em coleções de sistema (Favoritos).
--    As corretas (criadas em 20260610) já restringem is_system=false.
-- ------------------------------------------------------------
DROP POLICY IF EXISTS "Users delete own collections" ON public.collections;
DROP POLICY IF EXISTS "Users update own collections" ON public.collections;

-- ------------------------------------------------------------
-- 2. rea_ratings: restringir SELECT ao próprio usuário
--    rating_avg e rating_count são denormalizados em reas,
--    então o catálogo não precisa ler rea_ratings diretamente.
--    O RateReaPopover já filtra por user_id = auth.uid().
-- ------------------------------------------------------------
DROP POLICY IF EXISTS "Ratings são visíveis a todos" ON public.rea_ratings;

CREATE POLICY "Usuário lê a própria avaliação"
ON public.rea_ratings
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- ------------------------------------------------------------
-- 3. Verificação final: garante que RLS está habilitado em
--    todas as tabelas (idempotente, seguro repetir).
-- ------------------------------------------------------------
ALTER TABLE public.reas             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rea_ratings      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rea_reports      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rea_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collections      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collection_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_interests   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subject_areas    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tags             ENABLE ROW LEVEL SECURITY;
