[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][uri]$BaseUrl,
    [ValidateRange(1, 10)][int]$MaxAttempts = 6,
    [ValidateRange(0, 60)][int]$DelaySeconds = 10
)

$ErrorActionPreference = "Stop"
if ($BaseUrl.Scheme -ne "https") {
    throw "Public site smoke test requires HTTPS."
}

$base = $BaseUrl.AbsoluteUri.TrimEnd('/') + '/'
$temporary = Join-Path ([System.IO.Path]::GetTempPath()) (
    "country-issue-cloud-public-smoke-" + [guid]::NewGuid()
)
$targets = [ordered]@{
    "index.html" = $base
    "about.html" = $base + "about.html"
    "data/v2/latest.json" = $base + "data/v2/latest.json"
    "data/v2/dates.json" = $base + "data/v2/dates.json"
    "data/v2/calendar.json" = $base + "data/v2/calendar.json"
    "data/v2/status.json" = $base + "data/v2/status.json"
}

try {
    foreach ($attempt in 1..$MaxAttempts) {
        try {
            foreach ($entry in $targets.GetEnumerator()) {
                $destination = Join-Path $temporary $entry.Key
                New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) |
                    Out-Null
                Invoke-WebRequest -Uri $entry.Value -OutFile $destination -TimeoutSec 20
            }
            $dateIndexPath = Join-Path $temporary "data/v2/dates.json"
            $dateValues = @(Get-Content -LiteralPath $dateIndexPath -Raw | ConvertFrom-Json)
            if ($dateValues.Count -lt 1 -or $dateValues.Count -gt 7) {
                throw "Public date index must contain between one and seven dates."
            }
            foreach ($dateValue in $dateValues) {
                if ($dateValue -notmatch '^\d{4}-\d{2}-\d{2}$') {
                    throw "Public date index contains an invalid date."
                }
                $datedDestination = Join-Path $temporary "data/v2/$dateValue.json"
                Invoke-WebRequest `
                    -Uri ($base + "data/v2/$dateValue.json") `
                    -OutFile $datedDestination `
                    -TimeoutSec 20
            }
            & (Join-Path $PSScriptRoot "check-public-artifact.ps1") -Path $temporary
            $index = Get-Content -LiteralPath (Join-Path $temporary "index.html") -Raw
            foreach ($required in @('data-countries', 'data-issues', 'data-dialog')) {
                if (-not $index.Contains($required)) {
                    throw "Public index is missing required UI marker: $required"
                }
            }
            Write-Host "PASS: Public site v2 data and primary UI markers are available at $base"
            exit 0
        } catch {
            if ($attempt -eq $MaxAttempts) {
                throw
            }
            Write-Warning "Public smoke attempt $attempt failed; retrying after $DelaySeconds seconds."
            Start-Sleep -Seconds $DelaySeconds
        }
    }
} finally {
    if (Test-Path -LiteralPath $temporary) {
        Remove-Item -LiteralPath $temporary -Recurse -Force
    }
}
