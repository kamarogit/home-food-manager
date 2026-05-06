import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  createCategory,
  createIngredient,
  createIngredientMasterWithDefault,
  createStorageLocation,
  deleteIngredient,
  listCategories,
  listIngredientMasters,
  listIngredients,
  listStorageLocations,
  patchCategory,
  patchIngredient,
  patchIngredientMaster,
  patchStorageLocation,
} from "./api";
import type { Category, Ingredient, IngredientMaster, QuantityStatus, StorageLocation } from "./types";
import "./App.css";

const quantityOptions: QuantityStatus[] = ["多い", "少ない", "購入必要"];
type AdminTab = "ingredient" | "master" | "category" | "storage";
type StockListTab = "purchase" | "expired";
type InventorySortKey =
  | "updated_at"
  | "storage_location"
  | "expiry_date"
  | "opened_date"
  | "ingredient_name"
  | "quantity_status";
type InventoryHeaderPanel = "ingredient_name" | "quantity_status" | "storage_location" | "expiry_date" | null;

function isAdminTab(value: string | null): value is AdminTab {
  return value === "ingredient" || value === "master" || value === "category" || value === "storage";
}

function resolveInitialTab(): AdminTab {
  if (typeof window === "undefined") {
    return "ingredient";
  }
  const params = new URLSearchParams(window.location.search);
  const tabFromQuery = params.get("tab");
  if (isAdminTab(tabFromQuery)) {
    return tabFromQuery;
  }
  const tabFromStorage = window.localStorage.getItem("activeAdminTab");
  return isAdminTab(tabFromStorage) ? tabFromStorage : "ingredient";
}

function App() {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window === "undefined") {
      return "light";
    }
    const stored = window.localStorage.getItem("theme");
    return stored === "dark" ? "dark" : "light";
  });
  const [masters, setMasters] = useState<IngredientMaster[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [storageLocations, setStorageLocations] = useState<StorageLocation[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [searchName, setSearchName] = useState("");
  const [searchStatus, setSearchStatus] = useState("");
  const [searchLocation, setSearchLocation] = useState("");
  const [activeTab, setActiveTab] = useState<AdminTab>(resolveInitialTab);
  const [form, setForm] = useState({
    id: 0,
    ingredient_master_id: "",
    quantity_status: "少ない" as QuantityStatus,
    storage_location: "未設定",
    expiry_date: "",
    opened_date: "",
    note: "",
  });
  const [masterForm, setMasterForm] = useState({
    id: 0,
    name: "",
    nameReading: "",
    aliases: "",
    categoryId: "",
    defaultStorageLocation: "未設定",
  });
  const [categoryForm, setCategoryForm] = useState({ name: "" });
  const [masterFilterCategoryId, setMasterFilterCategoryId] = useState("");
  const [masterFilterStorageLocation, setMasterFilterStorageLocation] = useState("");
  const [showInactiveMasters, setShowInactiveMasters] = useState(false);
  const [stockListTab, setStockListTab] = useState<StockListTab>("purchase");
  const [storageLocationForm, setStorageLocationForm] = useState({ name: "" });
  const [masterQuery, setMasterQuery] = useState("");
  const [showMasterOptions, setShowMasterOptions] = useState(false);
  const [highlightedMasterIndex, setHighlightedMasterIndex] = useState(0);
  const [inventorySortKey, setInventorySortKey] = useState<InventorySortKey>("updated_at");
  const [inventorySortOrder, setInventorySortOrder] = useState<"asc" | "desc">("desc");
  const [inventoryFilterLocation, setInventoryFilterLocation] = useState("");
  const [inventoryFilterQuantity, setInventoryFilterQuantity] = useState("");
  const [inventoryHeaderPanel, setInventoryHeaderPanel] = useState<InventoryHeaderPanel>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [pendingDeleteItem, setPendingDeleteItem] = useState<Ingredient | null>(null);
  const [editForm, setEditForm] = useState({
    id: 0,
    ingredient_master_id: "",
    quantity_status: "少ない" as QuantityStatus,
    storage_location: "未設定",
    expiry_date: "",
    opened_date: "",
    note: "",
  });

  const purchaseNeeded = useMemo(
    () => ingredients.filter((item) => item.quantity_status === "購入必要"),
    [ingredients],
  );
  const expiredItems = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return ingredients.filter((item) => {
      if (!item.expiry_date) {
        return false;
      }
      const expiry = new Date(item.expiry_date);
      expiry.setHours(0, 0, 0, 0);
      return expiry < today;
    });
  }, [ingredients]);
  const filteredMasters = useMemo(
    () =>
      masters.filter((master) => {
        if (!showInactiveMasters && !master.is_active) {
          return false;
        }
        if (masterFilterCategoryId && String(master.category_id ?? "") !== masterFilterCategoryId) {
          return false;
        }
        if (masterFilterStorageLocation) {
          const storage = master.default_storage_location ?? "未設定";
          if (storage !== masterFilterStorageLocation) {
            return false;
          }
        }
        return true;
      }),
    [masters, masterFilterCategoryId, masterFilterStorageLocation, showInactiveMasters],
  );
  const activeStorageOptions = useMemo(() => {
    const names = storageLocations.filter((s) => s.is_active).map((s) => s.name);
    return [...names, "未設定"];
  }, [storageLocations]);
  const storageFilterOptions = useMemo(() => {
    const names = storageLocations.map((s) => s.name);
    return [...new Set([...names, "未設定"])];
  }, [storageLocations]);
  const activeMasters = useMemo(() => masters.filter((m) => m.is_active), [masters]);
  const filteredActiveMasters = useMemo(() => {
    const query = masterQuery.trim().toLowerCase();
    if (!query) {
      return activeMasters.slice(0, 20);
    }
    return activeMasters
      .filter((m) => {
        const hay = `${m.name} ${m.category_name ?? ""} ${m.name_reading ?? ""} ${m.aliases ?? ""}`.toLowerCase();
        return hay.includes(query);
      })
      .slice(0, 20);
  }, [activeMasters, masterQuery]);
  const displayedIngredients = useMemo(() => {
    const filtered = ingredients.filter((item) => {
      if (inventoryFilterLocation && (item.storage_location ?? "未設定") !== inventoryFilterLocation) {
        return false;
      }
      if (inventoryFilterQuantity && item.quantity_status !== inventoryFilterQuantity) {
        return false;
      }
      return true;
    });

    const sorted = [...filtered].sort((a, b) => {
      let left = "";
      let right = "";
      if (inventorySortKey === "updated_at") {
        left = a.updated_at ?? "";
        right = b.updated_at ?? "";
      } else if (inventorySortKey === "storage_location") {
        left = a.storage_location ?? "未設定";
        right = b.storage_location ?? "未設定";
      } else if (inventorySortKey === "expiry_date") {
        left = a.expiry_date ?? "9999-12-31";
        right = b.expiry_date ?? "9999-12-31";
      } else if (inventorySortKey === "opened_date") {
        left = a.opened_date ?? "9999-12-31";
        right = b.opened_date ?? "9999-12-31";
      } else if (inventorySortKey === "ingredient_name") {
        left = a.ingredient_name;
        right = b.ingredient_name;
      } else {
        left = a.quantity_status;
        right = b.quantity_status;
      }
      const compared = left.localeCompare(right, "ja");
      return inventorySortOrder === "asc" ? compared : -compared;
    });
    return sorted;
  }, [ingredients, inventoryFilterLocation, inventoryFilterQuantity, inventorySortKey, inventorySortOrder]);

  const refreshMasters = async () => setMasters(await listIngredientMasters(true));
  const refreshCategories = async () => setCategories(await listCategories(true));
  const refreshStorageLocations = async () => setStorageLocations(await listStorageLocations(true));
  const refreshIngredients = async () => {
    setIngredients(
      await listIngredients({
        name: searchName || undefined,
        quantity_status: (searchStatus as QuantityStatus) || undefined,
        storage_location: searchLocation || undefined,
      }),
    );
  };

  useEffect(() => {
    refreshMasters().catch(console.error);
    refreshCategories().catch(console.error);
    refreshStorageLocations().catch(console.error);
    refreshIngredients().catch(console.error);
  }, []);

  useEffect(() => {
    window.localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    const handlePopState = () => {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get("tab");
      setActiveTab(isAdminTab(tab) ? tab : "ingredient");
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("tab") === activeTab) {
      return;
    }
    params.set("tab", activeTab);
    const query = params.toString();
    const nextUrl = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
    window.history.replaceState({}, "", nextUrl);
    window.localStorage.setItem("activeAdminTab", activeTab);
  }, [activeTab]);

  async function onSubmitIngredient(e: FormEvent) {
    e.preventDefault();
    if (!form.ingredient_master_id) {
      return;
    }
    const payload = {
      ingredient_master_id: Number(form.ingredient_master_id),
      quantity_status: form.quantity_status,
      storage_location: form.storage_location || null,
      expiry_date: form.expiry_date || null,
      opened_date: form.opened_date || null,
      note: form.note || null,
    };
    if (form.id > 0) {
      await patchIngredient(form.id, payload);
    } else {
      await createIngredient(payload);
    }
    setForm({
      id: 0,
      ingredient_master_id: "",
      quantity_status: "少ない",
      storage_location: "未設定",
      expiry_date: "",
      opened_date: "",
      note: "",
    });
    setMasterQuery("");
    await refreshIngredients();
  }

  async function onSubmitMaster(e: FormEvent) {
    e.preventDefault();
    const categoryId = masterForm.categoryId ? Number(masterForm.categoryId) : null;
    const defaultStorageLocation =
      masterForm.defaultStorageLocation === "未設定" ? null : masterForm.defaultStorageLocation;
    const nameReading = masterForm.nameReading.trim() || null;
    const aliases = masterForm.aliases.trim() || null;
    if (masterForm.id > 0) {
      await patchIngredientMaster(masterForm.id, {
        name: masterForm.name,
        name_reading: nameReading,
        aliases,
        category_id: categoryId,
        default_storage_location: defaultStorageLocation,
      });
    } else {
      await createIngredientMasterWithDefault(masterForm.name, categoryId, defaultStorageLocation, {
        name_reading: nameReading,
        aliases,
      });
    }
    setMasterForm({
      id: 0,
      name: "",
      nameReading: "",
      aliases: "",
      categoryId: "",
      defaultStorageLocation: "未設定",
    });
    await refreshMasters();
  }

  async function onSubmitCategory(e: FormEvent) {
    e.preventDefault();
    await createCategory(categoryForm.name);
    setCategoryForm({ name: "" });
    await refreshCategories();
  }

  async function onSubmitStorageLocation(e: FormEvent) {
    e.preventDefault();
    await createStorageLocation(storageLocationForm.name);
    setStorageLocationForm({ name: "" });
    await refreshStorageLocations();
  }

  function selectMaster(master: IngredientMaster) {
    setForm((p) => ({
      ...p,
      ingredient_master_id: String(master.id),
      storage_location: master.default_storage_location ?? "未設定",
    }));
    setMasterQuery(master.category_name ? `${master.name} (${master.category_name})` : master.name);
    setShowMasterOptions(false);
  }

  function toggleInventorySort(key: InventorySortKey) {
    if (inventorySortKey === key) {
      setInventorySortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setInventorySortKey(key);
      setInventorySortOrder("asc");
    }
  }

  function sortIndicator(key: InventorySortKey) {
    if (inventorySortKey !== key) {
      return "";
    }
    return inventorySortOrder === "asc" ? "↑" : "↓";
  }

  function openEditModal(item: Ingredient) {
    setEditForm({
      id: item.id,
      ingredient_master_id: String(item.ingredient_master_id),
      quantity_status: item.quantity_status,
      storage_location: item.storage_location ?? "未設定",
      expiry_date: item.expiry_date ?? "",
      opened_date: item.opened_date ?? "",
      note: item.note ?? "",
    });
    setIsEditModalOpen(true);
  }

  async function onSubmitEditModal(e: FormEvent) {
    e.preventDefault();
    if (!editForm.ingredient_master_id) {
      return;
    }
    await patchIngredient(editForm.id, {
      ingredient_master_id: Number(editForm.ingredient_master_id),
      quantity_status: editForm.quantity_status,
      storage_location: editForm.storage_location || null,
      expiry_date: editForm.expiry_date || null,
      opened_date: editForm.opened_date || null,
      note: editForm.note || null,
    });
    setIsEditModalOpen(false);
    await refreshIngredients();
  }

  async function onConfirmDeleteExpired() {
    if (!pendingDeleteItem) {
      return;
    }
    await deleteIngredient(pendingDeleteItem.id);
    setPendingDeleteItem(null);
    await refreshIngredients();
  }

  return (
    <main className={`app ${theme === "dark" ? "app--dark" : "app--light"}`}>
      <section className="app__hero">
        <div className="hero-top">
          <div>
            <h1 className="app__title">家庭用食材管理 MVP</h1>
            <p className="app__subtitle">在庫を見える化して、買い忘れと重複購入を減らします。</p>
          </div>
          <button
            type="button"
            className="secondary"
            onClick={() => setTheme((prev) => (prev === "light" ? "dark" : "light"))}
          >
            {theme === "light" ? "ダークテーマ" : "ライトテーマ"}
          </button>
        </div>
      </section>

      <div className="grid">
        <section className="card">
          <h2>検索・絞り込み</h2>
          <div className="controls-row">
            <input value={searchName} onChange={(e) => setSearchName(e.target.value)} placeholder="食材名" />
            <select value={searchStatus} onChange={(e) => setSearchStatus(e.target.value)}>
              <option value="">残量すべて</option>
              {quantityOptions.map((q) => (
                <option key={q} value={q}>
                  {q}
                </option>
              ))}
            </select>
            <select value={searchLocation} onChange={(e) => setSearchLocation(e.target.value)}>
              <option value="">保存場所すべて</option>
              {activeStorageOptions.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
            <button onClick={() => refreshIngredients().catch(console.error)}>検索</button>
          </div>
        </section>

        <section className="card card--wide">
          <h2>在庫一覧</h2>
          {inventoryHeaderPanel && (
            <div className="table-toolbar">
              {inventoryHeaderPanel === "quantity_status" && (
                <select value={inventoryFilterQuantity} onChange={(e) => setInventoryFilterQuantity(e.target.value)}>
                  <option value="">残量フィルター: すべて</option>
                  {quantityOptions.map((q) => (
                    <option key={q} value={q}>
                      {q}
                    </option>
                  ))}
                </select>
              )}
              {inventoryHeaderPanel === "storage_location" && (
                <select value={inventoryFilterLocation} onChange={(e) => setInventoryFilterLocation(e.target.value)}>
                  <option value="">場所フィルター: すべて</option>
                  {storageFilterOptions.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
              )}
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setInventorySortKey("updated_at");
                  setInventorySortOrder("desc");
                  setInventoryFilterLocation("");
                  setInventoryFilterQuantity("");
                  setInventoryHeaderPanel(null);
                }}
              >
                リセット
              </button>
            </div>
          )}
          <p className="empty-note">表示件数: {displayedIngredients.length} / 全件: {ingredients.length}</p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>
                    <button type="button" className="header-button" onClick={() => toggleInventorySort("ingredient_name")}>
                      食材 {sortIndicator("ingredient_name")}
                    </button>
                  </th>
                  <th>
                    <button
                      type="button"
                      className="header-button"
                      onClick={() => {
                        toggleInventorySort("quantity_status");
                        setInventoryHeaderPanel((prev) => (prev === "quantity_status" ? null : "quantity_status"));
                      }}
                    >
                      残量 {sortIndicator("quantity_status")}
                    </button>
                  </th>
                  <th>
                    <button
                      type="button"
                      className="header-button"
                      onClick={() => {
                        toggleInventorySort("storage_location");
                        setInventoryHeaderPanel((prev) => (prev === "storage_location" ? null : "storage_location"));
                      }}
                    >
                      場所 {sortIndicator("storage_location")}
                    </button>
                  </th>
                  <th>
                    <button type="button" className="header-button" onClick={() => toggleInventorySort("expiry_date")}>
                      期限 {sortIndicator("expiry_date")}
                    </button>
                  </th>
                  <th>
                    <button type="button" className="header-button" onClick={() => toggleInventorySort("opened_date")}>
                      開封日 {sortIndicator("opened_date")}
                    </button>
                  </th>
                  <th>メモ</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {displayedIngredients.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.ingredient_name}</td>
                    <td>{item.quantity_status}</td>
                    <td>{item.storage_location ?? ""}</td>
                    <td>{item.expiry_date ?? ""}</td>
                    <td>{item.opened_date ?? ""}</td>
                    <td>{item.note ?? ""}</td>
                    <td>
                      <div className="inline-actions">
                        <button
                          onClick={() => openEditModal(item)}
                        >
                          編集
                        </button>
                        <button
                          className="secondary"
                          onClick={async () => {
                            await deleteIngredient(item.id);
                            await refreshIngredients();
                          }}
                        >
                          削除
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="card">
          <h2>購入必要一覧</h2>
          <div className="tab-row">
            <button
              type="button"
              className={stockListTab === "purchase" ? "tab-button is-active" : "tab-button"}
              onClick={() => setStockListTab("purchase")}
            >
              購入必要
            </button>
            <button
              type="button"
              className={stockListTab === "expired" ? "tab-button is-active" : "tab-button"}
              onClick={() => setStockListTab("expired")}
            >
              期限切れ
            </button>
          </div>
          {stockListTab === "purchase" ? (
            purchaseNeeded.length > 0 ? (
              <ul className="pill-list">
                {purchaseNeeded.map((item) => (
                  <li
                    key={item.id}
                    className="clickable-pill"
                    onClick={() => openEditModal(item)}
                    title="クリックで編集"
                  >
                    {item.ingredient_name}（{item.storage_location ?? "未設定"}）
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty-note">購入必要の在庫はありません。</p>
            )
          ) : expiredItems.length > 0 ? (
            <ul className="pill-list">
              {expiredItems.map((item) => (
                <li
                  key={item.id}
                  className="clickable-pill danger"
                  onClick={() => setPendingDeleteItem(item)}
                  title="クリックで削除確認"
                >
                  {item.ingredient_name}（期限: {item.expiry_date}）
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-note">期限切れの在庫はありません。</p>
          )}
        </section>

        <section className="card">
          <h2>管理タブ</h2>
          <div className="tab-row">
            <button
              type="button"
              className={activeTab === "ingredient" ? "tab-button is-active" : "tab-button"}
              onClick={() => setActiveTab("ingredient")}
            >
              在庫登録
            </button>
            <button
              type="button"
              className={activeTab === "master" ? "tab-button is-active" : "tab-button"}
              onClick={() => setActiveTab("master")}
            >
              マスタ管理
            </button>
            <button
              type="button"
              className={activeTab === "category" ? "tab-button is-active" : "tab-button"}
              onClick={() => setActiveTab("category")}
            >
              カテゴリ管理
            </button>
            <button
              type="button"
              className={activeTab === "storage" ? "tab-button is-active" : "tab-button"}
              onClick={() => setActiveTab("storage")}
            >
              保存場所管理
            </button>
          </div>

          {activeTab === "ingredient" && (
            <div className="tab-panel">
              <h3>{form.id > 0 ? "在庫編集" : "在庫登録"}</h3>
              <form onSubmit={onSubmitIngredient} className="stack">
                <div className="combo-box">
                  <input
                    required
                    value={masterQuery}
                    placeholder="食材を検索して選択"
                    onFocus={() => setShowMasterOptions(true)}
                    onChange={(e) => {
                      setMasterQuery(e.target.value);
                      setShowMasterOptions(true);
                      setHighlightedMasterIndex(0);
                      setForm((p) => ({ ...p, ingredient_master_id: "" }));
                    }}
                    onKeyDown={(e) => {
                      if (!showMasterOptions) {
                        return;
                      }
                      if (e.key === "ArrowDown") {
                        e.preventDefault();
                        setHighlightedMasterIndex((idx) => Math.min(idx + 1, filteredActiveMasters.length - 1));
                      } else if (e.key === "ArrowUp") {
                        e.preventDefault();
                        setHighlightedMasterIndex((idx) => Math.max(idx - 1, 0));
                      } else if (e.key === "Enter" && filteredActiveMasters.length > 0) {
                        e.preventDefault();
                        selectMaster(filteredActiveMasters[highlightedMasterIndex] ?? filteredActiveMasters[0]);
                      } else if (e.key === "Escape") {
                        setShowMasterOptions(false);
                      }
                    }}
                    onBlur={() => setTimeout(() => setShowMasterOptions(false), 120)}
                  />
                  {showMasterOptions && (
                    <div className="combo-box__menu">
                      {filteredActiveMasters.length > 0 ? (
                        filteredActiveMasters.map((master, index) => (
                          <button
                            type="button"
                            key={master.id}
                            className={
                              index === highlightedMasterIndex
                                ? "combo-box__item is-highlighted"
                                : "combo-box__item"
                            }
                            onMouseDown={(e) => e.preventDefault()}
                            onClick={() => selectMaster(master)}
                          >
                            {master.name}
                            {master.category_name ? ` (${master.category_name})` : ""}
                          </button>
                        ))
                      ) : (
                        <div className="combo-box__empty">候補が見つかりません</div>
                      )}
                    </div>
                  )}
                </div>
                <select
                  value={form.quantity_status}
                  onChange={(e) => setForm((p) => ({ ...p, quantity_status: e.target.value as QuantityStatus }))}
                >
                  {quantityOptions.map((q) => (
                    <option key={q} value={q}>
                      {q}
                    </option>
                  ))}
                </select>
                <select
                  value={form.storage_location}
                  onChange={(e) => setForm((p) => ({ ...p, storage_location: e.target.value }))}
                >
                  {activeStorageOptions.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
                <label>
                  期限
                  <input
                    type="date"
                    value={form.expiry_date}
                    onChange={(e) => setForm((p) => ({ ...p, expiry_date: e.target.value }))}
                  />
                </label>
                <label>
                  開封日
                  <input
                    type="date"
                    value={form.opened_date}
                    onChange={(e) => setForm((p) => ({ ...p, opened_date: e.target.value }))}
                  />
                </label>
                <textarea value={form.note} onChange={(e) => setForm((p) => ({ ...p, note: e.target.value }))} />
                <button type="submit">{form.id > 0 ? "更新" : "登録"}</button>
              </form>
            </div>
          )}

          {activeTab === "master" && (
            <div className="tab-panel">
              <h3>{masterForm.id > 0 ? "食材マスタ編集" : "食材マスタ管理"}</h3>
              <form onSubmit={onSubmitMaster} className="stack">
                <input
                  value={masterForm.name}
                  onChange={(e) => setMasterForm((p) => ({ ...p, name: e.target.value }))}
                  placeholder="食材名（正式名称・一意）"
                  required
                />
                <input
                  value={masterForm.nameReading}
                  onChange={(e) => setMasterForm((p) => ({ ...p, nameReading: e.target.value }))}
                  placeholder="よみがな（任意・LLM検索用）"
                />
                <label className="field-label">
                  別名・表記ゆれ（任意・1行に1つ。LLMが埋めてもOK）
                  <textarea
                    rows={3}
                    value={masterForm.aliases}
                    onChange={(e) => setMasterForm((p) => ({ ...p, aliases: e.target.value }))}
                  />
                </label>
                <div className="controls-row">
                <select
                  value={masterForm.categoryId}
                  onChange={(e) => setMasterForm((p) => ({ ...p, categoryId: e.target.value }))}
                >
                  <option value="">カテゴリ未設定</option>
                  {categories.filter((c) => c.is_active).map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
                <select
                  value={masterForm.defaultStorageLocation}
                  onChange={(e) => setMasterForm((p) => ({ ...p, defaultStorageLocation: e.target.value }))}
                >
                  {storageFilterOptions.map((loc) => (
                    <option key={loc} value={loc}>
                      デフォルト保存場所: {loc}
                    </option>
                  ))}
                </select>
                <button type="submit">{masterForm.id > 0 ? "更新" : "追加"}</button>
                {masterForm.id > 0 && (
                  <button
                    type="button"
                    className="secondary"
                    onClick={() =>
                      setMasterForm({
                        id: 0,
                        name: "",
                        nameReading: "",
                        aliases: "",
                        categoryId: "",
                        defaultStorageLocation: "未設定",
                      })
                    }
                  >
                    編集をキャンセル
                  </button>
                )}
                </div>
              </form>
              <div className="section-divider" />
              <div className="subsection-label">登録済みマスタの絞り込み</div>
              <label className="toggle-row">
                <input
                  type="checkbox"
                  checked={showInactiveMasters}
                  onChange={(e) => setShowInactiveMasters(e.target.checked)}
                />
                無効化済みのマスタも表示
              </label>
              <div className="controls-row">
                <select value={masterFilterCategoryId} onChange={(e) => setMasterFilterCategoryId(e.target.value)}>
                  <option value="">カテゴリ: すべて</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
                <select
                  value={masterFilterStorageLocation}
                  onChange={(e) => setMasterFilterStorageLocation(e.target.value)}
                >
                  <option value="">デフォルト保存場所: すべて</option>
                  {storageFilterOptions.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
              </div>
              <ul className="compact-list">
                {filteredMasters.map((m) => (
                  <li key={m.id}>
                    <div className="list-row">
                      <div className="list-row__main">
                        <strong>{m.name}</strong>
                        <span className="list-row__sub">
                          読み: {m.name_reading ?? "-"} / 別名:{" "}
                          {m.aliases ? m.aliases.replace(/\n/g, "、") : "-"} / カテゴリ: {m.category_name ?? "-"} /
                          既定保存場所: {m.default_storage_location ?? "未設定"}
                        </span>
                      </div>
                      <span className={m.is_active ? "status-badge is-active" : "status-badge is-inactive"}>
                        {m.is_active ? "有効" : "無効"}
                      </span>
                      <button
                        className="row-action"
                        onClick={() =>
                          setMasterForm({
                            id: m.id,
                            name: m.name,
                            nameReading: m.name_reading ?? "",
                            aliases: m.aliases ?? "",
                            categoryId: m.category_id ? String(m.category_id) : "",
                            defaultStorageLocation: m.default_storage_location ?? "未設定",
                          })
                        }
                      >
                        編集
                      </button>
                      <button
                        className="secondary row-action"
                        onClick={() =>
                          patchIngredientMaster(m.id, { is_active: !m.is_active }).then(refreshMasters)
                        }
                      >
                        {m.is_active ? "無効化" : "有効化"}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {activeTab === "category" && (
            <div className="tab-panel">
              <h3>カテゴリ管理</h3>
              <form onSubmit={onSubmitCategory} className="controls-row">
                <input
                  value={categoryForm.name}
                  onChange={(e) => setCategoryForm({ name: e.target.value })}
                  placeholder="カテゴリ名"
                  required
                />
                <button type="submit">追加</button>
              </form>
              <ul className="compact-list">
                {categories.map((c) => (
                  <li key={c.id}>
                    <div className="list-row">
                      <div className="list-row__main">
                        <strong>{c.name}</strong>
                      </div>
                      <span className={c.is_active ? "status-badge is-active" : "status-badge is-inactive"}>
                        {c.is_active ? "有効" : "無効"}
                      </span>
                      <button
                        className="secondary row-action"
                        onClick={() =>
                          patchCategory(c.id, { is_active: !c.is_active }).then(refreshCategories)
                        }
                      >
                        {c.is_active ? "無効化" : "有効化"}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {activeTab === "storage" && (
            <div className="tab-panel">
              <h3>保存場所管理</h3>
              <form onSubmit={onSubmitStorageLocation} className="controls-row">
                <input
                  value={storageLocationForm.name}
                  onChange={(e) => setStorageLocationForm({ name: e.target.value })}
                  placeholder="保存場所名"
                  required
                />
                <button type="submit">追加</button>
              </form>
              <ul className="compact-list">
                {storageLocations.map((loc) => (
                  <li key={loc.id}>
                    <div className="list-row">
                      <div className="list-row__main">
                        <strong>{loc.name}</strong>
                      </div>
                      <span className={loc.is_active ? "status-badge is-active" : "status-badge is-inactive"}>
                        {loc.is_active ? "有効" : "無効"}
                      </span>
                      <button
                        className="secondary row-action"
                        onClick={() =>
                          patchStorageLocation(loc.id, { is_active: !loc.is_active }).then(
                            refreshStorageLocations,
                          )
                        }
                      >
                        {loc.is_active ? "無効化" : "有効化"}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
      {isEditModalOpen && (
        <div className="modal-backdrop" onClick={() => setIsEditModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>在庫を編集</h3>
            <form onSubmit={onSubmitEditModal} className="stack">
              <select
                required
                value={editForm.ingredient_master_id}
                onChange={(e) =>
                  setEditForm((p) => {
                    const selectedMaster = masters.find((m) => String(m.id) === e.target.value);
                    return {
                      ...p,
                      ingredient_master_id: e.target.value,
                      storage_location: selectedMaster?.default_storage_location ?? "未設定",
                    };
                  })
                }
              >
                <option value="">食材を選択</option>
                {masters
                  .filter((m) => m.is_active || String(m.id) === editForm.ingredient_master_id)
                  .map((master) => (
                    <option key={master.id} value={master.id}>
                      {master.name}
                    </option>
                  ))}
              </select>
              <select
                value={editForm.quantity_status}
                onChange={(e) =>
                  setEditForm((p) => ({ ...p, quantity_status: e.target.value as QuantityStatus }))
                }
              >
                {quantityOptions.map((q) => (
                  <option key={q} value={q}>
                    {q}
                  </option>
                ))}
              </select>
              <select
                value={editForm.storage_location}
                onChange={(e) => setEditForm((p) => ({ ...p, storage_location: e.target.value }))}
              >
                {activeStorageOptions.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
              <label>
                期限
                <input
                  type="date"
                  value={editForm.expiry_date}
                  onChange={(e) => setEditForm((p) => ({ ...p, expiry_date: e.target.value }))}
                />
              </label>
              <label>
                開封日
                <input
                  type="date"
                  value={editForm.opened_date}
                  onChange={(e) => setEditForm((p) => ({ ...p, opened_date: e.target.value }))}
                />
              </label>
              <textarea value={editForm.note} onChange={(e) => setEditForm((p) => ({ ...p, note: e.target.value }))} />
              <div className="inline-actions">
                <button type="submit">更新</button>
                <button type="button" className="secondary" onClick={() => setIsEditModalOpen(false)}>
                  キャンセル
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {pendingDeleteItem && (
        <div className="modal-backdrop" onClick={() => setPendingDeleteItem(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>期限切れ在庫を削除</h3>
            <p className="empty-note">
              「{pendingDeleteItem.ingredient_name}」を削除します。よろしいですか？
            </p>
            <div className="inline-actions">
              <button type="button" className="danger-button" onClick={onConfirmDeleteExpired}>
                削除する
              </button>
              <button type="button" className="secondary" onClick={() => setPendingDeleteItem(null)}>
                キャンセル
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

export default App;
