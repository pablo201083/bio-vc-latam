param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack"
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
        if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($char) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            [void]$builder.Append($char)
        }
    }
    return (($builder.ToString().ToLowerInvariant()) -replace '[^a-z0-9]+', '').Trim()
}

$qualityDir = Join-Path $Root 'quality'
$masterPath = Join-Path $Root 'startup_master_dataset.csv'
$entitiesPath = Join-Path $Root 'canonical\canonical_entities.csv'
$aliasesPath = Join-Path $Root 'canonical\canonical_aliases.csv'
$edgesPath = Join-Path $Root 'canonical\canonical_investment_edges.csv'

$master = Import-Csv -LiteralPath $masterPath
$entities = Import-Csv -LiteralPath $entitiesPath
$aliases = Import-Csv -LiteralPath $aliasesPath
$edges = Import-Csv -LiteralPath $edgesPath

$edgeByStartup = @{}
foreach ($edge in $edges) {
    $sid = Clean-Text $edge.startup_id
    if ($sid) {
        if (-not $edgeByStartup.ContainsKey($sid)) { $edgeByStartup[$sid] = 0 }
        $edgeByStartup[$sid] += 1
    }
}

$pipelineRows = New-Object System.Collections.Generic.List[object]
foreach ($row in $master) {
    $scope = Clean-Text $row.scope_decision
    $sourceUrl = Clean-Text $row.source_url
    $country = Clean-Text $row.structured_country
    $review = Clean-Text $row.review_status
    $quality = Clean-Text $row.quality_band
    $startupId = Clean-Text $row.startup_id
    $sourceType = Clean-Text $row.source_type
    $capitalEdges = if ($edgeByStartup.ContainsKey($startupId)) { [int]$edgeByStartup[$startupId] } else { 0 }

    $needsSource = -not $sourceUrl
    $needsScope = -not $scope
    $needsCountry = ($scope -eq 'include' -and -not $country)
    $needsQualityUpgrade = ($scope -eq 'include' -and ($quality -eq 'fragile' -or $review -eq 'taxonomy_stub'))
    $needsCapitalEdge = ($scope -eq 'include' -and $capitalEdges -eq 0)

    $state = 'ready_for_analysis'
    if ($needsSource) {
        $state = 'source_needed'
    } elseif ($needsScope) {
        $state = 'scope_decision_needed'
    } elseif ($needsCountry) {
        $state = 'country_needed'
    } elseif ($needsQualityUpgrade) {
        $state = 'quality_upgrade_needed'
    } elseif ($scope -eq 'exclude' -and $review -eq 'reviewed') {
        $state = 'exclude_confirmed'
    } elseif ($scope -eq 'include' -and $review -eq 'reviewed') {
        $state = 'ready_for_semantic'
    } elseif ($scope -eq 'include' -and $review -eq 'seeded') {
        $state = 'source_backed_seeded'
    }

    $priority = 0
    if ($needsSource) { $priority += 100 }
    if ($needsScope) { $priority += 80 }
    if ($needsCountry) { $priority += 50 }
    if ($needsQualityUpgrade) { $priority += 60 }
    if ($needsCapitalEdge) { $priority += 20 }
    if ($scope -eq 'include') { $priority += 10 }
    if ($quality -eq 'high') { $priority -= 5 }

    $pipelineRows.Add([PSCustomObject]@{
        entity_type = 'startup'
        entity_id = $startupId
        entity_name = $row.startup_name
        pipeline_state = $state
        scope_decision = $scope
        review_status = $review
        quality_band = $quality
        data_quality_score_10 = $row.data_quality_score_10
        source_type = $sourceType
        source_url = $sourceUrl
        structured_country = $country
        capital_edge_count = $capitalEdges
        needs_source = [string]$needsSource
        needs_scope_decision = [string]$needsScope
        needs_country = [string]$needsCountry
        needs_quality_upgrade = [string]$needsQualityUpgrade
        needs_capital_edge = [string]$needsCapitalEdge
        priority_score = $priority
    }) | Out-Null
}

$pipelinePath = Join-Path $qualityDir 'project_pipeline_status.csv'
$pipelineRows |
    Sort-Object @{ Expression = { [int]$_.priority_score }; Descending = $true }, entity_name |
    Export-Csv -LiteralPath $pipelinePath -NoTypeInformation -Encoding UTF8

$summaryPath = Join-Path $qualityDir 'project_pipeline_summary.csv'
$pipelineRows |
    Group-Object pipeline_state |
    Sort-Object Count -Descending |
    ForEach-Object {
        [PSCustomObject]@{
            pipeline_state = $_.Name
            count = $_.Count
            include_count = @($_.Group | Where-Object { $_.scope_decision -eq 'include' }).Count
            exclude_count = @($_.Group | Where-Object { $_.scope_decision -eq 'exclude' }).Count
            avg_priority_score = [Math]::Round((($_.Group | Measure-Object priority_score -Average).Average), 1)
        }
    } |
    Export-Csv -LiteralPath $summaryPath -NoTypeInformation -Encoding UTF8

$startupIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
foreach ($row in $master) { [void]$startupIds.Add([string]$row.startup_id) }

$startupLookup = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
foreach ($row in $master) {
    $startupLookup[(Normalize-Key ([string]$row.startup_id))] = [string]$row.startup_id
    $startupLookup[(Normalize-Key ([string]$row.startup_name))] = [string]$row.startup_id
}
foreach ($alias in $aliases) {
    $key = Normalize-Key ([string]$alias.alias)
    if ($key -and $startupIds.Contains([string]$alias.entity_id)) {
        $startupLookup[$key] = [string]$alias.entity_id
    }
}

$edgeQueue = New-Object System.Collections.Generic.List[object]
foreach ($edge in $edges) {
    $rawStartupId = Clean-Text $edge.startup_id
    $norm = Normalize-Key $rawStartupId
    if ($startupIds.Contains($rawStartupId) -or $startupLookup.ContainsKey($norm)) { continue }

    $action = 'review_add_startup_or_alias'
    if ($rawStartupId -eq '0' -or -not $rawStartupId) {
        $action = 'exclude_malformed_edge'
    } elseif (($edge.source_file -match 'graphml|edgeseco') -and ($edge.relation_type_raw -match 'investment_or_membership|investment')) {
        $action = 'review_historical_edge'
    }

    $suggested = ''
    foreach ($key in $startupLookup.Keys) {
        if ($norm.Length -ge 5 -and ($key -like "*$norm*" -or $norm -like "*$key*")) {
            $suggested = $startupLookup[$key]
            break
        }
    }

    $edgeQueue.Add([PSCustomObject]@{
        investment_id = $edge.investment_id
        investor_id = $edge.investor_id
        raw_startup_id = $rawStartupId
        normalized_startup_key = $norm
        suggested_startup_id = $suggested
        source_file = $edge.source_file
        relation_type_raw = $edge.relation_type_raw
        recommended_action = $action
        notes = $edge.notes
    }) | Out-Null
}

$edgeQueuePath = Join-Path $qualityDir 'canonical_edge_resolution_queue.csv'
$edgeQueue |
    Sort-Object recommended_action, raw_startup_id |
    Export-Csv -LiteralPath $edgeQueuePath -NoTypeInformation -Encoding UTF8

Write-Output "Project pipeline status built:"
Write-Output "  Pipeline: $pipelinePath"
Write-Output "  Summary: $summaryPath"
Write-Output "  Edge queue: $edgeQueuePath"
