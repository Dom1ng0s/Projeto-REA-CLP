
-- Migration 2: recommendation engine

-- Silence warn from previous migration: trigger fn is internal-only
REVOKE EXECUTE ON FUNCTION public.ensure_subject_area() FROM PUBLIC, anon, authenticated;

-- 1) Event log
CREATE TYPE public.rea_event_type AS ENUM (
  'view', 'search_click', 'save_to_collection', 'remove_from_collection',
  'rating', 'rating_update', 'report'
);

CREATE TABLE public.rea_interactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  rea_id uuid NOT NULL REFERENCES public.reas(id) ON DELETE CASCADE,
  event_type public.rea_event_type NOT NULL,
  value numeric(6,3) NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT ON public.rea_interactions TO authenticated;
GRANT ALL ON public.rea_interactions TO service_role;

ALTER TABLE public.rea_interactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users insert own interactions"
  ON public.rea_interactions FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users view own interactions"
  ON public.rea_interactions FOR SELECT TO authenticated
  USING (auth.uid() = user_id OR public.has_role(auth.uid(), 'admin'));

CREATE INDEX idx_rea_interactions_user_created
  ON public.rea_interactions (user_id, created_at DESC);
CREATE INDEX idx_rea_interactions_rea
  ON public.rea_interactions (rea_id);

-- 2) Delta per event_type (matches Sprint 3 plan)
CREATE OR REPLACE FUNCTION public.event_delta(p_event public.rea_event_type, p_value numeric)
RETURNS numeric
LANGUAGE sql IMMUTABLE
AS $$
  SELECT CASE p_event
    WHEN 'view'                   THEN 1.0
    WHEN 'search_click'           THEN 1.5
    WHEN 'save_to_collection'     THEN 3.0
    WHEN 'remove_from_collection' THEN -2.0
    WHEN 'report'                 THEN -5.0
    WHEN 'rating'                 THEN
      CASE WHEN p_value >= 5 THEN 5.0
           WHEN p_value >= 4 THEN 3.0
           WHEN p_value >= 3 THEN 1.0
           WHEN p_value >= 2 THEN -2.0
           ELSE -4.0 END
    WHEN 'rating_update'          THEN p_value -- caller pre-computes (new - old)
    ELSE 0
  END;
$$;

-- 3) Recompute trigger: upsert weights for each tag in REA
CREATE OR REPLACE FUNCTION public.recompute_user_interests()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_delta numeric;
  v_tag_slug text;
  v_tag_id uuid;
  v_rea_tags text[];
BEGIN
  v_delta := public.event_delta(NEW.event_type, NEW.value);
  IF v_delta = 0 THEN RETURN NEW; END IF;

  SELECT tags INTO v_rea_tags FROM public.reas WHERE id = NEW.rea_id;
  IF v_rea_tags IS NULL OR array_length(v_rea_tags, 1) IS NULL THEN
    RETURN NEW;
  END IF;

  FOREACH v_tag_slug IN ARRAY v_rea_tags LOOP
    SELECT id INTO v_tag_id FROM public.tags WHERE slug = lower(v_tag_slug);
    IF v_tag_id IS NULL THEN CONTINUE; END IF;

    INSERT INTO public.user_interests (user_id, tag_id, weight, source)
    VALUES (NEW.user_id, v_tag_id, GREATEST(0, LEAST(100, 1.0 + v_delta)), 'inferred')
    ON CONFLICT (user_id, tag_id) DO UPDATE
      SET weight = GREATEST(0, LEAST(100, public.user_interests.weight + v_delta)),
          updated_at = now();
  END LOOP;

  RETURN NEW;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.recompute_user_interests() FROM PUBLIC, anon, authenticated;

CREATE TRIGGER trg_rea_interactions_recompute
  AFTER INSERT ON public.rea_interactions
  FOR EACH ROW EXECUTE FUNCTION public.recompute_user_interests();

-- 4) Recommended feed RPC
CREATE OR REPLACE FUNCTION public.get_recommended_feed(p_limit integer DEFAULT 20)
RETURNS TABLE (
  id uuid,
  title text,
  description text,
  resource_url text,
  thumbnail_url text,
  source_url text,
  author text,
  format public.rea_format,
  license public.rea_license,
  language public.rea_language,
  subject_area text,
  education_level public.education_level,
  tags text[],
  status public.rea_status,
  rating_avg numeric,
  rating_count integer,
  report_count integer,
  submitted_by uuid,
  created_at timestamptz,
  updated_at timestamptz,
  score numeric
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user uuid := auth.uid();
  v_total_reas bigint;
BEGIN
  SELECT count(*) INTO v_total_reas FROM public.reas WHERE status = 'active';
  IF v_total_reas = 0 THEN RETURN; END IF;

  RETURN QUERY
  WITH tag_idf AS (
    SELECT t.slug, ln(1 + v_total_reas::numeric / NULLIF(count(r.id), 0)) AS idf
    FROM public.tags t
    LEFT JOIN public.reas r ON r.status = 'active' AND t.slug = ANY(r.tags)
    GROUP BY t.slug
  ),
  user_vec AS (
    SELECT t.slug, ui.weight
    FROM public.user_interests ui
    JOIN public.tags t ON t.id = ui.tag_id
    WHERE ui.user_id = v_user
  ),
  seen AS (
    SELECT DISTINCT rea_id FROM public.rea_interactions
    WHERE user_id = v_user AND created_at > now() - interval '7 days'
  ),
  scored AS (
    SELECT
      r.*,
      COALESCE((
        SELECT sum(uv.weight * ti.idf)
        FROM unnest(r.tags) AS rt
        JOIN user_vec uv ON uv.slug = lower(rt)
        JOIN tag_idf ti ON ti.slug = lower(rt)
      ), 0) AS tag_score,
      CASE WHEN s.rea_id IS NOT NULL THEN 1 ELSE 0 END AS seen_pen
    FROM public.reas r
    LEFT JOIN seen s ON s.rea_id = r.id
    WHERE r.status = 'active'
  )
  SELECT
    sc.id, sc.title, sc.description, sc.resource_url, sc.thumbnail_url, sc.source_url,
    sc.author, sc.format, sc.license, sc.language, sc.subject_area, sc.education_level,
    sc.tags, sc.status, sc.rating_avg, sc.rating_count, sc.report_count,
    sc.submitted_by, sc.created_at, sc.updated_at,
    (sc.tag_score
      + 0.8 * sc.rating_avg
      + 0.4 * ln(1 + sc.rating_count)
      + 0.2 * (1.0 / (1.0 + EXTRACT(EPOCH FROM (now() - sc.created_at)) / 86400.0 / 30.0))
      - 2.0 * sc.seen_pen
    )::numeric AS score
  FROM scored sc
  ORDER BY score DESC, sc.rating_avg DESC, sc.created_at DESC
  LIMIT p_limit;
END;
$$;

GRANT EXECUTE ON FUNCTION public.get_recommended_feed(integer) TO anon, authenticated;

-- 5) Temporal decay job
CREATE OR REPLACE FUNCTION public.decay_user_interests()
RETURNS void
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  UPDATE public.user_interests
  SET weight = GREATEST(0, weight * power(0.5, EXTRACT(EPOCH FROM (now() - updated_at)) / 86400.0 / 90.0))
  WHERE source = 'inferred';
$$;

REVOKE EXECUTE ON FUNCTION public.decay_user_interests() FROM PUBLIC, anon, authenticated;

-- 6) Schedule daily decay
CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule(
  'decay-user-interests-daily',
  '0 3 * * *',
  $$SELECT public.decay_user_interests();$$
);
