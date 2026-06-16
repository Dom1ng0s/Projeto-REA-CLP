import { useEffect, useState } from "react";
import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";

interface Props {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  url: string;
  title: string;
  onConfirm: () => void;
}

export function ExternalLinkConfirmDialog({ open, onOpenChange, url, title, onConfirm }: Props) {
  const { user } = useAuth();
  const [skipFuture, setSkipFuture] = useState(false);

  useEffect(() => {
    if (open) setSkipFuture(false);
  }, [open]);

  const handleConfirm = async () => {
    if (skipFuture && user) {
      await supabase
        .from("profiles")
        .update({ skip_external_warning: true })
        .eq("id", user.id);
    }
    onConfirm();
    onOpenChange(false);
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="font-display">Abrir conteúdo externo?</AlertDialogTitle>
          <AlertDialogDescription className="space-y-3">
            <span className="block">
              Você será redirecionado para um site externo para acessar{" "}
              <strong className="text-foreground">{title}</strong>.
            </span>
            <code className="block break-all rounded bg-muted px-2 py-1.5 text-xs font-mono text-foreground">
              {url}
            </code>
          </AlertDialogDescription>
        </AlertDialogHeader>

        {user && (
          <div className="flex items-center gap-2">
            <Checkbox
              id="skip-warning"
              checked={skipFuture}
              onCheckedChange={(v) => setSkipFuture(v === true)}
            />
            <Label htmlFor="skip-warning" className="text-sm font-normal cursor-pointer">
              Não perguntar novamente
            </Label>
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction onClick={handleConfirm}>
            <ExternalLink className="h-4 w-4 mr-2" />
            Abrir
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
