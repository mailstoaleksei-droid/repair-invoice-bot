param(
    [string]$Message = "Project sync"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$checklistPath = Join-Path $projectRoot "PROJECT_CHECKLIST_2026-03-27.md"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

if (Test-Path $checklistPath) {
    Add-Content -Path $checklistPath -Value "- [x] Sync $timestamp - $Message"
}

Push-Location $projectRoot
try {
    git add -A
    git commit -m $Message
    git push origin main
}
finally {
    Pop-Location
}
