import { useState } from "react";
import { Flag, Loader2 } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { z } from "zod";
import { Link } from "@tanstack/react-router";

import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

// Map UI label → enum em report_reason
const REASONS: Array<{ value: string; label: string; enum: string }> = [
  { value: "outdated", label: "Conteúdo incorreto ou desatualizado", enum: "misinformation" },
  { value: "low_quality", label: "Baixa qualidade didática", enum: "other" },
  { value: "broken_link", label: "Link quebrado ou recurso offline", enum: "broken_link" },
  { value: "format_issue", label: "Problemas de formatação/visualização", enum: "other" },
  { value: "misclassified", label: "Classificação incorreta", enum: "other" },
  { value: "spam", label: "Spam ou propaganda enganosa", enum: "spam" },
  { value: "copyright", label: "Violação de direitos autorais", enum: "copyright" },
  { value: "inappropriate", label: "Conteúdo inadequado ou ofensivo", enum: "inappropriate" },
  { value: "other", label: "Outro", enum: "other" },
];

const detailsSchema = z.string().trim().max(100, "Máximo de 100 caracteres");

export function ReportReaDialog({ reaId, reaTitle }: { reaId: string; reaTitle: string }) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<string>("");
  const [details, setDetails] = useState("");

  const reportMut = useMutation({
    mutationFn: async () => {
      const selected = REASONS.find((r) => r.value === reason);
      if (!selected) throw new Error("Selecione um motivo");
      let finalDetails: string | null = null;
      if (reason === "other") {
        const parsed = detailsSchema.safeParse(details);
        if (!parsed.success) throw new Error(parsed.error.issues[0].message);
        if (!parsed.data) throw new Error("Descreva o motivo");
        finalDetails = parsed.data;
      }
      const detailsWithLabel = finalDetails
        ? `[${selected.label}] ${finalDetails}`
        : `[${selected.label}]`;

      const { error } = await supabase
        .from("rea_reports")
        .insert({
          rea_id: reaId,
          user_id: user!.id,
          reason: selected.enum as any,
          details: detailsWithLabel,
        });
      if (error) throw error;
    },
    onSuccess: () => {
      toast.success("Denúncia enviada", {
        description: "Nossa equipe vai revisar este conteúdo.",
      });
      setOpen(false);
      setReason("");
      setDetails("");
    },
    onError: (e: Error) => toast.error("Erro", { description: e.message }),
  });

  if (!user) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <Button asChild variant="ghost" size="icon" className="h-8 w-8" aria-label="Denunciar">
            <Link to="/"><Flag className="h-4 w-4" /></Link>
          </Button>
        </TooltipTrigger>
        <TooltipContent>Denunciar</TooltipContent>
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
              className="h-8 w-8 text-muted-foreground hover:text-destructive"
              onClick={(e) => e.stopPropagation()}
              aria-label="Denunciar"
            >
              <Flag className="h-4 w-4" />
            </Button>
          </DialogTrigger>
        </TooltipTrigger>
        <TooltipContent>Denunciar</TooltipContent>
      </Tooltip>
      <DialogContent onClick={(e) => e.stopPropagation()}>
        <DialogHeader>
          <DialogTitle className="font-display">Denunciar conteúdo</DialogTitle>
          <DialogDescription className="line-clamp-2">{reaTitle}</DialogDescription>
        </DialogHeader>

        <RadioGroup value={reason} onValueChange={setReason} className="space-y-2 max-h-72 overflow-y-auto">
          {REASONS.map((r) => (
            <div key={r.value} className="flex items-center space-x-2">
              <RadioGroupItem value={r.value} id={`reason-${r.value}`} />
              <Label htmlFor={`reason-${r.value}`} className="cursor-pointer font-normal">
                {r.label}
              </Label>
            </div>
          ))}
        </RadioGroup>

        {reason === "other" && (
          <div className="space-y-1.5">
            <Label htmlFor="report-details" className="text-xs uppercase tracking-wide text-muted-foreground">
              Detalhes ({details.length}/100)
            </Label>
            <Textarea
              id="report-details"
              value={details}
              onChange={(e) => setDetails(e.target.value.slice(0, 100))}
              rows={3}
              maxLength={100}
              placeholder="Descreva o motivo..."
            />
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button
            onClick={() => reportMut.mutate()}
            disabled={!reason || reportMut.isPending || (reason === "other" && !details.trim())}
            variant="destructive"
          >
            {reportMut.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
            Enviar denúncia
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
