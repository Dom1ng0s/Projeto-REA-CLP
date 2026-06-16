
-- ============================================================
-- Sprint 4: Governança, Segurança e Analytics
-- ============================================================

-- ---------- Enums novos ----------
CREATE TYPE public.report_reason AS ENUM (
  'inappropriate', 'broken_link', 'copyright',
  'misinformation', 'spam', 'other'
);

CREATE TYPE public.report_state AS ENUM (
  'pending', 'dismissed', 'accepted'
);

-- ============================================================
-- Tabela: rea_ratings
-- ============================================================
CREATE TABLE public.rea_ratings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rea_id uuid NOT NULL REFERENCES public.reas(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  rating smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment text CHECK (comment IS NULL OR length(comment) <= 500),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rea_id, user_id)
);

CREATE INDEX rea_ratings_rea_idx ON public.rea_ratings (rea_id);
CREATE INDEX rea_ratings_user_idx ON public.rea_ratings (user_id);

GRANT SELECT ON public.rea_ratings TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.rea_ratings TO authenticated;
GRANT ALL ON public.rea_ratings TO service_role;

ALTER TABLE public.rea_ratings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Ratings são visíveis a todos"
  ON public.rea_ratings FOR SELECT
  USING (true);

CREATE POLICY "Usuário insere a própria avaliação"
  ON public.rea_ratings FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Usuário atualiza a própria avaliação"
  ON public.rea_ratings FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Usuário remove a própria avaliação"
  ON public.rea_ratings FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE TRIGGER trg_rea_ratings_updated_at
  BEFORE UPDATE ON public.rea_ratings
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ============================================================
-- Tabela: rea_reports
-- ============================================================
CREATE TABLE public.rea_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rea_id uuid NOT NULL REFERENCES public.reas(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  reason public.report_reason NOT NULL,
  details text CHECK (details IS NULL OR length(details) <= 1000),
  state public.report_state NOT NULL DEFAULT 'pending',
  resolved_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  resolved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rea_id, user_id)
);

CREATE INDEX rea_reports_rea_idx ON public.rea_reports (rea_id);
CREATE INDEX rea_reports_pending_idx ON public.rea_reports (state) WHERE state = 'pending';

GRANT SELECT, INSERT, UPDATE, DELETE ON public.rea_reports TO authenticated;
GRANT ALL ON public.rea_reports TO service_role;

ALTER TABLE public.rea_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuário vê as próprias denúncias"
  ON public.rea_reports FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id OR public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Usuário cria a própria denúncia"
  ON public.rea_reports FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Admin atualiza denúncias"
  ON public.rea_reports FOR UPDATE
  TO authenticated
  USING (public.has_role(auth.uid(), 'admin'))
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admin remove denúncias"
  ON public.rea_reports FOR DELETE
  TO authenticated
  USING (public.has_role(auth.uid(), 'admin'));

-- ============================================================
-- Trigger: recálculo de rating + regra dos 2.0
-- ============================================================
CREATE OR REPLACE FUNCTION public.recompute_rea_rating()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_rea_id uuid := COALESCE(NEW.rea_id, OLD.rea_id);
  v_avg numeric(3,2);
  v_count integer;
  v_status public.rea_status;
BEGIN
  SELECT COALESCE(AVG(rating)::numeric(3,2), 0), COUNT(*)
    INTO v_avg, v_count
    FROM public.rea_ratings WHERE rea_id = v_rea_id;

  SELECT status INTO v_status FROM public.reas WHERE id = v_rea_id FOR UPDATE;

  -- Regra: rebaixar para hidden_low_rating
  IF v_count >= 3 AND v_avg < 2.0 AND v_status = 'active' THEN
    v_status := 'hidden_low_rating';
  -- Reversão: voltar para active
  ELSIF v_status = 'hidden_low_rating' AND (v_count < 3 OR v_avg >= 2.0) THEN
    v_status := 'active';
  END IF;

  UPDATE public.reas
     SET rating_avg = v_avg,
         rating_count = v_count,
         status = v_status,
         updated_at = now()
   WHERE id = v_rea_id;

  -- Log para o motor de recomendação (Sprint 3)
  IF TG_OP = 'INSERT' THEN
    INSERT INTO public.rea_interactions (user_id, rea_id, event_type, value)
    VALUES (NEW.user_id, NEW.rea_id, 'rating', NEW.rating);
  ELSIF TG_OP = 'UPDATE' AND NEW.rating <> OLD.rating THEN
    INSERT INTO public.rea_interactions (user_id, rea_id, event_type, value)
    VALUES (NEW.user_id, NEW.rea_id,
            'rating_update',
            public.event_delta('rating', NEW.rating) - public.event_delta('rating', OLD.rating));
  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER trg_rea_ratings_aiud
  AFTER INSERT OR UPDATE OR DELETE ON public.rea_ratings
  FOR EACH ROW EXECUTE FUNCTION public.recompute_rea_rating();

-- ============================================================
-- Trigger: recálculo de denúncias + regra dos 3+
-- ============================================================
CREATE OR REPLACE FUNCTION public.recompute_rea_reports()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_rea_id uuid := COALESCE(NEW.rea_id, OLD.rea_id);
  v_pending integer;
  v_status public.rea_status;
  v_avg numeric(3,2);
  v_count integer;
BEGIN
  SELECT COUNT(*) INTO v_pending
    FROM public.rea_reports
    WHERE rea_id = v_rea_id AND state = 'pending';

  SELECT status, rating_avg, rating_count
    INTO v_status, v_avg, v_count
    FROM public.reas WHERE id = v_rea_id FOR UPDATE;

  -- Regra: 3+ denúncias pendentes => sob revisão
  IF v_pending >= 3 AND v_status IN ('active', 'hidden_low_rating') THEN
    v_status := 'blocked_review';
  -- Reversão: denúncias caíram abaixo de 3 e status era blocked_review
  ELSIF v_status = 'blocked_review' AND v_pending < 3 THEN
    IF v_count >= 3 AND v_avg < 2.0 THEN
      v_status := 'hidden_low_rating';
    ELSE
      v_status := 'active';
    END IF;
  END IF;

  UPDATE public.reas
     SET report_count = v_pending,
         status = v_status,
         updated_at = now()
   WHERE id = v_rea_id;

  -- Log denúncia no motor de recomendação
  IF TG_OP = 'INSERT' THEN
    INSERT INTO public.rea_interactions (user_id, rea_id, event_type, value)
    VALUES (NEW.user_id, NEW.rea_id, 'report', 0);
  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER trg_rea_reports_aiud
  AFTER INSERT OR UPDATE OR DELETE ON public.rea_reports
  FOR EACH ROW EXECUTE FUNCTION public.recompute_rea_reports();

-- ============================================================
-- RPC: admin_resolve_report
-- ============================================================
CREATE OR REPLACE FUNCTION public.admin_resolve_report(
  p_rea_id uuid,
  p_decision text -- 'restore' ou 'remove'
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_admin uuid := auth.uid();
BEGIN
  IF NOT public.has_role(v_admin, 'admin') THEN
    RAISE EXCEPTION 'forbidden: admin role required';
  END IF;

  IF p_decision = 'restore' THEN
    UPDATE public.rea_reports
       SET state = 'dismissed',
           resolved_by = v_admin,
           resolved_at = now()
     WHERE rea_id = p_rea_id AND state = 'pending';
  ELSIF p_decision = 'remove' THEN
    UPDATE public.rea_reports
       SET state = 'accepted',
           resolved_by = v_admin,
           resolved_at = now()
     WHERE rea_id = p_rea_id AND state = 'pending';

    UPDATE public.reas
       SET status = 'removed',
           updated_at = now()
     WHERE id = p_rea_id;
  ELSE
    RAISE EXCEPTION 'invalid decision: %', p_decision;
  END IF;
END;
$$;

GRANT EXECUTE ON FUNCTION public.admin_resolve_report(uuid, text) TO authenticated;

-- ============================================================
-- RPC: get_admin_metrics (CTR + contagens)
-- ============================================================
CREATE OR REPLACE FUNCTION public.get_admin_metrics()
RETURNS jsonb
LANGUAGE plpgsql
STABLE SECURITY DEFINER
SET search_path = public
AS $$
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
           COUNT(*) FILTER (WHERE e.event_type IN ('view','search_click','save_to_collection')) AS clicks,
           GREATEST(COUNT(*), 1) AS impressions_est
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
      )) FROM ctr_series), '[]'::jsonb),
    'pendingReviewCount', (SELECT count(*) FROM public.reas WHERE status = 'blocked_review'),
    'hiddenLowRatingCount', (SELECT count(*) FROM public.reas WHERE status = 'hidden_low_rating'),
    'activeReasCount', (SELECT count(*) FROM public.reas WHERE status = 'active'),
    'removedCount', (SELECT count(*) FROM public.reas WHERE status = 'removed')
  ) INTO v_result;

  RETURN v_result;
END;
$$;

GRANT EXECUTE ON FUNCTION public.get_admin_metrics() TO authenticated;

-- ============================================================
-- RPC: get_moderation_queue (lista REAs sob revisão + denúncias)
-- ============================================================
CREATE OR REPLACE FUNCTION public.get_moderation_queue()
RETURNS jsonb
LANGUAGE plpgsql
STABLE SECURITY DEFINER
SET search_path = public
AS $$
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
    ))
    FROM public.reas r
    WHERE r.status = 'blocked_review'
    ORDER BY r.updated_at DESC
  ), '[]'::jsonb);
END;
$$;

GRANT EXECUTE ON FUNCTION public.get_moderation_queue() TO authenticated;
