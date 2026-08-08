[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$workflow = Get-Content -LiteralPath (Join-Path $projectRoot ".github/workflows/pages.yml") -Raw
$builder = Get-Content -LiteralPath (Join-Path $PSScriptRoot "build-pages-site.ps1") -Raw
$publicSmoke = Get-Content -LiteralPath (Join-Path $PSScriptRoot "check-public-site.ps1") -Raw

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
    'if [[ "${{ github.event_name }}" == "schedule" ]]',
    'mode="fixture"',
    'environment: pages-production',
    'NAVER_CLIENT_ID: ${{ secrets.NAVER_CLIENT_ID }}',
    'NAVER_CLIENT_SECRET: ${{ secrets.NAVER_CLIENT_SECRET }}',
    'NEWSDATA_API_KEY: ${{ secrets.NEWSDATA_API_KEY }}',
    "needs.gate.outputs.should-run == 'true'"
)) {
    if (-not $workflow.Contains($required)) {
        throw "Missing Pages duplicate-run safeguard: $required"
    }
}
if (-not $workflow.Contains('mode="live"')) {
    throw "Scheduled Pages runs must select live data mode."
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
foreach ($required in @('publish-keyword-fixture', 'publish-keyword-live', 'data/v2')) {
    if (-not $builder.Contains($required)) {
        throw "Pages builder is missing the v2 keyword path: $required"
    }
}
if (-not $builder.Contains('--enable-newsdata')) {
    throw "The live Pages builder must enable the NewsData supplement."
}
foreach ($required in @(
    'public-smoke:',
    'if: ${{ always() }}',
    'check-public-site.ps1',
    'github.repository_owner',
    'github.event.repository.name'
)) {
    if (-not $workflow.Contains($required)) {
        throw "Pages workflow is missing the public smoke safeguard: $required"
    }
}
foreach ($required in @('https', 'data/v2/latest.json', 'data/v2/dates.json', 'data-dialog')) {
    if (-not $publicSmoke.Contains($required)) {
        throw "Public smoke script is missing a required contract check: $required"
    }
}
if (-not $publicSmoke.Contains('[System.IO.Path]::GetTempPath()')) {
    throw "Public smoke must use a cross-platform temporary directory."
}
if ($publicSmoke.Contains('$LASTEXITCODE -ne 0')) {
    throw "Public smoke must rely on PowerShell exception propagation."
}

Write-Host "PASS: Pages schedules and duplicate-run safeguards are present."
