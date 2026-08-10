[CmdletBinding()]
param(
    [ValidateSet("fixture", "live", "preserve")][string]$Mode = "fixture",
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$AttemptMarkerPath,
    [string]$RuntimeDirectory,
    [string]$AdminOutputDirectory
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
$dataPath = Join-Path $outputPath "data/v2"
$runtimePath = if ([string]::IsNullOrWhiteSpace($RuntimeDirectory)) {
    Join-Path $env:TEMP ("country-issue-cloud-pages-" + [guid]::NewGuid())
} else {
    [System.IO.Path]::GetFullPath($RuntimeDirectory)
}
$runtimeLeaf = Split-Path -Leaf $runtimePath
$runtimeInProject = $runtimePath.StartsWith(
    $projectPath.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase
)
$runtimeInTemp = $runtimePath.StartsWith(
    $tempPath.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase
)
if (
    -not [string]::IsNullOrWhiteSpace($RuntimeDirectory) -and
    ($runtimeLeaf -ne "pages-data" -or (-not $runtimeInProject -and -not $runtimeInTemp))
) {
    throw "Runtime directory must end with 'pages-data' under the project or temp directory."
}
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
Copy-Item -LiteralPath (Join-Path $frontendPath "favicon.svg") -Destination $outputPath
Copy-Item -LiteralPath (Join-Path $frontendPath "styles.css") -Destination $outputPath
Copy-Item -LiteralPath (Join-Path $frontendPath "src") -Destination $outputPath -Recurse
New-Item -ItemType File -Path (Join-Path $outputPath ".nojekyll") | Out-Null

if ($Mode -eq "fixture") {
    & $uvCommand run --project (Join-Path $projectRoot "backend") python -m app.batch.cli publish-keyword-fixture `
        --evaluation-dir (Join-Path $projectRoot "sample-data/evaluation") `
        --data-dir $runtimePath `
        --site-data-dir $dataPath
} elseif ($Mode -eq "live") {
    if ([string]::IsNullOrWhiteSpace($AttemptMarkerPath)) {
        throw "Live mode requires an attempt marker path."
    }
    $markerPath = [System.IO.Path]::GetFullPath($AttemptMarkerPath)
    $markerRoot = [System.IO.Path]::GetFullPath(
        (Join-Path $projectRoot ".runtime/pages-run-marker")
    )
    if (-not $markerPath.StartsWith(
        $markerRoot.TrimEnd('\') + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Attempt marker must be stored under .runtime/pages-run-marker."
    }
    if (-not (Test-Path -LiteralPath $markerPath)) {
        throw "Live attempt marker must be persisted before collection starts."
    }
    & $uvCommand run --project (Join-Path $projectRoot "backend") python -m app.batch.cli publish-keyword-live `
        --sources-config (Join-Path $projectRoot "config/sources.example.yml") `
        --data-dir $runtimePath `
        --site-data-dir $dataPath `
        --lookback-hours 24 `
        --enable-newsdata
} else {
    & $uvCommand run --project (Join-Path $projectRoot "backend") python -m app.batch.cli publish-existing-keyword-data `
        --data-dir $runtimePath `
        --site-data-dir $dataPath
}
$generationExitCode = $LASTEXITCODE
if ($Mode -eq "live" -and -not [string]::IsNullOrWhiteSpace($AdminOutputDirectory)) {
    $adminPath = [System.IO.Path]::GetFullPath($AdminOutputDirectory)
    $adminLeaf = Split-Path -Leaf $adminPath
    if (
        $adminLeaf -ne "admin" -or
        -not $adminPath.StartsWith(
            $projectPath.TrimEnd('\') + '\',
            [System.StringComparison]::OrdinalIgnoreCase
        )
    ) {
        throw "Admin output directory must end with 'admin' under the project directory."
    }
    if (Test-Path -LiteralPath $adminPath) {
        Remove-Item -LiteralPath $adminPath -Recurse -Force
    }
    New-Item -ItemType Directory -Path $adminPath | Out-Null
    $diagnostics = Join-Path $runtimePath "runtime/collection-diagnostics.json"
    $articles = Join-Path $runtimePath "runtime/admin/selected-articles.json"
    if (Test-Path -LiteralPath $diagnostics) {
        Copy-Item -LiteralPath $diagnostics -Destination $adminPath
    }
    if (Test-Path -LiteralPath $articles) {
        Copy-Item -LiteralPath $articles -Destination $adminPath
    }
}
if ($generationExitCode -ne 0) {
    throw "Pages data generation failed with exit code $generationExitCode"
}

& (Join-Path $PSScriptRoot "check-public-artifact.ps1") -Path $outputPath
if ($LASTEXITCODE -ne 0) {
    throw "Public artifact validation failed with exit code $LASTEXITCODE"
}
