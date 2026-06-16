import type { Database } from "@/integrations/supabase/types";

type ReaFormat = Database["public"]["Enums"]["rea_format"];
type ReaLicense = Database["public"]["Enums"]["rea_license"];
type ReaLanguage = Database["public"]["Enums"]["rea_language"];
type ReaStatus = Database["public"]["Enums"]["rea_status"];

export const formatLabel: Record<ReaFormat, string> = {
  video: "Vídeo",
  audio: "Áudio",
  text: "Texto",
  image: "Imagem",
  interactive: "Interativo",
  slides: "Slides",
  other: "Outro",
};

export const licenseLabel: Record<ReaLicense, string> = {
  cc_by: "CC BY",
  cc_by_sa: "CC BY-SA",
  cc_by_nc: "CC BY-NC",
  cc_by_nc_sa: "CC BY-NC-SA",
  cc_by_nd: "CC BY-ND",
  cc0: "CC0",
  public_domain: "Domínio público",
  other: "Outra",
};

export const languageLabel: Record<ReaLanguage, string> = {
  pt_br: "Português (BR)",
  en: "Inglês",
  es: "Espanhol",
  other: "Outro",
};

export const statusLabel: Record<ReaStatus, string> = {
  active: "Ativo",
  hidden_low_rating: "Oculto (baixa nota)",
  blocked_review: "Em revisão",
  removed: "Removido",
};

export type EducationLevel =
  | "infantil"
  | "fundamental"
  | "medio"
  | "tecnico"
  | "graduacao"
  | "pos_graduacao"
  | "extensao"
  | "livre";

export const educationLabel: Record<EducationLevel, string> = {
  infantil: "Educação infantil",
  fundamental: "Ensino fundamental",
  medio: "Ensino médio",
  tecnico: "Técnico",
  graduacao: "Graduação",
  pos_graduacao: "Pós-graduação",
  extensao: "Extensão",
  livre: "Livre",
};

export const formatOptions = Object.entries(formatLabel) as [ReaFormat, string][];
export const licenseOptions = Object.entries(licenseLabel) as [ReaLicense, string][];
export const languageOptions = Object.entries(languageLabel) as [ReaLanguage, string][];
export const educationOptions = Object.entries(educationLabel) as [EducationLevel, string][];
