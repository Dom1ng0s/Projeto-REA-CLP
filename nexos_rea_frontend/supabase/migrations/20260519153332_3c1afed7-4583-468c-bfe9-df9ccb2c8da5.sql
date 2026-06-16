
-- Enums
CREATE TYPE public.interest_source AS ENUM ('manual', 'inferred');
CREATE TYPE public.collection_visibility AS ENUM ('private', 'public');

-- Tags
CREATE TABLE public.tags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text UNIQUE NOT NULL,
  label text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.tags ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tags are viewable by everyone" ON public.tags FOR SELECT USING (true);
CREATE POLICY "Admins can insert tags" ON public.tags FOR INSERT WITH CHECK (public.has_role(auth.uid(), 'admin'));
CREATE POLICY "Admins can update tags" ON public.tags FOR UPDATE USING (public.has_role(auth.uid(), 'admin'));
CREATE POLICY "Admins can delete tags" ON public.tags FOR DELETE USING (public.has_role(auth.uid(), 'admin'));

-- Seed tags a partir dos REAs existentes
INSERT INTO public.tags (slug, label)
SELECT DISTINCT lower(trim(t)), initcap(replace(trim(t), '-', ' '))
FROM public.reas, unnest(reas.tags) AS t
WHERE trim(t) <> ''
ON CONFLICT (slug) DO NOTHING;

-- User interests
CREATE TABLE public.user_interests (
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  tag_id uuid NOT NULL REFERENCES public.tags(id) ON DELETE CASCADE,
  weight numeric(5,3) NOT NULL DEFAULT 1.000,
  source public.interest_source NOT NULL DEFAULT 'manual',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, tag_id)
);
CREATE INDEX idx_user_interests_user ON public.user_interests(user_id);
ALTER TABLE public.user_interests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own interests" ON public.user_interests FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own interests" ON public.user_interests FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users update own interests" ON public.user_interests FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users delete own interests" ON public.user_interests FOR DELETE USING (auth.uid() = user_id);

CREATE TRIGGER trg_user_interests_updated_at BEFORE UPDATE ON public.user_interests FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Collections
CREATE TABLE public.collections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title text NOT NULL,
  description text,
  visibility public.collection_visibility NOT NULL DEFAULT 'private',
  cover_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX idx_collections_user_title ON public.collections(user_id, lower(title));
CREATE INDEX idx_collections_user ON public.collections(user_id);
CREATE INDEX idx_collections_public ON public.collections(visibility) WHERE visibility = 'public';
ALTER TABLE public.collections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Owners and public can view collections" ON public.collections FOR SELECT
  USING (auth.uid() = user_id OR visibility = 'public');
CREATE POLICY "Users insert own collections" ON public.collections FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users update own collections" ON public.collections FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users delete own collections" ON public.collections FOR DELETE USING (auth.uid() = user_id);

CREATE TRIGGER trg_collections_updated_at BEFORE UPDATE ON public.collections FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Collection items
CREATE TABLE public.collection_items (
  collection_id uuid NOT NULL REFERENCES public.collections(id) ON DELETE CASCADE,
  rea_id uuid NOT NULL REFERENCES public.reas(id) ON DELETE CASCADE,
  position integer NOT NULL DEFAULT 0,
  note text,
  added_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (collection_id, rea_id)
);
CREATE INDEX idx_collection_items_collection ON public.collection_items(collection_id, position);
ALTER TABLE public.collection_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "View items via parent collection" ON public.collection_items FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.collections c
    WHERE c.id = collection_items.collection_id
      AND (c.user_id = auth.uid() OR c.visibility = 'public')
  ));
CREATE POLICY "Owners insert items" ON public.collection_items FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM public.collections c
    WHERE c.id = collection_items.collection_id AND c.user_id = auth.uid()
  ));
CREATE POLICY "Owners update items" ON public.collection_items FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM public.collections c
    WHERE c.id = collection_items.collection_id AND c.user_id = auth.uid()
  ));
CREATE POLICY "Owners delete items" ON public.collection_items FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM public.collections c
    WHERE c.id = collection_items.collection_id AND c.user_id = auth.uid()
  ));
