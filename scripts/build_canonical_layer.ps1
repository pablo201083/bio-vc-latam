param(
    [string]$StagingDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\canonical",
    [double]$AutoMergeThreshold = 0.97
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Normalize-Key {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ''
    }

    $decomposed = $Value.Trim().ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD)
    $builder = New-Object System.Text.StringBuilder
    foreach ($char in $decomposed.ToCharArray()) {
        $category = [Globalization.CharUnicodeInfo]::GetUnicodeCategory($char)
        if ($category -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            [void]$builder.Append($char)
        }
    }

    return (($builder.ToString()) -replace '[^a-z0-9]+', '').Trim()
}

function New-DirIfMissing {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Normalize-EntityType {
    param([string]$EntityTypeRaw)
    switch ($EntityTypeRaw) {
        'startup' { return 'startup' }
        'investor' { return 'investor' }
        default { return 'unknown' }
    }
}

New-DirIfMissing -Path $OutputDir

$entitiesPath = Join-Path $StagingDir 'entities_raw.csv'
$edgesPath = Join-Path $StagingDir 'investment_edges_raw.csv'
$mergesPath = Join-Path $StagingDir 'merge_suggestions.csv'
$manualEntitiesPath = Join-Path $OutputDir 'manual_canonical_entities.csv'
$manualAliasesPath = Join-Path $OutputDir 'manual_canonical_aliases.csv'
$manualEdgesPath = Join-Path $OutputDir 'manual_canonical_investment_edges.csv'
$manualMergeOverridesPath = Join-Path $OutputDir 'manual_canonical_merge_overrides.csv'
$manualEdgeExclusionsPath = Join-Path $OutputDir 'manual_investment_edge_exclusions.csv'

$entities = Import-Csv -LiteralPath $entitiesPath
$edges = Import-Csv -LiteralPath $edgesPath
$merges = @(Import-Csv -LiteralPath $mergesPath)
$manualEntities = if (Test-Path -LiteralPath $manualEntitiesPath) { @(Import-Csv -LiteralPath $manualEntitiesPath) } else { @() }
$manualAliases = if (Test-Path -LiteralPath $manualAliasesPath) { @(Import-Csv -LiteralPath $manualAliasesPath) } else { @() }
$manualEdges = if (Test-Path -LiteralPath $manualEdgesPath) { @(Import-Csv -LiteralPath $manualEdgesPath) } else { @() }
$manualMergeOverrides = if (Test-Path -LiteralPath $manualMergeOverridesPath) { @(Import-Csv -LiteralPath $manualMergeOverridesPath) } else { @() }
$manualEdgeExclusions = if (Test-Path -LiteralPath $manualEdgeExclusionsPath) { @(Import-Csv -LiteralPath $manualEdgeExclusionsPath) } else { @() }

if (@($manualMergeOverrides).Count -gt 0) {
    $merges = @($merges + $manualMergeOverrides)
}

if (@($manualEdges).Count -gt 0) {
    $edges = @($edges + $manualEdges)
}

$entityById = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)
foreach ($entity in $entities) {
    $entityById[$entity.entity_id] = $entity
}

$autoMergeMap = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
$aliasRows = New-Object System.Collections.Generic.List[object]
$reviewRows = New-Object System.Collections.Generic.List[object]

foreach ($merge in $merges) {
    $confidence = [double]$merge.merge_confidence
    if ($confidence -ge $AutoMergeThreshold) {
        $autoMergeMap[$merge.alias_entity_id] = $merge.canonical_entity_id
        $aliasRows.Add([PSCustomObject]@{
            alias_id = "alias-" + $merge.alias_entity_id
            entity_id = $merge.canonical_entity_id
            alias = $merge.alias_name
            alias_type = 'merge_from_staging'
            is_preferred = 0
            source_entity_id = $merge.alias_entity_id
            merge_confidence = $merge.merge_confidence
            merge_reason = $merge.merge_reason
        })
    } else {
        $reviewRows.Add([PSCustomObject]@{
            review_type = 'merge_candidate_below_threshold'
            canonical_entity_id = $merge.canonical_entity_id
            canonical_name = $merge.canonical_name
            alias_entity_id = $merge.alias_entity_id
            alias_name = $merge.alias_name
            merge_confidence = $merge.merge_confidence
            notes = $merge.merge_reason
        })
    }
}

$canonicalEntities = New-Object System.Collections.Generic.List[object]
$emitted = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)

foreach ($entity in $entities) {
    if ($autoMergeMap.ContainsKey($entity.entity_id)) {
        continue
    }

    $entityId = $entity.entity_id
    $canonicalName = $entity.canonical_name
    $slug = $entity.slug

    $canonicalEntities.Add([PSCustomObject]@{
        entity_id = $entityId
        entity_type = Normalize-EntityType -EntityTypeRaw $entity.entity_type_raw
        canonical_name = $canonicalName
        slug = $slug
        source_presence = @(
            if ($entity.in_nodes_csv -eq 'True') { 'nodes_csv' }
            if ($entity.in_graphml -eq 'True') { 'graphml' }
        ) -join '|'
        quality_flags = $entity.quality_flags
        confidence_score = $entity.confidence_score
        staging_entity_id = $entity.entity_id
    })

    [void]$emitted.Add($entityId)

    if (-not [string]::IsNullOrWhiteSpace($entity.name_from_nodes_csv) -and $entity.name_from_nodes_csv -ne $canonicalName) {
        $aliasRows.Add([PSCustomObject]@{
            alias_id = "alias-" + $entityId + "-nodes"
            entity_id = $entityId
            alias = $entity.name_from_nodes_csv
            alias_type = 'source_name_nodes_csv'
            is_preferred = 0
            source_entity_id = $entityId
            merge_confidence = ''
            merge_reason = 'Alternative source label from nodes CSV'
        })
    }

    if (-not [string]::IsNullOrWhiteSpace($entity.name_from_graphml) -and $entity.name_from_graphml -ne $canonicalName) {
        $aliasRows.Add([PSCustomObject]@{
            alias_id = "alias-" + $entityId + "-graphml"
            entity_id = $entityId
            alias = $entity.name_from_graphml
            alias_type = 'source_name_graphml'
            is_preferred = 0
            source_entity_id = $entityId
            merge_confidence = ''
            merge_reason = 'Alternative source label from GraphML'
        })
    }
}

foreach ($manualEntity in $manualEntities) {
    if ($emitted.Contains([string]$manualEntity.entity_id)) {
        continue
    }

    $canonicalEntities.Add([PSCustomObject]@{
        entity_id = $manualEntity.entity_id
        entity_type = Normalize-EntityType -EntityTypeRaw $manualEntity.entity_type
        canonical_name = $manualEntity.canonical_name
        slug = $manualEntity.slug
        source_presence = $manualEntity.source_presence
        quality_flags = $manualEntity.quality_flags
        confidence_score = $manualEntity.confidence_score
        staging_entity_id = $manualEntity.staging_entity_id
    })

    [void]$emitted.Add([string]$manualEntity.entity_id)
}

foreach ($merge in $merges | Where-Object { [double]$_.merge_confidence -ge $AutoMergeThreshold }) {
    if ($entityById.ContainsKey($merge.alias_entity_id) -and $entityById.ContainsKey($merge.canonical_entity_id)) {
        $aliasSource = $entityById[$merge.alias_entity_id]
        $canonicalSource = $entityById[$merge.canonical_entity_id]

        if ($aliasSource.canonical_name -ne $canonicalSource.canonical_name) {
            $aliasRows.Add([PSCustomObject]@{
                alias_id = "alias-" + $merge.alias_entity_id + "-canonical-name"
                entity_id = $merge.canonical_entity_id
                alias = $aliasSource.canonical_name
                alias_type = 'merged_canonical_name'
                is_preferred = 0
                source_entity_id = $merge.alias_entity_id
                merge_confidence = $merge.merge_confidence
                merge_reason = $merge.merge_reason
            })
        }
    }
}

foreach ($manualAlias in $manualAliases) {
    $aliasRows.Add([PSCustomObject]@{
        alias_id = $manualAlias.alias_id
        entity_id = $manualAlias.entity_id
        alias = $manualAlias.alias
        alias_type = $manualAlias.alias_type
        is_preferred = $manualAlias.is_preferred
        source_entity_id = $manualAlias.source_entity_id
        merge_confidence = $manualAlias.merge_confidence
        merge_reason = $manualAlias.merge_reason
    })
}

$entityResolutionMap = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)

function Register-ResolutionKey {
    param(
        [System.Collections.IDictionary]$ResolutionMap,
        [string]$RawValue,
        [string]$CanonicalEntityId
    )

    $normalized = Normalize-Key $RawValue
    if ([string]::IsNullOrWhiteSpace($normalized) -or [string]::IsNullOrWhiteSpace($CanonicalEntityId)) {
        return
    }

    if (-not $ResolutionMap.ContainsKey($normalized)) {
        $ResolutionMap[$normalized] = $CanonicalEntityId
    }
}

foreach ($entity in $canonicalEntities) {
    Register-ResolutionKey -ResolutionMap $entityResolutionMap -RawValue $entity.entity_id -CanonicalEntityId $entity.entity_id
    Register-ResolutionKey -ResolutionMap $entityResolutionMap -RawValue $entity.canonical_name -CanonicalEntityId $entity.entity_id
}

foreach ($alias in $aliasRows) {
    Register-ResolutionKey -ResolutionMap $entityResolutionMap -RawValue $alias.alias -CanonicalEntityId $alias.entity_id
    Register-ResolutionKey -ResolutionMap $entityResolutionMap -RawValue $alias.source_entity_id -CanonicalEntityId $alias.entity_id
}

function Resolve-CanonicalEntityId {
    param(
        [string]$CandidateId,
        [System.Collections.IDictionary]$AutoMergeMap,
        [System.Collections.Generic.HashSet[string]]$EmittedEntityIds,
        [System.Collections.IDictionary]$ResolutionMap
    )

    if ([string]::IsNullOrWhiteSpace($CandidateId)) {
        return ''
    }

    if ($AutoMergeMap.ContainsKey($CandidateId)) {
        return [string]$AutoMergeMap[$CandidateId]
    }

    if ($EmittedEntityIds.Contains($CandidateId)) {
        return [string]$CandidateId
    }

    $normalized = Normalize-Key $CandidateId
    if (-not [string]::IsNullOrWhiteSpace($normalized) -and $ResolutionMap.ContainsKey($normalized)) {
        return [string]$ResolutionMap[$normalized]
    }

    return [string]$CandidateId
}

$edgeExclusionRules = New-Object System.Collections.Generic.List[object]
foreach ($rule in $manualEdgeExclusions) {
    $resolvedInvestorId = Resolve-CanonicalEntityId -CandidateId $rule.investor_id -AutoMergeMap $autoMergeMap -EmittedEntityIds $emitted -ResolutionMap $entityResolutionMap
    $edgeExclusionRules.Add([PSCustomObject]@{
        investor_id = [string]$resolvedInvestorId
        source_file = [string]$rule.source_file
        reason = [string]$rule.reason
    })
}

function Test-EdgeExcluded {
    param(
        [string]$InvestorId,
        [string]$SourceFile,
        [System.Collections.Generic.List[object]]$Rules
    )

    foreach ($rule in $Rules) {
        if ($rule.investor_id -ne $InvestorId) {
            continue
        }
        if ([string]::IsNullOrWhiteSpace($rule.source_file) -or $rule.source_file -eq $SourceFile) {
            return $rule.reason
        }
    }

    return ''
}

$canonicalEdges = New-Object System.Collections.Generic.List[object]
foreach ($edge in $edges) {
    $resolvedInvestorId = ''
    $resolvedStartupId = ''

    if (-not [string]::IsNullOrWhiteSpace($edge.investor_id_candidate)) {
        $resolvedInvestorId = Resolve-CanonicalEntityId -CandidateId $edge.investor_id_candidate -AutoMergeMap $autoMergeMap -EmittedEntityIds $emitted -ResolutionMap $entityResolutionMap
    }
    if (-not [string]::IsNullOrWhiteSpace($edge.startup_id_candidate)) {
        $resolvedStartupId = Resolve-CanonicalEntityId -CandidateId $edge.startup_id_candidate -AutoMergeMap $autoMergeMap -EmittedEntityIds $emitted -ResolutionMap $entityResolutionMap
    }

    if ([string]::IsNullOrWhiteSpace($resolvedInvestorId) -or [string]::IsNullOrWhiteSpace($resolvedStartupId)) {
        $reviewRows.Add([PSCustomObject]@{
            review_type = 'edge_missing_resolved_endpoint'
            canonical_entity_id = $edge.raw_edge_id
            canonical_name = $edge.source_id
            alias_entity_id = $edge.target_id
            alias_name = $edge.source_file
            merge_confidence = $edge.confidence_score
            notes = 'Edge skipped because investor or startup could not be resolved'
        })
        continue
    }

    $edgeExclusionReason = Test-EdgeExcluded -InvestorId $resolvedInvestorId -SourceFile ([string]$edge.source_file) -Rules $edgeExclusionRules
    if (-not [string]::IsNullOrWhiteSpace($edgeExclusionReason)) {
        $reviewRows.Add([PSCustomObject]@{
            review_type = 'edge_excluded_manual_rule'
            canonical_entity_id = $resolvedInvestorId
            canonical_name = $resolvedStartupId
            alias_entity_id = $edge.raw_edge_id
            alias_name = $edge.source_file
            merge_confidence = $edge.confidence_score
            notes = $edgeExclusionReason
        })
        continue
    }

    $canonicalEdges.Add([PSCustomObject]@{
        investment_id = if ([string]::IsNullOrWhiteSpace($edge.raw_edge_id)) { "edge-$resolvedInvestorId-$resolvedStartupId" } else { $edge.raw_edge_id }
        investor_id = $resolvedInvestorId
        startup_id = $resolvedStartupId
        relation_type_raw = $edge.relation_type_raw
        direction_status = $edge.direction_status
        confidence_score = $edge.confidence_score
        source_file = $edge.source_file
        notes = $edge.notes
    })
}

$canonicalEntities |
    Sort-Object entity_type, canonical_name |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'canonical_entities.csv') -NoTypeInformation -Encoding UTF8

$aliasRows |
    Sort-Object entity_id, alias |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'canonical_aliases.csv') -NoTypeInformation -Encoding UTF8

$canonicalEdges |
    Sort-Object investor_id, startup_id, source_file |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'canonical_investment_edges.csv') -NoTypeInformation -Encoding UTF8

$reviewRows |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'canonical_review_queue.csv') -NoTypeInformation -Encoding UTF8

@(
    [PSCustomObject]@{metric='canonical_entities'; value=[int]$canonicalEntities.Count}
    [PSCustomObject]@{metric='canonical_aliases'; value=[int]$aliasRows.Count}
    [PSCustomObject]@{metric='canonical_investment_edges'; value=[int]$canonicalEdges.Count}
    [PSCustomObject]@{metric='review_queue_items'; value=[int]$reviewRows.Count}
    [PSCustomObject]@{metric='auto_merge_threshold'; value=[double]$AutoMergeThreshold}
) |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'canonical_summary.csv') -NoTypeInformation -Encoding UTF8

Write-Output "Canonical layer built: $OutputDir"
