# GitHub CI / Branch-Protection

## Branching
- `main`   : Releases
- `develop`: laufende stabile Entwicklung (Default)
- `feature/*`: Arbeitszweige → PR nach `develop`

## Workflows
- `.github/workflows/ci.yml`:
  - Job `addon`: Luacheck via LuaRocks (local install)
  - Job `python`: ruff + black + pytest
- `.github/workflows/release.yml`:
  - Zip baut & Release anlegt (bei Tag auf `main`)

## Required Checks (empfohlen)
- Für `develop` & `main`: `addon`, `python` (strict, up-to-date)

## Review-Pflicht
- Solo-Dev: auf `develop` optional disabled
- Auf `main`: aktiv lassen (bewusste Releases)

## gh-CLI Snippets
Default-Branch:
```bash
gh api -X PATCH repos/<owner>/<repo> -f default_branch=develop
````

Branch-Protection (kann über die UI unter Settings → Branches konfiguriert werden).
