# 初期マスタ用 JSON テンプレート

エージェントやスクリプトが **コピーして編集**しやすいサンプルです。API の詳細は [AGENT_BULK_SETUP.md](../AGENT_BULK_SETUP.md) を参照してください。

## ファイル一覧

| ファイル | 用途 |
|----------|------|
| `storage-locations.sample.json` | `POST /storage-locations` 用。配列の各要素を 1 件ずつ POST。 |
| `categories.sample.json` | `POST /categories` 用。同上。 |
| `ingredient-masters.sample.json` | **1 行 1 マスタ**。`category_name` はカテゴリの `name` と一致させる。POST 前に `category_id` に変換する。 |
| `bulk-seed.example.json` | 上記をまとめた**例**（保存場所・カテゴリ・マスタ一式）。マスタは `category_name` 形式。 |

## 投入の流れ（エージェント向け）

1. `GET /storage-locations?include_inactive=true` と `GET /categories?include_inactive=true` で既存を確認。
2. `storage-locations.sample.json`（または `bulk-seed` 内の配列）の各要素を、無ければ `POST`（409 はスキップ）。
3. カテゴリも同様。
4. 食材マスタ: `category_name` → `GET /categories` の結果から `id` を引き、`POST /ingredient-masters` の JSON は **API 形**（`category_id` 整数、`default_storage_location` は保存場所の `name` と完全一致）に組み立てる。

## API 直送形式の例（マスタ 1 件）

```json
{
  "name": "玉ねぎ",
  "category_id": 1,
  "default_storage_location": "野菜室",
  "default_expiry_days": 14,
  "name_reading": "たまねぎ",
  "aliases": "タマネギ\n玉葱"
}
```

`default_storage_location` に `null` を使うか省略するか、`"未設定"` なら保存場所マスタに無くてよい。
