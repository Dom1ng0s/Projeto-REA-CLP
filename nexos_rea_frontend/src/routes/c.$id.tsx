import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Globe, Loader2 } from "lucide-react";

import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { ReaCard, ReaCardSkeleton } from "@/components/ReaCard";
import type { Database } from "@/integrations/supabase/types";
import type { CollectionRow } from "@/lib/types/profile";

type Rea = Database["public"]["Tables"]["reas"]["Row"];

export const Route = createFileRoute("/c/$id")({
  component: PublicCollectionPage,
  head: () => ({
    meta: [
      { title: `Coleção pública — Nexos REA` },
      { name: "description", content: `Coleção compartilhada de Recursos Educacionais Abertos.` },
    ],
  }),
});

function PublicCollectionPage() {
  const { id } = Route.useParams();

  const collectionQ = useQuery({
    queryKey: ["public-collection", id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("collections" as any)
        .select("*")
        .eq("id", id)
        .eq("visibility", "public")
        .maybeSingle();
      if (error) throw error;
      return data as unknown as CollectionRow | null;
    },
  });

  const itemsQ = useQuery({
    enabled: !!collectionQ.data,
    queryKey: ["public-collection-items", id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("collection_items" as any)
        .select("rea_id, position, reas(*)")
        .eq("collection_id", id)
        .order("position", { ascending: true });
      if (error) throw error;
      return (data as unknown as { rea_id: string; position: number; reas: Rea }[]) ?? [];
    },
  });

  if (collectionQ.isLoading) {
    return <div className="flex items-center justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;
  }

  if (!collectionQ.data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center">
        <h1 className="font-display text-3xl">Coleção indisponível</h1>
        <p className="mt-2 text-muted-foreground">
          Esta coleção não existe ou não está pública.
        </p>
        <Button asChild className="mt-6"><Link to="/catalogo">Explorar catálogo</Link></Button>
      </div>
    );
  }

  const c = collectionQ.data;
  const items = itemsQ.data ?? [];

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 py-10 space-y-8">
      <header className="space-y-3">
        <div className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
          <Globe className="h-3.5 w-3.5" /> Coleção pública
        </div>
        <h1 className="font-display text-5xl text-foreground">{c.title}</h1>
        {c.description && (
          <p className="max-w-2xl text-muted-foreground">{c.description}</p>
        )}
      </header>

      <section className="space-y-4">
        <h2 className="font-display text-2xl">REAs ({items.length})</h2>
        {itemsQ.isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => <ReaCardSkeleton key={i} />)}
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground py-8">Esta coleção ainda não tem REAs.</p>
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((it) => <li key={it.rea_id}><ReaCard rea={it.reas} /></li>)}
          </ul>
        )}
      </section>
    </div>
  );
}
