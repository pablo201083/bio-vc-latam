param(
    [string]$TaxonomyPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_taxonomy_assignments_v1.csv",
    [string]$NodesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\full_gephi_graph\nodes_full.csv",
    [string]$ManualOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\manual_startup_taxonomy_overrides.csv",
    [string]$ManualProfileOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\manual_startup_profile_overrides.csv",
    [string]$OutputScoresPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\startup_data_quality_scores.csv",
    [string]$OutputReviewPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\startup_review_quality_queue.csv",
    [string]$OutputSummaryPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\startup_data_quality_summary.md"
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

function Has-Value {
    param([object]$Value)
    return -not [string]::IsNullOrWhiteSpace((Clean-Text -Value $Value))
}

function Get-Field {
    param(
        [object]$Row,
        [string]$Name
    )

    $property = $Row.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }
    return $property.Value
}

function Join-Flags {
    param([System.Collections.Generic.List[string]]$Flags)
    if ($Flags.Count -eq 0) { return '' }
    return ($Flags | Select-Object -Unique) -join '; '
}

function Normalize-Key {
    param([string]$Text)
    $value = Clean-Text $Text
    if (-not $value) { return '' }
    $value = $value.ToLowerInvariant()
    $value = [regex]::Replace($value, '[^a-z0-9]+', '')
    return $value
}

function Add-Lookup {
    param(
        [hashtable]$Table,
        [string]$Id,
        [string]$Name,
        [object]$Value
    )

    foreach ($key in @((Normalize-Key $Id), (Normalize-Key $Name)) | Where-Object { $_ } | Select-Object -Unique) {
        $Table[$key] = $Value
    }
}

function Get-Lookup {
    param(
        [hashtable]$Table,
        [string]$Id,
        [string]$Name
    )

    foreach ($key in @((Normalize-Key $Id), (Normalize-Key $Name)) | Where-Object { $_ } | Select-Object -Unique) {
        if ($Table.ContainsKey($key)) {
            return $Table[$key]
        }
    }
    return $null
}

if (-not (Test-Path -LiteralPath $TaxonomyPath)) {
    throw "Missing taxonomy file: $TaxonomyPath"
}
if (-not (Test-Path -LiteralPath $NodesPath)) {
    throw "Missing nodes file: $NodesPath"
}

$taxonomyRows = Import-Csv -LiteralPath $TaxonomyPath
$startupNodes = Import-Csv -LiteralPath $NodesPath | Where-Object { $_.d1 -in 'Startup', 'Startup4' }
$manualOverrideRows = if (Test-Path -LiteralPath $ManualOverridesPath) { Import-Csv -LiteralPath $ManualOverridesPath } else { @() }
$manualProfileRows = if (Test-Path -LiteralPath $ManualProfileOverridesPath) { Import-Csv -LiteralPath $ManualProfileOverridesPath } else { @() }
$nodesById = @{}
foreach ($node in $startupNodes) {
    $nodesById[[string]$node.id] = $node
}

$manualOverridesByKey = @{}
foreach ($row in $manualOverrideRows) {
    Add-Lookup -Table $manualOverridesByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -Value $row
}

$manualProfilesByKey = @{}
foreach ($row in $manualProfileRows) {
    Add-Lookup -Table $manualProfilesByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -Value $row
}

$scores = foreach ($row in $taxonomyRows) {
    $node = if ($nodesById.ContainsKey([string]$row.startup_id)) { $nodesById[[string]$row.startup_id] } else { $null }
    $manualOverride = Get-Lookup -Table $manualOverridesByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name)
    $manualProfile = Get-Lookup -Table $manualProfilesByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name)
    $flags = New-Object 'System.Collections.Generic.List[string]'

    $country = Clean-Text $row.structured_country
    $sector = Clean-Text $row.structured_sector
    $valuation = Clean-Text $row.valuation_tier
    $origin = if ($null -ne $node) { Clean-Text $node.d8 } else { '' }
    $legacyTrl = if ($null -ne $node) { Clean-Text $node.d3 } else { '' }
    $currentTrl = Clean-Text $row.trl_current
    $currentTrlSource = Clean-Text $row.trl_current_source_url
    $scopeDecision = Clean-Text $row.scope_decision
    $scopeReason = Clean-Text $row.scope_reason
    $assignmentMethod = Clean-Text $row.assignment_method
    $evidenceSource = Clean-Text $row.evidence_source
    $macroTheme = Clean-Text $row.macro_theme
    $manualSourceType = if ($null -ne $manualProfile) { Clean-Text $manualProfile.source_type } else { '' }
    $manualSourceUrl = if ($null -ne $manualProfile) { Clean-Text $manualProfile.source_url } else { '' }
    $manualReviewStatus = if ($null -ne $manualProfile) { Clean-Text $manualProfile.review_status } else { '' }
    $confidence = 0.0
    if (Has-Value $row.confidence) {
        $confidence = [double]$row.confidence
    }

    $degree = 0
    if ($null -ne $node -and (Has-Value $node.degree)) {
        $degree = [int]$node.degree
    }

    $hasManualEvidence = ($null -ne $manualOverride) -or ($null -ne $manualProfile)
    $hasPublicEvidence = $hasManualEvidence -and (Has-Value $evidenceSource -or Has-Value $manualSourceType -or Has-Value $manualSourceUrl)

    $entityScore = 0
    if (Has-Value $country) {
        $entityScore += 1
    } elseif ($hasPublicEvidence) {
        $entityScore += 0.5
        [void]$flags.Add('country_unconfirmed')
    } else {
        [void]$flags.Add('missing_country')
    }
    if ((Has-Value $valuation) -or (Has-Value $origin) -or $hasPublicEvidence) {
        $entityScore += 1
    } else {
        [void]$flags.Add('missing_basic_context')
    }

    $taxonomyScore = 0
    if ($assignmentMethod -eq 'manual_override') {
        $taxonomyScore = 2
    } elseif ($assignmentMethod -eq 'manual_seed') {
        $taxonomyScore = 2
    } elseif ($confidence -ge 0.65 -or $assignmentMethod -in @('keyword_override', 'sector_plus_keyword')) {
        $taxonomyScore = 1.5
    } elseif ($assignmentMethod -in @('keyword_rule', 'unclassified_keyword', 'sector_default')) {
        $taxonomyScore = 1
    } else {
        $taxonomyScore = 0
        [void]$flags.Add('fallback_taxonomy')
    }

    $scopeScore = 0
    if ($scopeDecision -eq 'include' -or $scopeDecision -eq 'exclude') {
        $scopeScore = 2
    } elseif ($scopeDecision -eq 'review') {
        if ($scopeReason -match 'possible_climate_materiality|planetary_boundaries') {
            $scopeScore = 1
            [void]$flags.Add('needs_scope_research')
        } else {
            $scopeScore = 0.5
            [void]$flags.Add('scope_unclear')
        }
    } else {
        [void]$flags.Add('missing_scope_decision')
    }

    $maturityScore = 0
    if ($scopeDecision -eq 'exclude') {
        if ($hasPublicEvidence) {
            $maturityScore = 1.5
        } else {
            $maturityScore = 0.5
        }
    } elseif ((Has-Value $currentTrl) -and (Has-Value $currentTrlSource)) {
        $maturityScore = 2
    } elseif (Has-Value $legacyTrl) {
        $maturityScore = 1
        [void]$flags.Add('needs_current_trl_research')
    } elseif ($hasPublicEvidence) {
        $maturityScore = 1
        [void]$flags.Add('needs_current_trl_research')
    } else {
        [void]$flags.Add('missing_trl')
    }

    $networkScore = 0
    if ($degree -ge 5) {
        $networkScore += 1
    } elseif ($degree -gt 0) {
        $networkScore += 0.5
        if (-not $hasPublicEvidence) {
            [void]$flags.Add('thin_graph_context')
        }
    } else {
        if ($hasPublicEvidence) {
            $networkScore += 0.5
        } else {
            [void]$flags.Add('no_graph_context')
        }
    }

    if ((Has-Value $sector) -and $sector -ne 'Other / Unclassified') {
        $networkScore += 1
    } elseif ($hasPublicEvidence) {
        $networkScore += 0.5
    } else {
        [void]$flags.Add('unclassified_sector')
    }

    $totalScore = [Math]::Round(($entityScore + $taxonomyScore + $scopeScore + $maturityScore + $networkScore), 1)

    $qualityBand =
        if ($totalScore -ge 8.5) { 'high' }
        elseif ($totalScore -ge 6.5) { 'medium' }
        elseif ($totalScore -ge 4.5) { 'fragile' }
        else { 'poor' }

    $researchPriority = [Math]::Round(
        (
            $(if ($scopeDecision -eq 'review') { 4 } elseif ($scopeDecision -eq 'include') { 2 } else { 0 }) +
            $(if ($qualityBand -eq 'poor') { 4 } elseif ($qualityBand -eq 'fragile') { 3 } elseif ($qualityBand -eq 'medium') { 2 } else { 1 }) +
            $(if ($degree -ge 10) { 2 } elseif ($degree -ge 5) { 1 } else { 0 })
        ),
        1
    )

    [PSCustomObject]@{
        startup_id = [string]$row.startup_id
        startup_name = [string]$row.startup_name
        scope_decision = $scopeDecision
        scope_reason = $scopeReason
        macro_theme = $macroTheme
        emergent_theme = [string]$row.emergent_theme
        structured_sector = $sector
        structured_country = $country
        degree = $degree
        confidence = $confidence
        data_quality_score_10 = $totalScore
        quality_band = $qualityBand
        research_priority = $researchPriority
        entity_basics_score = $entityScore
        taxonomy_confidence_score = $taxonomyScore
        scope_clarity_score = $scopeScore
        maturity_evidence_score = $maturityScore
        graph_context_score = $networkScore
        assignment_method = $assignmentMethod
        evidence_source = $evidenceSource
        has_current_trl = (Has-Value $currentTrl)
        missing_signals = (Join-Flags -Flags $flags)
    }
}

$scores = @($scores) | Sort-Object scope_decision, data_quality_score_10, startup_name
$scores | Export-Csv -LiteralPath $OutputScoresPath -NoTypeInformation -Encoding UTF8

$reviewQueue = @(
    $scores |
        Where-Object { $_.scope_decision -eq 'review' } |
        Sort-Object @{ Expression = 'research_priority'; Descending = $true }, @{ Expression = 'data_quality_score_10'; Ascending = $true }, @{ Expression = 'degree'; Descending = $true }, startup_name
)
$reviewQueue | Export-Csv -LiteralPath $OutputReviewPath -NoTypeInformation -Encoding UTF8

$summary = New-Object 'System.Collections.Generic.List[string]'
[void]$summary.Add("# Startup Data Quality")
[void]$summary.Add("")
[void]$summary.Add('Archivo principal: `quality/startup_data_quality_scores.csv`')
[void]$summary.Add("")
[void]$summary.Add("## Escala")
[void]$summary.Add("")
[void]$summary.Add('- `0-10` puntos')
[void]$summary.Add('- `entity_basics_score`')
[void]$summary.Add('- `taxonomy_confidence_score`')
[void]$summary.Add('- `scope_clarity_score`')
[void]$summary.Add('- `maturity_evidence_score`')
[void]$summary.Add('- `graph_context_score`')
[void]$summary.Add("")
[void]$summary.Add("## Totales")
[void]$summary.Add("")
[void]$summary.Add("- startups auditadas: $(@($scores).Count)")
[void]$summary.Add("- include: $(@($scores | Where-Object { $_.scope_decision -eq 'include' }).Count)")
[void]$summary.Add("- review: $(@($scores | Where-Object { $_.scope_decision -eq 'review' }).Count)")
[void]$summary.Add("- exclude: $(@($scores | Where-Object { $_.scope_decision -eq 'exclude' }).Count)")
[void]$summary.Add("")
[void]$summary.Add("## Bandas")
[void]$summary.Add("")
foreach ($group in ($scores | Group-Object quality_band | Sort-Object Name)) {
    [void]$summary.Add("- $($group.Name): $($group.Count)")
}
[void]$summary.Add("")
[void]$summary.Add("## Review queue prioritario")
[void]$summary.Add("")
foreach ($row in ($reviewQueue | Select-Object -First 20)) {
    [void]$summary.Add("- $($row.startup_name): score $($row.data_quality_score_10), priority $($row.research_priority), flags $($row.missing_signals)")
}

Set-Content -LiteralPath $OutputSummaryPath -Value ($summary -join [Environment]::NewLine) -Encoding UTF8

Write-Output "Startup data quality audit built:"
Write-Output "  Scores: $OutputScoresPath"
Write-Output "  Review queue: $OutputReviewPath"
Write-Output "  Summary: $OutputSummaryPath"
