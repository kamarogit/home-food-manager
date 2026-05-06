# エージェント向け: 初期マスタ一括登録ガイド

この文書は **LLM エージェントや自動化スクリプト**が、家庭用食材管理アプリ（home-food-manager）の API を通じて、**保存場所・カテゴリ・食材マスタ**を大量登録するときの仕様と手順をまとめたものです。人間が読んでも構いません。

**コピー用の JSON 例**は [templates/](templates/) にあります（`bulk-seed.example.json` ほか）。

## 前提

- **認証なし**（ローカル／信頼できるネットワーク想定）。インターネットに晒す構成では使わないでください。
- **ベース URL**（例）  
  - Docker Compose 既定: `http://localhost:8000`  
  - 別マシンから: `http://<ホストIP>:8000`
- **CORS**: フロントと API が別オリジンのときはバックエンドの環境変数 **`CORS_ORIGINS`** にフロントの URL を含める。詳細はリポジトリの `README.md` と `.env.example`。
- **Content-Type**: `application/json`
- **文字コード**: UTF-8。食材名・別名は日本語可。

## 登録の順序（重要）

1. **保存場所**（`POST /storage-locations`）  
2. **カテゴリ**（`POST /categories`）  
3. **食材マスタ**（`POST /ingredient-masters`）… `category_id` と、任意で `default_storage_location`（**保存場所の `name` と完全一致**）が必要

順序を守らないと、マスタ作成時に「有効なカテゴリ」「有効な保存場所」エラーになります。

## 既存データの確認

マイグレーションやシードで **カテゴリ・保存場所が既に入っている**ことがあります。二重登録は **409 Conflict** になるため、先に一覧を取得してください。

```http
GET /categories?include_inactive=true
GET /storage-locations?include_inactive=true
GET /ingredient-masters?include_inactive=true
```

- `include_inactive=false`（省略可）のときは **有効なものだけ**返ります。
- 食材マスタは `name` で部分一致検索: `GET /ingredient-masters?name=卵`

## エンドポイント仕様

### 保存場所

| 項目 | 内容 |
|------|------|
| 作成 | `POST /storage-locations` |
| 本文 | `{"name": string, "sort_order": number}`（`sort_order` 省略時は 0） |
| 制約 | `name` は 1〜100 文字、**一意** |
| 成功 | `201` + JSON（`id`, `name`, `is_active`, `sort_order`, …） |
| 重複 | `409`（保存場所名が重複） |

### カテゴリ

| 項目 | 内容 |
|------|------|
| 作成 | `POST /categories` |
| 本文 | `{"name": string, "sort_order": number}`（`sort_order` 省略時は 0） |
| 制約 | `name` は 1〜255 文字、**一意** |
| 成功 | `201` + JSON（`id`, `name`, …） |
| 重複 | `409`（カテゴリ名が重複） |

### 食材マスタ

| 項目 | 内容 |
|------|------|
| 作成 | `POST /ingredient-masters` |
| 本文 | 下表参照 |
| 制約 | `name` は **一意**（正式名称として登録。表記ゆれは `aliases` へ） |
| 成功 | `201` + JSON（`id`, `category_name`, …） |
| 重複 | `409`（食材マスタ名が重複） |
| 無効参照 | `400`（カテゴリ ID が無効／非アクティブ、保存場所名が DB に無い等） |

**`POST /ingredient-masters` ボディ（JSON）**

| フィールド | 必須 | 説明 |
|------------|------|------|
| `name` | はい | 食材の正式名（一意） |
| `category_id` | いいえ | 既存カテゴリの `id`。`null` 可 |
| `default_storage_location` | いいえ | **既存の保存場所 `name` と完全一致**。`null` または省略、または UI と同様に論理上の「未設定」扱いは **`"未設定"`** も可（この場合は保存場所マスタに行が無くてよい） |
| `default_expiry_days` | いいえ | 0〜3650。未開封の目安日数。**開封日入力時の期限自動計算にも同じ値が使われる** |
| `name_reading` | いいえ | 読み（ひらがな等） |
| `aliases` | いいえ | **別名・表記ゆれ。改行区切り**で複数可（アプリ・検索で利用） |

## エージェント向け運用ルール

1. **べき等性**: 同じ名前を再 `POST` すると 409 になる。大量投入前に `GET` で存在確認するか、409 を「既にある」とみなしてスキップする。
2. **ID の解決**: カテゴリ・保存場所を作ったらレスポンスの `id` / `name` をマップに保持し、マスタ作成で使う。
3. **`default_storage_location`**: 保存場所一覧に無い文字列を入れると **400**。必ず先に `POST /storage-locations` するか、`null` / `"未設定"` にする。
4. **`category_id`**: 無効 ID や無効化済みカテゴリは **400**。
5. **バッチの粒度**: API に一括エンドポイントは無い。ループで 1 件ずつ送る。レート制限は設けていないが、失敗時は本文を読んで再試行方針を決める。
6. **Swagger**: 人間・エージェントとも `GET /docs` で OpenAPI を確認できる。

## リクエスト例（curl）

置き換え: `BASE=http://localhost:8000`

```bash
# 保存場所
curl -sS -X POST "$BASE/storage-locations" \
  -H "Content-Type: application/json" \
  -d '{"name":"冷蔵","sort_order":0}'

# カテゴリ
curl -sS -X POST "$BASE/categories" \
  -H "Content-Type: application/json" \
  -d '{"name":"野菜","sort_order":0}'

# 食材マスタ（category_id は一覧で取得した値に差し替え）
curl -sS -X POST "$BASE/ingredient-masters" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "玉ねぎ",
    "category_id": 1,
    "default_storage_location": "冷蔵",
    "default_expiry_days": 14,
    "name_reading": "たまねぎ",
    "aliases": "タマネギ\n洋葱"
  }'
```

## 推奨ワークフロー（エージェント用プロンプトの骨子）

ユーザーから「冷蔵庫向けのカテゴリと食材を増やしたい」等の指示を受けたら:

1. `BASE` を環境変数またはユーザー確認で決める。
2. `GET /categories?include_inactive=true` と `GET /storage-locations?include_inactive=true` で現状把握。
3. 足りない保存場所・カテゴリだけ `POST`（409 はスキップ可）。
4. 各食材について `POST /ingredient-masters`。**`name` の重複に注意**（表記ゆれは `aliases`）。
5. 終了時に `GET /ingredient-masters?include_inactive=true` で件数確認（任意）。

## MCP について

リポジトリには **FastMCP** サーバ（`mcp_server/`）があり、食材マスタの作成・一覧やカテゴリ／保存場所の**一覧**などがツール化されています。**カテゴリ・保存場所の新規作成は MCP ツールに無い**ため、一括初期化では **HTTP の `POST /categories` と `POST /storage-locations` を直接呼ぶ**必要があります。

## 在庫（ingredients）について

本ガイドのスコープは **マスタ準備**までです。実在庫の登録は `POST /ingredients`（別仕様。`ingredient_master_id`・`quantity_status` 等が必要）。初期セットアップ後に別指示で扱ってください。

---

**まとめ**: エージェントは **保存場所 → カテゴリ → 食材マスタ**の順で HTTP API を叩き、**名前の一意制約と 409** を前提にべき等に動くと安全です。
