# Architektur (Kurzfassung)

- Addon (Lua) sammelt Snapshot-Daten & zeigt Tipps (kein Netz, keine Automatisierung).
- Extern: Docker-Stack mit `ollama` (LLM), `mcp` (FastAPI), `watcher` (Python).
- Datenfluss:
  - **Streaming:** `Logs/WoWCombatLog.txt` → watcher tail → MCP `/tools/ingest_combat_event`.
  - **Snapshot:** SavedVariables `AICompanion.lua` (Export-Button oder /reload) → watcher → MCP `/tools/generate_tips` → schreibt Tipps in `pendingReco` → im Spiel via Panel.
- Snapshot-Fokus v1: Quest-Status, Berufe, Zone/Map, Itemlevel und Open-World-Hinweise.
- Multi-Character-Basis: `characterKey` identifiziert Exporte und Empfehlungen accountweit.

- LLM-Strategie: primär lokal (Ollama `llama3.2`, Fallback `mistral-nemo`), optional API (OpenAI).
- i18n: UI DE/EN; Tipps in Client-Locale.
- Git-Flow: `develop` (Default), `feature/*` → PR → `develop`; Release via PR `develop → main` + Tag.

Siehe `docs/ADDON_RULES.md` & `docs/PRIVACY.md`.
