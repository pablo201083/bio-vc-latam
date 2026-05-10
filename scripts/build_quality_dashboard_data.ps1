param(
    [string]$MasterPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$SemanticAssignmentsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_single_level_assignments.csv",
    [string]$SourceRegistryPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_registry.csv",
    [string]$FundObservationsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\fund_portfolio_observations.csv",
    [string]$ValidationReportPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\reference_validation_report.csv",
    [string]$CurationPriorityPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_curation_priority_current.csv",
    [string]$CurationWorkstreamSummaryPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\curation_workstream_summary.csv",
    [string]$OutputJsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\quality-dashboard-data.js"
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

if (-not (Test-Path -LiteralPath $MasterPath)) {
    throw "Missing master dataset: $MasterPath"
}

$master = Import-Csv -LiteralPath $MasterPath
$semanticAssignments = if (Test-Path -LiteralPath $SemanticAssignmentsPath) { Import-Csv -LiteralPath $SemanticAssignmentsPath } else { @() }
$sourceRegistry = if (Test-Path -LiteralPath $SourceRegistryPath) { Import-Csv -LiteralPath $SourceRegistryPath } else { @() }
$fundObservations = if (Test-Path -LiteralPath $FundObservationsPath) { Import-Csv -LiteralPath $FundObservationsPath } else { @() }
$validationRows = if (Test-Path -LiteralPath $ValidationReportPath) { Import-Csv -LiteralPath $ValidationReportPath } else { @() }
$curationPriorityRows = if (Test-Path -LiteralPath $CurationPriorityPath) { Import-Csv -LiteralPath $CurationPriorityPath } else { @() }
$curationWorkstreamSummaryRows = if (Test-Path -LiteralPath $CurationWorkstreamSummaryPath) { Import-Csv -LiteralPath $CurationWorkstreamSummaryPath } else { @() }
$semanticById = @{}
foreach ($row in $semanticAssignments) { $semanticById[$row.startup_id] = $row }

$enriched = foreach ($row in $master) {
    $semantic = if ($semanticById.ContainsKey($row.startup_id)) { $semanticById[$row.startup_id] } else { $null }
    [pscustomobject]@{
        startup_id = $row.startup_id
        startup_name = $row.startup_name
        scope_decision = $row.scope_decision
        scope_status = $row.scope_status
        quality_band = $row.quality_band
        data_quality_score_10 = $row.data_quality_score_10
        missing_signals = $row.missing_signals
        source_url = $row.source_url
        structured_country = $row.structured_country
        review_status = $row.review_status
        bio_lens_tags = $row.bio_lens_tags
        domain_tags = $row.domain_tags
        technology_tags = $row.technology_tags
        scale_tags = $row.scale_tags
        semantic_single_theme = if ($null -ne $semantic) { $semantic.semantic_single_theme } else { '' }
        semantic_single_confidence = if ($null -ne $semantic) { $semantic.semantic_single_confidence } else { '' }
    }
}

$includeRows = @($enriched | Where-Object { $_.scope_decision -eq 'include' })
$excludeRows = @($enriched | Where-Object { $_.scope_decision -eq 'exclude' })
$includeTotal = [Math]::Max(1, @($includeRows).Count)
$excludeTotal = [Math]::Max(1, @($excludeRows).Count)
$includeSourcePct = [Math]::Round((@($includeRows | Where-Object { Clean-Text $_.source_url }).Count / $includeTotal) * 100, 1)
$includeReviewedPct = [Math]::Round((@($includeRows | Where-Object { $_.review_status -eq 'reviewed' }).Count / $includeTotal) * 100, 1)
$includeHighQualityPct = [Math]::Round((@($includeRows | Where-Object { $_.quality_band -eq 'high' }).Count / $includeTotal) * 100, 1)
$semanticHighPct = [Math]::Round((@($includeRows | Where-Object { $_.semantic_single_confidence -eq 'high' }).Count / $includeTotal) * 100, 1)
$excludeReviewedPct = [Math]::Round((@($excludeRows | Where-Object { $_.review_status -eq 'reviewed' }).Count / $excludeTotal) * 100, 1)
$overallReadinessPct = [Math]::Round((($includeSourcePct + $includeReviewedPct + $includeHighQualityPct + $semanticHighPct + $excludeReviewedPct) / 5.0), 1)

$summary = [pscustomobject]@{
    generated_at = (Get-Date).ToString('s')
    startup_total = @($enriched).Count
    include = @($enriched | Where-Object { $_.scope_decision -eq 'include' }).Count
    review = @($enriched | Where-Object { $_.scope_decision -eq 'review' }).Count
    exclude = @($enriched | Where-Object { $_.scope_decision -eq 'exclude' }).Count
    high_quality = @($enriched | Where-Object { $_.quality_band -eq 'high' }).Count
    medium_quality = @($enriched | Where-Object { $_.quality_band -eq 'medium' }).Count
    fragile_quality = @($enriched | Where-Object { $_.quality_band -eq 'fragile' }).Count
    poor_quality = @($enriched | Where-Object { $_.quality_band -eq 'poor' }).Count
    avg_quality_score = [Math]::Round((($enriched | Measure-Object -Property data_quality_score_10 -Average).Average), 2)
    source_url_coverage_pct = [Math]::Round((@($enriched | Where-Object { Clean-Text $_.source_url }).Count / [Math]::Max(1, @($enriched).Count)) * 100, 1)
    include_source_url_coverage_pct = [Math]::Round((@($enriched | Where-Object { $_.scope_decision -eq 'include' -and (Clean-Text $_.source_url) }).Count / [Math]::Max(1, @($enriched | Where-Object { $_.scope_decision -eq 'include' }).Count)) * 100, 1)
    validation_errors = @($validationRows | Where-Object { $_.severity -eq 'error' -and $_.status -eq 'fail' }).Count
    validation_warnings = @($validationRows | Where-Object { $_.severity -eq 'warning' -and $_.status -eq 'warn' }).Count
    include_reviewed = @($includeRows | Where-Object { $_.review_status -eq 'reviewed' }).Count
    include_seeded = @($includeRows | Where-Object { $_.review_status -eq 'seeded' }).Count
    include_high_quality = @($includeRows | Where-Object { $_.quality_band -eq 'high' }).Count
    include_medium_quality = @($includeRows | Where-Object { $_.quality_band -eq 'medium' }).Count
    include_fragile_quality = @($includeRows | Where-Object { $_.quality_band -eq 'fragile' }).Count
    semantic_high_confidence = @($includeRows | Where-Object { $_.semantic_single_confidence -eq 'high' }).Count
    semantic_medium_confidence = @($includeRows | Where-Object { $_.semantic_single_confidence -eq 'medium' }).Count
    semantic_low_confidence = @($includeRows | Where-Object { $_.semantic_single_confidence -eq 'low' }).Count
    exclude_reviewed = @($excludeRows | Where-Object { $_.review_status -eq 'reviewed' }).Count
    include_reviewed_pct = $includeReviewedPct
    include_high_quality_pct = $includeHighQualityPct
    semantic_high_confidence_pct = $semanticHighPct
    exclude_reviewed_pct = $excludeReviewedPct
    overall_readiness_pct = $overallReadinessPct
}

$qualityBands = @(
    $enriched | Group-Object quality_band | Sort-Object Name | ForEach-Object {
        [pscustomobject]@{ band = $_.Name; count = $_.Count }
    }
)

$scopeCounts = @(
    $enriched | Group-Object scope_decision | Sort-Object Name | ForEach-Object {
        [pscustomobject]@{ scope = $_.Name; count = $_.Count }
    }
)

$semanticCategories = @(
    $enriched |
      Where-Object { $_.scope_decision -eq 'include' -and (Clean-Text $_.semantic_single_theme) } |
      Group-Object semantic_single_theme |
      Sort-Object Count -Descending |
      ForEach-Object {
        [pscustomobject]@{
            theme = $_.Name
            count = $_.Count
        }
      }
)

function Get-TagCounts {
    param(
        [object[]]$Rows,
        [string]$FieldName
    )

    $counts = @{}
    foreach ($row in $Rows) {
        $raw = Clean-Text $row.$FieldName
        if (-not $raw) { continue }
        foreach ($tag in $raw.Split(';')) {
            $item = $tag.Trim()
            if ([string]::IsNullOrWhiteSpace($item)) { continue }
            $counts[$item] = 1 + $(if ($counts.ContainsKey($item)) { [int]$counts[$item] } else { 0 })
        }
    }

    return @(
        $counts.GetEnumerator() |
            Sort-Object @{ Expression = 'Value'; Descending = $true }, @{ Expression = 'Key'; Descending = $false } |
            ForEach-Object {
                [pscustomobject]@{
                    tag = $_.Key
                    count = $_.Value
                }
            }
    )
}

$includeRowsForTags = @($includeRows)
$strategicTagCounts = [pscustomobject]@{
    bio_lens = @(Get-TagCounts -Rows $includeRowsForTags -FieldName 'bio_lens_tags')
    domain = @(Get-TagCounts -Rows $includeRowsForTags -FieldName 'domain_tags')
    technology = @(Get-TagCounts -Rows $includeRowsForTags -FieldName 'technology_tags')
    scale = @(Get-TagCounts -Rows $includeRowsForTags -FieldName 'scale_tags')
}

$flagCounts = @{}
foreach ($row in $enriched) {
    foreach ($flag in (Clean-Text $row.missing_signals).Split(';')) {
        $item = $flag.Trim()
        if ([string]::IsNullOrWhiteSpace($item)) { continue }
        $flagCounts[$item] = 1 + $(if ($flagCounts.ContainsKey($item)) { [int]$flagCounts[$item] } else { 0 })
    }
}
$topFlags = @(
    $flagCounts.GetEnumerator() |
      Sort-Object Value -Descending |
      Select-Object -First 12 |
      ForEach-Object { [pscustomobject]@{ flag = $_.Key; count = $_.Value } }
)

$bestQuality = @(
    $enriched |
      Sort-Object @{ Expression = 'data_quality_score_10'; Descending = $true }, startup_name |
      Select-Object -First 20 startup_name, data_quality_score_10, scope_decision, semantic_single_theme
)

$reviewQueue = @(
    $enriched |
      Where-Object { $_.quality_band -eq 'fragile' -and $_.scope_decision -eq 'include' } |
      Sort-Object @{ Expression = 'data_quality_score_10'; Ascending = $true }, startup_name |
      Select-Object -First 40 startup_name, data_quality_score_10, semantic_single_theme, missing_signals
)

$curationProgress = @(
    [pscustomobject]@{
        dimension = 'Fuente externa include'
        pct = $includeSourcePct
        ready = @($includeRows | Where-Object { Clean-Text $_.source_url }).Count
        total = @($includeRows).Count
        note = 'Base para evidencia auditable'
        tone = 'good'
    }
    [pscustomobject]@{
        dimension = 'Perfiles reviewed'
        pct = $includeReviewedPct
        ready = $summary.include_reviewed
        total = @($includeRows).Count
        note = 'Seeded restante es backlog editorial'
        tone = 'work'
    }
    [pscustomobject]@{
        dimension = 'Alta calidad include'
        pct = $includeHighQualityPct
        ready = $summary.include_high_quality
        total = @($includeRows).Count
        note = 'Fuente + summary + estructura defendible'
        tone = 'work'
    }
    [pscustomobject]@{
        dimension = 'Alta confianza semantica'
        pct = $semanticHighPct
        ready = $summary.semantic_high_confidence
        total = @($includeRows).Count
        note = 'Menos ruido para clustering y mapa'
        tone = 'watch'
    }
    [pscustomobject]@{
        dimension = 'Frontera exclude revisada'
        pct = $excludeReviewedPct
        ready = $summary.exclude_reviewed
        total = @($excludeRows).Count
        note = 'Defiende el recorte del universo BIO'
        tone = 'work'
    }
)

$curationQueue = @(
    $curationPriorityRows |
        Where-Object { Clean-Text $_.curation_reasons } |
        Select-Object -First 30 startup_name, current_theme, semantic_confidence, semantic_margin, quality_band, review_status, source_type, curation_reasons, suggested_action
)

$fundBackedStartupIds = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($row in ($fundObservations | Where-Object { $_.master_scope_decision -eq 'include' -and $_.master_scope_status -eq 'confirmed' })) {
    [void]$fundBackedStartupIds.Add([string]$row.startup_id)
}

$readinessDimensions = @(
    [pscustomobject]@{
        dimension = 'Fuente externa'
        ready = @($includeRows | Where-Object { Clean-Text $_.source_url }).Count
        total = @($includeRows).Count
        note = 'Include con source_url'
    }
    [pscustomobject]@{
        dimension = 'Pais/base'
        ready = @($includeRows | Where-Object { Clean-Text $_.structured_country }).Count
        total = @($includeRows).Count
        note = 'Include con structured_country'
    }
    [pscustomobject]@{
        dimension = 'Perfil revisado'
        ready = @($includeRows | Where-Object { $_.review_status -eq 'reviewed' }).Count
        total = @($includeRows).Count
        note = 'Include con review_status reviewed'
    }
    [pscustomobject]@{
        dimension = 'Scope confirmado'
        ready = @($includeRows | Where-Object { $_.scope_status -eq 'confirmed' }).Count
        total = @($includeRows).Count
        note = 'Include confirmed'
    }
    [pscustomobject]@{
        dimension = 'Capital mapeado'
        ready = $fundBackedStartupIds.Count
        total = @($includeRows).Count
        note = 'Include en carteras publicables'
    }
    [pscustomobject]@{
        dimension = 'Theme asignado'
        ready = @($includeRows | Where-Object { Clean-Text $_.semantic_single_theme }).Count
        total = @($includeRows).Count
        note = 'Include con categoria semantica'
    }
) | ForEach-Object {
    [pscustomobject]@{
        dimension = $_.dimension
        ready = $_.ready
        total = $_.total
        pct = [Math]::Round(([double]$_.ready / [Math]::Max(1, [double]$_.total)) * 100, 1)
        note = $_.note
    }
}

$sourceTrust = @(
    $sourceRegistry |
        Group-Object trust_tier |
        Sort-Object Name |
        ForEach-Object {
            [pscustomobject]@{
                trust_tier = $_.Name
                source_count = $_.Count
                include_count = @($_.Group | ForEach-Object { [int]$_.include_count } | Measure-Object -Sum).Sum
            }
        }
)

$validationSummary = @(
    $validationRows |
        Sort-Object @{ Expression = { if ($_.status -eq 'fail') { 0 } elseif ($_.status -eq 'warn') { 1 } else { 2 } }; Descending = $false }, check_id |
        Select-Object check_id, severity, status, count, message
)

$payload = [pscustomobject]@{
    summary = $summary
    readiness_dimensions = $readinessDimensions
    source_trust = $sourceTrust
    validation = $validationSummary
    quality_bands = $qualityBands
    scope_counts = $scopeCounts
    semantic_categories = $semanticCategories
    strategic_tag_counts = $strategicTagCounts
    top_flags = $topFlags
    review_queue = $reviewQueue
    curation_progress = $curationProgress
    curation_queue = $curationQueue
    curation_workstreams = @($curationWorkstreamSummaryRows)
    best_quality = $bestQuality
}

$js = "window.QUALITY_DASHBOARD_DATA = " + ($payload | ConvertTo-Json -Depth 8) + ";"
Set-Content -LiteralPath $OutputJsPath -Value $js -Encoding UTF8

Write-Output "Quality dashboard data built: $OutputJsPath"
