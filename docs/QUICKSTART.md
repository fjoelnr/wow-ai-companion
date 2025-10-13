# Quickstart (EN)

This is the default English quickstart guide.
See also `Quickstart_DE.md` for German translation.

## Prerequisites
- Git, Docker, Python / Miniconda installed
- WoW (Retail) installed

## Setup Steps
1. Clone the repo:
   ```
   git clone https://github.com/fjoelnr/wow-ai-companion.git
   cd wow-ai-companion
   ```
2. Install the addon into your WoW folder:
   `addon/AICompanion → <WoW>/Interface/AddOns/AICompanion`
3. Mirror or mount `svshare`:
   - `<WoW>/WTF/.../SavedVariables/AICompanion.lua`
   - `<WoW>/Logs/WoWCombatLog.txt`
4. Start Docker stack:
   ```
   docker compose up -d --build
   ```
5. Validate MCP server:
   ```
   curl http://localhost:8080/tools/ping
   ```
6. In-game: `/aicoach export` then `/aicoach tips`

— END OF Quickstart (EN) —
