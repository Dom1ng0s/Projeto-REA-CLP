import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Sparkles, ShieldCheck, Compass, LogOut, FolderOpen, UserIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HomeAuthPanel } from "@/components/HomeAuthPanel";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Nexos REA — Recomendação adaptativa de REAs" },
      {
        name: "description",
        content:
          "Acabe com o tempo perdido procurando Recursos Educacionais Abertos. Catálogo curado, busca inteligente e recomendações personalizadas.",
      },
    ],
  }),
  component: HomePage,
});

function HomePage() {
  const { user, loading } = useAuth();

  const handleLogout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
      toast.error("Erro ao sair", { description: error.message });
      return;
    }
    toast.success("Sessão encerrada");
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] min-h-0">
      {/* Hero / Auth split — ocupa todo o espaço restante */}
      <section className="relative overflow-hidden flex-1 min-h-0 flex items-center">
        <div className="absolute inset-0 -z-10 bg-gradient-to-br from-secondary via-background to-background" />
        <div className="absolute -top-24 -right-24 -z-10 h-72 w-72 rounded-full bg-accent/20 blur-3xl" />
        <div className="absolute -bottom-24 -left-24 -z-10 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />

        <div className="mx-auto grid w-full max-w-6xl gap-6 px-4 sm:px-6 py-6 md:grid-cols-2 md:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
              <Sparkles className="h-3 w-3 text-accent" />
              Recomendação adaptativa de REAs
            </div>
            <h1 className="mt-5 font-display text-4xl sm:text-5xl md:text-6xl leading-[1.05] text-foreground">
              O recurso certo,
              <br />
              <span className="italic text-primary">no momento certo.</span>
            </h1>
            <p className="mt-4 max-w-xl text-sm sm:text-base text-muted-foreground">
              Nexos REA conecta professores e estudantes aos melhores Recursos
              Educacionais Abertos com busca curada, avaliação aberta e
              recomendações que aprendem com você.
            </p>
            <div className="mt-5">
              <Button asChild size="lg">
                <Link to="/catalogo">
                  Explorar catálogo <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>

          <div className="flex justify-center md:justify-end">
            {loading ? (
              <div className="h-72 w-full max-w-md animate-pulse rounded-xl bg-muted/50" />
            ) : user ? (
              <div className="w-full max-w-md rounded-xl border border-border bg-card/95 backdrop-blur p-6 shadow-lg">
                <h2 className="font-display text-2xl">Bem-vindo de volta</h2>
                <p className="mt-1 text-sm text-muted-foreground truncate">{user.email}</p>
                <div className="mt-4 flex flex-col gap-2">
                  <Button asChild size="lg">
                    <Link to="/catalogo">
                      Ir para o catálogo <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                  <Button asChild variant="outline">
                    <Link to="/colecoes"><FolderOpen className="h-4 w-4 mr-2" /> Minhas coleções</Link>
                  </Button>
                  <Button asChild variant="outline">
                    <Link to="/perfil"><UserIcon className="h-4 w-4 mr-2" /> Meu perfil</Link>
                  </Button>
                  <Button variant="ghost" onClick={handleLogout}>
                    <LogOut className="h-4 w-4 mr-2" /> Sair
                  </Button>
                </div>
              </div>
            ) : (
              <HomeAuthPanel />
            )}
          </div>
        </div>
      </section>

      {/* Rodapé sempre visível */}
      <footer className="shrink-0 border-t border-border bg-card/40">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-4">
          <div className="grid gap-4 md:grid-cols-3">
            {[
              { icon: Compass, title: "Catálogo curado", body: "Metadados completos, licença explícita e classificação por área e nível." },
              { icon: Sparkles, title: "Recomendação personalizada", body: "Sugestões em destaque no topo do catálogo conforme você interage." },
              { icon: ShieldCheck, title: "Confiança aberta", body: "Avaliações da comunidade e moderação automática de conteúdo." },
            ].map(({ icon: Icon, title, body }) => (
              <div key={title} className="flex items-start gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-display text-sm text-foreground">{title}</h3>
                  <p className="text-xs text-muted-foreground line-clamp-2">{body}</p>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-center text-[11px] text-muted-foreground">
            Nexos REA · Recursos Educacionais Abertos · Grupo Epsilon
          </p>
        </div>
      </footer>
    </div>
  );
}
