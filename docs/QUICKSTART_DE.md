# Quickstart (DE)

Dieser Leitfaden bringt dich von 0 → laufendes System (Addon + Watcher + MCP).

## Voraussetzungen
- Windows-PC mit WoW (_retail_)
- Git, Docker Desktop, VS Code
- Optional: Miniconda (für lokale Python-Tools)
- Linux-Server **oder** derselbe Windows-PC für Docker (localhost)

## 1) Repo klonen
```bash
git clone https://github.com/fjoelnr/wow-ai-companion.git
cd wow-ai-companion
````

## 2) Addon installieren

Kopiere den Ordner:

```
addon/AICompanion → <WoW>\_retail_\Interface\AddOns\AICompanion
```

Im Spiel `/aicoach` testen (Panel/Slash-Befehle sichtbar?).

## 3) SavedVariables & Combatlog freigeben

* Stelle sicher, dass **/combatlog** im Spiel aktiviert wurde (einmal ins Chatfenster eingeben).
* Teile/Spiegele **beide Pfade** in `./svshare` (SMB, Syncthing, rsync):

  * `…\_retail_\WTF\Account\<ACCOUNT>\SavedVariables\AICompanion.lua`
  * `…\_retail_\Logs\WoWCombatLog.txt`

## 4) Docker-Stack starten

```bash
docker compose up -d --build
# (einmalig) Modelle für Ollama ziehen:
curl http://localhost:11434/api/pull -d '{"name":"gpt-oss:20b"}'
curl http://localhost:11434/api/pull -d '{"name":"mistral:7b"}'
```

## 5) MCP-Server prüfen

```bash
curl http://localhost:8080/healthz       # -> {"ok": true}
curl http://localhost:8080/tools/ping     # -> {"pong": true}
```

## 6) End-to-End

1. Im Spiel: `/aicoach export`
2. Watcher-Logs: `docker logs -f ai-watcher` (Tipps sollten generiert werden)
3. Im Spiel: `/aicoach tips` (Tipps-Panel)
