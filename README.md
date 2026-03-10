# WoW AI Companion (Coach)

➡ **Schnellstart:** siehe [`docs/QUICKSTART_DE.md`](docs/QUICKSTART_DE.md)  
Weitere Doku:
- Setup Windows (WoW): [`docs/SETUP_WINDOWS_WOW.md`](docs/SETUP_WINDOWS_WOW.md)
- Setup Docker-Host: [`docs/SETUP_SERVER_DOCKER.md`](docs/SETUP_SERVER_DOCKER.md)
- ENV Variablen: [`docs/ENV_VARS.md`](docs/ENV_VARS.md)
- CI/Branch-Protection: [`docs/CI_GITHUB.md`](docs/CI_GITHUB.md)
- Git-Workflow: [`docs/WORKFLOW_GIT.md`](docs/WORKFLOW_GIT.md)
- Troubleshooting: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)

Ein **ToS-konformer** World of Warcraft Copilot: gibt **Tipps & Hinweise**, automatisiert **nichts**.
- Addon (Lua) sammelt Daten & zeigt Empfehlungen.
- Externe Analyse (Docker, Linux) via MCP-Server + LLM (lokal über Ollama oder API).
- Fokus v1: Erkundung/Quests/Sammelziele/Rares. Kampf-Coach später.

## ANR Context Layer

Dieses Repository wurde mit einer ANR-konformen Kontextschicht erweitert.

- Global context: `AGENTS.md`
- Repository map: `.agents/context-index.md`
- Local context: `addon/AGENT.md`, `agents/AGENT.md`, `mcp-server/AGENT.md`, `external/python/AGENT.md`, `docs/AGENT.md`, `tools/AGENT.md`
- Skills: `.agents/skills/`
- Workflows: `.agents/workflows/`
- Guardrails: `.agents/guardrails/`
- Manifest: `anr.yaml`

## Schnellstart (kurz)
1) Addon nach `_retail_/Interface/AddOns/AICompanion/` kopieren.  
2) Docker starten (`docker-compose.yml`) → `ollama`, `mcp`, `watcher`.  
3) Im Spiel: `/aicoach export` → extern Analyse → `/reload` → Tippspanel.

Siehe `docs/ARCHITECTURE.md` für Details.

## Branching
- `main` = Releases (tags)
- `develop` = stabile Entwicklungsbasis
- `feature/*` = PR → `develop`; Release via PR `develop → main` + Tag

## Lizenzen
- Addon (Lua): MIT (siehe `LICENSE`)
- External/MCP: Apache-2.0 (siehe `LICENSE-APACHE`)
