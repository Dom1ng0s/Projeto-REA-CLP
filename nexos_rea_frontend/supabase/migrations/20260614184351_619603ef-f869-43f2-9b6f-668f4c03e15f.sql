DROP POLICY IF EXISTS "Users delete own collections" ON public.collections;
DROP POLICY IF EXISTS "Users update own collections" ON public.collections;
DROP POLICY IF EXISTS "Ratings são visíveis a todos" ON public.rea_ratings;
CREATE POLICY "Usuário lê a própria avaliação"
ON public.rea_ratings
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);