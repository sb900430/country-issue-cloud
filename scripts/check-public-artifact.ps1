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
$calendar = Join-Path $resolved "data/v2/calendar.json"
$status = Join-Path $resolved "data/v2/status.json"
if (
    -not (Test-Path -LiteralPath $latest) -or
    -not (Test-Path -LiteralPath $dates) -or
    -not (Test-Path -LiteralPath $calendar) -or
    -not (Test-Path -LiteralPath $status)
) {
    throw "Public artifact is missing required JSON files."
}
$payload = Get-Content -LiteralPath $latest -Raw | ConvertFrom-Json
if ($payload.schema_version -ne "2.0") {
    throw "Public artifact must use keyword Schema 2.0."
}
foreach ($country in @("US", "JP", "KR")) {
    $countryPayload = $payload.countries.$country
    if (
        ($countryPayload.status -eq "success" -and $countryPayload.top_keywords.Count -notin 3..5) -or
        ($countryPayload.status -ne "success" -and $countryPayload.top_keywords.Count -gt 5)
    ) {
        throw "Public artifact contains an invalid keyword count for $country."
    }
}
$dateValues = @(Get-Content -LiteralPath $dates -Raw | ConvertFrom-Json)
if ($dateValues.Count -lt 1 -or $dateValues.Count -gt 7) {
    throw "Public artifact must contain between one and seven dates."
}
if ($dateValues -notcontains $payload.date) {
    throw "Public artifact latest date must be included in dates.json."
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
        $countryPayload = $datedPayload.countries.$country
        if (
            ($countryPayload.status -eq "success" -and $countryPayload.top_keywords.Count -notin 3..5) -or
            ($countryPayload.status -ne "success" -and $countryPayload.top_keywords.Count -gt 5)
        ) {
            throw "Dated public artifact contains an invalid keyword count for $country."
        }
    }
}
$statusPayload = Get-Content -LiteralPath $status -Raw | ConvertFrom-Json
if (
    $statusPayload.schema_version -ne "1.0" -or
    $statusPayload.attempted_date -ne $dateValues[0] -or
    $statusPayload.displayed_date -ne $payload.date
) {
    throw "Public artifact contains inconsistent publication status."
}
$calendarPayload = Get-Content -LiteralPath $calendar -Raw | ConvertFrom-Json
$calendarDays = @($calendarPayload.days)
if (
    $calendarPayload.schema_version -ne "1.0" -or
    $calendarDays.Count -ne $dateValues.Count
) {
    throw "Public artifact contains an invalid publication calendar."
}
for ($index = 0; $index -lt $dateValues.Count; $index++) {
    if ($calendarDays[$index].date -ne $dateValues[$index]) {
        throw "Public artifact calendar and date index are inconsistent."
    }
}
Write-Host "PASS: Public Pages artifact contains required JSON and no secret patterns."
