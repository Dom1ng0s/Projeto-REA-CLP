export interface Tag {
  id: string;
  slug: string;
  label: string;
}

export type InterestSource = "manual" | "inferred";
export type CollectionVisibility = "private" | "public";

export interface UserInterestRow {
  user_id: string;
  tag_id: string;
  weight: number;
  source: InterestSource;
}

export interface CollectionRow {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  visibility: CollectionVisibility;
  cover_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface CollectionItemRow {
  collection_id: string;
  rea_id: string;
  position: number;
  note: string | null;
  added_at: string;
}
