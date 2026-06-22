/**
 * Cliente para a API REST Flask (nexos_rea_backend).
 * Usado pelo catálogo para busca, filtros e paginação.
 * Autenticação: passa o token Supabase quando disponível.
 */

import type { Database } from "@/integrations/supabase/types";

export type Rea = Database["public"]["Tables"]["reas"]["Row"];

// SSR (Cloudflare Worker): globalThis.BACKEND_API_URL via wrangler vars
// Client-side (browser): import.meta.env.VITE_BACKEND_API_URL baked no bundle pelo Vite
const BASE_URL =
  (typeof globalThis !== "undefined" && (globalThis as any).BACKEND_API_URL) ||
  import.meta.env?.VITE_BACKEND_API_URL ||
  "http://localhost:5000";

interface FlaskPagination {
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

interface FlaskReaListResponse {
  items: unknown[];
  pagination: FlaskPagination;
}

export interface ReaFilters {
  q?: string;
  format?: string;
  language?: string;
  subject_area?: string;
  education_level?: string;
  min_rating?: number;
  unrated_only?: boolean;
  page?: number;
  per_page?: number;
}

export async function listReas(
  filters: ReaFilters = {},
  token?: string,
): Promise<{ items: Rea[]; total: number }> {
  const params = new URLSearchParams();

  if (filters.q)               params.set("q", filters.q);
  if (filters.format)          params.set("format", filters.format);
  if (filters.language)        params.set("language", filters.language);
  if (filters.subject_area)    params.set("subject_area", filters.subject_area);
  if (filters.education_level) params.set("education_level", filters.education_level);
  if (filters.unrated_only)    params.set("unrated_only", "true");
  else if (filters.min_rating) params.set("min_rating", String(filters.min_rating));
  if (filters.page)            params.set("page", String(filters.page));
  if (filters.per_page)        params.set("per_page", String(filters.per_page));

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}/api/reas/?${params}`, { headers });

  if (!res.ok) {
    throw new Error(`Erro ao buscar REAs: ${res.status}`);
  }

  const json = await res.json();
  const data = json.data as FlaskReaListResponse;

  // Flask retorna os mesmos campos do Supabase (alinhados na Sprint A).
  return { items: data.items as Rea[], total: data.pagination.total };
}

export interface ReaSubmitPayload {
  title: string;
  resource_url: string;
  format: string;
  license: string;
  subject_area: string;
  education_level: string;
  description?: string;
  author?: string;
  language?: string;
  thumbnail_url?: string;
  tags?: string[];
}

export async function submitRea(payload: ReaSubmitPayload, token: string): Promise<Rea> {
  const res = await fetch(`${BASE_URL}/api/reas/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.message ?? "Erro ao enviar REA.");
  return json.data as Rea;
}
