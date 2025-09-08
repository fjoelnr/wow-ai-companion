# WoW AI Companion (Coach)

Ein **ToS-konformer** World of Warcraft Copilot: gibt **Tipps & Hinweise**, automatisiert **nichts**.
- Addon (Lua) sammelt Daten & zeigt Empfehlungen.
- Externe Analyse (Docker, Linux) via MCP-Server + LLM (lokal über Ollama oder API).
- Fokus v1: Erkundung/Quests/Sammelziele/Rares. Kampf-Coach später.

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
