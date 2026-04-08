# home-food-manager

家庭用食材管理MVP（FastAPI + React + FastMCP）です。  
このリポジトリは Docker Compose で動作する構成です。

## 起動

```bash
docker compose up --build
```

- Web UI: `http://localhost:5173`
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

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
