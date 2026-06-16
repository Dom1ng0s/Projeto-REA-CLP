export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.5"
  }
  public: {
    Tables: {
      collection_items: {
        Row: {
          added_at: string
          collection_id: string
          note: string | null
          position: number
          rea_id: string
        }
        Insert: {
          added_at?: string
          collection_id: string
          note?: string | null
          position?: number
          rea_id: string
        }
        Update: {
          added_at?: string
          collection_id?: string
          note?: string | null
          position?: number
          rea_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "collection_items_collection_id_fkey"
            columns: ["collection_id"]
            isOneToOne: false
            referencedRelation: "collections"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "collection_items_rea_id_fkey"
            columns: ["rea_id"]
            isOneToOne: false
            referencedRelation: "reas"
            referencedColumns: ["id"]
          },
        ]
      }
      collections: {
        Row: {
          cover_url: string | null
          created_at: string
          description: string | null
          id: string
          is_system: boolean
          title: string
          updated_at: string
          user_id: string
          visibility: Database["public"]["Enums"]["collection_visibility"]
        }
        Insert: {
          cover_url?: string | null
          created_at?: string
          description?: string | null
          id?: string
          is_system?: boolean
          title: string
          updated_at?: string
          user_id: string
          visibility?: Database["public"]["Enums"]["collection_visibility"]
        }
        Update: {
          cover_url?: string | null
          created_at?: string
          description?: string | null
          id?: string
          is_system?: boolean
          title?: string
          updated_at?: string
          user_id?: string
          visibility?: Database["public"]["Enums"]["collection_visibility"]
        }
        Relationships: []
      }
      profiles: {
        Row: {
          avatar_url: string | null
          bio: string | null
          created_at: string
          display_name: string | null
          id: string
          skip_external_warning: boolean
          updated_at: string
        }
        Insert: {
          avatar_url?: string | null
          bio?: string | null
          created_at?: string
          display_name?: string | null
          id: string
          skip_external_warning?: boolean
          updated_at?: string
        }
        Update: {
          avatar_url?: string | null
          bio?: string | null
          created_at?: string
          display_name?: string | null
          id?: string
          skip_external_warning?: boolean
          updated_at?: string
        }
        Relationships: []
      }
      rea_interactions: {
        Row: {
          created_at: string
          event_type: Database["public"]["Enums"]["rea_event_type"]
          id: string
          rea_id: string
          user_id: string
          value: number
        }
        Insert: {
          created_at?: string
          event_type: Database["public"]["Enums"]["rea_event_type"]
          id?: string
          rea_id: string
          user_id: string
          value?: number
        }
        Update: {
          created_at?: string
          event_type?: Database["public"]["Enums"]["rea_event_type"]
          id?: string
          rea_id?: string
          user_id?: string
          value?: number
        }
        Relationships: [
          {
            foreignKeyName: "rea_interactions_rea_id_fkey"
            columns: ["rea_id"]
            isOneToOne: false
            referencedRelation: "reas"
            referencedColumns: ["id"]
          },
        ]
      }
      rea_ratings: {
        Row: {
          comment: string | null
          created_at: string
          id: string
          rating: number
          rea_id: string
          updated_at: string
          user_id: string
        }
        Insert: {
          comment?: string | null
          created_at?: string
          id?: string
          rating: number
          rea_id: string
          updated_at?: string
          user_id: string
        }
        Update: {
          comment?: string | null
          created_at?: string
          id?: string
          rating?: number
          rea_id?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "rea_ratings_rea_id_fkey"
            columns: ["rea_id"]
            isOneToOne: false
            referencedRelation: "reas"
            referencedColumns: ["id"]
          },
        ]
      }
      rea_reports: {
        Row: {
          created_at: string
          details: string | null
          id: string
          rea_id: string
          reason: Database["public"]["Enums"]["report_reason"]
          resolved_at: string | null
          resolved_by: string | null
          state: Database["public"]["Enums"]["report_state"]
          user_id: string
        }
        Insert: {
          created_at?: string
          details?: string | null
          id?: string
          rea_id: string
          reason: Database["public"]["Enums"]["report_reason"]
          resolved_at?: string | null
          resolved_by?: string | null
          state?: Database["public"]["Enums"]["report_state"]
          user_id: string
        }
        Update: {
          created_at?: string
          details?: string | null
          id?: string
          rea_id?: string
          reason?: Database["public"]["Enums"]["report_reason"]
          resolved_at?: string | null
          resolved_by?: string | null
          state?: Database["public"]["Enums"]["report_state"]
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "rea_reports_rea_id_fkey"
            columns: ["rea_id"]
            isOneToOne: false
            referencedRelation: "reas"
            referencedColumns: ["id"]
          },
        ]
      }
      reas: {
        Row: {
          author: string | null
          created_at: string
          description: string | null
          education_level: Database["public"]["Enums"]["education_level"]
          format: Database["public"]["Enums"]["rea_format"]
          id: string
          language: Database["public"]["Enums"]["rea_language"]
          license: Database["public"]["Enums"]["rea_license"]
          rating_avg: number
          rating_count: number
          report_count: number
          resource_url: string
          source_url: string | null
          status: Database["public"]["Enums"]["rea_status"]
          subject_area: string
          submitted_by: string | null
          tags: string[]
          thumbnail_url: string | null
          title: string
          updated_at: string
        }
        Insert: {
          author?: string | null
          created_at?: string
          description?: string | null
          education_level: Database["public"]["Enums"]["education_level"]
          format: Database["public"]["Enums"]["rea_format"]
          id?: string
          language?: Database["public"]["Enums"]["rea_language"]
          license: Database["public"]["Enums"]["rea_license"]
          rating_avg?: number
          rating_count?: number
          report_count?: number
          resource_url: string
          source_url?: string | null
          status?: Database["public"]["Enums"]["rea_status"]
          subject_area: string
          submitted_by?: string | null
          tags?: string[]
          thumbnail_url?: string | null
          title: string
          updated_at?: string
        }
        Update: {
          author?: string | null
          created_at?: string
          description?: string | null
          education_level?: Database["public"]["Enums"]["education_level"]
          format?: Database["public"]["Enums"]["rea_format"]
          id?: string
          language?: Database["public"]["Enums"]["rea_language"]
          license?: Database["public"]["Enums"]["rea_license"]
          rating_avg?: number
          rating_count?: number
          report_count?: number
          resource_url?: string
          source_url?: string | null
          status?: Database["public"]["Enums"]["rea_status"]
          subject_area?: string
          submitted_by?: string | null
          tags?: string[]
          thumbnail_url?: string | null
          title?: string
          updated_at?: string
        }
        Relationships: []
      }
      subject_areas: {
        Row: {
          created_at: string
          id: string
          label: string
          slug: string
        }
        Insert: {
          created_at?: string
          id?: string
          label: string
          slug: string
        }
        Update: {
          created_at?: string
          id?: string
          label?: string
          slug?: string
        }
        Relationships: []
      }
      tags: {
        Row: {
          created_at: string
          id: string
          label: string
          slug: string
        }
        Insert: {
          created_at?: string
          id?: string
          label: string
          slug: string
        }
        Update: {
          created_at?: string
          id?: string
          label?: string
          slug?: string
        }
        Relationships: []
      }
      user_interests: {
        Row: {
          created_at: string
          source: Database["public"]["Enums"]["interest_source"]
          tag_id: string
          updated_at: string
          user_id: string
          weight: number
        }
        Insert: {
          created_at?: string
          source?: Database["public"]["Enums"]["interest_source"]
          tag_id: string
          updated_at?: string
          user_id: string
          weight?: number
        }
        Update: {
          created_at?: string
          source?: Database["public"]["Enums"]["interest_source"]
          tag_id?: string
          updated_at?: string
          user_id?: string
          weight?: number
        }
        Relationships: [
          {
            foreignKeyName: "user_interests_tag_id_fkey"
            columns: ["tag_id"]
            isOneToOne: false
            referencedRelation: "tags"
            referencedColumns: ["id"]
          },
        ]
      }
      user_roles: {
        Row: {
          granted_at: string
          id: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Insert: {
          granted_at?: string
          id?: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Update: {
          granted_at?: string
          id?: string
          role?: Database["public"]["Enums"]["app_role"]
          user_id?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      admin_list_reas: {
        Args: {
          p_limit?: number
          p_offset?: number
          p_query?: string
          p_statuses: string[]
        }
        Returns: Json
      }
      admin_resolve_report: {
        Args: { p_decision: string; p_rea_id: string }
        Returns: undefined
      }
      admin_set_rea_status: {
        Args: { p_rea_id: string; p_status: string }
        Returns: undefined
      }
      decay_user_interests: { Args: never; Returns: undefined }
      ensure_favorites_collection: {
        Args: { _user_id: string }
        Returns: string
      }
      event_delta: {
        Args: {
          p_event: Database["public"]["Enums"]["rea_event_type"]
          p_value: number
        }
        Returns: number
      }
      get_admin_metrics: { Args: never; Returns: Json }
      get_moderation_queue: { Args: never; Returns: Json }
      get_recommended_feed: {
        Args: { p_limit?: number }
        Returns: {
          author: string
          created_at: string
          description: string
          education_level: Database["public"]["Enums"]["education_level"]
          format: Database["public"]["Enums"]["rea_format"]
          id: string
          language: Database["public"]["Enums"]["rea_language"]
          license: Database["public"]["Enums"]["rea_license"]
          rating_avg: number
          rating_count: number
          report_count: number
          resource_url: string
          score: number
          source_url: string
          status: Database["public"]["Enums"]["rea_status"]
          subject_area: string
          submitted_by: string
          tags: string[]
          thumbnail_url: string
          title: string
          updated_at: string
        }[]
      }
      has_role: {
        Args: {
          _role: Database["public"]["Enums"]["app_role"]
          _user_id: string
        }
        Returns: boolean
      }
    }
    Enums: {
      app_role: "admin" | "user"
      collection_visibility: "private" | "public"
      education_level:
        | "infantil"
        | "fundamental"
        | "medio"
        | "tecnico"
        | "graduacao"
        | "pos_graduacao"
        | "extensao"
        | "livre"
      interest_source: "manual" | "inferred"
      rea_event_type:
        | "view"
        | "search_click"
        | "save_to_collection"
        | "remove_from_collection"
        | "rating"
        | "rating_update"
        | "report"
      rea_format:
        | "video"
        | "audio"
        | "text"
        | "image"
        | "interactive"
        | "slides"
        | "other"
      rea_language: "pt_br" | "en" | "es" | "other"
      rea_license:
        | "cc_by"
        | "cc_by_sa"
        | "cc_by_nc"
        | "cc_by_nc_sa"
        | "cc_by_nd"
        | "cc0"
        | "public_domain"
        | "other"
      rea_status: "active" | "hidden_low_rating" | "blocked_review" | "removed"
      report_reason:
        | "inappropriate"
        | "broken_link"
        | "copyright"
        | "misinformation"
        | "spam"
        | "other"
      report_state: "pending" | "dismissed" | "accepted"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      app_role: ["admin", "user"],
      collection_visibility: ["private", "public"],
      education_level: [
        "infantil",
        "fundamental",
        "medio",
        "tecnico",
        "graduacao",
        "pos_graduacao",
        "extensao",
        "livre",
      ],
      interest_source: ["manual", "inferred"],
      rea_event_type: [
        "view",
        "search_click",
        "save_to_collection",
        "remove_from_collection",
        "rating",
        "rating_update",
        "report",
      ],
      rea_format: [
        "video",
        "audio",
        "text",
        "image",
        "interactive",
        "slides",
        "other",
      ],
      rea_language: ["pt_br", "en", "es", "other"],
      rea_license: [
        "cc_by",
        "cc_by_sa",
        "cc_by_nc",
        "cc_by_nc_sa",
        "cc_by_nd",
        "cc0",
        "public_domain",
        "other",
      ],
      rea_status: ["active", "hidden_low_rating", "blocked_review", "removed"],
      report_reason: [
        "inappropriate",
        "broken_link",
        "copyright",
        "misinformation",
        "spam",
        "other",
      ],
      report_state: ["pending", "dismissed", "accepted"],
    },
  },
} as const
