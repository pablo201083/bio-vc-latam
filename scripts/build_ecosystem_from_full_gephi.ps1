param(
    [string]$FullGephiDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\full_gephi_graph",
    [string]$OutputPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\ecosystem-integrated-data.js",
    [string]$TaxonomyPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_taxonomy_assignments_v1.csv",
    [string]$MasterDatasetPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$AliasOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\manual_alias_overrides.csv"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-NormalizedType {
    param(
        [string]$RawType,
        [string]$InvestorType,
        [string]$InstitutionType
    )

    switch ($RawType) {
        'Startup' { return 'startup' }
        'Startup4' { return 'startup' }
        'Founder' { return 'founder' }
        'Founder4' { return 'founder' }
        'Investor' { return 'capital' }
        'Investor4' { return 'capital' }
        'Accelerator' { return 'capital' }
        'Corporate VC' { return 'capital' }
        'University' { return 'institution' }
        'Research Institute' { return 'institution' }
        'Knowledge Hub' { return 'institution' }
        'Knowledge Hub4' { return 'institution' }
        'Chamber' { return 'institution' }
        'Corporate' { return 'institution' }
        default {
            if (-not [string]::IsNullOrWhiteSpace($InvestorType)) { return 'capital' }
            if (-not [string]::IsNullOrWhiteSpace($InstitutionType)) { return 'institution' }
            return 'institution'
        }
    }
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

function Normalize-Key {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ''
    }

    $decomposed = $Value.Normalize([Text.NormalizationForm]::FormD)
    $builder = New-Object System.Text.StringBuilder
    foreach ($char in $decomposed.ToCharArray()) {
        $category = [Globalization.CharUnicodeInfo]::GetUnicodeCategory($char)
        if ($category -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            [void]$builder.Append($char)
        }
    }

    return (($builder.ToString().ToLowerInvariant()) -replace '[^a-z0-9]+', '').Trim()
}

function Get-NodeScore {
    param(
        [object]$NodeRow,
        [object]$MasterRow
    )

    $score = 0
    if ($null -ne $MasterRow) { $score += 100 }
    if (-not [string]::IsNullOrWhiteSpace([string](Get-Field -Row $NodeRow -Name 'd2'))) { $score += 6 }
    if (-not [string]::IsNullOrWhiteSpace([string](Get-Field -Row $NodeRow -Name 'd4'))) { $score += 4 }
    if (Get-Field -Row $NodeRow -Name 'degree') { $score += [int](Get-Field -Row $NodeRow -Name 'degree') }
    if (Get-Field -Row $NodeRow -Name 'size_gephi') { $score += [math]::Round([double](Get-Field -Row $NodeRow -Name 'size_gephi')) }
    $label = [string](Get-Field -Row $NodeRow -Name 'label')
    if ($label -match '\s') { $score += 3 }
    return $score
}

$nodesPath = Join-Path $FullGephiDir 'nodes_full.csv'
$edgesPath = Join-Path $FullGephiDir 'edges_full.csv'
$summaryPath = Join-Path $FullGephiDir 'summary_full.csv'

if (-not (Test-Path -LiteralPath $nodesPath)) {
    throw "Missing nodes file: $nodesPath"
}
if (-not (Test-Path -LiteralPath $edgesPath)) {
    throw "Missing edges file: $edgesPath"
}

$rawNodes = Import-Csv -LiteralPath $nodesPath
$rawEdges = Import-Csv -LiteralPath $edgesPath
$rawSummary = if (Test-Path -LiteralPath $summaryPath) { Import-Csv -LiteralPath $summaryPath } else { @() }
$taxonomyRows = if (Test-Path -LiteralPath $TaxonomyPath) { Import-Csv -LiteralPath $TaxonomyPath } else { @() }
$masterRows = if (Test-Path -LiteralPath $MasterDatasetPath) { Import-Csv -LiteralPath $MasterDatasetPath } else { @() }
$aliasRows = if (Test-Path -LiteralPath $AliasOverridesPath) { Import-Csv -LiteralPath $AliasOverridesPath } else { @() }

$taxonomyById = @{}
foreach ($row in $taxonomyRows) {
    $taxonomyById[[string]$row.startup_id] = $row
}

$masterById = @{}
$masterByKey = @{}
foreach ($row in $masterRows) {
    $masterById[[string]$row.startup_id] = $row
    foreach ($key in @(
        (Normalize-Key ([string]$row.startup_id)),
        (Normalize-Key ([string]$row.startup_name))
    ) | Where-Object { $_ }) {
        if (-not $masterByKey.ContainsKey($key)) {
            $masterByKey[$key] = $row
        }
    }
}

$aliasMap = @{}
foreach ($row in $aliasRows) {
    $aliasKey = Normalize-Key ([string]$row.alias_name)
    $canonicalKey = Normalize-Key ([string]$row.canonical_name)
    if ($aliasKey -and $canonicalKey) {
        $aliasMap[$aliasKey] = $canonicalKey
    }
}

$neighborSets = @{}
foreach ($edge in $rawEdges) {
    if (-not $neighborSets.ContainsKey($edge.source)) {
        $neighborSets[$edge.source] = New-Object System.Collections.Generic.HashSet[string]
    }
    if (-not $neighborSets.ContainsKey($edge.target)) {
        $neighborSets[$edge.target] = New-Object System.Collections.Generic.HashSet[string]
    }
    [void]$neighborSets[$edge.source].Add([string]$edge.target)
    [void]$neighborSets[$edge.target].Add([string]$edge.source)
}

$startupCandidatesByCanonicalId = @{}
$nonStartupNodes = New-Object System.Collections.Generic.List[object]
$nodeIdRemap = @{}

foreach ($node in $rawNodes) {
    $nodeId = [string](Get-Field -Row $node -Name 'id')
    $nodeLabel = [string](Get-Field -Row $node -Name 'label')
    $rawType = [string](Get-Field -Row $node -Name 'd1')
    $investorType = [string](Get-Field -Row $node -Name 'd11')
    $institutionType = [string](Get-Field -Row $node -Name 'd10')
    $normalizedType = Get-NormalizedType -RawType $rawType -InvestorType $investorType -InstitutionType $institutionType

    if ($normalizedType -eq 'startup') {
        $candidateKeys = @(
            (Normalize-Key $nodeId),
            (Normalize-Key $nodeLabel)
        ) | Where-Object { $_ }

        $masterRow = $null
        foreach ($candidateKey in $candidateKeys) {
            $lookupKey = if ($aliasMap.ContainsKey($candidateKey)) { [string]$aliasMap[$candidateKey] } else { $candidateKey }
            if ($masterByKey.ContainsKey($lookupKey)) {
                $masterRow = $masterByKey[$lookupKey]
                break
            }
        }

        $canonicalId = if ($null -ne $masterRow) { [string]$masterRow.startup_id } else { $nodeId }
        $nodeIdRemap[$nodeId] = $canonicalId
        $score = Get-NodeScore -NodeRow $node -MasterRow $masterRow
        $existing = if ($startupCandidatesByCanonicalId.ContainsKey($canonicalId)) { $startupCandidatesByCanonicalId[$canonicalId] } else { $null }
        if ($null -eq $existing -or $score -gt [int]$existing.score) {
            $startupCandidatesByCanonicalId[$canonicalId] = [PSCustomObject]@{
                row = $node
                master = $masterRow
                score = $score
                canonical_id = $canonicalId
                canonical_label = if ($null -ne $masterRow) { [string]$masterRow.startup_name } else { $nodeLabel }
            }
        }
        continue
    }

    $nodeIdRemap[$nodeId] = $nodeId
    $nonStartupNodes.Add($node)
}

$effectiveNodes = @($nonStartupNodes.ToArray()) + @($startupCandidatesByCanonicalId.Values | ForEach-Object { $_.row })

$nodes = foreach ($node in $effectiveNodes) {
    $nodeId = [string](Get-Field -Row $node -Name 'id')
    $rawType = [string](Get-Field -Row $node -Name 'd1')
    $investorType = [string](Get-Field -Row $node -Name 'd11')
    $institutionType = [string](Get-Field -Row $node -Name 'd10')
    $degreeField = Get-Field -Row $node -Name 'degree'
    $pageRankField = Get-Field -Row $node -Name 'pageranks'
    $gephiSizeField = Get-Field -Row $node -Name 'size_gephi'
    $degree = if ($neighborSets.ContainsKey($nodeId)) { $neighborSets[$nodeId].Count } elseif ($degreeField) { [int]$degreeField } else { 0 }
    $normalizedType = Get-NormalizedType -RawType $rawType -InvestorType $investorType -InstitutionType $institutionType
    $pageRank = if ($pageRankField) { [double]$pageRankField } else { 0.0 }
    $gephiSize = if ($gephiSizeField) { [double]$gephiSizeField } else { 1.0 }
    $size =
        if ($normalizedType -eq 'capital') { [Math]::Min(52, [Math]::Max(8, $gephiSize * 0.95)) }
        elseif ($normalizedType -eq 'institution') { [Math]::Min(50, [Math]::Max(7, $gephiSize * 0.88)) }
        elseif ($normalizedType -eq 'founder') { [Math]::Min(14, [Math]::Max(3, $gephiSize * 0.34)) }
        else { [Math]::Min(20, [Math]::Max(4, $gephiSize * 0.45)) }
    $canonicalId = if ($nodeIdRemap.ContainsKey($nodeId)) { [string]$nodeIdRemap[$nodeId] } else { $nodeId }
    $master = if ($masterById.ContainsKey($canonicalId)) { $masterById[$canonicalId] } else { $null }
    $taxonomy = if ($taxonomyById.ContainsKey($canonicalId)) { $taxonomyById[$canonicalId] } else { $null }
    $thesisFit = if ($null -ne $taxonomy) { [string](Get-Field -Row $taxonomy -Name 'thesis_fit') } else { '' }
    $macroTheme = if ($null -ne $taxonomy) { [string](Get-Field -Row $taxonomy -Name 'macro_theme') } else { '' }
    $scopeDecision = if ($null -ne $taxonomy) { [string](Get-Field -Row $taxonomy -Name 'scope_decision') } else { '' }
    $scopeReason = if ($null -ne $taxonomy) { [string](Get-Field -Row $taxonomy -Name 'scope_reason') } else { '' }
    $scopeSource = if ($null -ne $taxonomy) { [string](Get-Field -Row $taxonomy -Name 'scope_source') } else { '' }
    $isIncludedInThesisScope = if ($normalizedType -ne 'startup') { $true } else { $scopeDecision -ne 'exclude' }
    $nodeLabel = if ($null -ne $master) { [string]$master.startup_name } else { [string](Get-Field -Row $node -Name 'label') }

    [PSCustomObject]@{
        id = $canonicalId
        label = $nodeLabel
        type = $normalizedType
        size = [Math]::Round($size, 1)
        degree = $degree
        confidence_score = 1
        sources = 'full_gephi'
        quality_flags = ''
        canonical_type = $normalizedType
        structured_match = $true
        structured_type = $rawType
        structured_country = Get-Field -Row $node -Name 'd2'
        structured_sector = Get-Field -Row $node -Name 'd4'
        structured_label = [string](Get-Field -Row $node -Name 'label')
        structured_slug = $nodeId
        structured_raw_attrs = @(
            (Get-Field -Row $node -Name 'd11'),
            (Get-Field -Row $node -Name 'd10'),
            (Get-Field -Row $node -Name 'd8'),
            (Get-Field -Row $node -Name 'd7'),
            (Get-Field -Row $node -Name 'd6'),
            (Get-Field -Row $node -Name 'd5'),
            (Get-Field -Row $node -Name 'd4'),
            (Get-Field -Row $node -Name 'd3'),
            (Get-Field -Row $node -Name 'd2'),
            $rawType
        ) -join '|'
        pagerank = [Math]::Round($pageRank, 12)
        gephi_x = if (Get-Field -Row $node -Name 'x') { [double](Get-Field -Row $node -Name 'x') } else { 0.0 }
        gephi_y = if (Get-Field -Row $node -Name 'y') { [double](Get-Field -Row $node -Name 'y') } else { 0.0 }
        gephi_z = if (Get-Field -Row $node -Name 'z') { [double](Get-Field -Row $node -Name 'z') } else { 0.0 }
        gephi_size = [Math]::Round($gephiSize, 4)
        gephi_r = if (Get-Field -Row $node -Name 'r') { [double](Get-Field -Row $node -Name 'r') } else { 0.0 }
        gephi_g = if (Get-Field -Row $node -Name 'g') { [double](Get-Field -Row $node -Name 'g') } else { 0.0 }
        gephi_b = if (Get-Field -Row $node -Name 'b') { [double](Get-Field -Row $node -Name 'b') } else { 0.0 }
        gephi_alpha = if (Get-Field -Row $node -Name 'alpha') { [double](Get-Field -Row $node -Name 'alpha') } else { 1.0 }
        investor_type = $investorType
        institution_type = $institutionType
        origin = Get-Field -Row $node -Name 'd8'
        scientist = Get-Field -Row $node -Name 'd7'
        gender = Get-Field -Row $node -Name 'd6'
        valuation_tier = Get-Field -Row $node -Name 'd5'
        trl = Get-Field -Row $node -Name 'd3'
        thesis_fit = $thesisFit
        macro_theme = $macroTheme
        scope_decision = $scopeDecision
        scope_reason = $scopeReason
        scope_source = $scopeSource
        included_in_thesis_scope = $isIncludedInThesisScope
    }
}

$includedNodeIds = New-Object System.Collections.Generic.HashSet[string]
foreach ($node in $nodes) {
    if ($node.type -eq 'startup') {
        if ($node.included_in_thesis_scope) {
            [void]$includedNodeIds.Add([string]$node.id)
        }
    } else {
        [void]$includedNodeIds.Add([string]$node.id)
    }
}

$dedupedEdges = @{}
$edges = foreach ($edge in $rawEdges) {
    $sourceId = if ($nodeIdRemap.ContainsKey([string]$edge.source)) { [string]$nodeIdRemap[[string]$edge.source] } else { [string]$edge.source }
    $targetId = if ($nodeIdRemap.ContainsKey([string]$edge.target)) { [string]$nodeIdRemap[[string]$edge.target] } else { [string]$edge.target }
    if ($sourceId -eq $targetId) { continue }
    if (-not $includedNodeIds.Contains($sourceId)) { continue }
    if (-not $includedNodeIds.Contains($targetId)) { continue }
    $kind = if ($edge.d12) { [string]$edge.d12 } else { 'unknown' }
    $edgeKey = "$sourceId|$targetId|$kind"
    if ($dedupedEdges.ContainsKey($edgeKey)) { continue }
    $dedupedEdges[$edgeKey] = $true
    [PSCustomObject]@{
        source = $sourceId
        target = $targetId
        kind = if ($edge.d12) { $edge.d12 } else { 'unknown' }
        confidence = 1
        source_kind = 'full_gephi'
        weight = $edge.weight
        directed = $edge.directed
    }
}

$connectedNodeIds = New-Object System.Collections.Generic.HashSet[string]
foreach ($edge in $edges) {
    [void]$connectedNodeIds.Add([string]$edge.source)
    [void]$connectedNodeIds.Add([string]$edge.target)
}

$nodes = @(
    $nodes | Where-Object {
        if ($_.type -eq 'startup') {
            $_.included_in_thesis_scope -and $connectedNodeIds.Contains([string]$_.id)
        } else {
            $connectedNodeIds.Contains([string]$_.id)
        }
    }
)

$relationshipCounts = @{}
foreach ($edge in $edges) {
    $key = [string]$edge.kind
    $relationshipCounts[$key] = 1 + $(if ($relationshipCounts.ContainsKey($key)) { [int]$relationshipCounts[$key] } else { 0 })
}

$rawTypeCounts = @{}
foreach ($node in $rawNodes) {
    $key = if ([string]::IsNullOrWhiteSpace($node.d1)) { 'Unknown' } else { [string]$node.d1 }
    $rawTypeCounts[$key] = 1 + $(if ($rawTypeCounts.ContainsKey($key)) { [int]$rawTypeCounts[$key] } else { 0 })
}

$summaryLookup = @{}
foreach ($row in $rawSummary) {
    $summaryLookup[[string]$row.metric] = [string]$row.value
}

$summary = [PSCustomObject]@{
    generated_at = (Get-Date).ToString('s')
    nodes_total = @($nodes).Count
    edges_total = @($edges).Count
    connected_capital = @($nodes | Where-Object { $_.type -eq 'capital' }).Count
    connected_institutions = @($nodes | Where-Object { $_.type -eq 'institution' }).Count
    connected_founders = @($nodes | Where-Object { $_.type -eq 'founder' }).Count
    connected_startups = @($nodes | Where-Object { $_.type -eq 'startup' }).Count
    thesis_scope_startups = @($nodes | Where-Object { $_.type -eq 'startup' -and $_.included_in_thesis_scope }).Count
    scope_include_startups = @($nodes | Where-Object { $_.type -eq 'startup' -and $_.scope_decision -eq 'include' }).Count
    scope_review_startups = @($nodes | Where-Object { $_.type -eq 'startup' -and $_.scope_decision -eq 'review' }).Count
    excluded_scope_startups = @($taxonomyRows | Where-Object { $_.scope_decision -eq 'exclude' }).Count
    provenance_rows = @($nodes).Count + @($edges).Count
    structured_nodes_total = if ($summaryLookup.ContainsKey('nodes_total')) { [int]$summaryLookup['nodes_total'] } else { @($nodes).Count }
    structured_matches_total = @($nodes).Count
    structured_unmatched_total = 0
    source_mode = 'full_gephi'
}

$coverage = [PSCustomObject]@{
    structured_nodes_total = $summary.structured_nodes_total
    connected_nodes_total = @($nodes).Count
    structured_matches_total = @($nodes).Count
    structured_unmatched_total = 0
    structured_type_counts = @(
        $rawTypeCounts.GetEnumerator() |
            Sort-Object Name |
            ForEach-Object {
                [PSCustomObject]@{
                    type = $_.Name
                    count = $_.Value
                }
            }
    )
    relationship_counts = @(
        $relationshipCounts.GetEnumerator() |
            Sort-Object Name |
            ForEach-Object {
                [PSCustomObject]@{
                    kind = $_.Name
                    count = $_.Value
                }
            }
    )
    unmatched_preview = @()
}

$payload = [PSCustomObject]@{
    summary = $summary
    nodes = @($nodes)
    edges = @($edges)
    coverage = $coverage
}

$js = "window.ECOSYSTEM_DATA = " + ($payload | ConvertTo-Json -Depth 8) + ";"
Set-Content -LiteralPath $OutputPath -Value $js -Encoding UTF8

Write-Output "Full Gephi ecosystem data built: $OutputPath"
