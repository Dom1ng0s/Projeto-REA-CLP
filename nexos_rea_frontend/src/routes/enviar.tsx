import { useState, useRef } from "react";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import { submitRea } from "@/lib/flask-api";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  formatOptions,
  licenseOptions,
  languageOptions,
  educationOptions,
} from "@/lib/rea-labels";

export const Route = createFileRoute("/enviar")({
  beforeLoad: async () => {
    const { data } = await supabase.auth.getUser();
    if (!data.user) throw redirect({ to: "/login" });
  },
  head: () => ({
    meta: [{ title: "Enviar REA — Nexos REA" }],
  }),
  component: EnviarPage,
});

const EMPTY = {
  title: "",
  resource_url: "",
  format: "",
  license: "",
  subject_area: "",
  education_level: "",
  description: "",
  author: "",
  language: "pt_br",
  thumbnail_url: "",
};

function EnviarPage() {
  const { session } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState(EMPTY);
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const tagRef = useRef<HTMLInputElement>(null);

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

  const mutation = useMutation({
    mutationFn: async () => {
      if (!session?.access_token) throw new Error("Sessão expirada. Faça login novamente.");
      return submitRea(
        {
          title: form.title.trim(),
          resource_url: form.resource_url.trim(),
          format: form.format,
          license: form.license,
          subject_area: form.subject_area,
          education_level: form.education_level,
          description: form.description.trim() || undefined,
          author: form.author.trim() || undefined,
          language: form.language || "pt_br",
          thumbnail_url: form.thumbnail_url.trim() || undefined,
          tags,
        },
        session.access_token,
      );
    },
    onSuccess: () => {
      toast.success("REA enviado com sucesso!");
      navigate({ to: "/catalogo" });
    },
    onError: (e: Error) => {
      toast.error("Erro ao enviar", { description: e.message });
    },
  });

  function set(field: keyof typeof EMPTY, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function addTag() {
    const raw = tagInput.trim().toLowerCase().replace(/\s+/g, "-");
    if (raw && !tags.includes(raw)) setTags((t) => [...t, raw]);
    setTagInput("");
  }

  function handleTagKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag();
    }
  }

  function removeTag(tag: string) {
    setTags((t) => t.filter((x) => x !== tag));
  }

  const requiredFilled =
    form.title.trim() &&
    form.resource_url.trim() &&
    form.format &&
    form.license &&
    form.subject_area &&
    form.education_level;

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 md:py-14">
      <header className="mb-8">
        <h1 className="font-display text-4xl md:text-5xl text-foreground">Enviar REA</h1>
        <p className="mt-2 text-muted-foreground">
          Compartilhe um Recurso Educacional Aberto com a comunidade.
        </p>
      </header>

      <div className="space-y-6">
        {/* Informações básicas */}
        <section className="rounded-lg border border-border bg-card p-6 space-y-4">
          <h2 className="font-medium text-foreground">Informações básicas</h2>

          <div className="space-y-1.5">
            <Label htmlFor="title">
              Título <span className="text-destructive">*</span>
            </Label>
            <Input
              id="title"
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
              placeholder="Nome do recurso"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="resource_url">
              URL do recurso <span className="text-destructive">*</span>
            </Label>
            <Input
              id="resource_url"
              type="url"
              value={form.resource_url}
              onChange={(e) => set("resource_url", e.target.value)}
              placeholder="https://..."
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="description">Descrição</Label>
            <Textarea
              id="description"
              rows={4}
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              placeholder="Descreva o recurso brevemente…"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="author">Autor</Label>
            <Input
              id="author"
              value={form.author}
              onChange={(e) => set("author", e.target.value)}
              placeholder="Nome do autor ou organização"
            />
          </div>
        </section>

        {/* Classificação */}
        <section className="rounded-lg border border-border bg-card p-6 space-y-4">
          <h2 className="font-medium text-foreground">Classificação</h2>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>
                Área do conhecimento <span className="text-destructive">*</span>
              </Label>
              <Select value={form.subject_area} onValueChange={(v) => set("subject_area", v)}>
                <SelectTrigger><SelectValue placeholder="Selecione…" /></SelectTrigger>
                <SelectContent>
                  {(subjectAreas ?? []).map((s) => (
                    <SelectItem key={s.slug} value={s.label}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>
                Nível de ensino <span className="text-destructive">*</span>
              </Label>
              <Select value={form.education_level} onValueChange={(v) => set("education_level", v)}>
                <SelectTrigger><SelectValue placeholder="Selecione…" /></SelectTrigger>
                <SelectContent>
                  {educationOptions.map(([v, label]) => (
                    <SelectItem key={v} value={v}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>
                Formato <span className="text-destructive">*</span>
              </Label>
              <Select value={form.format} onValueChange={(v) => set("format", v)}>
                <SelectTrigger><SelectValue placeholder="Selecione…" /></SelectTrigger>
                <SelectContent>
                  {formatOptions.map(([v, label]) => (
                    <SelectItem key={v} value={v}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>
                Licença <span className="text-destructive">*</span>
              </Label>
              <Select value={form.license} onValueChange={(v) => set("license", v)}>
                <SelectTrigger><SelectValue placeholder="Selecione…" /></SelectTrigger>
                <SelectContent>
                  {licenseOptions.map(([v, label]) => (
                    <SelectItem key={v} value={v}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>Idioma</Label>
              <Select value={form.language} onValueChange={(v) => set("language", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {languageOptions.map(([v, label]) => (
                    <SelectItem key={v} value={v}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Tags */}
          <div className="space-y-1.5">
            <Label htmlFor="tags">Tags</Label>
            <div className="flex flex-wrap gap-1.5 mb-1.5">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-foreground"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
                    className="ml-0.5 text-muted-foreground hover:text-foreground"
                    aria-label={`Remover tag ${tag}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <Input
              id="tags"
              ref={tagRef}
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={handleTagKey}
              onBlur={addTag}
              placeholder="Digite uma tag e pressione Enter"
            />
            <p className="text-xs text-muted-foreground">Pressione Enter ou vírgula para adicionar.</p>
          </div>
        </section>

        {/* Mídia */}
        <section className="rounded-lg border border-border bg-card p-6 space-y-4">
          <h2 className="font-medium text-foreground">Mídia</h2>
          <div className="space-y-1.5">
            <Label htmlFor="thumbnail_url">URL da miniatura</Label>
            <Input
              id="thumbnail_url"
              type="url"
              value={form.thumbnail_url}
              onChange={(e) => set("thumbnail_url", e.target.value)}
              placeholder="https://... (imagem de capa)"
            />
          </div>
        </section>

        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-muted-foreground">
            <span className="text-destructive">*</span> Campos obrigatórios
          </p>
          <Button
            onClick={() => mutation.mutate()}
            disabled={!requiredFilled || mutation.isPending}
            size="lg"
          >
            {mutation.isPending ? "Enviando…" : "Enviar REA"}
          </Button>
        </div>
      </div>
    </div>
  );
}
