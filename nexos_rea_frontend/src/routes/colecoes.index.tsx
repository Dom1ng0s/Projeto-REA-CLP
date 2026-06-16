import { useState } from "react";
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderOpen, Globe, Lock, Plus, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import type { CollectionRow, CollectionVisibility } from "@/lib/types/profile";

export const Route = createFileRoute("/colecoes/")({
  beforeLoad: async () => {
    const { data } = await supabase.auth.getUser();
    if (!data.user) throw redirect({ to: "/login" });
  },
  component: CollectionsListPage,
  head: () => ({ meta: [{ title: "Minhas coleções — Nexos REA" }] }),
});

function CollectionsListPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<CollectionVisibility>("private");

  const collectionsQ = useQuery({
    enabled: !!user,
    queryKey: ["my-collections", user?.id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("collections" as any)
        .select("*")
        .eq("user_id", user!.id)
        .order("is_system", { ascending: false })
        .order("updated_at", { ascending: false });
      if (error) throw error;
      return (data as unknown as (CollectionRow & { is_system?: boolean })[]) ?? [];
    },
  });


  const createMut = useMutation({
    mutationFn: async () => {
      const { data, error } = await supabase
        .from("collections" as any)
        .insert({
          user_id: user!.id,
          title: title.trim(),
          description: description.trim() || null,
          visibility,
        })
        .select("*")
        .single();
      if (error) throw error;
      return data as unknown as CollectionRow;
    },
    onSuccess: () => {
      toast.success("Coleção criada");
      setOpen(false);
      setTitle(""); setDescription(""); setVisibility("private");
      qc.invalidateQueries({ queryKey: ["my-collections"] });
    },
    onError: (e: Error) => toast.error("Erro ao criar", { description: e.message }),
  });

  if (!user) return null;

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 py-10 space-y-8">
      <header className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-display text-4xl text-foreground">Minhas coleções</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Organize os REAs que importam para você. Coleções públicas podem ser compartilhadas via link.
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="h-4 w-4 mr-2" /> Nova coleção</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-display">Nova coleção</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4">
              <div className="grid gap-1.5">
                <Label htmlFor="t">Título</Label>
                <Input id="t" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={120} />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="d">Descrição (opcional)</Label>
                <Input id="d" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={400} />
              </div>
              <div className="grid gap-1.5">
                <Label>Visibilidade</Label>
                <Select value={visibility} onValueChange={(v) => setVisibility(v as CollectionVisibility)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="private">Privada (apenas você)</SelectItem>
                    <SelectItem value="public">Pública (qualquer pessoa com o link)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>Cancelar</Button>
              <Button
                onClick={() => createMut.mutate()}
                disabled={!title.trim() || createMut.isPending}
              >
                Criar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </header>

      {collectionsQ.isLoading ? (
        <div className="flex items-center justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
      ) : (collectionsQ.data?.length ?? 0) === 0 ? (
        <div className="rounded-lg border border-dashed border-border py-16 text-center">
          <FolderOpen className="mx-auto h-10 w-10 text-muted-foreground/60" />
          <p className="mt-4 font-display text-xl">Nenhuma coleção ainda</p>
          <p className="text-sm text-muted-foreground">Crie sua primeira coleção para começar a salvar REAs.</p>
        </div>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {collectionsQ.data!.map((c) => (
            <li key={c.id}>
              <Link
                to="/colecoes/$id"
                params={{ id: c.id }}
                className="block h-full rounded-lg border border-border bg-card p-5 transition-all hover:border-primary/40 hover:shadow-md"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-display text-xl line-clamp-2">
                    {c.is_system ? "❤️ " : ""}{c.title}
                  </h3>
                  {c.is_system ? (
                    <Badge variant="secondary" className="shrink-0 text-[10px]">Sistema</Badge>
                  ) : c.visibility === "public" ? (
                    <Globe className="h-4 w-4 text-primary shrink-0" />
                  ) : (
                    <Lock className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                </div>

                {c.description && (
                  <p className="mt-2 text-sm text-muted-foreground line-clamp-3">{c.description}</p>
                )}
                <p className="mt-4 text-[10px] uppercase tracking-wide text-muted-foreground">
                  Atualizada em {new Date(c.updated_at).toLocaleDateString("pt-BR")}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
