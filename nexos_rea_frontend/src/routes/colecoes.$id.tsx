import { useEffect, useState } from "react";
import { createFileRoute, Link, useNavigate, redirect } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Globe, Lock, Save, Share2, Trash2, Loader2, X } from "lucide-react";
import { toast } from "sonner";

import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ReaCard, ReaCardSkeleton } from "@/components/ReaCard";
import type { Database } from "@/integrations/supabase/types";
import type { CollectionRow, CollectionVisibility } from "@/lib/types/profile";

type Rea = Database["public"]["Tables"]["reas"]["Row"];

export const Route = createFileRoute("/colecoes/$id")({
  beforeLoad: async () => {
    const { data } = await supabase.auth.getUser();
    if (!data.user) throw redirect({ to: "/login" });
  },
  component: CollectionDetailPage,
});

function CollectionDetailPage() {
  const { id } = Route.useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const collectionQ = useQuery({
    enabled: !!user,
    queryKey: ["collection-detail", id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("collections" as any).select("*").eq("id", id).single();
      if (error) throw error;
      return data as unknown as CollectionRow;
    },
  });

  const itemsQ = useQuery({
    enabled: !!user,
    queryKey: ["collection-items", id],
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

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<CollectionVisibility>("private");

  useEffect(() => {
    if (collectionQ.data) {
      setTitle(collectionQ.data.title);
      setDescription(collectionQ.data.description ?? "");
      setVisibility(collectionQ.data.visibility);
    }
  }, [collectionQ.data]);

  const saveMut = useMutation({
    mutationFn: async () => {
      const { error } = await supabase
        .from("collections" as any)
        .update({ title: title.trim(), description: description.trim() || null, visibility })
        .eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => {
      toast.success("Coleção atualizada");
      qc.invalidateQueries({ queryKey: ["collection-detail", id] });
      qc.invalidateQueries({ queryKey: ["my-collections"] });
    },
    onError: (e: Error) => toast.error("Erro", { description: e.message }),
  });

  const removeItemMut = useMutation({
    mutationFn: async (reaId: string) => {
      const { error } = await supabase
        .from("collection_items" as any)
        .delete()
        .eq("collection_id", id)
        .eq("rea_id", reaId);
      if (error) throw error;
    },
    onSuccess: () => {
      toast.success("REA removido");
      qc.invalidateQueries({ queryKey: ["collection-items", id] });
    },
    onError: (e: Error) => toast.error("Erro", { description: e.message }),
  });

  const deleteMut = useMutation({
    mutationFn: async () => {
      const { error } = await supabase.from("collections" as any).delete().eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => {
      toast.success("Coleção excluída");
      qc.invalidateQueries({ queryKey: ["my-collections"] });
      navigate({ to: "/colecoes" });
    },
    onError: (e: Error) => toast.error("Erro", { description: e.message }),
  });

  function copyShareLink() {
    const url = `${window.location.origin}/c/${id}`;
    navigator.clipboard.writeText(url).then(
      () => toast.success("Link copiado", { description: url }),
      () => toast.error("Não foi possível copiar"),
    );
  }

  if (!user) return null;
  if (collectionQ.isLoading) {
    return <div className="flex items-center justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;
  }
  if (collectionQ.error || !collectionQ.data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center">
        <p className="text-muted-foreground">Coleção não encontrada ou sem permissão de acesso.</p>
        <Button asChild className="mt-4"><Link to="/colecoes">Voltar</Link></Button>
      </div>
    );
  }

  const items = itemsQ.data ?? [];
  const isSystem = !!(collectionQ.data as any)?.is_system;

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 py-10 space-y-8">
      <Link to="/colecoes" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4 mr-1" /> Voltar
      </Link>

      <section className="space-y-4 rounded-lg border border-border bg-card p-6">
        {isSystem ? (
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-destructive/10 text-destructive text-xl">
              ❤️
            </div>
            <div>
              <h1 className="font-display text-3xl">{collectionQ.data!.title}</h1>
              <p className="text-sm text-muted-foreground">
                Coleção automática do sistema. Não pode ser editada ou excluída.
              </p>
            </div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-start">
            <div className="grid gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="t">Título</Label>
                <Input id="t" value={title} onChange={(e) => setTitle(e.target.value)} className="font-display text-xl h-auto py-2" />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="d">Descrição</Label>
                <Textarea id="d" value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
              </div>
              <div className="grid gap-1.5 max-w-xs">
                <Label>Visibilidade</Label>
                <Select value={visibility} onValueChange={(v) => setVisibility(v as CollectionVisibility)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="private">
                      <span className="inline-flex items-center"><Lock className="h-3.5 w-3.5 mr-2" />Privada</span>
                    </SelectItem>
                    <SelectItem value="public">
                      <span className="inline-flex items-center"><Globe className="h-3.5 w-3.5 mr-2" />Pública</span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Button onClick={() => saveMut.mutate()} disabled={!title.trim() || saveMut.isPending}>
                {saveMut.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                Salvar
              </Button>
              {visibility === "public" && (
                <Button variant="outline" onClick={copyShareLink}>
                  <Share2 className="h-4 w-4 mr-2" /> Compartilhar
                </Button>
              )}
              <Button
                variant="ghost"
                className="text-destructive hover:text-destructive"
                onClick={() => {
                  if (confirm("Excluir esta coleção? Os itens serão removidos.")) deleteMut.mutate();
                }}
                disabled={deleteMut.isPending}
              >
                <Trash2 className="h-4 w-4 mr-2" /> Excluir
              </Button>
            </div>
          </div>
        )}
      </section>


      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-2xl">REAs ({items.length})</h2>
        </div>
        {itemsQ.isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => <ReaCardSkeleton key={i} />)}
          </div>
        ) : items.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border py-16 text-center">
            <p className="text-sm text-muted-foreground">Nenhum REA nesta coleção.</p>
            <Button asChild variant="outline" className="mt-4"><Link to="/catalogo">Explorar catálogo</Link></Button>
          </div>
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((it) => (
              <li key={it.rea_id} className="relative group">
                <ReaCard rea={it.reas} />
                <button
                  type="button"
                  onClick={() => removeItemMut.mutate(it.rea_id)}
                  disabled={removeItemMut.isPending}
                  className="absolute top-2 right-2 z-10 inline-flex h-7 w-7 items-center justify-center rounded-full bg-background/90 backdrop-blur border border-border opacity-0 transition-opacity group-hover:opacity-100 hover:bg-destructive hover:text-destructive-foreground"
                  aria-label="Remover da coleção"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
