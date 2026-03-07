# Umgebungsvariablen (ENV)

## Watcher (external/python/watcher.py)

| Variable | Default | Beschreibung |
|---|---|---|
| `SV_PATH` | (required) | Pfad zu AICompanion.lua (SavedVariables, lesen) |
| `SV_WRITE` | `= SV_PATH` | Pfad zu AICompanion.lua (Tipps zurückschreiben) — meist identisch |
| `COMBATLOG_PATH` | (required) | Pfad zu WoWCombatLog.txt |
| `MCP_URL` | `http://mcp:8080` | Basis-URL des MCP-Servers |
| `TIPS_COUNT` | `5` | Anzahl Tipps pro Analyse |
| `POLL_INTERVAL` | `2.0` | Abfrage-Intervall in Sekunden |

## MCP-Server (mcp-server/server.py)

### Provider-Auswahl

| Variable | Default | Beschreibung |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | LLM-Backend: `ollama`, `openai` oder `openrouter` |
| `LLM_MODE` | `local` | **Veraltet** – Backward-Compat: `local` = ollama, `api` = openai. Wird ignoriert wenn `LLM_PROVIDER` gesetzt ist. |

### Ollama (lokal)

| Variable | Default | Beschreibung |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API Endpoint |
| `OLLAMA_MODEL` | `llama3.2` | Primäres Modell |
| `OLLAMA_FALLBACK_MODEL` | `mistral-nemo` | Fallback wenn primäres Modell fehlschlägt |

### OpenAI

| Variable | Default | Beschreibung |
|---|---|---|
| `OPENAI_API_KEY` | (required) | OpenAI API Key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI Modellname |

### OpenRouter

| Variable | Default | Beschreibung |
|---|---|---|
| `OPENROUTER_API_KEY` | (required) | OpenRouter API Key ([openrouter.ai](https://openrouter.ai)) |
| `OPENROUTER_MODEL` | `anthropic/claude-sonnet-4` | Modell über OpenRouter (siehe [Modell-Liste](https://openrouter.ai/models)) |

## Beispiel .env

```bash
# Lokaler Ollama (Default)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2

# Oder: OpenRouter mit Claude
# LLM_PROVIDER=openrouter
# OPENROUTER_API_KEY=sk-or-v1-...
# OPENROUTER_MODEL=anthropic/claude-sonnet-4

# Oder: OpenAI direkt
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
```
