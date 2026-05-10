param(
    [string]$IntegratedDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\integrated",
    [string]$StructuredNodesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\structured_gephi\structured_nodes_426112025.csv",
    [string]$OutputPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\ecosystem-integrated-data.js"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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

    return ((($builder.ToString()).ToLowerInvariant()) -replace '[^a-z0-9]+', '-').Trim('-')
}

$entities = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_entities.csv')
$relations = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_relations.csv')
$provenance = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_provenance.csv')
$structuredNodes =
    if (Test-Path -LiteralPath $StructuredNodesPath) {
        Import-Csv -LiteralPath $StructuredNodesPath
    } else {
        @()
    }

$neighbors = @{}
foreach ($relation in $relations) {
    if (-not $neighbors.ContainsKey($relation.source_entity_id)) {
        $neighbors[$relation.source_entity_id] = New-Object System.Collections.Generic.HashSet[string]
    }
    if (-not $neighbors.ContainsKey($relation.target_entity_id)) {
        $neighbors[$relation.target_entity_id] = New-Object System.Collections.Generic.HashSet[string]
    }
    [void]$neighbors[$relation.source_entity_id].Add([string]$relation.target_entity_id)
    [void]$neighbors[$relation.target_entity_id].Add([string]$relation.source_entity_id)
}

$degree = @{}
foreach ($entityId in $neighbors.Keys) {
    $degree[$entityId] = $neighbors[$entityId].Count
}

$connectedIds = @($degree.Keys)

$structuredLookup = @{}
$structuredMatchedSlugs = New-Object System.Collections.Generic.HashSet[string]
foreach ($structuredNode in $structuredNodes) {
    $keys = @(
        (Normalize-Key $structuredNode.slug),
        (Normalize-Key $structuredNode.label),
        (Normalize-Key $structuredNode.inferred_sector)
    ) | Where-Object { $_ }

    foreach ($key in $keys) {
        if (-not $structuredLookup.ContainsKey($key)) {
            $structuredLookup[$key] = $structuredNode
        }
    }
}

$nodes = foreach ($entity in $entities | Where-Object { $connectedIds -contains $_.entity_id }) {
    $d = if ($degree.ContainsKey($entity.entity_id)) { [int]$degree[$entity.entity_id] } else { 0 }
    $size =
        if ($entity.integrated_type -eq 'capital') { [Math]::Min(44, 10 + $d) }
        elseif ($entity.integrated_type -eq 'institution') { [Math]::Min(32, 8 + ($d * 0.8)) }
        else { [Math]::Min(16, 4 + ($d * 0.35)) }

    $match = $null
    $entityKeys = @(
        (Normalize-Key $entity.slug),
        (Normalize-Key $entity.canonical_name)
    ) | Where-Object { $_ }

    foreach ($entityKey in $entityKeys) {
        if ($structuredLookup.ContainsKey($entityKey)) {
            $match = $structuredLookup[$entityKey]
            break
        }
    }

    if ($null -ne $match) {
        [void]$structuredMatchedSlugs.Add([string]$match.slug)
    }

    [PSCustomObject]@{
        id = $entity.entity_id
        label = $entity.canonical_name
        type = $entity.integrated_type
        size = [Math]::Round($size, 1)
        degree = $d
        confidence_score = $entity.confidence_score
        sources = $entity.integrated_sources
        quality_flags = $entity.quality_flags
        canonical_type = $entity.canonical_type
        structured_match = ($null -ne $match)
        structured_type = if ($null -ne $match) { $match.inferred_type } else { '' }
        structured_country = if ($null -ne $match) { $match.inferred_country } else { '' }
        structured_sector = if ($null -ne $match) { $match.inferred_sector } else { '' }
        structured_label = if ($null -ne $match) { $match.label } else { '' }
        structured_slug = if ($null -ne $match) { $match.slug } else { '' }
        structured_raw_attrs = if ($null -ne $match) { $match.raw_attrs } else { '' }
    }
}

$edges = foreach ($relation in $relations) {
    [PSCustomObject]@{
        source = $relation.source_entity_id
        target = $relation.target_entity_id
        kind = $relation.relation_type
        confidence = $relation.confidence
        source_kind = $relation.source_kind
    }
}

$unmatchedStructured = @(
    $structuredNodes |
        Where-Object { -not $structuredMatchedSlugs.Contains([string]$_.slug) } |
        Sort-Object inferred_type, label
)

$structuredTypeCounts = @{}
foreach ($row in $structuredNodes) {
    $typeKey = if ([string]::IsNullOrWhiteSpace($row.inferred_type)) { 'Unknown' } else { [string]$row.inferred_type }
    $currentCount = if ($structuredTypeCounts.ContainsKey($typeKey)) { [int]$structuredTypeCounts[$typeKey] } else { 0 }
    $structuredTypeCounts[$typeKey] = 1 + $currentCount
}

$summary = [PSCustomObject]@{
    generated_at = (Get-Date).ToString('s')
    nodes_total = @($nodes).Count
    edges_total = @($edges).Count
    connected_capital = @($nodes | Where-Object { $_.type -eq 'capital' }).Count
    connected_institutions = @($nodes | Where-Object { $_.type -eq 'institution' }).Count
    connected_startups = @($nodes | Where-Object { $_.type -eq 'startup' }).Count
    provenance_rows = @($provenance).Count
    structured_nodes_total = @($structuredNodes).Count
    structured_matches_total = @($nodes | Where-Object { $_.structured_match }).Count
    structured_unmatched_total = @($unmatchedStructured).Count
}

$payload = [PSCustomObject]@{
    summary = $summary
    nodes = @($nodes)
    edges = @($edges)
    coverage = [PSCustomObject]@{
        structured_nodes_total = @($structuredNodes).Count
        connected_nodes_total = @($nodes).Count
        structured_matches_total = @($nodes | Where-Object { $_.structured_match }).Count
        structured_unmatched_total = @($unmatchedStructured).Count
        structured_type_counts = @(
            $structuredTypeCounts.GetEnumerator() |
                Sort-Object Name |
                ForEach-Object {
                    [PSCustomObject]@{
                        type = $_.Name
                        count = $_.Value
                    }
                }
        )
        unmatched_preview = @(
            $unmatchedStructured |
                Select-Object -First 18 |
                ForEach-Object {
                    [PSCustomObject]@{
                        label = $_.label
                        type = $_.inferred_type
                        country = $_.inferred_country
                        sector = $_.inferred_sector
                    }
                }
        )
    }
}

$js = "window.ECOSYSTEM_DATA = " + ($payload | ConvertTo-Json -Depth 7) + ";"
Set-Content -LiteralPath $OutputPath -Value $js -Encoding UTF8

Write-Output "Integrated ecosystem data built: $OutputPath"
