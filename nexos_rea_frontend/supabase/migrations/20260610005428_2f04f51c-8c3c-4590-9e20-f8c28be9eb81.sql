
-- 1. is_system flag on collections
ALTER TABLE public.collections
  ADD COLUMN IF NOT EXISTS is_system boolean NOT NULL DEFAULT false;

CREATE UNIQUE INDEX IF NOT EXISTS collections_user_system_unique
  ON public.collections (user_id)
  WHERE is_system = true;

-- 2. ensure_favorites_collection
CREATE OR REPLACE FUNCTION public.ensure_favorites_collection(_user_id uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_id uuid;
BEGIN
  SELECT id INTO v_id
    FROM public.collections
    WHERE user_id = _user_id AND is_system = true
    LIMIT 1;

  IF v_id IS NULL THEN
    INSERT INTO public.collections (user_id, title, description, visibility, is_system)
    VALUES (_user_id, 'Favoritos', 'Seus REAs favoritos', 'private', true)
    RETURNING id INTO v_id;
  END IF;

  RETURN v_id;
END;
$$;

GRANT EXECUTE ON FUNCTION public.ensure_favorites_collection(uuid) TO authenticated, service_role;

-- 3. Trigger on new auth.users to create favorites
CREATE OR REPLACE FUNCTION public.handle_new_user_favorites()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  PERFORM public.ensure_favorites_collection(NEW.id);
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created_favorites ON auth.users;
CREATE TRIGGER on_auth_user_created_favorites
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user_favorites();

-- 4. Backfill favorites for existing users
INSERT INTO public.collections (user_id, title, description, visibility, is_system)
SELECT u.id, 'Favoritos', 'Seus REAs favoritos', 'private', true
FROM auth.users u
WHERE NOT EXISTS (
  SELECT 1 FROM public.collections c
  WHERE c.user_id = u.id AND c.is_system = true
);

-- 5. Block update/delete of system collections via RLS
DROP POLICY IF EXISTS "Users can update their own collections" ON public.collections;
DROP POLICY IF EXISTS "Users can delete their own collections" ON public.collections;

CREATE POLICY "Users can update their non-system collections"
  ON public.collections FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id AND is_system = false)
  WITH CHECK (auth.uid() = user_id AND is_system = false);

CREATE POLICY "Users can delete their non-system collections"
  ON public.collections FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id AND is_system = false);

-- 6. skip_external_warning on profiles
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS skip_external_warning boolean NOT NULL DEFAULT false;
