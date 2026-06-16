import { useState } from "react";
import { Star, ImageOff, Sparkles, Heart } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Database } from "@/integrations/supabase/types";
import {
  formatLabel,
  languageLabel,
  licenseLabel,
  educationLabel,
  type EducationLevel,
} from "@/lib/rea-labels";
import { AddToCollectionDialog } from "@/components/AddToCollectionDialog";
import { ExternalLinkConfirmDialog } from "@/components/ExternalLinkConfirmDialog";
import { RateReaPopover } from "@/components/RateReaPopover";
import { ReportReaDialog } from "@/components/ReportReaDialog";
import { logInteraction } from "@/lib/interactions";
import { useFavoritedSet, useToggleFavorite } from "@/hooks/use-favorites";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/integrations/supabase/client";

type Rea = Database["public"]["Tables"]["reas"]["Row"];

function ThumbPlaceholder() {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-2 bg-muted text-muted-foreground">
      <ImageOff className="h-8 w-8 opacity-50" />
      <span className="text-[10px] uppercase tracking-wider opacity-60">
        Sem imagem
      </span>
    </div>
  );
}

export function ReaCard({ rea, recommended = false }: { rea: Rea; recommended?: boolean }) {
  const { user } = useAuth();
  const rating = Number(rea.rating_avg);
  const hasRating = rea.rating_count > 0;
  const [imgError, setImgError] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const showImage = rea.thumbnail_url && rea.thumbnail_url.trim().length > 0 && !imgError;
  const eduKey = rea.education_level as EducationLevel;

  const favSet = useFavoritedSet();
  const isFav = !!favSet.data?.has(rea.id);
  const toggleFav = useToggleFavorite();

  const prefQ = useQuery({
    enabled: !!user,
    queryKey: ["profile-skip-warning", user?.id],
    queryFn: async () => {
      const { data } = await supabase
        .from("profiles")
        .select("skip_external_warning")
        .eq("id", user!.id)
        .maybeSingle();
      return data?.skip_external_warning ?? false;
    },
    staleTime: 60_000,
  });

  const myRatingQ = useQuery({
    enabled: !!user,
    queryKey: ["my-rating", rea.id, user?.id],
    queryFn: async () => {
      const { data } = await supabase
        .from("rea_ratings")
        .select("rating")
        .eq("rea_id", rea.id)
        .eq("user_id", user!.id)
        .maybeSingle();
      return data?.rating ?? 0;
    },
  });
  const myRating = myRatingQ.data ?? 0;

  function doOpen() {
    void logInteraction(rea.id, "view");
    window.open(rea.resource_url, "_blank", "noopener,noreferrer");
  }

  function handleCardClick(e: React.MouseEvent) {
    if ((e.target as HTMLElement).closest("[data-card-action]")) return;
    if (prefQ.data) doOpen();
    else setConfirmOpen(true);
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (prefQ.data) doOpen();
      else setConfirmOpen(true);
    }
  }

  return (
    <TooltipProvider delayDuration={200}>
      <article
        role="button"
        tabIndex={0}
        onClick={handleCardClick}
        onKeyDown={handleKey}
        className="group relative flex flex-col overflow-hidden rounded-lg border border-border bg-card transition-all hover:border-primary/30 hover:shadow-md cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/40"
      >
        <div className="relative aspect-[16/9] overflow-hidden bg-secondary">
          {showImage ? (
            <img
              src={rea.thumbnail_url!}
              alt={rea.title}
              loading="lazy"
              onError={() => setImgError(true)}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <ThumbPlaceholder />
          )}
          <Badge
            variant="secondary"
            className="absolute top-2 left-2 bg-background/90 backdrop-blur"
          >
            {formatLabel[rea.format]}
          </Badge>
          {recommended && (
            <Tooltip>
              <TooltipTrigger asChild>
                <div
                  aria-label="Recomendado para você"
                  className="absolute top-2 right-2 flex h-7 w-7 items-center justify-center rounded-full bg-accent text-accent-foreground shadow-md ring-2 ring-background"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="left">Recomendado para você</TooltipContent>
            </Tooltip>
          )}
          {myRating > 0 && (
            <Badge className="absolute bottom-2 right-2 bg-accent text-accent-foreground gap-1">
              <Star className="h-3 w-3 fill-current" /> Você: {myRating}
            </Badge>
          )}
        </div>

        <div className="flex flex-1 flex-col gap-3 p-4">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-display text-lg leading-tight text-card-foreground line-clamp-2">
              {rea.title}
            </h3>
            {hasRating && (
              <div className="flex shrink-0 items-center gap-1 text-sm">
                <Star className="h-3.5 w-3.5 fill-accent text-accent" />
                <span className="font-medium">{rating.toFixed(1)}</span>
                <span className="text-xs text-muted-foreground">
                  ({rea.rating_count})
                </span>
              </div>
            )}
          </div>

          {rea.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {rea.description}
            </p>
          )}

          <div className="flex flex-wrap gap-1.5">
            <Badge variant="outline" className="text-[10px]">
              {rea.subject_area}
            </Badge>
            <Badge variant="outline" className="text-[10px]">
              {educationLabel[eduKey] ?? rea.education_level}
            </Badge>
            <Badge variant="outline" className="text-[10px]">
              {languageLabel[rea.language]}
            </Badge>
          </div>

          <div
            className="mt-auto flex items-center justify-between gap-2 border-t border-border/60 pt-3"
            data-card-action
            onClick={(e) => e.stopPropagation()}
          >
            <span className="text-xs text-muted-foreground truncate">
              {licenseLabel[rea.license]}
            </span>
            <div className="flex items-center gap-0.5">
              {user && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      disabled={toggleFav.isPending}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFav.mutate({ reaId: rea.id, isFav });
                      }}
                      aria-label={isFav ? "Remover dos favoritos" : "Favoritar"}
                      aria-pressed={isFav}
                    >
                      <Heart className={`h-4 w-4 ${isFav ? "fill-destructive text-destructive" : ""}`} />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>{isFav ? "Remover dos favoritos" : "Favoritar"}</TooltipContent>
                </Tooltip>
              )}
              <RateReaPopover reaId={rea.id} reaTitle={rea.title} />
              <AddToCollectionDialog reaId={rea.id} reaTitle={rea.title} />
              <ReportReaDialog reaId={rea.id} reaTitle={rea.title} />
            </div>
          </div>
        </div>
      </article>

      <ExternalLinkConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        url={rea.resource_url}
        title={rea.title}
        onConfirm={doOpen}
      />
    </TooltipProvider>
  );
}

export function ReaCardSkeleton() {
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-border bg-card">
      <div className="aspect-[16/9] animate-pulse bg-muted" />
      <div className="p-4 space-y-3">
        <div className="h-5 w-4/5 animate-pulse rounded bg-muted" />
        <div className="h-3 w-full animate-pulse rounded bg-muted" />
        <div className="h-3 w-2/3 animate-pulse rounded bg-muted" />
      </div>
    </div>
  );
}
