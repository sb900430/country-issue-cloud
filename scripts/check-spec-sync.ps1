[CmdletBinding()]
param(
    [switch]$Staged
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$koreanSpec = Join-Path $projectRoot "PROJECT_SPEC.md"
$japaneseSpec = Join-Path $projectRoot "PROJECT_SPEC_JA.md"

if (-not (Test-Path -LiteralPath $koreanSpec) -or -not (Test-Path -LiteralPath $japaneseSpec)) {
    throw "Both Korean and Japanese specification files are required."
}

function Get-ChangedFileNames {
    if ($Staged) {
        return @(git -C $projectRoot diff --cached --name-only)
    }

    $statusLines = @(git -C $projectRoot status --porcelain)
    return @($statusLines | ForEach-Object {
        if ($_.Length -ge 4) { $_.Substring(3).Trim([char]34) }
    })
}

function Get-SectionNumbers([string]$Path) {
    $matches = Select-String -Path $Path -Pattern '^## ([0-9]+)\.' -Encoding UTF8
    return @($matches | ForEach-Object { [int]$_.Matches[0].Groups[1].Value })
}

function Get-FeatureIds([string]$Path) {
    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path
    return @([regex]::Matches($text, 'F-[0-9]{2}') | ForEach-Object Value | Sort-Object -Unique)
}

$changedFiles = Get-ChangedFileNames
$koreanChanged = $changedFiles -contains "PROJECT_SPEC.md"
$japaneseChanged = $changedFiles -contains "PROJECT_SPEC_JA.md"

if ($koreanChanged -xor $japaneseChanged) {
    throw "Update PROJECT_SPEC.md and PROJECT_SPEC_JA.md together."
}

$expectedSections = 1..22
$koreanSections = Get-SectionNumbers $koreanSpec
$japaneseSections = Get-SectionNumbers $japaneseSpec

if ((Compare-Object $expectedSections $koreanSections) -or (Compare-Object $expectedSections $japaneseSections)) {
    throw "Both specifications must contain sections 1 through 22."
}

$koreanFeatures = Get-FeatureIds $koreanSpec
$japaneseFeatures = Get-FeatureIds $japaneseSpec
if (Compare-Object $koreanFeatures $japaneseFeatures) {
    throw "Feature IDs do not match between the specifications."
}

$requiredTokens = @(
    '/api/v1',
    'USD 10',
    'v0.8.0-local-mvp',
    'feat: scaffold local environment',
    'feat: implement local data API',
    'feat: implement country news collection',
    'feat: implement issue extraction and ranking',
    'feat: complete pipeline and web demo',
    'feat: connect Android to local API',
    'feat: implement Android UI and offline cache',
    'release: complete local MVP'
)

$koreanText = Get-Content -Raw -Encoding UTF8 -LiteralPath $koreanSpec
$japaneseText = Get-Content -Raw -Encoding UTF8 -LiteralPath $japaneseSpec
foreach ($token in $requiredTokens) {
    if (-not $koreanText.Contains($token) -or -not $japaneseText.Contains($token)) {
        throw "Required synchronized token is missing: $token"
    }
}

Write-Host "PASS: Korean and Japanese specification structures are synchronized." -ForegroundColor Green
