import { useEffect, useMemo, useState } from "react";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Save } from "lucide-react";
import { toast } from "sonner";

import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import type { Tag, UserInterestRow } from "@/lib/types/profile";

export const Route = createFileRoute("/perfil")({
  beforeLoad: async () => {
    const { data } = await supabase.auth.getUser();
    if (!data.user) throw redirect({ to: "/login" });
  },
  component: PerfilPage,
  head: () => ({ meta: [{ title: "Meu perfil — Nexos REA" }] }),
});

function PerfilPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [selectedTagIds, setSelectedTagIds] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState("");

  useEffect(() => {
    if (!user) navigate({ to: "/login" });
  }, [user, navigate]);

  const profileQ = useQuery({
    enabled: !!user,
    queryKey: ["profile", user?.id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("profiles").select("*").eq("id", user!.id).maybeSingle();
      if (error) throw error;
      return data;
    },
  });

  const tagsQ = useQuery({
    queryKey: ["tags"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("tags" as any).select("*").order("label");
      if (error) throw error;
      return (data as unknown as Tag[]) ?? [];
    },
  });

  const interestsQ = useQuery({
    enabled: !!user,
    queryKey: ["user-interests", user?.id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("user_interests" as any).select("*").eq("user_id", user!.id);
      if (error) throw error;
      return (data as unknown as UserInterestRow[]) ?? [];
    },
  });

  useEffect(() => {
    if (profileQ.data) {
      setDisplayName(profileQ.data.display_name ?? "");
      setBio(profileQ.data.bio ?? "");
      setAvatarUrl(profileQ.data.avatar_url ?? "");
    }
  }, [profileQ.data]);

  useEffect(() => {
    if (interestsQ.data) setSelectedTagIds(new Set(interestsQ.data.map((i) => i.tag_id)));
  }, [interestsQ.data]);

  const filteredTags = useMemo(() => {
    const q = filter.trim().toLowerCase();
    return (tagsQ.data ?? []).filter((t) => !q || t.label.toLowerCase().includes(q) || t.slug.includes(q));
  }, [tagsQ.data, filter]);

  const saveProfileMut = useMutation({
    mutationFn: async () => {
      const { error } = await supabase
        .from("profiles")
        .update({ display_name: displayName || null, bio: bio || null, avatar_url: avatarUrl || null })
        .eq("id", user!.id);
      if (error) throw error;
    },
    onSuccess: () => {
      toast.success("Perfil atualizado");
      qc.invalidateQueries({ queryKey: ["profile"] });
    },
    onError: (e: Error) => toast.error("Erro", { description: e.message }),
  });

  const saveInterestsMut = useMutation({
    mutationFn: async () => {
      const current = new Set((interestsQ.data ?? []).map((i) => i.tag_id));
      const toAdd = [...selectedTagIds].filter((id) => !current.has(id));
      const toRemove = [...current].filter((id) => !selectedTagIds.has(id));

      if (toRemove.length) {
        const { error } = await supabase
          .from("user_interests" as any)
          .delete()
          .eq("user_id", user!.id)
          .in("tag_id", toRemove);
        if (error) throw error;
      }
      if (toAdd.length) {
        const { error } = await supabase
          .from("user_interests" as any)
          .insert(toAdd.map((tag_id) => ({ user_id: user!.id, tag_id, source: "manual" })));
        if (error) throw error;
      }
    },
    onSuccess: () => {
      toast.success("Interesses atualizados");
      qc.invalidateQueries({ queryKey: ["user-interests"] });
    },
    onError: (e: Error) => toast.error("Erro", { description: e.message }),
  });

  function toggleTag(id: string) {
    setSelectedTagIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  if (!user) return null;

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 space-y-10">
      <header>
        <h1 className="font-display text-4xl text-foreground">Meu perfil</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Seus interesses alimentam o motor de recomendação adaptativo.
        </p>
      </header>

      <section className="space-y-4 rounded-lg border border-border bg-card p-6">
        <h2 className="font-display text-2xl">Dados</h2>
        <div className="grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="dn">Nome de exibição</Label>
            <Input id="dn" value={displayName} onChange={(e) => setDisplayName(e.target.value)} maxLength={80} />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="bio">Bio</Label>
            <Textarea id="bio" value={bio} onChange={(e) => setBio(e.target.value)} rows={3} maxLength={400} />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="av">URL do avatar</Label>
            <Input id="av" value={avatarUrl} onChange={(e) => setAvatarUrl(e.target.value)} placeholder="https://..." />
          </div>
        </div>
        <div className="flex justify-end">
          <Button onClick={() => saveProfileMut.mutate()} disabled={saveProfileMut.isPending}>
            {saveProfileMut.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            Salvar perfil
          </Button>
        </div>
      </section>

      <section className="space-y-4 rounded-lg border border-border bg-card p-6">
        <div className="flex items-end justify-between gap-3">
          <div>
            <h2 className="font-display text-2xl">Interesses</h2>
            <p className="text-sm text-muted-foreground">
              Selecionados: <strong>{selectedTagIds.size}</strong>
            </p>
          </div>
          <Button onClick={() => saveInterestsMut.mutate()} disabled={saveInterestsMut.isPending}>
            {saveInterestsMut.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            Salvar interesses
          </Button>
        </div>
        <Input placeholder="Buscar tag..." value={filter} onChange={(e) => setFilter(e.target.value)} />
        {tagsQ.isLoading ? (
          <div className="flex items-center justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
        ) : filteredTags.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">Nenhuma tag encontrada.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {filteredTags.map((t) => {
              const active = selectedTagIds.has(t.id);
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => toggleTag(t.id)}
                  className="transition-transform active:scale-95"
                >
                  <Badge
                    variant={active ? "default" : "outline"}
                    className="cursor-pointer text-xs"
                  >
                    {t.label}
                  </Badge>
                </button>
              );
            })}
          </div>
        )}
      </section>

      <PreferencesSection userId={user.id} />
      <HistorySection userId={user.id} />
    </div>
  );
}

function PreferencesSection({ userId }: { userId: string }) {
  const qc = useQueryClient();
  const prefQ = useQuery({
    queryKey: ["profile-skip-warning", userId],
    queryFn: async () => {
      const { data } = await supabase
        .from("profiles")
        .select("skip_external_warning")
        .eq("id", userId)
        .maybeSingle();
      return data?.skip_external_warning ?? false;
    },
  });
  const toggleMut = useMutation({
    mutationFn: async (v: boolean) => {
      const { error } = await supabase
        .from("profiles")
        .update({ skip_external_warning: v })
        .eq("id", userId);
      if (error) throw error;
      return v;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profile-skip-warning"] });
      toast.success("Preferência atualizada");
    },
    onError: (e: Error) => toast.error("Erro", { description: e.message }),
  });

  return (
    <section className="space-y-4 rounded-lg border border-border bg-card p-6">
      <h2 className="font-display text-2xl">Preferências</h2>
      <div className="flex items-center justify-between gap-4">
        <div className="space-y-0.5">
          <Label htmlFor="ext-warn" className="text-sm">
            Avisar antes de abrir links externos
          </Label>
          <p className="text-xs text-muted-foreground">
            Mostra um aviso ao clicar em um REA antes de abrir o conteúdo em um site externo.
          </p>
        </div>
        <Switch
          id="ext-warn"
          checked={!prefQ.data}
          disabled={toggleMut.isPending}
          onCheckedChange={(v) => toggleMut.mutate(!v)}
        />
      </div>
    </section>
  );
}

function HistorySection({ userId }: { userId: string }) {
  const historyQ = useQuery({
    queryKey: ["view-history", userId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("rea_interactions" as any)
        .select("rea_id, created_at, reas(id, title, thumbnail_url, subject_area)")
        .eq("user_id", userId)
        .eq("event_type", "view")
        .order("created_at", { ascending: false })
        .limit(50);
      if (error) throw error;
      const seen = new Set<string>();
      const out: any[] = [];
      for (const r of (data ?? []) as any[]) {
        if (seen.has(r.rea_id) || !r.reas) continue;
        seen.add(r.rea_id);
        out.push(r);
        if (out.length >= 20) break;
      }
      return out;
    },
  });

  return (
    <section className="space-y-4 rounded-lg border border-border bg-card p-6">
      <h2 className="font-display text-2xl">Histórico de visualizações</h2>
      <p className="text-sm text-muted-foreground">Últimos 20 REAs que você acessou.</p>
      {historyQ.isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : (historyQ.data?.length ?? 0) === 0 ? (
        <p className="text-sm text-muted-foreground py-2">Nenhuma visualização registrada ainda.</p>
      ) : (
        <ul className="divide-y divide-border">
          {historyQ.data!.map((h: any) => (
            <li key={h.rea_id} className="flex items-center gap-3 py-2.5">
              {h.reas.thumbnail_url ? (
                <img src={h.reas.thumbnail_url} alt="" className="h-10 w-14 rounded object-cover shrink-0" />
              ) : (
                <div className="h-10 w-14 rounded bg-muted shrink-0" />
              )}
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{h.reas.title}</p>
                <p className="text-xs text-muted-foreground">
                  {h.reas.subject_area} · {new Date(h.created_at).toLocaleString("pt-BR")}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

