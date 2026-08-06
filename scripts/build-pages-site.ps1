[CmdletBinding()]
param(
    [ValidateSet("fixture", "live")][string]$Mode = "fixture",
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$outputPath = [System.IO.Path]::GetFullPath($OutputDirectory)
$outputLeaf = Split-Path -Leaf $outputPath
if ($outputLeaf -notin @("site", "preview-site")) {
    throw "Output directory must end with 'site' or 'preview-site'."
}
$pathRoot = [System.IO.Path]::GetPathRoot($outputPath)
$projectPath = [System.IO.Path]::GetFullPath($projectRoot)
$tempPath = [System.IO.Path]::GetFullPath($env:TEMP)
$isProjectChild = $outputPath.StartsWith(
    $projectPath.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase
)
$isTempChild = $outputPath.StartsWith(
    $tempPath.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase
)
if (
    $outputPath -eq $pathRoot -or
    $outputPath -eq $projectPath -or
    (-not $isProjectChild -and -not $isTempChild)
) {
    throw "Refusing to replace a broad output directory."
}
$frontendPath = Join-Path $projectRoot "frontend"
$dataPath = Join-Path $outputPath "data/v1"
$runtimePath = Join-Path $env:TEMP ("country-issue-cloud-pages-" + [guid]::NewGuid())
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCommand) {
    $uvCommand = Join-Path $projectRoot ".tools/uv/bin/uv.exe"
}

if (Test-Path -LiteralPath $outputPath) {
    Remove-Item -LiteralPath $outputPath -Recurse -Force
}
New-Item -ItemType Directory -Path $outputPath | Out-Null
Copy-Item -LiteralPath (Join-Path $frontendPath "index.html") -Destination $outputPath
Copy-Item -LiteralPath (Join-Path $frontendPath "about.html") -Destination $outputPath
Copy-Item -LiteralPath (Join-Path $frontendPath "styles.css") -Destination $outputPath
Copy-Item -LiteralPath (Join-Path $frontendPath "src") -Destination $outputPath -Recurse
New-Item -ItemType File -Path (Join-Path $outputPath ".nojekyll") | Out-Null

if ($Mode -eq "fixture") {
    & $uvCommand run --project (Join-Path $projectRoot "backend") python -m app.batch.cli publish-fixture `
        --fixture (Join-Path $projectRoot "sample-data/fixtures/issues_2026-08-03.json") `
        --data-dir $runtimePath `
        --site-data-dir $dataPath
} else {
    & $uvCommand run --project (Join-Path $projectRoot "backend") python -m app.batch.cli publish-live `
        --sources-config (Join-Path $projectRoot "config/sources.example.yml") `
        --data-dir $runtimePath `
        --site-data-dir $dataPath `
        --lookback-hours 168
}
if ($LASTEXITCODE -ne 0) {
    throw "Pages data generation failed with exit code $LASTEXITCODE"
}

& (Join-Path $PSScriptRoot "check-public-artifact.ps1") -Path $outputPath
if ($LASTEXITCODE -ne 0) {
    throw "Public artifact validation failed with exit code $LASTEXITCODE"
}
