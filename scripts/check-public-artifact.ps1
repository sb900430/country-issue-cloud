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

$latest = Join-Path $resolved "data/v1/latest.json"
$dates = Join-Path $resolved "data/v1/dates.json"
if (-not (Test-Path -LiteralPath $latest) -or -not (Test-Path -LiteralPath $dates)) {
    throw "Public artifact is missing required JSON files."
}
Write-Host "PASS: Public Pages artifact contains required JSON and no secret patterns."
