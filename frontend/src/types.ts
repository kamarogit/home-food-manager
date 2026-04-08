export type QuantityStatus = "多い" | "少ない" | "購入必要";

export type IngredientMaster = {
  id: number;
  name: string;
  category_id: number | null;
  category_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Category = {
  id: number;
  name: string;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type Ingredient = {
  id: number;
  ingredient_master_id: number;
  ingredient_name: string;
  ingredient_category: string | null;
  quantity_status: QuantityStatus;
  storage_location: string | null;
  expiry_date: string | null;
  opened_date: string | null;
  note: string | null;
  created_at: string;
  updated_at: string;
};

export type IngredientPayload = {
  ingredient_master_id: number;
  quantity_status: QuantityStatus;
  storage_location?: string | null;
  expiry_date?: string | null;
  opened_date?: string | null;
  note?: string | null;
};
