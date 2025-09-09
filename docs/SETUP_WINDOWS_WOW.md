# Setup: Windows Gaming-PC (WoW)

## 1) WoW-Addon
Kopiere:
````

<repo>\addon\AICompanion → <WoW>\_retail_\Interface\AddOns\AICompanion

```
Im Spiel: `/aicoach` (Hilfe), `/aicoach tips`, Export-Prompt erscheint automatisch bei bestimmten Ereignissen.

## 2) Combatlog
Im Spiel einmalig:
```

/combatlog

````
Dadurch schreibt WoW fortlaufend `Logs/WoWCombatLog.txt` (live streambar für die externe Analyse).

## 3) SavedVariables & Logs freigeben
Empfehlung: SMB (Windows-Freigabe) oder Syncthing.
- Freigeben:
  - `…\_retail_\WTF\Account\<ACCOUNT>\SavedVariables\AICompanion.lua`
  - `…\_retail_\Logs\WoWCombatLog.txt`
- Auf dem Docker-Host in `./svshare` einhängen/spiegeln.
  - Beispiel SMB-Mount (Linux-Host):
    ```bash
    sudo mkdir -p /srv/svshare
    sudo mount -t cifs //WINPC/ShareName /srv/svshare -o username=<user>,password=<pwd>,ro,iocharset=utf8
    ```

## 4) Optional: VS Code Aufgaben
Lege dir eine Task an, die das Addon in den AddOns-Ordner kopiert (für schnelle Iterationen).

