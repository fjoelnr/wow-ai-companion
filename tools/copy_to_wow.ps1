$source = "$PSScriptRoot\..\addon\AICompanion\"
$dest   = "C:\Program Files (x86)\World of Warcraft\_retail_\Interface\AddOns\AICompanion\"
if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
Copy-Item -Path $source -Destination $dest -Recurse
Write-Host "Addon kopiert. Starte WoW oder nutze /reload."
