$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$IncomingFolder = "C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"
$ManualFolder = Join-Path $IncomingFolder "manual"
$LogDir = Join-Path $ProjectRoot "logs"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "weekly_invoice_processing_$Stamp.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-RunLog {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
}

Set-Location $ProjectRoot
Start-Transcript -Path $LogFile -Append | Out-Null

try {
    Write-RunLog "Weekly invoice check started."
    Write-RunLog "Incoming folder: $IncomingFolder"

    if (-not (Test-Path -LiteralPath $IncomingFolder)) {
        throw "Incoming folder does not exist: $IncomingFolder"
    }

    $pdfFiles = Get-ChildItem -LiteralPath $IncomingFolder -File -Filter "*.pdf" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notlike "$ManualFolder*" }

    if (-not $pdfFiles -or $pdfFiles.Count -eq 0) {
        Write-RunLog "No PDF invoices found in EingangsRG. Nothing to process."
        exit 0
    }

    Write-RunLog ("PDF invoices found: {0}. Starting AI-enabled processing." -f $pdfFiles.Count)

    $env:PROCESSING_MODE = "report_only"
    $env:TELEGRAM_ENABLED = "true"
    $env:OPENAI_ENABLED = "true"
    $env:PYTHONIOENCODING = "utf-8"

    & python (Join-Path $ProjectRoot "process_pdf_v7_3.py")
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "Invoice processor failed with exit code $exitCode"
    }

    Write-RunLog "Weekly invoice processing finished successfully."
    exit 0
}
catch {
    Write-RunLog ("ERROR: {0}" -f $_.Exception.Message)
    exit 1
}
finally {
    Stop-Transcript | Out-Null
}
