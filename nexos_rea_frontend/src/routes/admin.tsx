import { createFileRoute, Outlet, Link, redirect } from "@tanstack/react-router";
import { supabase } from "@/integrations/supabase/client";
import { ShieldCheck, LayoutDashboard, Flag, Trash2 } from "lucide-react";

export const Route = createFileRoute("/admin")({
  beforeLoad: async () => {
    const { data: userData } = await supabase.auth.getUser();
    if (!userData.user) throw redirect({ to: "/" });
    const { data: isAdmin } = await supabase.rpc("has_role", {
      _user_id: userData.user.id,
      _role: "admin",
    });
    if (!isAdmin) throw redirect({ to: "/" });
  },
  component: AdminLayout,
  head: () => ({ meta: [{ title: "Admin — Nexos REA" }] }),
});

function AdminLayout() {
  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10 space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="font-display text-3xl">Painel administrativo</h1>
            <p className="text-sm text-muted-foreground">Governança, métricas e moderação.</p>
          </div>
        </div>
        <nav className="flex gap-1 rounded-md border border-border bg-card p-1">
          <Link
            to="/admin"
            activeOptions={{ exact: true }}
            className="flex items-center gap-2 px-3 py-1.5 rounded text-sm text-foreground/70 hover:text-foreground data-[status=active]:bg-primary data-[status=active]:text-primary-foreground"
          >
            <LayoutDashboard className="h-4 w-4" /> Métricas
          </Link>
          <Link
            to="/admin/moderacao"
            className="flex items-center gap-2 px-3 py-1.5 rounded text-sm text-foreground/70 hover:text-foreground data-[status=active]:bg-primary data-[status=active]:text-primary-foreground"
          >
            <Flag className="h-4 w-4" /> Moderação
          </Link>
          <Link
            to="/admin/removidos"
            className="flex items-center gap-2 px-3 py-1.5 rounded text-sm text-foreground/70 hover:text-foreground data-[status=active]:bg-primary data-[status=active]:text-primary-foreground"
          >
            <Trash2 className="h-4 w-4" /> Removidos
          </Link>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
