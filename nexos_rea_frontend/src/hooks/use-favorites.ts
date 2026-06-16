import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { logInteraction } from "@/lib/interactions";

async function getFavoritesCollectionId(userId: string): Promise<string> {
  const { data: existing, error: e1 } = await supabase
    .from("collections")
    .select("id")
    .eq("user_id", userId)
    .eq("is_system", true)
    .maybeSingle();
  if (e1) throw e1;
  if (existing?.id) return existing.id;

  const { data, error } = await (supabase.rpc as any)("ensure_favorites_collection", {
    _user_id: userId,
  });
  if (error) throw error;
  return data as string;
}

export function useFavoritesCollectionId() {
  const { user } = useAuth();
  return useQuery({
    enabled: !!user,
    queryKey: ["favorites-collection", user?.id],
    queryFn: () => getFavoritesCollectionId(user!.id),
    staleTime: 5 * 60_000,
  });
}

export function useFavoritedSet() {
  const { user } = useAuth();
  const favColQ = useFavoritesCollectionId();
  return useQuery({
    enabled: !!user && !!favColQ.data,
    queryKey: ["favorited-set", user?.id, favColQ.data],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("collection_items")
        .select("rea_id")
        .eq("collection_id", favColQ.data!);
      if (error) throw error;
      return new Set((data ?? []).map((r) => r.rea_id));
    },
  });
}

async function addFav(colId: string, reaId: string) {
  const { error } = await supabase
    .from("collection_items")
    .insert({ collection_id: colId, rea_id: reaId, position: 0 });
  if (error) throw error;
}

async function removeFav(colId: string, reaId: string) {
  const { error } = await supabase
    .from("collection_items")
    .delete()
    .eq("collection_id", colId)
    .eq("rea_id", reaId);
  if (error) throw error;
}

export function useToggleFavorite() {
  const { user } = useAuth();
  const favColQ = useFavoritesCollectionId();
  const qc = useQueryClient();

  const invalidateAll = (colId: string) => {
    qc.invalidateQueries({ queryKey: ["favorited-set"] });
    qc.invalidateQueries({ queryKey: ["collection-items", colId] });
    qc.invalidateQueries({ queryKey: ["my-collections"] });
  };

  return useMutation({
    mutationFn: async ({ reaId, isFav }: { reaId: string; isFav: boolean }) => {
      if (!user) throw new Error("Faça login para favoritar");
      const colId = favColQ.data ?? (await getFavoritesCollectionId(user.id));

      if (isFav) {
        await removeFav(colId, reaId);
        void logInteraction(reaId, "remove_from_collection");
        return { reaId, becameFav: false, colId };
      } else {
        await addFav(colId, reaId);
        void logInteraction(reaId, "save_to_collection");
        return { reaId, becameFav: true, colId };
      }
    },
    onSuccess: (result) => {
      invalidateAll(result.colId);
      toast.success(result.becameFav ? "Adicionado aos favoritos" : "Removido dos favoritos", {
        action: {
          label: "Desfazer",
          onClick: async () => {
            try {
              if (result.becameFav) await removeFav(result.colId, result.reaId);
              else await addFav(result.colId, result.reaId);
              invalidateAll(result.colId);
            } catch (e) {
              toast.error("Não foi possível desfazer");
            }
          },
        },
      });
    },
    onError: (e: Error) => toast.error("Erro", { description: e.message }),
  });
}
