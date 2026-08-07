[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$workflow = Get-Content -LiteralPath (Join-Path $projectRoot ".github/workflows/pages.yml") -Raw
$builder = Get-Content -LiteralPath (Join-Path $PSScriptRoot "build-pages-site.ps1") -Raw

foreach ($cron in @('0 0 * * *', '0 1 * * *', '0 3 * * *')) {
    if (-not $workflow.Contains('cron: "' + $cron + '"')) {
        throw "Missing expected Pages cron: $cron"
    }
}
foreach ($required in @(
    'actions/cache/restore@v4',
    'lookup-only: true',
    'actions/cache/save@v4',
    "Persist today's live-attempt marker before collection",
    'force_live_retry',
    "needs.gate.outputs.should-run == 'true'"
)) {
    if (-not $workflow.Contains($required)) {
        throw "Missing Pages duplicate-run safeguard: $required"
    }
}
$claimIndex = $workflow.IndexOf("Claim today's live attempt")
$saveIndex = $workflow.IndexOf("Persist today's live-attempt marker before collection")
$buildIndex = $workflow.IndexOf("Build validated Pages artifact")
if (
    $claimIndex -lt 0 -or
    $saveIndex -lt $claimIndex -or
    $buildIndex -lt $saveIndex
) {
    throw "The live-attempt marker must be persisted before collection starts."
}
if (-not $builder.Contains('Live attempt marker must be persisted before collection starts.')) {
    throw "The Pages builder must reject live collection without a persisted marker."
}

Write-Host "PASS: Pages schedules and duplicate-run safeguards are present."
