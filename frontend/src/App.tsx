import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  createCategory,
  createIngredient,
  createIngredientMaster,
  deleteIngredient,
  listCategories,
  listIngredientMasters,
  listIngredients,
  patchIngredient,
  patchIngredientMaster,
} from "./api";
import type { Category, Ingredient, IngredientMaster, QuantityStatus } from "./types";

const quantityOptions: QuantityStatus[] = ["多い", "少ない", "購入必要"];
const storageOptions = ["冷蔵", "冷凍", "野菜室", "常温", "棚", "その他", "未設定"];

function App() {
  const [masters, setMasters] = useState<IngredientMaster[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [searchName, setSearchName] = useState("");
  const [searchStatus, setSearchStatus] = useState("");
  const [searchLocation, setSearchLocation] = useState("");
  const [form, setForm] = useState({
    id: 0,
    ingredient_master_id: "",
    quantity_status: "少ない" as QuantityStatus,
    storage_location: "未設定",
    expiry_date: "",
    opened_date: "",
    note: "",
  });
  const [masterForm, setMasterForm] = useState({ name: "", categoryId: "" });
  const [categoryForm, setCategoryForm] = useState({ name: "" });

  const purchaseNeeded = useMemo(
    () => ingredients.filter((item) => item.quantity_status === "購入必要"),
    [ingredients],
  );

  const refreshMasters = async () => setMasters(await listIngredientMasters(true));
  const refreshCategories = async () => setCategories(await listCategories(true));
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
    refreshIngredients().catch(console.error);
  }, []);

  async function onSubmitIngredient(e: FormEvent) {
    e.preventDefault();
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
    await refreshIngredients();
  }

  async function onSubmitMaster(e: FormEvent) {
    e.preventDefault();
    await createIngredientMaster(
      masterForm.name,
      masterForm.categoryId ? Number(masterForm.categoryId) : null,
    );
    setMasterForm({ name: "", categoryId: "" });
    await refreshMasters();
  }

  async function onSubmitCategory(e: FormEvent) {
    e.preventDefault();
    await createCategory(categoryForm.name);
    setCategoryForm({ name: "" });
    await refreshCategories();
  }

  return (
    <main style={{ fontFamily: "sans-serif", maxWidth: 1100, margin: "0 auto", padding: 16 }}>
      <h1>家庭用食材管理 MVP</h1>

      <section>
        <h2>検索・絞り込み</h2>
        <div style={{ display: "flex", gap: 8 }}>
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
            {storageOptions.map((loc) => (
              <option key={loc} value={loc}>
                {loc}
              </option>
            ))}
          </select>
          <button onClick={() => refreshIngredients().catch(console.error)}>検索</button>
        </div>
      </section>

      <section>
        <h2>在庫一覧</h2>
        <table width="100%" cellPadding={6}>
          <thead>
            <tr>
              <th>ID</th>
              <th>食材</th>
              <th>残量</th>
              <th>場所</th>
              <th>期限</th>
              <th>開封日</th>
              <th>メモ</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {ingredients.map((item) => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td>{item.ingredient_name}</td>
                <td>{item.quantity_status}</td>
                <td>{item.storage_location ?? ""}</td>
                <td>{item.expiry_date ?? ""}</td>
                <td>{item.opened_date ?? ""}</td>
                <td>{item.note ?? ""}</td>
                <td>
                  <button
                    onClick={() =>
                      setForm({
                        id: item.id,
                        ingredient_master_id: String(item.ingredient_master_id),
                        quantity_status: item.quantity_status,
                        storage_location: item.storage_location ?? "未設定",
                        expiry_date: item.expiry_date ?? "",
                        opened_date: item.opened_date ?? "",
                        note: item.note ?? "",
                      })
                    }
                  >
                    編集
                  </button>
                  <button
                    onClick={async () => {
                      await deleteIngredient(item.id);
                      await refreshIngredients();
                    }}
                  >
                    削除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>購入必要一覧</h2>
        <ul>
          {purchaseNeeded.map((item) => (
            <li key={item.id}>
              {item.ingredient_name}（{item.storage_location ?? "未設定"}）
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>{form.id > 0 ? "在庫編集" : "在庫登録"}</h2>
        <form onSubmit={onSubmitIngredient} style={{ display: "grid", gap: 8, maxWidth: 480 }}>
          <select
            required
            value={form.ingredient_master_id}
            onChange={(e) => setForm((p) => ({ ...p, ingredient_master_id: e.target.value }))}
          >
            <option value="">食材を選択</option>
            {masters.filter((m) => m.is_active).map((master) => (
              <option key={master.id} value={master.id}>
                {master.name}
              </option>
            ))}
          </select>
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
            {storageOptions.map((loc) => (
              <option key={loc} value={loc}>
                {loc}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={form.expiry_date}
            onChange={(e) => setForm((p) => ({ ...p, expiry_date: e.target.value }))}
          />
          <input
            type="date"
            value={form.opened_date}
            onChange={(e) => setForm((p) => ({ ...p, opened_date: e.target.value }))}
          />
          <textarea value={form.note} onChange={(e) => setForm((p) => ({ ...p, note: e.target.value }))} />
          <button type="submit">{form.id > 0 ? "更新" : "登録"}</button>
        </form>
      </section>

      <section>
        <h2>食材マスタ管理</h2>
        <form onSubmit={onSubmitMaster} style={{ display: "flex", gap: 8 }}>
          <input
            value={masterForm.name}
            onChange={(e) => setMasterForm((p) => ({ ...p, name: e.target.value }))}
            placeholder="食材名"
            required
          />
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
          <button type="submit">追加</button>
        </form>
        <ul>
          {masters.map((m) => (
            <li key={m.id}>
              {m.name} ({m.category_name ?? "-"}) / {m.is_active ? "有効" : "無効"}
              {m.is_active && (
                <button onClick={() => patchIngredientMaster(m.id, { is_active: false }).then(refreshMasters)}>
                  無効化
                </button>
              )}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>カテゴリ管理</h2>
        <form onSubmit={onSubmitCategory} style={{ display: "flex", gap: 8 }}>
          <input
            value={categoryForm.name}
            onChange={(e) => setCategoryForm({ name: e.target.value })}
            placeholder="カテゴリ名"
            required
          />
          <button type="submit">追加</button>
        </form>
        <ul>
          {categories.map((c) => (
            <li key={c.id}>
              {c.name} / {c.is_active ? "有効" : "無効"}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

export default App;
