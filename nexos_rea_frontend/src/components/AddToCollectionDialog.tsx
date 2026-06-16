import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Plus, Check, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { CollectionRow } from "@/lib/types/profile";
import { logInteraction } from "@/lib/interactions";

export function AddToCollectionDialog({ reaId, reaTitle }: { reaId: string; reaTitle: string }) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const qc = useQueryClient();

  const collectionsQ = useQuery({
    enabled: open && !!user,
    queryKey: ["my-collections", user?.id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("collections" as any)
        .select("*")
        .eq("user_id", user!.id)
        .order("updated_at", { ascending: false });
      if (error) throw error;
      return (data as unknown as CollectionRow[]) ?? [];
    },
  });

  const membershipQ = useQuery({
    enabled: open && !!user,
    queryKey: ["collection-membership", reaId, user?.id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("collection_items" as any)
        .select("collection_id")
        .eq("rea_id", reaId);
      if (error) throw error;
      return new Set((data as unknown as { collection_id: string }[]).map((r) => r.collection_id));
    },
  });

  const toggleMut = useMutation({
    mutationFn: async ({ collectionId, present }: { collectionId: string; present: boolean }) => {
      if (present) {
        const { error } = await supabase
          .from("collection_items" as any)
          .delete()
          .eq("collection_id", collectionId)
          .eq("rea_id", reaId);
        if (error) throw error;
        void logInteraction(reaId, "remove_from_collection");
      } else {
        const { error } = await supabase
          .from("collection_items" as any)
          .insert({ collection_id: collectionId, rea_id: reaId, position: 0 });
        if (error) throw error;
        void logInteraction(reaId, "save_to_collection");
      }
    },
    onSuccess: (_d, vars) => {
      toast.success(vars.present ? "Removido da coleção" : "Adicionado à coleção");
      qc.invalidateQueries({ queryKey: ["collection-membership", reaId] });
      qc.invalidateQueries({ queryKey: ["collection-detail"] });
    },
    onError: (e: Error) => toast.error("Erro", { description: e.message }),
  });

  const createMut = useMutation({
    mutationFn: async (title: string) => {
      const { data, error } = await supabase
        .from("collections" as any)
        .insert({ user_id: user!.id, title })
        .select("*")
        .single();
      if (error) throw error;
      const created = data as unknown as CollectionRow;
      const { error: e2 } = await supabase
        .from("collection_items" as any)
        .insert({ collection_id: created.id, rea_id: reaId, position: 0 });
      if (e2) throw e2;
      void logInteraction(reaId, "save_to_collection");
      return created;
    },
    onSuccess: () => {
      toast.success("Coleção criada e REA adicionado");
      setNewTitle("");
      qc.invalidateQueries({ queryKey: ["my-collections"] });
      qc.invalidateQueries({ queryKey: ["collection-membership", reaId] });
    },
    onError: (e: Error) => toast.error("Erro ao criar", { description: e.message }),
  });

  if (!user) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <Button asChild variant="ghost" size="icon" className="h-8 w-8" aria-label="Salvar em coleção">
            <Link to="/login"><Plus className="h-4 w-4" /></Link>
          </Button>
        </TooltipTrigger>
        <TooltipContent>Salvar em coleção</TooltipContent>
      </Tooltip>
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <Tooltip>
        <TooltipTrigger asChild>
          <DialogTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              aria-label="Salvar em coleção"
              onClick={(e) => e.stopPropagation()}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </DialogTrigger>
        </TooltipTrigger>
        <TooltipContent>Salvar em coleção</TooltipContent>
      </Tooltip>
      <DialogContent onClick={(e) => e.stopPropagation()}>
        <DialogHeader>
          <DialogTitle className="font-display">Adicionar à coleção</DialogTitle>
          <DialogDescription className="line-clamp-2">{reaTitle}</DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <Label className="text-xs uppercase tracking-wide text-muted-foreground">Suas coleções</Label>
          <ScrollArea className="h-56 rounded-md border border-border">
            {collectionsQ.isLoading ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            ) : (collectionsQ.data?.length ?? 0) === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-muted-foreground">
                Você ainda não criou nenhuma coleção.
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {collectionsQ.data!.map((c) => {
                  const present = membershipQ.data?.has(c.id) ?? false;
                  return (
                    <li key={c.id}>
                      <button
                        type="button"
                        onClick={() => toggleMut.mutate({ collectionId: c.id, present })}
                        disabled={toggleMut.isPending}
                        className="flex w-full items-center justify-between gap-3 px-3 py-2.5 text-left text-sm transition-colors hover:bg-secondary/60"
                      >
                        <div className="min-w-0">
                          <div className="truncate font-medium">{c.title}</div>
                          <div className="text-xs text-muted-foreground">
                            {c.visibility === "public" ? "Pública" : "Privada"}
                          </div>
                        </div>
                        {present && <Check className="h-4 w-4 text-primary" />}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </ScrollArea>

          <div className="space-y-2 border-t border-border pt-3">
            <Label htmlFor="new-collection" className="text-xs uppercase tracking-wide text-muted-foreground">
              Criar nova coleção
            </Label>
            <div className="flex gap-2">
              <Input
                id="new-collection"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Ex.: Para revisar"
                maxLength={120}
              />
              <Button
                type="button"
                onClick={() => newTitle.trim() && createMut.mutate(newTitle.trim())}
                disabled={!newTitle.trim() || createMut.isPending}
              >
                Criar
              </Button>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Fechar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
