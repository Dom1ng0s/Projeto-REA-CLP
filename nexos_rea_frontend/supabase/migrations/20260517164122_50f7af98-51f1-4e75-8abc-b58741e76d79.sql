
-- =========================================
-- ENUMS
-- =========================================
CREATE TYPE public.app_role AS ENUM ('admin', 'user');
CREATE TYPE public.rea_status AS ENUM ('active', 'hidden_low_rating', 'blocked_review', 'removed');
CREATE TYPE public.rea_format AS ENUM ('video', 'audio', 'text', 'image', 'interactive', 'slides', 'other');
CREATE TYPE public.rea_license AS ENUM ('cc_by', 'cc_by_sa', 'cc_by_nc', 'cc_by_nc_sa', 'cc_by_nd', 'cc0', 'public_domain', 'other');
CREATE TYPE public.rea_language AS ENUM ('pt_br', 'en', 'es', 'other');

-- =========================================
-- updated_at trigger helper
-- =========================================
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

-- =========================================
-- PROFILES
-- =========================================
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  bio TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Profiles are viewable by everyone"
  ON public.profiles FOR SELECT
  USING (true);

CREATE POLICY "Users can insert own profile"
  ON public.profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE TRIGGER profiles_set_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1))
  );
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =========================================
-- USER_ROLES
-- =========================================
CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role public.app_role NOT NULL,
  granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, role)
);

ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- SECURITY DEFINER role checker (avoids RLS recursion)
CREATE OR REPLACE FUNCTION public.has_role(_user_id UUID, _role public.app_role)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = _user_id AND role = _role
  )
$$;

CREATE POLICY "Users can view own roles"
  ON public.user_roles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Admins can view all roles"
  ON public.user_roles FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can insert roles"
  ON public.user_roles FOR INSERT
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete roles"
  ON public.user_roles FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));

-- =========================================
-- REAS
-- =========================================
CREATE TABLE public.reas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  resource_url TEXT NOT NULL,
  thumbnail_url TEXT,
  source_url TEXT,
  author TEXT,
  format public.rea_format NOT NULL,
  license public.rea_license NOT NULL,
  language public.rea_language NOT NULL DEFAULT 'pt_br',
  subject_area TEXT NOT NULL,
  education_level TEXT NOT NULL,
  tags TEXT[] NOT NULL DEFAULT '{}',
  status public.rea_status NOT NULL DEFAULT 'active',
  rating_avg NUMERIC(3,2) NOT NULL DEFAULT 0,
  rating_count INTEGER NOT NULL DEFAULT 0,
  report_count INTEGER NOT NULL DEFAULT 0,
  submitted_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX reas_tags_gin_idx ON public.reas USING GIN (tags);
CREATE INDEX reas_status_idx ON public.reas (status);
CREATE INDEX reas_subject_area_idx ON public.reas (subject_area);
CREATE INDEX reas_education_level_idx ON public.reas (education_level);
CREATE INDEX reas_language_idx ON public.reas (language);
CREATE INDEX reas_format_idx ON public.reas (format);

CREATE TRIGGER reas_set_updated_at
  BEFORE UPDATE ON public.reas
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.reas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Active REAs are viewable by everyone"
  ON public.reas FOR SELECT
  USING (status = 'active');

CREATE POLICY "Admins can view all REAs"
  ON public.reas FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can insert REAs"
  ON public.reas FOR INSERT
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can update REAs"
  ON public.reas FOR UPDATE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete REAs"
  ON public.reas FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));
