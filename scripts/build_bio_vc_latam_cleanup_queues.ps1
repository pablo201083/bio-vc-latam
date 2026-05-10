param(
    [string]$MasterCsv = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$CapitalNodesCsv = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\gephi_export\startup_capital_relational\nodes.csv",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$rows = Import-Csv -LiteralPath $MasterCsv
$capitalById = @{}
if (Test-Path -LiteralPath $CapitalNodesCsv) {
    foreach ($node in (Import-Csv -LiteralPath $CapitalNodesCsv)) {
        $capitalById[$node.Id] = $node
    }
}

function Has-CapitalSignal {
    param([string]$StartupId)
    return $capitalById.ContainsKey($StartupId)
}

function Bio-SignalScore {
    param($Row)
    $text = @(
        $Row.startup_name,
        $Row.startup_summary_v1,
        $Row.business_one_liner,
        $Row.market_label,
        $Row.transition_function,
        $Row.technical_stack,
        $Row.industry_destination,
        $Row.thesis_scope_note,
        $Row.macro_theme,
        $Row.emergent_theme
    ) -join " "
    $text = $text.ToLowerInvariant()

    $score = 0
    foreach ($term in @("bio", "biotech", "biological", "microbial", "fermentation", "enzyme", "protein", "cell", "genomic", "diagnostic", "therapeutic", "crop", "soil", "regenerative", "carbon", "water", "climate", "circular", "material", "food", "health")) {
        if ($text.Contains($term)) { $score += 1 }
    }
    if (Has-CapitalSignal $Row.startup_id) { $score += 3 }
    if (-not [string]::IsNullOrWhiteSpace($Row.source_url)) { $score += 2 }
    if ($Row.structured_sector -eq "Digital Economy") { $score -= 2 }
    return $score
}

function Missing-Country {
    param($Row)
    return [string]::IsNullOrWhiteSpace($Row.structured_country)
}

$excludeProvisional = @(
    foreach ($row in $rows) {
        if ($row.scope_decision -ne "exclude" -or $row.scope_status -ne "provisional") { continue }
        [PSCustomObject]@{
            startup_id = $row.startup_id
            startup_name = $row.startup_name
            cleanup_priority = Bio-SignalScore $row
            current_scope = "$($row.scope_decision)/$($row.scope_status)"
            scope_reason = $row.scope_reason
            structured_country = $row.structured_country
            has_capital_signal = Has-CapitalSignal $row.startup_id
            has_source_url = -not [string]::IsNullOrWhiteSpace($row.source_url)
            macro_theme = $row.macro_theme
            emergent_theme = $row.emergent_theme
            summary = $row.startup_summary_v1
            source_url = $row.source_url
            action_needed = "verify_false_negative_or_confirm_exclude"
        }
    }
) | Sort-Object @{ Expression = "cleanup_priority"; Descending = $true }, @{ Expression = "startup_name"; Descending = $false }

$includeMissingCountry = @(
    foreach ($row in $rows) {
        if ($row.scope_decision -ne "include") { continue }
        if (-not (Missing-Country $row)) { continue }
        [PSCustomObject]@{
            startup_id = $row.startup_id
            startup_name = $row.startup_name
            cleanup_priority = Bio-SignalScore $row
            current_scope = "$($row.scope_decision)/$($row.scope_status)"
            structured_country = $row.structured_country
            has_capital_signal = Has-CapitalSignal $row.startup_id
            source_url = $row.source_url
            source_type = $row.source_type
            semantic_or_macro_theme = $row.macro_theme
            summary = $row.startup_summary_v1
            action_needed = "fill_founding_or_base_country"
        }
    }
) | Sort-Object @{ Expression = "cleanup_priority"; Descending = $true }, @{ Expression = "startup_name"; Descending = $false }

$includeFragile = @(
    foreach ($row in $rows) {
        if ($row.scope_decision -ne "include" -or $row.quality_band -ne "fragile") { continue }
        [PSCustomObject]@{
            startup_id = $row.startup_id
            startup_name = $row.startup_name
            cleanup_priority = Bio-SignalScore $row
            current_scope = "$($row.scope_decision)/$($row.scope_status)"
            structured_country = $row.structured_country
            missing_signals = $row.missing_signals
            source_url = $row.source_url
            source_type = $row.source_type
            summary = $row.startup_summary_v1
            action_needed = "upgrade_source_description_country_or_quality"
        }
    }
) | Sort-Object @{ Expression = "cleanup_priority"; Descending = $true }, @{ Expression = "startup_name"; Descending = $false }

$all = @()
$all += $excludeProvisional | Select-Object *, @{Name="queue"; Expression={"01_exclude_provisional_false_negative_review"}}
$all += $includeMissingCountry | Select-Object *, @{Name="queue"; Expression={"02_include_missing_country"}}
$all += $includeFragile | Select-Object *, @{Name="queue"; Expression={"03_include_fragile_quality"}}

$excludeProvisional | Export-Csv -LiteralPath (Join-Path $OutputDir "bio_vc_latam_exclude_provisional_review.csv") -NoTypeInformation -Encoding UTF8
$includeMissingCountry | Export-Csv -LiteralPath (Join-Path $OutputDir "bio_vc_latam_include_missing_country.csv") -NoTypeInformation -Encoding UTF8
$includeFragile | Export-Csv -LiteralPath (Join-Path $OutputDir "bio_vc_latam_include_fragile.csv") -NoTypeInformation -Encoding UTF8
$all | Export-Csv -LiteralPath (Join-Path $OutputDir "bio_vc_latam_cleanup_queue.csv") -NoTypeInformation -Encoding UTF8

$topExclude = $excludeProvisional | Select-Object -First 15
$topCountry = $includeMissingCountry | Select-Object -First 15
$topFragile = $includeFragile | Select-Object -First 15

$report = @"
# BIO VC LATAM cleanup queue

Objetivo: cerrar el universo de startups BIO VC LATAM y su red de capital con menos ambiguedad posible.

## Foto de trabajo

- Exclude provisional a revisar por falsos negativos: $($excludeProvisional.Count)
- Include sin pais/base claro: $($includeMissingCountry.Count)
- Include fragile: $($includeFragile.Count)

## Orden recomendado

1. Revisar exclude provisional con mayor senal BIO/capital.
2. Completar founding/base country para include confirmadas.
3. Endurecer las include fragile.
4. Regenerar base, dashboards y export capital.

## Top exclude provisional a revisar

$($topExclude | ForEach-Object { "- $($_.startup_name) | priority $($_.cleanup_priority) | capital=$($_.has_capital_signal) | $($_.macro_theme)" } | Out-String)

## Top include sin pais/base

$($topCountry | ForEach-Object { "- $($_.startup_name) | priority $($_.cleanup_priority) | source=$($_.source_url)" } | Out-String)

## Include fragile

$($topFragile | ForEach-Object { "- $($_.startup_name) | missing=$($_.missing_signals) | source=$($_.source_url)" } | Out-String)
"@

Set-Content -LiteralPath (Join-Path $OutputDir "bio_vc_latam_cleanup_queue.md") -Value $report -Encoding UTF8

Write-Output "BIO VC LATAM cleanup queues written to $OutputDir"
