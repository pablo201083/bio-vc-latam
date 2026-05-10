param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack",
    [string]$OutputPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_registry.csv"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Clean-Text {
    param([object]$Value)
    if ($null -eq $Value) { return '' }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return '' }
    if ($text.Trim().ToLowerInvariant() -eq 'nan') { return '' }
    return $text.Trim()
}

function Normalize-Key {
    param([string]$Value)
    $text = Clean-Text $Value
    if (-not $text) { return '' }
    $decomposed = $text.Normalize([Text.NormalizationForm]::FormD)
    $builder = New-Object System.Text.StringBuilder
    foreach ($char in $decomposed.ToCharArray()) {
        $category = [Globalization.CharUnicodeInfo]::GetUnicodeCategory($char)
        if ($category -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            [void]$builder.Append($char)
        }
    }
    return (($builder.ToString().ToLowerInvariant()) -replace '[^a-z0-9]+', '-').Trim('-')
}

function Get-SourceOwner {
    param([string]$Url)
    $text = Clean-Text $Url
    if (-not $text) { return '' }
    try {
        $uri = [Uri]$text
        return $uri.Host.ToLowerInvariant() -replace '^www\.', ''
    } catch {
        return ''
    }
}

function Get-TrustTier {
    param([string]$SourceType, [string]$Url)
    $type = (Clean-Text $SourceType).ToLowerInvariant()
    $owner = Get-SourceOwner -Url $Url

    if ($type -match 'official_portfolio|official_website|official_company|official_public') { return 1 }
    if ($owner -match 'gridexponential|sf500|theganeshalab|theyieldlablatam|kptl|spventures|sosv|indiebio|zentynel|chileglobalventures') { return 1 }
    if ($type -match 'linkedin|f6s|crunchbase|cbinsights|external_profile|public_company') { return 2 }
    if ($type -match 'manual|secondary|public') { return 3 }
    return 4
}

$masterPath = Join-Path $Root 'startup_master_dataset.csv'
if (-not (Test-Path -LiteralPath $masterPath)) {
    throw "Missing master dataset: $masterPath"
}

$master = Import-Csv -LiteralPath $masterPath
$registry = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)

foreach ($row in $master) {
    $url = Clean-Text $row.source_url
    if (-not $url) { continue }

    $sourceType = Clean-Text $row.source_type
    $sourceId = Normalize-Key ($url + '|' + $sourceType)
    if (-not $registry.ContainsKey($sourceId)) {
        $registry[$sourceId] = [PSCustomObject]@{
            source_id = $sourceId
            source_url = $url
            source_owner = Get-SourceOwner -Url $url
            source_type = $sourceType
            trust_tier = Get-TrustTier -SourceType $sourceType -Url $url
            startup_count = 0
            include_count = 0
            reviewed_count = 0
            seeded_count = 0
            first_source_date = Clean-Text $row.source_date
            examples = New-Object System.Collections.Generic.List[string]
        }
    }

    $entry = $registry[$sourceId]
    $entry.startup_count = [int]$entry.startup_count + 1
    if ($row.scope_decision -eq 'include') { $entry.include_count = [int]$entry.include_count + 1 }
    if ($row.review_status -eq 'reviewed') { $entry.reviewed_count = [int]$entry.reviewed_count + 1 }
    if ($row.review_status -eq 'seeded') { $entry.seeded_count = [int]$entry.seeded_count + 1 }
    if ($entry.examples.Count -lt 5) { $entry.examples.Add((Clean-Text $row.startup_name)) | Out-Null }
}

$rows = @(
    $registry.Values |
        Sort-Object @{ Expression = { [int]$_.trust_tier }; Descending = $false }, `
                    @{ Expression = { [int]$_.include_count }; Descending = $true }, `
                    @{ Expression = { [string]$_.source_owner }; Descending = $false } |
        ForEach-Object {
            [PSCustomObject]@{
                source_id = $_.source_id
                source_url = $_.source_url
                source_owner = $_.source_owner
                source_type = $_.source_type
                trust_tier = $_.trust_tier
                startup_count = $_.startup_count
                include_count = $_.include_count
                reviewed_count = $_.reviewed_count
                seeded_count = $_.seeded_count
                first_source_date = $_.first_source_date
                examples = ($_.examples -join '; ')
            }
        }
)

$rows | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding UTF8
Write-Output "Source registry built: $OutputPath"
