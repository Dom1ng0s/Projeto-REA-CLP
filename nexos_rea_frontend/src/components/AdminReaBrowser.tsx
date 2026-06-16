import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, CheckCircle2, Trash2, Flag, Search, Undo2, ChevronLeft, ChevronRight } from "lucide-react";
import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useDebouncedValue } from "@/hooks/use-debounced-value";

const REASON_LABEL: Record<string, string> = {
  inappropriate: "Inadequado ou ofensivo",
  spam: "Spam",
  copyright: "Direitos autorais",
  broken_link: "Link quebrado",
  misinformation: "Conteúdo incorreto/desatualizado",
  other: "Outro",
};

const STATUS_LABEL: Record<string, string> = {
  active: "Ativo",
  blocked_review: "Sob revisão (denúncias)",
  hidden_low_rating: "Sob revisão (nota baixa)",
  removed: "Removido",
};

type Item = {
  id: string;
  title: string;
  thumbnail_url: string | null;
  subject_area: string;
  education_level: string;
  status: string;
  rating_avg: number;
  rating_count: number;
  report_count: number;
  created_at: string;
  updated_at: string;
  pendingReports: Array<{ id: string; reason: string; details: string | null; created_at: string }>;
};

const PAGE_SIZE = 12;

export function AdminReaBrowser({
  statuses,
  title,
  emptyMessage,
  showRestore = true,
  showRemove = true,
  showSendToReview = false,
}: {
  statuses: string[];
  title: string;
  emptyMessage: string;
  showRestore?: boolean;
  showRemove?: boolean;
  showSendToReview?: boolean;
}) {
  const qc = useQueryClient();
  const [query, setQuery] = useState("");
  const debounced = useDebouncedValue(query, 300);
  const [page, setPage] = useState(0);

  useEffect(() => { setPage(0); }, [debounced]);

  const listQ = useQuery({
    queryKey: ["admin-list-reas", statuses.join(","), debounced, page],
    queryFn: async () => {
      const { data, error } = await supabase.rpc("admin_list_reas" as any, {
        p_statuses: statuses,
        p_query: debounced || null,
        p_limit: PAGE_SIZE,
        p_offset: page * PAGE_SIZE,
      });
      if (error) throw error;
      return data as unknown as { total: number; items: Item[] };
    },
  });

  const setStatusMut = useMutation({
    mutationFn: async ({ reaId, status }: { reaId: string; status: string }) => {
      const { error } = await supabase.rpc("admin_set_rea_status" as any, {
        p_rea_id: reaId,
        p_status: status,
      });
      if (error) throw error;
    },
    onSuccess: (_d, vars) => {
      const labels: Record<string, string> = {
        active: "Conteúdo restaurado",
        removed: "Conteúdo removido",
        blocked_review: "Enviado para revisão",
      };
      toast.success(labels[vars.status] ?? "Status atualizado");
      qc.invalidateQueries({ queryKey: ["admin-list-reas"] });
      qc.invalidateQueries({ queryKey: ["admin-metrics"] });
    },
    onError: (e: Error) => toast.error("Erro", { description: e.message }),
  });

  const items = listQ.data?.items ?? [];
  const total = listQ.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Buscar por título, autor ou área..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-9"
            aria-label="Buscar"
          />
        </div>
        <p className="text-sm text-muted-foreground">
          {listQ.isLoading ? "Carregando…" : (
            <><strong className="text-foreground">{total}</strong> {total === 1 ? "resultado" : "resultados"}</>
          )}
        </p>
      </div>

      {listQ.isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border bg-card p-12 text-center">
          <Flag className="mx-auto h-10 w-10 text-muted-foreground/60" />
          <p className="mt-4 font-display text-xl">{title}</p>
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        </div>
      ) : (
        <>
          {items.map((it) => (
            <article key={it.id} className="rounded-lg border border-border bg-card p-5">
              <div className="flex gap-4 flex-wrap">
                {it.thumbnail_url && (
                  <img src={it.thumbnail_url} alt="" className="h-24 w-32 rounded object-cover" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 flex-wrap">
                    <div className="min-w-0">
                      <h2 className="font-display text-xl line-clamp-2">{it.title}</h2>
                      <p className="text-xs text-muted-foreground mt-1">
                        {it.subject_area} · {it.education_level} · ★ {Number(it.rating_avg).toFixed(1)} ({it.rating_count})
                      </p>
                    </div>
                    <Badge variant={it.status === "removed" ? "destructive" : "secondary"}>
                      {STATUS_LABEL[it.status] ?? it.status}
                    </Badge>
                  </div>

                  {it.pendingReports.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {it.pendingReports.map((r) => (
                        <div key={r.id} className="rounded bg-muted/50 px-3 py-2 text-xs">
                          <div className="flex items-center justify-between gap-2">
                            <strong className="text-foreground">{REASON_LABEL[r.reason] ?? r.reason}</strong>
                            <span className="text-muted-foreground">
                              {new Date(r.created_at).toLocaleDateString("pt-BR")}
                            </span>
                          </div>
                          {r.details && <p className="mt-1 text-muted-foreground">{r.details}</p>}
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="mt-4 flex gap-2 flex-wrap">
                    {showRestore && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setStatusMut.mutate({ reaId: it.id, status: "active" })}
                        disabled={setStatusMut.isPending}
                      >
                        {it.status === "removed" ? (
                          <><Undo2 className="h-4 w-4 mr-1.5" /> Desfazer remoção</>
                        ) : (
                          <><CheckCircle2 className="h-4 w-4 mr-1.5" /> Restaurar</>
                        )}
                      </Button>
                    )}
                    {showSendToReview && it.status === "active" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setStatusMut.mutate({ reaId: it.id, status: "blocked_review" })}
                        disabled={setStatusMut.isPending}
                      >
                        <Flag className="h-4 w-4 mr-1.5" /> Enviar à revisão
                      </Button>
                    )}
                    {showRemove && it.status !== "removed" && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => {
                          if (confirm("Remover este REA?")) {
                            setStatusMut.mutate({ reaId: it.id, status: "removed" });
                          }
                        }}
                        disabled={setStatusMut.isPending}
                      >
                        <Trash2 className="h-4 w-4 mr-1.5" /> Remover
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </article>
          ))}

          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}>
                <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
              </Button>
              <span className="text-sm text-muted-foreground px-3">
                Página <strong className="text-foreground">{page + 1}</strong> de {totalPages}
              </span>
              <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}>
                Próxima <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
