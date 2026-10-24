# Waits for the current Run 3 to end. If it ended without building the site
# (for example because the Pro usage limit was reached), retries every 20 minutes.
# Start from the repo root:  powershell -ExecutionPolicy Bypass -File .\watchdog.ps1

Set-Location $PSScriptRoot
$out = "runs/run3.txt"
$needs = @("docs/index.html", "docs/js/app.js", "README.md")
$maxChecks = 21   # 21 x 20 minutes = 7 hours

function Get-Stamp { (Get-Date).ToString("dd.MM.yyyy HH:mm") }
function Test-Done { @($needs | Where-Object { -not (Test-Path $_) }).Count -eq 0 }
function Test-Ended { (Test-Path $out) -and (Select-String -Path $out -Pattern "Run 3 ended" -Quiet) }

for ($i = 1; $i -le $maxChecks; $i++) {
    if (Test-Ended) {
        if (Test-Done) {
            "$(Get-Stamp) Run 3 has finished and the site files exist. Watchdog stops."
            exit 0
        }
        "$(Get-Stamp) Run 3 ended without the site files. Starting it again (check $i of $maxChecks)."
        powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -Only 3
        if (Test-Done) { continue }
        "$(Get-Stamp) Retry did not finish. Waiting 20 minutes before the next try."
        Start-Sleep -Seconds 1200
        continue
    }
    "$(Get-Stamp) Run 3 still running. Next check in 20 minutes ($i of $maxChecks)."
    Start-Sleep -Seconds 1200
}
"$(Get-Stamp) Gave up after $maxChecks checks. Read LOG.md and runs/run3.txt."
