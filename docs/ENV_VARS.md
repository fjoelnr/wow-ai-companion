# Umgebungsvariablen (ENV)

## Watcher (external/python/watcher.py)
- `SV_PATH`   : Pfad zu AICompanion.lua (SavedVariables, lesen)
- `SV_WRITE`  : Pfad zu AICompanion.lua (Tipps zurückschreiben) — meist identisch
- `COMBATLOG_PATH` : Pfad zu WoWCombatLog.txt
- `MCP_URL`   : Basis-URL des MCP-Servers (z. B. http://mcp:8080 oder http://localhost:8080)
- `TIPS_COUNT`: Anzahl Tipps (Default 5)
- `POLL_INTERVAL`: Abfrage-Intervall in Sekunden (Default 2.0)

## MCP-Server (mcp-server/server.py)
- `LLM_MODE`  : `local` | `api`
- `OLLAMA_BASE_URL` : z. B. `http://ollama:11434`
- `OLLAMA_MODEL`    : z. B. `gpt-oss:20b`
- `OLLAMA_FALLBACK_MODEL` : z. B. `mistral:7b`
- `OPENAI_API_KEY`  : falls `LLM_MODE=api`
- `OPENAI_MODEL`    : z. B. `gpt-5-mini`
