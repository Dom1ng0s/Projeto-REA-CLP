import { Link, useNavigate, useRouter } from "@tanstack/react-router";
import { BookOpen, FolderOpen, LogOut, Search, ShieldCheck, User as UserIcon } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export function Header() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const router = useRouter();

  const isAdminQ = useQuery({
    enabled: !!user,
    queryKey: ["is-admin", user?.id],
    queryFn: async () => {
      const { data } = await supabase.rpc("has_role", { _user_id: user!.id, _role: "admin" });
      return !!data;
    },
    staleTime: 5 * 60_000,
  });
  const isAdmin = !!isAdminQ.data;


  const handleLogout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
      toast.error("Erro ao sair", { description: error.message });
      return;
    }
    toast.success("Sessão encerrada");
    router.invalidate();
    navigate({ to: "/" });
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/60 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground transition-transform group-hover:rotate-[-4deg]">
            <BookOpen className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <div className="font-display text-xl text-foreground">Nexos REA</div>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          <Link
            to="/"
            activeOptions={{ exact: true }}
            className="px-3 py-2 text-sm text-foreground/70 transition-colors hover:text-foreground data-[status=active]:text-foreground data-[status=active]:font-medium"
          >
            Início
          </Link>
          <Link
            to="/catalogo"
            className="px-3 py-2 text-sm text-foreground/70 transition-colors hover:text-foreground data-[status=active]:text-foreground data-[status=active]:font-medium"
          >
            Catálogo
          </Link>
          {user && (
            <>
              <Link
                to="/colecoes"
                className="px-3 py-2 text-sm text-foreground/70 transition-colors hover:text-foreground data-[status=active]:text-foreground data-[status=active]:font-medium"
              >
                Coleções
              </Link>
              <Link
                to="/perfil"
                className="px-3 py-2 text-sm text-foreground/70 transition-colors hover:text-foreground data-[status=active]:text-foreground data-[status=active]:font-medium"
              >
                Perfil
              </Link>
              {isAdmin && (
                <Link
                  to="/admin"
                  className="px-3 py-2 text-sm text-primary transition-colors hover:text-primary/80 data-[status=active]:font-medium inline-flex items-center gap-1"
                >
                  <ShieldCheck className="h-3.5 w-3.5" /> Admin
                </Link>
              )}

            </>
          )}
        </nav>

        <div className="flex items-center gap-2">
          <Button
            asChild
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Catálogo"
          >
            <Link to="/catalogo">
              <Search className="h-4 w-4" />
            </Link>
          </Button>

          {loading ? (
            <div className="h-9 w-20 animate-pulse rounded-md bg-muted" />
          ) : user ? (
            <>
              <Button asChild variant="ghost" size="icon" className="md:hidden" aria-label="Coleções">
                <Link to="/colecoes"><FolderOpen className="h-4 w-4" /></Link>
              </Button>
              <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                <Link to="/perfil">
                  <UserIcon className="h-3.5 w-3.5 mr-1.5" />
                  <span className="max-w-[140px] truncate">{user.email}</span>
                </Link>
              </Button>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-3.5 w-3.5 sm:mr-1.5" />
                <span className="hidden sm:inline">Sair</span>
              </Button>
            </>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link to="/login">Entrar</Link>
              </Button>
              <Button asChild size="sm">
                <Link to="/registro">Criar conta</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
