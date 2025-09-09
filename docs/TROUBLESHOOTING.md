# Troubleshooting

## MCP gibt 404 auf /tools/ping
- `server.py` Version prüfen: Ping/Healthz-Endpunkte vorhanden?
- Container neu bauen:
  ```bash
  docker compose build mcp && docker compose up -d mcp
  ```

## Watcher findet Dateien nicht

- ENV `SV_PATH`, `SV_WRITE`, `COMBATLOG_PATH` kontrollieren
- Prüfen, ob `./svshare` richtig gemountet/gesynct ist

## Keine Tipps im Spiel

- Nach Export `/reload` ausführen (SavedVariables werden geschrieben)
- Watcher-Logs checken (`ai-watcher`), ob Tipps generiert & zurückgeschrieben wurden
- `/aicoach tips` öffnet Panel

## CI: luacheck Permission-Error

- Workflow muss `luarocks --local install luacheck` + `$HOME/.luarocks/bin` → PATH setzen (siehe ci.yml im Repo)

## CI: black meckert

- Lokal Black installieren & ausführen:

  ```powershell
  black external/python/watcher.py
  ```
