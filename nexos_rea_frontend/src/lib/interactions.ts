import { supabase } from "@/integrations/supabase/client";

type EventType =
  | "view"
  | "search_click"
  | "save_to_collection"
  | "remove_from_collection"
  | "rating"
  | "rating_update"
  | "report";

export async function logInteraction(
  reaId: string,
  eventType: EventType,
  value = 0,
): Promise<void> {
  const { data: auth } = await supabase.auth.getUser();
  if (!auth.user) return;
  await supabase
    .from("rea_interactions")
    .insert({ user_id: auth.user.id, rea_id: reaId, event_type: eventType, value });
}
