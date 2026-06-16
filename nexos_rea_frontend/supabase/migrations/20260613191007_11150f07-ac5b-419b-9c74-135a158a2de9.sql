
-- Merge hidden_low_rating into "sob revisão" for admin UI, and add admin RPCs for browsing/managing REAs by status.

-- 1) get_admin_metrics: combine hidden + blocked under pendingReviewCount
CREATE OR REPLACE FUNCTION public.get_admin_metrics()
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_admin uuid := auth.uid();
  v_result jsonb;
BEGIN
  IF NOT public.has_role(v_admin, 'admin') THEN
    RAISE EXCEPTION 'forbidden: admin role required';
  END IF;

  WITH series AS (
    SELECT generate_series(
      date_trunc('day', now()) - interval '29 days',
      date_trunc('day', now()),
      interval '1 day'
    )::date AS d
  ),
  events AS (
    SELECT date_trunc('day', created_at)::date AS d,
           event_type
      FROM public.rea_interactions
      WHERE created_at >= now() - interval '30 days'
  ),
  agg AS (
    SELECT s.d,
           COUNT(e.*) FILTER (WHERE e.event_type IN ('view','search_click','save_to_collection')) AS clicks,
           GREATEST(COUNT(e.*), 0) AS impressions_est
      FROM series s
      LEFT JOIN events e ON e.d = s.d
      GROUP BY s.d
  ),
  ctr_series AS (
    SELECT d,
           clicks,
           impressions_est AS impressions,
           CASE WHEN impressions_est > 0
                THEN ROUND((clicks::numeric / impressions_est) * 100, 2) / 100.0
                ELSE 0 END AS ctr
      FROM agg
      ORDER BY d
  )
  SELECT jsonb_build_object(
    'ctrAvg30d', COALESCE((SELECT AVG(ctr) FROM ctr_series), 0),
    'ctrSeries', COALESCE((SELECT jsonb_agg(jsonb_build_object(
        'bucketStart', d, 'impressions', impressions, 'clicks', clicks, 'ctr', ctr
      ) ORDER BY d) FROM ctr_series), '[]'::jsonb),
    'pendingReviewCount', (SELECT count(*) FROM public.reas WHERE status IN ('blocked_review','hidden_low_rating')),
    'activeReasCount', (SELECT count(*) FROM public.reas WHERE status = 'active'),
    'removedCount', (SELECT count(*) FROM public.reas WHERE status = 'removed')
  ) INTO v_result;

  RETURN v_result;
END;
$function$;

-- 2) get_moderation_queue: include hidden_low_rating
CREATE OR REPLACE FUNCTION public.get_moderation_queue()
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_admin uuid := auth.uid();
BEGIN
  IF NOT public.has_role(v_admin, 'admin') THEN
    RAISE EXCEPTION 'forbidden: admin role required';
  END IF;

  RETURN COALESCE((
    SELECT jsonb_agg(jsonb_build_object(
      'rea', jsonb_build_object(
        'id', r.id,
        'title', r.title,
        'thumbnail_url', r.thumbnail_url,
        'subject_area', r.subject_area,
        'education_level', r.education_level,
        'status', r.status,
        'rating_avg', r.rating_avg,
        'rating_count', r.rating_count,
        'report_count', r.report_count,
        'created_at', r.created_at
      ),
      'pendingReports', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'id', rp.id, 'reason', rp.reason, 'details', rp.details,
          'user_id', rp.user_id, 'created_at', rp.created_at
        ))
        FROM public.rea_reports rp
        WHERE rp.rea_id = r.id AND rp.state = 'pending'
      ), '[]'::jsonb)
    ) ORDER BY r.updated_at DESC)
    FROM public.reas r
    WHERE r.status IN ('blocked_review','hidden_low_rating')
  ), '[]'::jsonb);
END;
$function$;

-- 3) Admin-only function to set status directly (restore / remove)
CREATE OR REPLACE FUNCTION public.admin_set_rea_status(p_rea_id uuid, p_status text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_admin uuid := auth.uid();
BEGIN
  IF NOT public.has_role(v_admin, 'admin') THEN
    RAISE EXCEPTION 'forbidden: admin role required';
  END IF;
  IF p_status NOT IN ('active','removed','blocked_review','hidden_low_rating') THEN
    RAISE EXCEPTION 'invalid status: %', p_status;
  END IF;

  -- Resolve any pending reports when restoring or removing
  IF p_status IN ('active','removed') THEN
    UPDATE public.rea_reports
       SET state = CASE WHEN p_status = 'active' THEN 'dismissed'::report_state ELSE 'accepted'::report_state END,
           resolved_by = v_admin,
           resolved_at = now()
     WHERE rea_id = p_rea_id AND state = 'pending';
  END IF;

  UPDATE public.reas
     SET status = p_status::rea_status,
         updated_at = now()
   WHERE id = p_rea_id;
END;
$function$;

GRANT EXECUTE ON FUNCTION public.admin_set_rea_status(uuid, text) TO authenticated;

-- 4) Admin-only paged search across any statuses
CREATE OR REPLACE FUNCTION public.admin_list_reas(
  p_statuses text[],
  p_query text DEFAULT NULL,
  p_limit int DEFAULT 24,
  p_offset int DEFAULT 0
)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_admin uuid := auth.uid();
  v_total bigint;
  v_items jsonb;
  v_q text;
BEGIN
  IF NOT public.has_role(v_admin, 'admin') THEN
    RAISE EXCEPTION 'forbidden: admin role required';
  END IF;

  v_q := NULLIF(trim(coalesce(p_query, '')), '');

  SELECT count(*) INTO v_total
    FROM public.reas r
   WHERE r.status::text = ANY(p_statuses)
     AND (v_q IS NULL
          OR r.title ILIKE '%'||v_q||'%'
          OR r.description ILIKE '%'||v_q||'%'
          OR r.author ILIKE '%'||v_q||'%'
          OR r.subject_area ILIKE '%'||v_q||'%');

  SELECT COALESCE(jsonb_agg(row), '[]'::jsonb) INTO v_items
  FROM (
    SELECT jsonb_build_object(
      'id', r.id,
      'title', r.title,
      'thumbnail_url', r.thumbnail_url,
      'subject_area', r.subject_area,
      'education_level', r.education_level,
      'status', r.status,
      'rating_avg', r.rating_avg,
      'rating_count', r.rating_count,
      'report_count', r.report_count,
      'created_at', r.created_at,
      'updated_at', r.updated_at,
      'pendingReports', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'id', rp.id, 'reason', rp.reason, 'details', rp.details,
          'user_id', rp.user_id, 'created_at', rp.created_at
        ))
        FROM public.rea_reports rp
        WHERE rp.rea_id = r.id AND rp.state = 'pending'
      ), '[]'::jsonb)
    ) AS row
    FROM public.reas r
   WHERE r.status::text = ANY(p_statuses)
     AND (v_q IS NULL
          OR r.title ILIKE '%'||v_q||'%'
          OR r.description ILIKE '%'||v_q||'%'
          OR r.author ILIKE '%'||v_q||'%'
          OR r.subject_area ILIKE '%'||v_q||'%')
   ORDER BY r.updated_at DESC
   LIMIT p_limit OFFSET p_offset
  ) s;

  RETURN jsonb_build_object('total', v_total, 'items', v_items);
END;
$function$;

GRANT EXECUTE ON FUNCTION public.admin_list_reas(text[], text, int, int) TO authenticated;
