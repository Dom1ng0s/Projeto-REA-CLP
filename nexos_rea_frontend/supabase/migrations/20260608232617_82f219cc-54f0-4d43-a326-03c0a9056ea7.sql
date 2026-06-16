
-- Migration 1: education_level enum + subject_areas catalog

CREATE TYPE public.education_level AS ENUM (
  'infantil', 'fundamental', 'medio', 'tecnico',
  'graduacao', 'pos_graduacao', 'extensao', 'livre'
);

ALTER TABLE public.reas
  ALTER COLUMN education_level TYPE public.education_level
  USING (
    CASE education_level
      WHEN 'ensino_superior'    THEN 'graduacao'
      WHEN 'ensino_medio'       THEN 'medio'
      WHEN 'ensino_fundamental' THEN 'fundamental'
      ELSE 'livre'
    END
  )::public.education_level;

CREATE TABLE public.subject_areas (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  label text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

GRANT SELECT ON public.subject_areas TO anon, authenticated;
GRANT ALL ON public.subject_areas TO service_role;

ALTER TABLE public.subject_areas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "subject_areas viewable by everyone"
  ON public.subject_areas FOR SELECT USING (true);

CREATE POLICY "Admins manage subject_areas"
  ON public.subject_areas FOR ALL
  USING (public.has_role(auth.uid(), 'admin'))
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

INSERT INTO public.subject_areas (slug, label)
SELECT DISTINCT
  lower(regexp_replace(
    translate(subject_area,
      'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ',
      'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'),
    '[^a-zA-Z0-9]+', '-', 'g')),
  initcap(subject_area)
FROM public.reas
ON CONFLICT (slug) DO NOTHING;

CREATE OR REPLACE FUNCTION public.ensure_subject_area()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public
AS $$
DECLARE
  v_slug text;
BEGIN
  IF NEW.subject_area IS NULL OR length(trim(NEW.subject_area)) = 0 THEN
    RETURN NEW;
  END IF;

  v_slug := lower(regexp_replace(
    translate(NEW.subject_area,
      'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ',
      'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'),
    '[^a-zA-Z0-9]+', '-', 'g'));

  INSERT INTO public.subject_areas (slug, label)
  VALUES (v_slug, initcap(NEW.subject_area))
  ON CONFLICT (slug) DO NOTHING;

  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_reas_ensure_subject_area
  BEFORE INSERT OR UPDATE OF subject_area ON public.reas
  FOR EACH ROW EXECUTE FUNCTION public.ensure_subject_area();
