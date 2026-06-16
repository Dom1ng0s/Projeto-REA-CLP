import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { z } from "zod";
import { Loader2, LogIn, UserPlus, Mail, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Mode = "login" | "register" | "recover";

const loginSchema = z.object({
  email: z.string().email("E-mail inválido"),
  password: z.string().min(6, "Mínimo de 6 caracteres"),
});

const registerSchema = z.object({
  displayName: z.string().min(2, "Informe seu nome").max(80, "Nome muito longo"),
  email: z.string().email("E-mail inválido"),
  password: z.string().min(8, "Use pelo menos 8 caracteres"),
});

export function HomeAuthPanel() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("login");
  const [submitting, setSubmitting] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = loginSchema.safeParse({ email, password });
    if (!parsed.success) {
      toast.error(parsed.error.issues[0]?.message ?? "Dados inválidos");
      return;
    }
    setSubmitting(true);
    const { error } = await supabase.auth.signInWithPassword(parsed.data);
    setSubmitting(false);
    if (error) {
      toast.error("Não foi possível entrar", { description: error.message });
      return;
    }
    toast.success("Bem-vindo de volta!");
    navigate({ to: "/catalogo" });
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = registerSchema.safeParse({ displayName, email, password });
    if (!parsed.success) {
      toast.error(parsed.error.issues[0]?.message ?? "Dados inválidos");
      return;
    }
    setSubmitting(true);
    const { data, error } = await supabase.auth.signUp({
      email: parsed.data.email,
      password: parsed.data.password,
      options: {
        emailRedirectTo: `${window.location.origin}/`,
        data: { display_name: parsed.data.displayName },
      },
    });
    setSubmitting(false);
    if (error) {
      toast.error("Não foi possível criar a conta", { description: error.message });
      return;
    }
    if (data.session) {
      toast.success("Conta criada com sucesso!");
      navigate({ to: "/catalogo" });
    } else {
      toast.success("Conta criada!", {
        description: "Verifique seu e-mail para confirmar o cadastro.",
      });
      setMode("login");
    }
  };

  const handleRecover = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = z.string().email("E-mail inválido").safeParse(email);
    if (!parsed.success) {
      toast.error(parsed.error.issues[0]?.message);
      return;
    }
    setSubmitting(true);
    const { error } = await supabase.auth.resetPasswordForEmail(parsed.data, {
      redirectTo: `${window.location.origin}/redefinir-senha`,
    });
    setSubmitting(false);
    if (error) {
      toast.error("Erro", { description: error.message });
      return;
    }
    toast.success("E-mail enviado", {
      description: "Verifique sua caixa de entrada para redefinir a senha.",
    });
    setMode("login");
  };

  return (
    <div className="w-full max-w-md">
      <div className="rounded-xl border border-border bg-card/95 backdrop-blur p-6 sm:p-8 shadow-lg">
        {mode === "login" && (
          <>
            <h2 className="font-display text-2xl text-card-foreground">Entrar</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Acesse sua conta para avaliar e salvar recursos.
            </p>
            <form onSubmit={handleLogin} className="mt-5 space-y-4" noValidate>
              <div className="space-y-1.5">
                <Label htmlFor="email-login">E-mail</Label>
                <Input
                  id="email-login"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="voce@exemplo.com"
                />
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="pass-login">Senha</Label>
                  <button
                    type="button"
                    onClick={() => setMode("recover")}
                    className="text-xs text-primary hover:underline"
                  >
                    Esqueci minha senha
                  </button>
                </div>
                <Input
                  id="pass-login"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <Button type="submit" className="w-full" disabled={submitting} size="lg">
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : (
                  <><LogIn className="h-4 w-4 mr-2" /> Entrar</>
                )}
              </Button>
            </form>
            <p className="mt-5 text-center text-sm text-muted-foreground">
              Ainda não tem conta?{" "}
              <button
                type="button"
                onClick={() => setMode("register")}
                className="text-primary font-medium hover:underline"
              >
                Criar conta
              </button>
            </p>
          </>
        )}

        {mode === "register" && (
          <>
            <h2 className="font-display text-2xl text-card-foreground">Criar conta</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Gratuita. Em segundos. Sem cartão de crédito.
            </p>
            <form onSubmit={handleRegister} className="mt-5 space-y-4" noValidate>
              <div className="space-y-1.5">
                <Label htmlFor="name-reg">Nome</Label>
                <Input
                  id="name-reg"
                  type="text"
                  autoComplete="name"
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Como prefere ser chamado(a)"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="email-reg">E-mail</Label>
                <Input
                  id="email-reg"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="voce@exemplo.com"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="pass-reg">Senha</Label>
                <Input
                  id="pass-reg"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">Mínimo de 8 caracteres.</p>
              </div>
              <Button type="submit" className="w-full" disabled={submitting} size="lg">
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : (
                  <><UserPlus className="h-4 w-4 mr-2" /> Criar conta</>
                )}
              </Button>
            </form>
            <p className="mt-5 text-center text-sm text-muted-foreground">
              Já tem conta?{" "}
              <button
                type="button"
                onClick={() => setMode("login")}
                className="text-primary font-medium hover:underline"
              >
                Entrar
              </button>
            </p>
          </>
        )}

        {mode === "recover" && (
          <>
            <button
              type="button"
              onClick={() => setMode("login")}
              className="mb-3 inline-flex items-center text-xs text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="h-3 w-3 mr-1" /> Voltar
            </button>
            <h2 className="font-display text-2xl text-card-foreground">Recuperar senha</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Enviaremos um link para redefinir sua senha.
            </p>
            <form onSubmit={handleRecover} className="mt-5 space-y-4" noValidate>
              <div className="space-y-1.5">
                <Label htmlFor="email-rec">E-mail</Label>
                <Input
                  id="email-rec"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="voce@exemplo.com"
                />
              </div>
              <Button type="submit" className="w-full" disabled={submitting} size="lg">
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : (
                  <><Mail className="h-4 w-4 mr-2" /> Enviar link</>
                )}
              </Button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
