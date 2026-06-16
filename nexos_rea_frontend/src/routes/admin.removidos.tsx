import { createFileRoute } from "@tanstack/react-router";
import { AdminReaBrowser } from "@/components/AdminReaBrowser";

export const Route = createFileRoute("/admin/removidos")({
  component: RemovedPage,
});

function RemovedPage() {
  return (
    <AdminReaBrowser
      statuses={["removed"]}
      title="Nenhum conteúdo removido"
      emptyMessage="Conteúdos removidos aparecerão aqui para auditoria."
      showRestore
      showRemove={false}
      showSendToReview
    />
  );
}
