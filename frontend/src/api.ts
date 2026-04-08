import type {
  Category,
  Ingredient,
  IngredientMaster,
  IngredientPayload,
  QuantityStatus,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export function listIngredientMasters(includeInactive = true) {
  return request<IngredientMaster[]>(`/ingredient-masters?include_inactive=${includeInactive}`);
}

export function createIngredientMaster(name: string, categoryId: number | null) {
  return request<IngredientMaster>("/ingredient-masters", {
    method: "POST",
    body: JSON.stringify({ name, category_id: categoryId }),
  });
}

export function patchIngredientMaster(
  id: number,
  payload: Partial<Pick<IngredientMaster, "name" | "category_id" | "is_active">>,
) {
  return request<IngredientMaster>(`/ingredient-masters/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listCategories(includeInactive = true) {
  return request<Category[]>(`/categories?include_inactive=${includeInactive}`);
}

export function createCategory(name: string, sortOrder = 0) {
  return request<Category>("/categories", {
    method: "POST",
    body: JSON.stringify({ name, sort_order: sortOrder }),
  });
}

type IngredientFilter = {
  name?: string;
  storage_location?: string;
  quantity_status?: QuantityStatus;
  expiry_before?: string;
  has_opened_date?: boolean;
};

export function listIngredients(filter: IngredientFilter = {}) {
  const params = new URLSearchParams();
  Object.entries(filter).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return request<Ingredient[]>(`/ingredients${query ? `?${query}` : ""}`);
}

export function createIngredient(payload: IngredientPayload) {
  return request<Ingredient>("/ingredients", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function patchIngredient(id: number, payload: Partial<IngredientPayload>) {
  return request<Ingredient>(`/ingredients/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteIngredient(id: number) {
  return request<void>(`/ingredients/${id}`, { method: "DELETE" });
}
