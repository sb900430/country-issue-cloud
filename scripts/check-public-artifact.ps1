[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$Path)

$ErrorActionPreference = "Stop"
$resolved = Resolve-Path -LiteralPath $Path
$blockedPatterns = @(
    'AKIA[0-9A-Z]{16}',
    'sk-[A-Za-z0-9_-]{20,}',
    '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',
    '(?i)(api[_-]?key|client[_-]?secret|access[_-]?token)\s*[=:]\s*["''][^"'']{8,}'
)
$textExtensions = @('.html', '.css', '.js', '.json', '.txt', '.xml')

foreach ($file in Get-ChildItem -LiteralPath $resolved -Recurse -File) {
    if ($textExtensions -notcontains $file.Extension.ToLowerInvariant()) {
        continue
    }
    $content = Get-Content -LiteralPath $file.FullName -Raw
    foreach ($pattern in $blockedPatterns) {
        if ($content -match $pattern) {
            throw "Potential secret detected in public artifact: $($file.Name)"
        }
    }
}

$latest = Join-Path $resolved "data/v2/latest.json"
$dates = Join-Path $resolved "data/v2/dates.json"
if (-not (Test-Path -LiteralPath $latest) -or -not (Test-Path -LiteralPath $dates)) {
    throw "Public artifact is missing required JSON files."
}
$payload = Get-Content -LiteralPath $latest -Raw | ConvertFrom-Json
if ($payload.schema_version -ne "2.0") {
    throw "Public artifact must use keyword Schema 2.0."
}
foreach ($country in @("US", "JP", "KR")) {
    if ($payload.countries.$country.top_keywords.Count -ne 5) {
        throw "Public artifact must contain five keywords for $country."
    }
}
$dateValues = @(Get-Content -LiteralPath $dates -Raw | ConvertFrom-Json)
if ($dateValues.Count -lt 1 -or $dateValues.Count -gt 7) {
    throw "Public artifact must contain between one and seven dates."
}
if ($dateValues[0] -ne $payload.date) {
    throw "Public artifact latest date must be first in dates.json."
}
foreach ($dateValue in $dateValues) {
    if ($dateValue -notmatch '^\d{4}-\d{2}-\d{2}$') {
        throw "Public artifact contains an invalid date index."
    }
    $datedPath = Join-Path $resolved "data/v2/$dateValue.json"
    if (-not (Test-Path -LiteralPath $datedPath)) {
        throw "Public artifact is missing dated keyword data: $dateValue"
    }
    $datedPayload = Get-Content -LiteralPath $datedPath -Raw | ConvertFrom-Json
    if ($datedPayload.schema_version -ne "2.0" -or $datedPayload.date -ne $dateValue) {
        throw "Public artifact contains invalid dated keyword data: $dateValue"
    }
    foreach ($country in @("US", "JP", "KR")) {
        if ($datedPayload.countries.$country.top_keywords.Count -ne 5) {
            throw "Dated public artifact must contain five keywords for $country."
        }
    }
}
Write-Host "PASS: Public Pages artifact contains required JSON and no secret patterns."
