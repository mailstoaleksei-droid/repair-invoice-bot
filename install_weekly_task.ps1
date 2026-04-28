$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptPath = Join-Path $ProjectRoot "weekly_process_invoices.ps1"
$TaskName = "Repair Eingang Bot Weekly Invoice Processing"

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Weekly script not found: $ScriptPath"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9:00AM

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Description "AI-enabled weekly invoice PDF processing from EingangsRG. Excludes manual folder." `
    -Force | Out-Null

Write-Host "Scheduled task installed: $TaskName"
