# Arbeitsablauf (Git)

## Neues Feature
```bash
git switch develop
git pull
git switch -c feature/<kurzbeschreibung>
# Änderungen...
git commit -m "feat: ..."
git push -u origin feature/<kurzbeschreibung>
gh pr create --base develop --head feature/<kurzbeschreibung> --title "..." --body "..."
````

## Merge nach develop

* Checks grün, ggf. Review → Squash-Merge (empfohlen).

## Release

```bash
# PR develop -> main mergen (Checks + Review)
git checkout main
git pull
git tag v0.1.0
git push origin v0.1.0
# Release-Workflow lädt ZIP hoch
```
