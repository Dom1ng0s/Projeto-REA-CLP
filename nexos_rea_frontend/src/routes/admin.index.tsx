import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { Loader2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/admin/")({
  component: AdminDashboard,
});

type Metrics = {
  activeReasCount: number;
  pendingReviewCount: number;
  removedCount: number;
  ctrAvg30d: number;
  ctrSeries: Array<{ bucketStart: string; impressions: number; clicks: number; ctr: number }>;
};

function AdminDashboard() {
  const metricsQ = useQuery({
    queryKey: ["admin-metrics"],
    queryFn: async () => {
      const { data, error } = await supabase.rpc("get_admin_metrics" as any);
      if (error) throw error;
      return data as unknown as Metrics;
    },
  });

  if (metricsQ.isLoading) {
    return <div className="flex items-center justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;
  }
  if (metricsQ.error || !metricsQ.data) {
    return <p className="text-sm text-destructive">Erro ao carregar métricas.</p>;
  }

  const m = metricsQ.data;
  const cards: Array<{ label: string; value: number; tone: string; href?: "/admin/moderacao" | "/admin/removidos" }> = [
    { label: "REAs ativos", value: m.activeReasCount, tone: "text-foreground" },
    { label: "Sob revisão", value: m.pendingReviewCount, tone: "text-blue-600", href: "/admin/moderacao" },
    { label: "Removidos", value: m.removedCount, tone: "text-destructive", href: "/admin/removidos" },
  ];

  const series = (m.ctrSeries ?? []).map((s) => ({
    day: new Date(s.bucketStart).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
    impressions: s.impressions,
    clicks: s.clicks,
    ctr: Math.round(Number(s.ctr) * 10000) / 100,
  }));

  const totalClicks = series.reduce((a, s) => a + s.clicks, 0);
  const totalImpressions = series.reduce((a, s) => a + s.impressions, 0);
  const noActivity = totalClicks === 0 && totalImpressions === 0;

  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => (
          <div key={c.label} className="rounded-lg border border-border bg-card p-5">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">{c.label}</p>
            <p className={`mt-2 font-display text-4xl ${c.tone}`}>{c.value ?? 0}</p>
            {c.href && (
              <Button asChild variant="ghost" size="sm" className="mt-2 -ml-2 h-7 px-2 text-xs">
                <Link to={c.href}>
                  Ver lista <ArrowRight className="h-3 w-3 ml-1" />
                </Link>
              </Button>
            )}
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <h2 className="font-display text-xl mb-1">CTR — últimos 30 dias</h2>
        <p className="text-xs text-muted-foreground mb-4">
          Média 30d: <strong className="text-foreground">{(Number(m.ctrAvg30d) * 100).toFixed(2)}%</strong>
        </p>
        <div className="relative h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={series}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" fontSize={11} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} />
              <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }} />
              <Line type="monotone" dataKey="clicks" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} name="Cliques" />
              <Line type="monotone" dataKey="impressions" stroke="hsl(var(--accent))" strokeWidth={2} dot={false} name="Eventos" />
            </LineChart>
          </ResponsiveContainer>
          {noActivity && (
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="rounded-md border border-dashed border-border bg-background/80 px-4 py-2 text-sm text-muted-foreground backdrop-blur">
                Nenhum clique nos últimos 30 dias
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
