import { useState } from "react";
import { Star } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Link } from "@tanstack/react-router";

export function RateReaPopover({ reaId, reaTitle }: { reaId: string; reaTitle: string }) {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [hover, setHover] = useState(0);

  const myRatingQ = useQuery({
    enabled: !!user,
    queryKey: ["my-rating", reaId, user?.id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("rea_ratings")
        .select("rating")
        .eq("rea_id", reaId)
        .eq("user_id", user!.id)
        .maybeSingle();
      if (error) throw error;
      return data?.rating ?? 0;
    },
  });

  const rateMut = useMutation({
    mutationFn: async (rating: number) => {
      const { error } = await supabase
        .from("rea_ratings")
        .upsert(
          { rea_id: reaId, user_id: user!.id, rating },
          { onConflict: "rea_id,user_id" },
        );
      if (error) throw error;
      return rating;
    },
    onSuccess: (rating) => {
      toast.success(`Você avaliou ${reaTitle} com ${rating} ${rating === 1 ? "estrela" : "estrelas"}`);
      qc.invalidateQueries({ queryKey: ["my-rating", reaId] });
      qc.invalidateQueries({ queryKey: ["reas"] });
      qc.invalidateQueries({ queryKey: ["my-ratings"] });
      setOpen(false);
    },
    onError: (e: Error) => toast.error("Erro ao avaliar", { description: e.message }),
  });

  if (!user) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <Button asChild variant="ghost" size="icon" className="h-8 w-8" aria-label="Avaliar">
            <Link to="/"><Star className="h-4 w-4" /></Link>
          </Button>
        </TooltipTrigger>
        <TooltipContent>Avaliar</TooltipContent>
      </Tooltip>
    );
  }

  const current = myRatingQ.data ?? 0;
  const display = hover || current;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <Tooltip>
        <TooltipTrigger asChild>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={(e) => e.stopPropagation()}
              aria-label="Avaliar"
            >
              <Star className={`h-4 w-4 ${current > 0 ? "fill-accent text-accent" : ""}`} />
            </Button>
          </PopoverTrigger>
        </TooltipTrigger>
        <TooltipContent>{current > 0 ? `Sua avaliação: ${current}` : "Avaliar"}</TooltipContent>
      </Tooltip>
      <PopoverContent className="w-auto p-3" onClick={(e) => e.stopPropagation()}>
        <p className="text-xs text-muted-foreground mb-2">Sua avaliação</p>
        <div className="flex items-center gap-1" onMouseLeave={() => setHover(0)}>
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              onMouseEnter={() => setHover(n)}
              onClick={() => rateMut.mutate(n)}
              disabled={rateMut.isPending}
              className="p-1 transition-transform hover:scale-110 disabled:opacity-50"
              aria-label={`Dar ${n} estrelas`}
            >
              <Star
                className={`h-5 w-5 ${
                  n <= display ? "fill-accent text-accent" : "text-muted-foreground"
                }`}
              />
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
