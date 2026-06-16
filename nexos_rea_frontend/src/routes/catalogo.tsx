import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { Search, X, ChevronLeft, ChevronRight, SlidersHorizontal, Star, StarOff } from "lucide-react";
import { z } from "zod";
import { supabase } from "@/integrations/supabase/client";
import { listReas } from "@/lib/flask-api";
import { useAuth } from "@/hooks/use-auth";
import { ReaCard, ReaCardSkeleton } from "@/components/ReaCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { formatOptions, languageOptions, educationOptions, type EducationLevel } from "@/lib/rea-labels";
import type { Database } from "@/integrations/supabase/types";

type ReaFormat = Database["public"]["Enums"]["rea_format"];
type ReaLanguage = Database["public"]["Enums"]["rea_language"];
type Rea = Database["public"]["Tables"]["reas"]["Row"];

const PAGE_SIZE = 12;
const ALL = "__all__";

function StarsRow({ filled }: { filled: number }) {
  return (
    <span className="inline-flex items-center gap-0.5 align-middle">
      {[1, 2, 3, 4, 5].map((n) =>
        n <= filled ? (
          <Star key={n} className="h-3.5 w-3.5 fill-accent text-accent" />
        ) : (
          <Star key={n} className="h-3.5 w-3.5 text-muted-foreground/50" />
        ),
      )}
    </span>
  );
}

const ratingOptions: Array<{ value: string; render: React.ReactNode }> = [
  { value: "0", render: <span className="text-sm">Qualquer avaliação</span> },
  { value: "2", render: <span className="inline-flex items-center gap-2"><StarsRow filled={2} /> e acima</span> },
  { value: "3", render: <span className="inline-flex items-center gap-2"><StarsRow filled={3} /> e acima</span> },
  { value: "4", render: <span className="inline-flex items-center gap-2"><StarsRow filled={4} /> e acima</span> },
  { value: "none", render: <span className="inline-flex items-center gap-2"><StarOff className="h-3.5 w-3.5 text-muted-foreground" /> Sem avaliação</span> },
];

const searchSchema = z.object({
  q: z.string().optional().catch(""),
  format: z.string().optional().catch(ALL),
  language: z.string().optional().catch(ALL),
  subject: z.string().optional().catch(ALL),
  level: z.string().optional().catch(ALL),
  rating: z.string().optional().catch("0"),
  page: z.number().int().min(0).optional().catch(0),
});

export const Route = createFileRoute("/catalogo")({
  validateSearch: (s) => searchSchema.parse(s),
  head: () => ({
    meta: [
      { title: "Catálogo — Nexos REA" },
      {
        name: "description",
        content:
          "Busque Recursos Educacionais Abertos por área, nível, formato, idioma e tags.",
      },
    ],
  }),
  component: CatalogoPage,
});

function CatalogoPage() {
  const { user } = useAuth();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();

  const q = search.q ?? "";
  const format = (search.format ?? ALL) as ReaFormat | typeof ALL;
  const language = (search.language ?? ALL) as ReaLanguage | typeof ALL;
  const subject = search.subject ?? ALL;
  const level = (search.level ?? ALL) as EducationLevel | typeof ALL;
  const minRating = search.rating ?? "0";
  const page = search.page ?? 0;

  // Estado local da barra de busca (com debounce para sincronizar com URL)
  const [searchInput, setSearchInput] = useState(q);
  const debouncedSearch = useDebouncedValue(searchInput, 300);

  useEffect(() => {
    if ((debouncedSearch ?? "") !== (q ?? "")) {
      navigate({
        search: (prev: any) => ({ ...prev, q: debouncedSearch || undefined, page: 0 }),
        replace: true,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  const [filtersOpen, setFiltersOpen] = useState(() => {
    if (typeof window === "undefined") return true;
    return window.innerWidth >= 768;
  });

  function setParam(k: string, v: any) {
    navigate({
      search: (prev: any) => ({ ...prev, [k]: v, page: 0 }),
      replace: true,
    });
  }

  const { data: subjectAreas } = useQuery({
    queryKey: ["subject_areas"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("subject_areas" as never)
        .select("slug, label")
        .order("label");
      if (error) throw error;
      return (data as unknown as { slug: string; label: string }[]) ?? [];
    },
  });

  const { data: recommended } = useQuery({
    queryKey: ["reas", "recommended", user?.id ?? "anon"],
    enabled: !!user,
    queryFn: async () => {
      const { data, error } = await supabase.rpc("get_recommended_feed", { p_limit: 6 });
      if (error) throw error;
      return (data ?? []) as unknown as Rea[];
    },
  });

  const { data: sessionData } = useQuery({
    queryKey: ["session"],
    queryFn: async () => {
      const { data } = await supabase.auth.getSession();
      return data.session;
    },
  });

  const { data, isFetching, isLoading } = useQuery({
    queryKey: ["reas", "search", { q, format, language, subject, level, minRating, page }],
    queryFn: async () => {
      const subjectLabel =
        subject !== ALL
          ? subjectAreas?.find((s) => s.slug === subject)?.label
          : undefined;

      return listReas(
        {
          q:               q.trim() || undefined,
          format:          format !== ALL ? format : undefined,
          language:        language !== ALL ? language : undefined,
          subject_area:    subjectLabel,
          education_level: level !== ALL ? level : undefined,
          unrated_only:    minRating === "none",
          min_rating:      minRating !== "none" && Number(minRating) > 0 ? Number(minRating) : undefined,
          page:            page + 1,
          per_page:        PAGE_SIZE,
        },
        sessionData?.access_token,
      );
    },
    placeholderData: keepPreviousData,
  });

  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const hasFilters =
    !!q || format !== ALL || language !== ALL || subject !== ALL || level !== ALL || minRating !== "0";

  const showRecommended =
    !!user && page === 0 && !hasFilters && (recommended?.length ?? 0) > 0;

  const recommendedIds = new Set(showRecommended ? recommended!.map((r) => r.id) : []);
  const regularItems = (data?.items ?? []).filter((r) => !recommendedIds.has(r.id));

  const handleReset = () => {
    setSearchInput("");
    navigate({ search: {}, replace: true });
  };

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10 md:py-14">
      <header className="mb-8">
        <h1 className="font-display text-4xl md:text-5xl text-foreground">
          Catálogo
        </h1>
        <p className="mt-2 text-muted-foreground">
          Busque por título, autor, área, nível, formato ou idioma.
        </p>
      </header>

      {/* Busca */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          type="search"
          placeholder="Buscar por título, descrição ou autor…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="pl-9 h-11"
          aria-label="Termo de busca"
        />
      </div>

      {/* Filtros (colapsáveis) */}
      {filtersOpen && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5 mb-4">
          <div>
            <Label className="text-xs">Área</Label>
            <Select value={subject} onValueChange={(v) => setParam("subject", v === ALL ? undefined : v)}>
              <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Todas as áreas</SelectItem>
                {(subjectAreas ?? []).map((s) => (
                  <SelectItem key={s.slug} value={s.slug}>{s.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs">Nível de ensino</Label>
            <Select value={level} onValueChange={(v) => setParam("level", v === ALL ? undefined : v)}>
              <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Todos os níveis</SelectItem>
                {educationOptions.map(([v, label]) => (
                  <SelectItem key={v} value={v}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs">Formato</Label>
            <Select value={format} onValueChange={(v) => setParam("format", v === ALL ? undefined : v)}>
              <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Todos os formatos</SelectItem>
                {formatOptions.map(([v, label]) => (
                  <SelectItem key={v} value={v}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs">Idioma</Label>
            <Select value={language} onValueChange={(v) => setParam("language", v === ALL ? undefined : v)}>
              <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Todos os idiomas</SelectItem>
                {languageOptions.map(([v, label]) => (
                  <SelectItem key={v} value={v}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs">Avaliação mínima</Label>
            <Select value={minRating} onValueChange={(v) => setParam("rating", v === "0" ? undefined : v)}>
              <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                {ratingOptions.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.render}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-6 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setFiltersOpen((v) => !v)}
            aria-label={filtersOpen ? "Ocultar filtros" : "Mostrar filtros"}
            aria-pressed={filtersOpen}
          >
            <SlidersHorizontal className="h-4 w-4" />
          </Button>
          {isLoading ? "Carregando…" : (
            <>
              <strong className="text-foreground">{total}</strong>{" "}
              {total === 1 ? "recurso encontrado" : "recursos encontrados"}
            </>
          )}
        </div>
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={handleReset}>
            <X className="h-3.5 w-3.5 mr-1" /> Limpar filtros
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <ReaCardSkeleton key={i} />
          ))}
        </div>
      ) : (showRecommended || regularItems.length > 0) ? (
        <>
          <div className={`grid gap-6 sm:grid-cols-2 lg:grid-cols-3 ${isFetching ? "opacity-60" : ""}`}>
            {showRecommended && recommended!.map((rea) => (
              <ReaCard key={`rec-${rea.id}`} rea={rea} recommended />
            ))}
            {regularItems.map((rea) => (
              <ReaCard key={rea.id} rea={rea} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-10 flex items-center justify-center gap-2">
              <Button
                variant="outline" size="sm"
                onClick={() => navigate({ search: (p: any) => ({ ...p, page: Math.max(0, page - 1) }) })}
                disabled={page === 0}
              >
                <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
              </Button>
              <span className="text-sm text-muted-foreground px-3">
                Página <strong className="text-foreground">{page + 1}</strong> de {totalPages}
              </span>
              <Button
                variant="outline" size="sm"
                onClick={() => navigate({ search: (p: any) => ({ ...p, page: Math.min(totalPages - 1, page + 1) }) })}
                disabled={page >= totalPages - 1}
              >
                Próxima <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          )}
        </>
      ) : (
        <div className="rounded-lg border border-dashed border-border bg-card p-12 text-center">
          <h2 className="font-display text-xl text-foreground">Nenhum recurso encontrado</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Tente ajustar os termos da busca ou remover filtros.
          </p>
          {hasFilters && (
            <Button variant="outline" size="sm" onClick={handleReset} className="mt-4">
              Limpar filtros
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
