# Runs the three unattended Claude Code runs in order.
# Start from the repo root:  powershell -ExecutionPolicy Bypass -File .\run_all.ps1
# To run only one:           powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -Only 2
# One-off before the first run: start `claude` in this folder, accept the trust dialog, then /exit.

param([int]$Only = 0)

Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force runs | Out-Null

$course = "C:\Users\knbar\OneDrive\Skrivebord\AI in Accounting and Business"
$docs   = "C:\Users\knbar\Documents"

# Each run counts as finished only if the files it must produce exist.
$runs = @(
    @{ N = 1; File = "prompts/RUN1_inventory.md";  Needs = @("bank/questions.json", "bank/inventory.json", "MATERIALS_NOTES.md") },
    @{ N = 2; File = "prompts/RUN2_validation.md"; Needs = @("bank/exams.json", "VALIDATION_REPORT.md", "tests/validate.py") },
    @{ N = 3; File = "prompts/RUN3_site.md";       Needs = @("docs/index.html", "docs/js/app.js", "README.md") }
)

foreach ($r in $runs) {
    if ($Only -ne 0 -and $r.N -ne $Only) { continue }
    $out = "runs/run$($r.N).txt"
    $start = Get-Date
    "Run $($r.N) started $start" | Tee-Object -FilePath $out
    claude -p "Read CLAUDE.md, then read $($r.File) and carry out every step in it. Work unattended and do not ask questions." --permission-mode acceptEdits --add-dir "$course" --add-dir "$docs" *>> $out
    $code = $LASTEXITCODE
    $end = Get-Date
    $missing = @($r.Needs | Where-Object { -not (Test-Path $_) })
    "Run $($r.N) ended $end, exit code $code, minutes $([math]::Round(($end - $start).TotalMinutes, 1))" | Tee-Object -FilePath $out -Append
    if ($code -ne 0 -or $missing.Count -gt 0) {
        if ($missing.Count -gt 0) { "Missing after Run $($r.N): $($missing -join ', ')" | Tee-Object -FilePath $out -Append }
        "Run $($r.N) did not finish. Check $out and LOG.md, then rerun with -Only $($r.N). The run resumes from its checklist."
        exit 1
    }
}
"All requested runs finished. Read LOG.md."
