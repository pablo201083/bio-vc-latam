param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack",
    [string]$OutputPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\fund_portfolio_observations.csv"
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

function Get-ObservationClass {
    param([object]$Edge, [object]$Startup)
    $sourceType = (Clean-Text $Startup.source_type).ToLowerInvariant()
    if ($sourceType -match 'official_portfolio') { return 'official_portfolio' }
    if ($sourceType -match 'official_website|official_company|official_public') { return 'official_public_profile' }
    if ((Clean-Text $Edge.source_file) -match 'graphml|edgeseco') { return 'historical_graph' }
    return 'public_profile'
}

$entities = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_entities.csv')
$edges = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_investment_edges.csv')
$aliases = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_aliases.csv')
$master = Import-Csv -LiteralPath (Join-Path $Root 'startup_master_dataset.csv')

$fundsById = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)
foreach ($row in ($entities | Where-Object { $_.entity_type -eq 'investor' })) {
    $fundsById[[string]$row.entity_id] = $row
}

$startupsById = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)
$startupLookup = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
foreach ($row in $master) {
    $startupsById[[string]$row.startup_id] = $row
    $startupLookup[(Normalize-Key ([string]$row.startup_id))] = [string]$row.startup_id
    $startupLookup[(Normalize-Key ([string]$row.startup_name))] = [string]$row.startup_id
}

foreach ($alias in $aliases) {
    $key = Normalize-Key ([string]$alias.alias)
    if ($key -and $startupsById.ContainsKey([string]$alias.entity_id)) {
        $startupLookup[$key] = [string]$alias.entity_id
    }
}

$observationMap = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)

foreach ($edge in $edges) {
    if (-not $fundsById.ContainsKey([string]$edge.investor_id)) { continue }
    $startupId = if ($startupsById.ContainsKey([string]$edge.startup_id)) {
        [string]$edge.startup_id
    } else {
        $startupLookup[(Normalize-Key ([string]$edge.startup_id))]
    }
    if (-not $startupId -or -not $startupsById.ContainsKey($startupId)) { continue }

    $fund = $fundsById[[string]$edge.investor_id]
    $startup = $startupsById[$startupId]
    $observationKey = ([string]$fund.entity_id) + '|' + ([string]$startup.startup_id)
    if ($observationMap.ContainsKey($observationKey)) { continue }

    $observationMap[$observationKey] = [PSCustomObject]@{
        fund_id = [string]$fund.entity_id
        fund_name = [string]$fund.canonical_name
        startup_id = [string]$startup.startup_id
        startup_name = [string]$startup.startup_name
        startup_source_url = [string]$startup.source_url
        startup_source_type = [string]$startup.source_type
        observation_class = Get-ObservationClass -Edge $edge -Startup $startup
        edge_source_file = [string]$edge.source_file
        edge_confidence = [string]$edge.confidence_score
        in_master = $true
        master_scope_decision = [string]$startup.scope_decision
        master_scope_status = [string]$startup.scope_status
        macro_theme = [string]$startup.macro_theme
        structured_country = [string]$startup.structured_country
        data_quality_score_10 = [string]$startup.data_quality_score_10
    }
}

$observationMap.Values |
    Sort-Object fund_name, startup_name |
    Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding UTF8

Write-Output "Fund portfolio observations built: $OutputPath"
