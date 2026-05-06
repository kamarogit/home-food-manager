import type {
  Category,
  Ingredient,
  IngredientMaster,
  IngredientPayload,
  QuantityStatus,
  StorageLocation,
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

export function createIngredientMaster(
  name: string,
  categoryId: number | null,
  options?: { name_reading?: string | null; aliases?: string | null },
) {
  return request<IngredientMaster>("/ingredient-masters", {
    method: "POST",
    body: JSON.stringify({
      name,
      category_id: categoryId,
      name_reading: options?.name_reading ?? null,
      aliases: options?.aliases ?? null,
    }),
  });
}

export function createIngredientMasterWithDefault(
  name: string,
  categoryId: number | null,
  defaultStorageLocation: string | null,
  options?: { name_reading?: string | null; aliases?: string | null },
) {
  return request<IngredientMaster>("/ingredient-masters", {
    method: "POST",
    body: JSON.stringify({
      name,
      category_id: categoryId,
      default_storage_location: defaultStorageLocation,
      name_reading: options?.name_reading ?? null,
      aliases: options?.aliases ?? null,
    }),
  });
}

export function patchIngredientMaster(
  id: number,
  payload: Partial<
    Pick<
      IngredientMaster,
      | "name"
      | "name_reading"
      | "aliases"
      | "category_id"
      | "default_storage_location"
      | "is_active"
    >
  >,
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

export function patchCategory(
  id: number,
  payload: Partial<Pick<Category, "name" | "sort_order" | "is_active">>,
) {
  return request<Category>(`/categories/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listStorageLocations(includeInactive = true) {
  return request<StorageLocation[]>(`/storage-locations?include_inactive=${includeInactive}`);
}

export function createStorageLocation(name: string, sortOrder = 0) {
  return request<StorageLocation>("/storage-locations", {
    method: "POST",
    body: JSON.stringify({ name, sort_order: sortOrder }),
  });
}

export function patchStorageLocation(
  id: number,
  payload: Partial<Pick<StorageLocation, "name" | "sort_order" | "is_active">>,
) {
  return request<StorageLocation>(`/storage-locations/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
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
