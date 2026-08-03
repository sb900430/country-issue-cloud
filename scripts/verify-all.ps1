[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCommand) {
    $localUv = Join-Path $projectRoot ".tools/uv/bin/uv.exe"
    if (Test-Path -LiteralPath $localUv) {
        $uvCommand = $localUv
    }
}

function Invoke-VerificationStep {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )

    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Push-Location $projectRoot
try {
    Invoke-VerificationStep "Specification sync" {
        & (Join-Path $PSScriptRoot "check-spec-sync.ps1")
    }

    Invoke-VerificationStep "Secret scan" {
        & (Join-Path $PSScriptRoot "check-secrets.ps1")
    }

    if (Test-Path -LiteralPath "backend/pyproject.toml") {
        if (-not $uvCommand) {
            throw "The backend exists, but uv is unavailable."
        }
        Invoke-VerificationStep "Python Ruff" { & $uvCommand run --project backend ruff check backend }
        Invoke-VerificationStep "Python mypy" { & $uvCommand run --project backend mypy backend/app }
        Invoke-VerificationStep "Python pytest" { & $uvCommand run --project backend pytest backend/tests }
    } else {
        Write-Host "SKIP: backend scaffold is not present yet." -ForegroundColor Yellow
    }

    if (Test-Path -LiteralPath "frontend/package.json") {
        if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
            throw "The frontend exists, but npm is unavailable."
        }
        Invoke-VerificationStep "Web lint" { npm --prefix frontend run lint }
        Invoke-VerificationStep "Web test" { npm --prefix frontend test -- --run }
    } else {
        Write-Host "SKIP: frontend scaffold is not present yet." -ForegroundColor Yellow
    }

    if (Test-Path -LiteralPath "android/gradlew.bat") {
        Invoke-VerificationStep "Android verification" {
            Push-Location android
            try {
                & .\gradlew.bat ktlintCheck detekt lintDebug testDebugUnitTest assembleDebug
            } finally {
                Pop-Location
            }
        }
    } else {
        Write-Host "SKIP: Android scaffold is not present yet." -ForegroundColor Yellow
    }

    Write-Host "`nPASS: All currently available verification steps succeeded." -ForegroundColor Green
} finally {
    Pop-Location
}
