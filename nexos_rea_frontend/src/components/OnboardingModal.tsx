import { useState, useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { Sparkles } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export function OnboardingModal() {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    
    // 1. Verifica se o usuário acabou de se registrar
    const justRegistered = localStorage.getItem("showOnboarding");
    
    if (justRegistered === "true") {
      setOpen(true); // Abre o modal
      // 2. Apaga a flag imediatamente para garantir que NUNCA MAIS reapareça
      localStorage.removeItem("showOnboarding"); 
    }
  }, []);

  if (!mounted) return null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-[520px] p-8">
        <DialogHeader className="space-y-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-2">
            <Sparkles className="h-6 w-6" />
          </div>
          <DialogTitle className="font-display text-3xl leading-tight text-foreground">
            Personalize sua experiência no Nexos REA!
          </DialogTitle>
          <DialogDescription className="text-base text-muted-foreground space-y-4">
            <p>
              O nosso motor de recomendação foi feito para entregar o recurso
              certo, no momento certo. Para poupar o seu tempo e evitar que
              você veja materiais fora da sua área, precisamos conhecer um
              pouco mais sobre o que você busca.
            </p>
            <p>
              Acesse o seu perfil e selecione os seus Interesses. Quanto mais
              o sistema aprender sobre você, melhores serão as suas
              recomendações!
            </p>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-8 flex flex-col-reverse sm:flex-row sm:justify-end gap-3 sm:gap-2">
          <Button 
            variant="ghost" 
            onClick={() => setOpen(false)}
            className="w-full sm:w-auto"
          >
            Agora não
          </Button>
          <Button asChild className="w-full sm:w-auto" onClick={() => setOpen(false)}>
            <Link to="/perfil">
              Ir para Meu Perfil
            </Link>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}