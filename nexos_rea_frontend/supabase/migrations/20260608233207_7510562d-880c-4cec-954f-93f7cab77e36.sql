
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
#variable_conflict use_column
DECLARE
  v_user uuid := auth.uid();
  v_total_reas bigint;
BEGIN
  SELECT count(*) INTO v_total_reas FROM public.reas r WHERE r.status = 'active';
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
    SELECT DISTINCT ri.rea_id FROM public.rea_interactions ri
    WHERE ri.user_id = v_user AND ri.created_at > now() - interval '7 days'
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
