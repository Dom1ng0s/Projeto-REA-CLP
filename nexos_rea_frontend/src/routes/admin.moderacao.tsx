import { createFileRoute } from "@tanstack/react-router";
import { AdminReaBrowser } from "@/components/AdminReaBrowser";

export const Route = createFileRoute("/admin/moderacao")({
  component: ModerationPage,
});

function ModerationPage() {
  return (
    <AdminReaBrowser
      statuses={["blocked_review", "hidden_low_rating"]}
      title="Fila vazia"
      emptyMessage="Nenhum REA aguardando revisão."
      showRestore
      showRemove
    />
  );
}
