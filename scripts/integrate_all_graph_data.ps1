param(
    [string]$CanonicalDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\canonical",
    [string]$HistoricalDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\historical_consolidation\cleaned",
    [string]$InstitutionCandidatesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\ecosystem_institution_candidates.csv",
    [string]$RelationSeedsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\ecosystem_relation_seeds.csv",
    [string]$ManualAliasOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\manual_alias_overrides.csv",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\integrated"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Repair-Mojibake {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return '' }

    $value = [string]$Text
    $value = $value -replace 'Ã¡','á'
    $value = $value -replace 'Ã©','é'
    $value = $value -replace 'Ãí','í'
    $value = $value -replace 'Ã³','ó'
    $value = $value -replace 'Ãº','ú'
    $value = $value -replace 'Ã±','ñ'
    $value = $value -replace 'Ã¼','ü'
    $value = $value -replace 'Ã¤','ä'
    $value = $value -replace '�',''
    return $value
}

function Normalize-Name {
    param([string]$Name)
    if ([string]::IsNullOrWhiteSpace($Name)) { return '' }

    $n = Repair-Mojibake $Name
    $n = $n.ToLowerInvariant()
    $n = $n.Normalize([Text.NormalizationForm]::FormD)
    $chars = foreach ($c in $n.ToCharArray()) {
        if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($c) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            $c
        }
    }
    $n = -join $chars
    $n = $n -replace '[^a-z0-9]+',''
    return $n
}

function New-Slug {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return '' }

    $slug = Repair-Mojibake $Text
    $slug = $slug.ToLowerInvariant()
    $slug = $slug.Normalize([Text.NormalizationForm]::FormD)
    $chars = foreach ($c in $slug.ToCharArray()) {
        if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($c) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            $c
        }
    }
    $slug = -join $chars
    $slug = $slug -replace '[^a-z0-9]+','-'
    $slug = $slug.Trim('-')
    return $slug
}

function Map-Type {
    param([string]$Type)
    switch -Regex ($Type) {
        'investor|capital_candidate|capital' { return 'capital' }
        'institution_candidate|university|research_institute|accelerator' { return 'institution' }
        'startup|startup_candidate' { return 'startup' }
        default { return 'other' }
    }
}

function Get-SafeEntityId {
    param(
        [string]$EntityId,
        [string]$Slug,
        [string]$CanonicalName
    )

    if ($EntityId -match '^[a-z0-9-]+$' -and $EntityId -notmatch '^[0-9]+$') {
        return $EntityId
    }

    if (-not [string]::IsNullOrWhiteSpace($Slug)) {
        return $Slug
    }

    return (New-Slug $CanonicalName)
}

function Is-UsableHistoricalCandidate {
    param(
        [string]$Name,
        [string]$EntityType,
        [int]$SourceCount
    )

    if ([string]::IsNullOrWhiteSpace($Name)) { return $false }
    if ($EntityType -ne 'institution_candidate') { return $true }

    if ($Name -match 'Research Institute|University g|Knowledge|\.A$|\.B$|\.C$|Knowle|Investigaci$|Tecnolog$|Biolog$|Universidad$|Instituto$') {
        return $false
    }

    if ($SourceCount -ge 2) { return $true }

    return $Name -match 'Universidad de Buenos Aires|Universidad Nacional|Instituto Leloir|CONICET|INTA|ITBA|UCEMA|UdeSA|IAE Business School|Institut Pasteur Montevideo|IFIR|IPROBYQ|IAL|IQUIBICEN|Instituto Balseiro|Instituto Butantan'
}

Ensure-Dir -Path $OutputDir

$canonicalEntities = Import-Csv -LiteralPath (Join-Path $CanonicalDir 'canonical_entities.csv')
$canonicalAliases = Import-Csv -LiteralPath (Join-Path $CanonicalDir 'canonical_aliases.csv')
$canonicalEdges = Import-Csv -LiteralPath (Join-Path $CanonicalDir 'canonical_investment_edges.csv')
$canonicalReviewQueue = Import-Csv -LiteralPath (Join-Path $CanonicalDir 'canonical_review_queue.csv')
$historicalClean = Import-Csv -LiteralPath (Join-Path $HistoricalDir 'historical_entities_candidates_clean.csv')
$historicalHigh = Import-Csv -LiteralPath (Join-Path $HistoricalDir 'historical_entities_candidates_high_confidence.csv')
$historicalProvenance = Import-Csv -LiteralPath (Join-Path $HistoricalDir 'historical_entity_provenance_clean.csv')
$institutionCandidates = Import-Csv -LiteralPath $InstitutionCandidatesPath
$relationSeeds = Import-Csv -LiteralPath $RelationSeedsPath
$manualAliasOverrides = Import-Csv -LiteralPath $ManualAliasOverridesPath

$integratedEntities = New-Object System.Collections.Generic.List[object]
$integratedAliases = New-Object System.Collections.Generic.List[object]
$integratedProvenance = New-Object System.Collections.Generic.List[object]
$integratedRelations = New-Object System.Collections.Generic.List[object]
$reviewQueue = New-Object System.Collections.Generic.List[object]

$byNorm = @{}
$byId = @{}
$aliasNormToEntityId = @{}
$provenanceSeen = @{}
$relationSeen = @{}
$aliasSeen = @{}
$canonicalIdMap = @{}
$mergeEntityIdMap = @{}

function Add-Provenance {
    param(
        [string]$EntityId,
        [string]$CanonicalName,
        [string]$SourceFile,
        [string]$SourceKind,
        [string]$ExtractionMethod,
        [string]$Notes
    )

    $key = "$EntityId|$SourceFile|$SourceKind|$ExtractionMethod|$Notes"
    if ($provenanceSeen.ContainsKey($key)) { return }
    $provenanceSeen[$key] = $true

    $integratedProvenance.Add([PSCustomObject]@{
        entity_id = $EntityId
        canonical_name = $CanonicalName
        source_file = $SourceFile
        source_kind = $SourceKind
        extraction_method = $ExtractionMethod
        notes = $Notes
    }) | Out-Null
}

function Add-Alias {
    param(
        [string]$EntityId,
        [string]$Alias,
        [string]$AliasType,
        [string]$SourceKind,
        [string]$Notes
    )

    if ([string]::IsNullOrWhiteSpace($Alias)) { return }
    $key = "$EntityId|$Alias"
    if ($aliasSeen.ContainsKey($key)) { return }
    $aliasSeen[$key] = $true

    $integratedAliases.Add([PSCustomObject]@{
        entity_id = $EntityId
        alias = $Alias
        alias_type = $AliasType
        source_kind = $SourceKind
        notes = $Notes
    }) | Out-Null

    $aliasNorm = Normalize-Name $Alias
    if (-not [string]::IsNullOrWhiteSpace($aliasNorm)) {
        $aliasNormToEntityId[$aliasNorm] = $EntityId
    }
}

function Add-Relation {
    param(
        [string]$SourceId,
        [string]$TargetId,
        [string]$RelationType,
        [string]$SourceKind,
        [string]$Confidence,
        [string]$Notes
    )

    if ([string]::IsNullOrWhiteSpace($SourceId) -or [string]::IsNullOrWhiteSpace($TargetId)) { return }
    $key = "$SourceId|$TargetId|$RelationType|$SourceKind"
    if ($relationSeen.ContainsKey($key)) { return }
    $relationSeen[$key] = $true

    $integratedRelations.Add([PSCustomObject]@{
        source_entity_id = $SourceId
        target_entity_id = $TargetId
        relation_type = $RelationType
        source_kind = $SourceKind
        confidence = $Confidence
        notes = $Notes
    }) | Out-Null
}

function Resolve-Entity {
    param([string]$Name)
    $norm = Normalize-Name $Name
    if ([string]::IsNullOrWhiteSpace($norm)) { return $null }
    if ($byNorm.ContainsKey($norm)) { return $byNorm[$norm] }
    if ($aliasNormToEntityId.ContainsKey($norm) -and $byId.ContainsKey($aliasNormToEntityId[$norm])) {
        return $byId[$aliasNormToEntityId[$norm]]
    }
    return $null
}

function Resolve-MergedEntityId {
    param([string]$EntityId)

    $current = [string]$EntityId
    $guard = 0
    while ($mergeEntityIdMap.ContainsKey($current) -and $guard -lt 20) {
        $current = [string]$mergeEntityIdMap[$current]
        $guard++
    }
    return $current
}

foreach ($entity in $canonicalEntities) {
    $safeId = Get-SafeEntityId -EntityId ([string]$entity.entity_id) -Slug ([string]$entity.slug) -CanonicalName ([string]$entity.canonical_name)

    $row = [PSCustomObject]@{
        entity_id = $safeId
        canonical_name = $entity.canonical_name
        slug = $entity.slug
        integrated_type = (Map-Type $entity.entity_type)
        canonical_type = $entity.entity_type
        source_presence = $entity.source_presence
        quality_flags = $entity.quality_flags
        confidence_score = $entity.confidence_score
        integrated_sources = 'canonical'
    }

    $integratedEntities.Add($row) | Out-Null
    $byId[$row.entity_id] = $row
    $byNorm[(Normalize-Name $row.canonical_name)] = $row
    $canonicalIdMap[[string]$entity.entity_id] = $row.entity_id

    Add-Provenance -EntityId $row.entity_id -CanonicalName $row.canonical_name -SourceFile 'canonical_entities.csv' -SourceKind 'canonical' -ExtractionMethod 'canonical_base' -Notes $entity.source_presence
}

foreach ($alias in $canonicalAliases) {
    $mappedAliasEntityId = if ($canonicalIdMap.ContainsKey([string]$alias.entity_id)) { $canonicalIdMap[[string]$alias.entity_id] } else { [string]$alias.entity_id }
    Add-Alias -EntityId $mappedAliasEntityId -Alias $alias.alias -AliasType $alias.alias_type -SourceKind 'canonical' -Notes $alias.merge_reason
}

foreach ($review in $canonicalReviewQueue) {
    $confidence = 0.0
    [void][double]::TryParse([string]$review.merge_confidence, [ref]$confidence)
    $mappedReviewEntityId = if ($canonicalIdMap.ContainsKey([string]$review.canonical_entity_id)) { $canonicalIdMap[[string]$review.canonical_entity_id] } else { [string]$review.canonical_entity_id }
    if ($confidence -ge 0.94 -and $byId.ContainsKey($mappedReviewEntityId)) {
        Add-Alias -EntityId $mappedReviewEntityId -Alias $review.alias_name -AliasType 'auto_promoted_review_alias' -SourceKind 'canonical_review' -Notes $review.notes
    } else {
        $reviewQueue.Add([PSCustomObject]@{
            review_type = $review.review_type
            candidate_name = $review.alias_name
            candidate_type = 'alias_merge'
            notes = $review.notes
        }) | Out-Null
    }
}

foreach ($candidate in $historicalHigh) {
    $name = Repair-Mojibake ([string]$candidate.canonical_name_candidate)
    if (-not (Is-UsableHistoricalCandidate -Name $name -EntityType $candidate.entity_type_candidate -SourceCount ([int]$candidate.source_count))) { continue }
    $resolved = Resolve-Entity -Name $name
    $mappedType = Map-Type $candidate.entity_type_candidate

    if ($null -ne $resolved) {
        if ($resolved.canonical_name -ne $name) {
            Add-Alias -EntityId $resolved.entity_id -Alias $name -AliasType 'historical_match' -SourceKind 'historical' -Notes $candidate.sources
        }
        $resolved.integrated_sources = (@($resolved.integrated_sources -split '\|' | Where-Object { $_ }) + 'historical' | Select-Object -Unique) -join '|'
        Add-Provenance -EntityId $resolved.entity_id -CanonicalName $resolved.canonical_name -SourceFile $candidate.sources -SourceKind 'historical' -ExtractionMethod $candidate.extraction_methods -Notes $candidate.notes
    } else {
        $newId = New-Slug $name
        if ([string]::IsNullOrWhiteSpace($newId)) { continue }
        if ($byId.ContainsKey($newId)) {
            $reviewQueue.Add([PSCustomObject]@{
                review_type = 'id_collision'
                candidate_name = $name
                candidate_type = $mappedType
                notes = $candidate.sources
            }) | Out-Null
            continue
        }

        $row = [PSCustomObject]@{
            entity_id = $newId
            canonical_name = $name
            slug = $newId
            integrated_type = $mappedType
            canonical_type = $candidate.entity_type_candidate
            source_presence = 'historical'
            quality_flags = if ([string]$candidate.was_repaired -eq 'True') { 'name_repaired' } else { '' }
            confidence_score = if ([int]$candidate.source_count -ge 3) { 0.85 } elseif ([int]$candidate.source_count -eq 2) { 0.75 } else { 0.65 }
            integrated_sources = 'historical'
        }
        $integratedEntities.Add($row) | Out-Null
        $byId[$row.entity_id] = $row
        $byNorm[(Normalize-Name $row.canonical_name)] = $row

        Add-Provenance -EntityId $row.entity_id -CanonicalName $row.canonical_name -SourceFile $candidate.sources -SourceKind 'historical' -ExtractionMethod $candidate.extraction_methods -Notes $candidate.notes
    }
}

foreach ($candidate in ($historicalClean | Where-Object { $_.entity_type_candidate -in @('institution_candidate','capital_candidate') })) {
    $name = Repair-Mojibake ([string]$candidate.canonical_name_candidate)
    if (-not (Is-UsableHistoricalCandidate -Name $name -EntityType $candidate.entity_type_candidate -SourceCount ([int]$candidate.source_count))) { continue }
    $resolved = Resolve-Entity -Name $name
    $mappedType = Map-Type $candidate.entity_type_candidate

    if ($null -ne $resolved) {
        if ($resolved.canonical_name -ne $name) {
            Add-Alias -EntityId $resolved.entity_id -Alias $name -AliasType 'historical_clean_match' -SourceKind 'historical_clean' -Notes $candidate.sources
        }
        $resolved.integrated_sources = (@($resolved.integrated_sources -split '\|' | Where-Object { $_ }) + 'historical_clean' | Select-Object -Unique) -join '|'
        if ($mappedType -eq 'institution' -and $resolved.integrated_type -eq 'capital') {
            $resolved.quality_flags = (@($resolved.quality_flags -split '\|' | Where-Object { $_ }) + 'multi_role_capital_institution' | Select-Object -Unique) -join '|'
        }
        Add-Provenance -EntityId $resolved.entity_id -CanonicalName $resolved.canonical_name -SourceFile $candidate.sources -SourceKind 'historical_clean' -ExtractionMethod $candidate.extraction_methods -Notes $candidate.notes
        continue
    }

    $newId = New-Slug $name
    if ([string]::IsNullOrWhiteSpace($newId) -or $byId.ContainsKey($newId)) { continue }

    $row = [PSCustomObject]@{
        entity_id = $newId
        canonical_name = $name
        slug = $newId
        integrated_type = $mappedType
        canonical_type = $candidate.entity_type_candidate
        source_presence = 'historical_clean'
        quality_flags = 'low_source_count'
        confidence_score = if ([int]$candidate.source_count -ge 2) { 0.7 } else { 0.55 }
        integrated_sources = 'historical_clean'
    }
    $integratedEntities.Add($row) | Out-Null
    $byId[$row.entity_id] = $row
    $byNorm[(Normalize-Name $row.canonical_name)] = $row

    Add-Provenance -EntityId $row.entity_id -CanonicalName $row.canonical_name -SourceFile $candidate.sources -SourceKind 'historical_clean' -ExtractionMethod $candidate.extraction_methods -Notes $candidate.notes
}

foreach ($candidate in $institutionCandidates) {
    $name = Repair-Mojibake ([string]$candidate.label)
    $resolved = Resolve-Entity -Name $name

    if ($null -ne $resolved) {
        if ($resolved.canonical_name -ne $name) {
            Add-Alias -EntityId $resolved.entity_id -Alias $name -AliasType 'institution_seed_match' -SourceKind 'institution_candidates' -Notes $candidate.source_basis
        }
        if ($resolved.integrated_type -eq 'capital' -and $candidate.entity_type -eq 'accelerator') {
            $resolved.quality_flags = (@($resolved.quality_flags -split '\|' | Where-Object { $_ }) + 'multi_role_capital_accelerator' | Select-Object -Unique) -join '|'
        }
        $resolved.integrated_sources = (@($resolved.integrated_sources -split '\|' | Where-Object { $_ }) + 'institution_candidates' | Select-Object -Unique) -join '|'
        Add-Provenance -EntityId $resolved.entity_id -CanonicalName $resolved.canonical_name -SourceFile 'ecosystem_institution_candidates.csv' -SourceKind 'institution_candidates' -ExtractionMethod $candidate.source_basis -Notes $candidate.notes
        continue
    }

    $newId = if ([string]::IsNullOrWhiteSpace($candidate.entity_id)) { New-Slug $name } else { [string]$candidate.entity_id }
    if ([string]::IsNullOrWhiteSpace($newId) -or $byId.ContainsKey($newId)) { continue }

    $row = [PSCustomObject]@{
        entity_id = $newId
        canonical_name = $name
        slug = New-Slug $name
        integrated_type = 'institution'
        canonical_type = $candidate.entity_type
        source_presence = 'institution_candidates'
        quality_flags = ''
        confidence_score = 0.72
        integrated_sources = 'institution_candidates'
    }
    $integratedEntities.Add($row) | Out-Null
    $byId[$row.entity_id] = $row
    $byNorm[(Normalize-Name $row.canonical_name)] = $row

    Add-Provenance -EntityId $row.entity_id -CanonicalName $row.canonical_name -SourceFile 'ecosystem_institution_candidates.csv' -SourceKind 'institution_candidates' -ExtractionMethod $candidate.source_basis -Notes $candidate.notes
}

foreach ($override in $manualAliasOverrides) {
    $resolvedCanonical = Resolve-Entity -Name $override.canonical_name
    $resolvedAlias = Resolve-Entity -Name $override.alias_name

    if ($null -eq $resolvedCanonical) {
        $reviewQueue.Add([PSCustomObject]@{
            review_type = 'missing_manual_alias_canonical'
            candidate_name = $override.canonical_name
            candidate_type = 'manual_alias'
            notes = $override.alias_name
        }) | Out-Null
        continue
    }

    Add-Alias -EntityId $resolvedCanonical.entity_id -Alias $override.alias_name -AliasType 'manual_override' -SourceKind 'manual_alias_overrides' -Notes ($override.reason + '|' + $override.confidence)

    if ($null -ne $resolvedCanonical -and $null -ne $resolvedAlias -and $resolvedCanonical.entity_id -ne $resolvedAlias.entity_id) {
        $mergeEntityIdMap[$resolvedAlias.entity_id] = $resolvedCanonical.entity_id
        Add-Alias -EntityId $resolvedCanonical.entity_id -Alias $resolvedAlias.canonical_name -AliasType 'merged_entity_name' -SourceKind 'manual_alias_overrides' -Notes ($override.reason + '|entity_merge')
    }
}

foreach ($edge in $canonicalEdges) {
    $mappedInvestorId = if ($canonicalIdMap.ContainsKey([string]$edge.investor_id)) { $canonicalIdMap[[string]$edge.investor_id] } else { [string]$edge.investor_id }
    $mappedStartupId = if ($canonicalIdMap.ContainsKey([string]$edge.startup_id)) { $canonicalIdMap[[string]$edge.startup_id] } else { [string]$edge.startup_id }
    Add-Relation -SourceId $mappedInvestorId -TargetId $mappedStartupId -RelationType 'funded_by' -SourceKind 'canonical_investment' -Confidence $edge.confidence_score -Notes $edge.source_file
}

foreach ($seed in $relationSeeds) {
    $sourceEntity = Resolve-Entity -Name $seed.source_name
    $targetEntity = Resolve-Entity -Name $seed.target_name

    if ($null -eq $sourceEntity -or $null -eq $targetEntity) {
        $reviewQueue.Add([PSCustomObject]@{
            review_type = 'missing_seed_endpoint'
            candidate_name = "$($seed.source_name) -> $($seed.target_name)"
            candidate_type = $seed.relation_type
            notes = $seed.source_basis
        }) | Out-Null
        continue
    }

    Add-Relation -SourceId $sourceEntity.entity_id -TargetId $targetEntity.entity_id -RelationType $seed.relation_type -SourceKind 'ecosystem_seed' -Confidence $seed.confidence -Notes ($seed.source_basis + '|' + $seed.notes)
}

$remappedAliases = New-Object System.Collections.Generic.List[object]
$remappedAliasSeen = @{}
foreach ($alias in $integratedAliases) {
    $targetEntityId = Resolve-MergedEntityId $alias.entity_id
    $key = "$targetEntityId|$($alias.alias)"
    if ($remappedAliasSeen.ContainsKey($key)) { continue }
    $remappedAliasSeen[$key] = $true
    $remappedAliases.Add([PSCustomObject]@{
        entity_id = $targetEntityId
        alias = $alias.alias
        alias_type = $alias.alias_type
        source_kind = $alias.source_kind
        notes = $alias.notes
    }) | Out-Null
}
$integratedAliases = $remappedAliases

$remappedProvenance = New-Object System.Collections.Generic.List[object]
$remappedProvSeen = @{}
foreach ($prov in $integratedProvenance) {
    $targetEntityId = Resolve-MergedEntityId $prov.entity_id
    $key = "$targetEntityId|$($prov.source_file)|$($prov.source_kind)|$($prov.extraction_method)|$($prov.notes)"
    if ($remappedProvSeen.ContainsKey($key)) { continue }
    $remappedProvSeen[$key] = $true

    $canonicalName = $prov.canonical_name
    if ($byId.ContainsKey($targetEntityId)) {
        $canonicalName = $byId[$targetEntityId].canonical_name
    }

    $remappedProvenance.Add([PSCustomObject]@{
        entity_id = $targetEntityId
        canonical_name = $canonicalName
        source_file = $prov.source_file
        source_kind = $prov.source_kind
        extraction_method = $prov.extraction_method
        notes = $prov.notes
    }) | Out-Null
}
$integratedProvenance = $remappedProvenance

$remappedRelations = New-Object System.Collections.Generic.List[object]
$remappedRelSeen = @{}
foreach ($rel in $integratedRelations) {
    $sourceId = Resolve-MergedEntityId $rel.source_entity_id
    $targetId = Resolve-MergedEntityId $rel.target_entity_id
    $key = "$sourceId|$targetId|$($rel.relation_type)|$($rel.source_kind)"
    if ($remappedRelSeen.ContainsKey($key)) { continue }
    $remappedRelSeen[$key] = $true
    $remappedRelations.Add([PSCustomObject]@{
        source_entity_id = $sourceId
        target_entity_id = $targetId
        relation_type = $rel.relation_type
        source_kind = $rel.source_kind
        confidence = $rel.confidence
        notes = $rel.notes
    }) | Out-Null
}
$integratedRelations = $remappedRelations

$mergedAway = @($mergeEntityIdMap.Keys)
$integratedEntities = @($integratedEntities | Where-Object { $mergedAway -notcontains $_.entity_id })

$entityById = @{}
foreach ($entity in ($integratedEntities | Sort-Object {[double]$_.confidence_score} -Descending)) {
    if ($entityById.ContainsKey($entity.entity_id)) {
        $winner = $entityById[$entity.entity_id]
        if ($winner.canonical_name -ne $entity.canonical_name) {
            Add-Alias -EntityId $winner.entity_id -Alias $entity.canonical_name -AliasType 'duplicate_entity_id_name' -SourceKind 'integration_cleanup' -Notes 'same_entity_id_multiple_names'
        }
        continue
    }
    $entityById[$entity.entity_id] = $entity
}
$integratedEntities = @($entityById.Values)

$autoGroups = $integratedEntities |
    Group-Object { (Normalize-Name $_.canonical_name) + '|' + $_.integrated_type } |
    Where-Object { $_.Count -gt 1 }

$autoMergeMap = @{}
foreach ($group in $autoGroups) {
    $winner = $group.Group |
        Sort-Object @{Expression={[double]$_.confidence_score};Descending=$true}, @{Expression={$_.integrated_sources.Length};Descending=$true}, @{Expression={$_.canonical_name.Length};Descending=$true} |
        Select-Object -First 1

    foreach ($loser in ($group.Group | Where-Object { $_.entity_id -ne $winner.entity_id })) {
        $autoMergeMap[$loser.entity_id] = $winner.entity_id
        Add-Alias -EntityId $winner.entity_id -Alias $loser.canonical_name -AliasType 'auto_norm_merge' -SourceKind 'integration_cleanup' -Notes 'same_normalized_name'
    }
}

function Resolve-AllEntityId {
    param([string]$EntityId)
    $current = Resolve-MergedEntityId $EntityId
    $guard = 0
    while ($autoMergeMap.ContainsKey($current) -and $guard -lt 20) {
        $current = [string]$autoMergeMap[$current]
        $guard++
    }
    return $current
}

$remappedAliases2 = New-Object System.Collections.Generic.List[object]
$seenAliases2 = @{}
foreach ($alias in $integratedAliases) {
    $targetEntityId = Resolve-AllEntityId $alias.entity_id
    $key = "$targetEntityId|$($alias.alias)"
    if ($seenAliases2.ContainsKey($key)) { continue }
    $seenAliases2[$key] = $true
    $remappedAliases2.Add([PSCustomObject]@{
        entity_id = $targetEntityId
        alias = $alias.alias
        alias_type = $alias.alias_type
        source_kind = $alias.source_kind
        notes = $alias.notes
    }) | Out-Null
}
$integratedAliases = $remappedAliases2

$remappedProv2 = New-Object System.Collections.Generic.List[object]
$seenProv2 = @{}
foreach ($prov in $integratedProvenance) {
    $targetEntityId = Resolve-AllEntityId $prov.entity_id
    $key = "$targetEntityId|$($prov.source_file)|$($prov.source_kind)|$($prov.extraction_method)|$($prov.notes)"
    if ($seenProv2.ContainsKey($key)) { continue }
    $seenProv2[$key] = $true
    $canonicalName = $prov.canonical_name
    $winnerEntity = $integratedEntities | Where-Object { $_.entity_id -eq $targetEntityId } | Select-Object -First 1
    if ($null -ne $winnerEntity) { $canonicalName = $winnerEntity.canonical_name }
    $remappedProv2.Add([PSCustomObject]@{
        entity_id = $targetEntityId
        canonical_name = $canonicalName
        source_file = $prov.source_file
        source_kind = $prov.source_kind
        extraction_method = $prov.extraction_method
        notes = $prov.notes
    }) | Out-Null
}
$integratedProvenance = $remappedProv2

$remappedRelations2 = New-Object System.Collections.Generic.List[object]
$seenRels2 = @{}
foreach ($rel in $integratedRelations) {
    $sourceId = Resolve-AllEntityId $rel.source_entity_id
    $targetId = Resolve-AllEntityId $rel.target_entity_id
    $key = "$sourceId|$targetId|$($rel.relation_type)|$($rel.source_kind)"
    if ($seenRels2.ContainsKey($key)) { continue }
    $seenRels2[$key] = $true
    $remappedRelations2.Add([PSCustomObject]@{
        source_entity_id = $sourceId
        target_entity_id = $targetId
        relation_type = $rel.relation_type
        source_kind = $rel.source_kind
        confidence = $rel.confidence
        notes = $rel.notes
    }) | Out-Null
}
$integratedRelations = $remappedRelations2

$autoMergedAway = @($autoMergeMap.Keys)
$integratedEntities = @($integratedEntities | Where-Object { $autoMergedAway -notcontains $_.entity_id })

$canonicalFundedPairs = @{}
foreach ($rel in $integratedRelations | Where-Object { $_.relation_type -eq 'funded_by' -and $_.source_kind -eq 'canonical_investment' }) {
    $canonicalFundedPairs["$($rel.source_entity_id)|$($rel.target_entity_id)"] = $true
}

$integratedRelations = @(
    foreach ($rel in $integratedRelations) {
        if ($rel.relation_type -eq 'funded_by' -and $rel.source_kind -eq 'ecosystem_seed') {
            $pair = "$($rel.source_entity_id)|$($rel.target_entity_id)"
            if ($canonicalFundedPairs.ContainsKey($pair)) { continue }
        }
        $rel
    }
)

$integratedEntities |
    Sort-Object integrated_type, canonical_name |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'integrated_entities.csv') -NoTypeInformation -Encoding UTF8

$integratedAliases |
    Sort-Object entity_id, alias |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'integrated_aliases.csv') -NoTypeInformation -Encoding UTF8

$integratedProvenance |
    Sort-Object entity_id, source_kind, source_file |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'integrated_provenance.csv') -NoTypeInformation -Encoding UTF8

$integratedRelations |
    Sort-Object relation_type, source_entity_id, target_entity_id |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'integrated_relations.csv') -NoTypeInformation -Encoding UTF8

$reviewQueue |
    Sort-Object review_type, candidate_name |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'integrated_review_queue.csv') -NoTypeInformation -Encoding UTF8

@(
    [PSCustomObject]@{ metric='integrated_entities'; value=[int]$integratedEntities.Count }
    [PSCustomObject]@{ metric='integrated_aliases'; value=[int]$integratedAliases.Count }
    [PSCustomObject]@{ metric='integrated_provenance'; value=[int]$integratedProvenance.Count }
    [PSCustomObject]@{ metric='integrated_relations'; value=[int]$integratedRelations.Count }
    [PSCustomObject]@{ metric='integrated_review_queue'; value=[int]$reviewQueue.Count }
    [PSCustomObject]@{ metric='historical_clean_entities_used'; value=[int]@($historicalClean).Count }
    [PSCustomObject]@{ metric='historical_high_entities_used'; value=[int]@($historicalHigh).Count }
) | Export-Csv -LiteralPath (Join-Path $OutputDir 'integrated_summary.csv') -NoTypeInformation -Encoding UTF8

Write-Output "Integration complete: $OutputDir"
