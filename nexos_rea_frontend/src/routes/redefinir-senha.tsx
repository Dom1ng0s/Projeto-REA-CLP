import { useEffect, useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { z } from "zod";
import { Loader2, KeyRound } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { AuthShell } from "@/components/AuthShell";

export const Route = createFileRoute("/redefinir-senha")({
  head: () => ({
    meta: [{ title: "Redefinir senha — Nexos REA" }],
  }),
  component: ResetPasswordPage,
});

const schema = z
  .object({
    password: z.string().min(8, "Use pelo menos 8 caracteres"),
    confirm: z.string(),
  })
  .refine((d) => d.password === d.confirm, {
    message: "As senhas não conferem",
    path: ["confirm"],
  });

function ResetPasswordPage() {
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [ready, setReady] = useState(false);

  // Supabase entrega tokens no hash; o cliente os processa automaticamente.
  // Aguardamos o evento PASSWORD_RECOVERY ou uma sessão válida antes de habilitar.
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === "PASSWORD_RECOVERY" || session) setReady(true);
      },
    );
    // Caso já estejamos com sessão na carga inicial
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) setReady(true);
    });
    return () => subscription.unsubscribe();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = schema.safeParse({ password, confirm });
    if (!parsed.success) {
      toast.error(parsed.error.issues[0]?.message ?? "Dados inválidos");
      return;
    }
    setSubmitting(true);
    const { error } = await supabase.auth.updateUser({
      password: parsed.data.password,
    });
    setSubmitting(false);
    if (error) {
      toast.error("Não foi possível atualizar a senha", {
        description: error.message,
      });
      return;
    }
    toast.success("Senha atualizada!");
    await supabase.auth.signOut();
    navigate({ to: "/login" });
  };

  return (
    <AuthShell
      title="Redefinir senha"
      subtitle="Defina uma nova senha para acessar sua conta."
    >
      {!ready ? (
        <div className="rounded-md border border-dashed border-border bg-muted/30 p-4 text-sm text-muted-foreground">
          Abra esta página pelo link enviado ao seu e-mail. Se já o fez, aguarde
          um instante…
          <div className="mt-3">
            <Link to="/recuperar-senha" className="text-primary hover:underline">
              Reenviar link
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="password">Nova senha</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="confirm">Confirmar nova senha</Label>
            <Input
              id="confirm"
              type="password"
              autoComplete="new-password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </div>
          <Button type="submit" className="w-full" disabled={submitting} size="lg">
            {submitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <KeyRound className="h-4 w-4 mr-2" /> Salvar nova senha
              </>
            )}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
