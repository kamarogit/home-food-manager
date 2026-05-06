# home-food-manager

家庭用食材管理MVP（FastAPI + React + FastMCP）です。  
このリポジトリは Docker Compose で動作する構成です。

バックエンド・MCP をローカルでテストする場合は **Python 3.13**（`backend` / `mcp_server` の Dockerfile と同じ）を使ってください。  
[pyenv](https://github.com/pyenv/pyenv) や [asdf](https://asdf-vm.com/) を使う場合、リポジトリ直下の `.python-version` が 3.13 を指します。

## 起動

```bash
docker compose up --build
```

- Web UI: `http://localhost:5173`
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## 初期データを LLM エージェントに任せる

保存場所・カテゴリ・食材マスタを API 経由で大量登録する手順は、エージェント向けに **[docs/AGENT_BULK_SETUP.md](docs/AGENT_BULK_SETUP.md)** にまとめています。サンプル JSON は **[docs/templates/](docs/templates/)**（`bulk-seed.example.json` など）を参照してください。

## MCP サーバ起動

MCP サーバは通常起動から分離し、必要なときだけ profile 付きで起動します。

```bash
docker compose --profile mcp up --build
```

## 停止

```bash
docker compose down
```

データ（SQLite）は named volume `backend_data` に保存されます。  
完全初期化する場合は以下を実行してください。

```bash
docker compose down -v
```
