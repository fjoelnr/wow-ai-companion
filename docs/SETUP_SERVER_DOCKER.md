# Setup: Docker-Host (Linux/Windows)

## 1) .env (optional, für API-Fallback)
Erstelle im Repo-Root:

OPENAI_API_KEY="dein-api-schlüssel-hier"

## 2) docker-compose.yml (bereit im Repo)
Services:
- `ollama`: lokales LLM
- `mcp`: MCP-Server (FastAPI)
- `watcher`: liest SavedVariables & tailt CombatLog

## 3) Volumes/Share
Stelle sicher, dass `./svshare` die beiden Dateien enthält:
- `WTF/.../SavedVariables/AICompanion.lua`
- `Logs/WoWCombatLog.txt`

## 4) Start
```bash
docker compose up -d --build
````

## 5) Modelle (einmalig) für Ollama

```bash
curl http://localhost:11434/api/pull -d '{"name":"gpt-oss:20b"}'
curl http://localhost:11434/api/pull -d '{"name":"mistral:7b"}'
```

## 6) Healthchecks

```bash
curl http://localhost:8080/healthz
curl http://localhost:8080/tools/ping
```

## 7) Logs

```bash
docker logs -f ai-mcp
docker logs -f ai-watcher
```
