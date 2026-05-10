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

function Upsert-Entity {
    param(
        [object[]]$Rows,
        [string]$EntityId,
        [string]$EntityType,
        [string]$CanonicalName,
        [string]$Slug,
        [string]$SourcePresence,
        [string]$QualityFlags,
        [string]$ConfidenceScore
    )

    foreach ($row in $Rows) {
        if ((Clean-Text $row.entity_id) -ne $EntityId) { continue }
        $row.entity_type = $EntityType
        $row.canonical_name = $CanonicalName
        $row.slug = $Slug
        $row.source_presence = $SourcePresence
        $row.quality_flags = $QualityFlags
        $row.confidence_score = $ConfidenceScore
        $row.staging_entity_id = $EntityId
        return $Rows
    }

    return @($Rows) + [pscustomobject]@{
        entity_id = $EntityId
        entity_type = $EntityType
        canonical_name = $CanonicalName
        slug = $Slug
        source_presence = $SourcePresence
        quality_flags = $QualityFlags
        confidence_score = $ConfidenceScore
        staging_entity_id = $EntityId
    }
}

function Upsert-AllocatorEdge {
    param(
        [object[]]$Rows,
        [string]$AllocatorId,
        [string]$AllocatorName,
        [string]$AllocatorType,
        [string]$TargetFundId,
        [string]$TargetFundName,
        [string]$TargetVehicle,
        [string]$RelationType,
        [string]$AmountUsd,
        [string]$Year,
        [string]$SectorLens,
        [string]$RegionLens,
        [string]$SourceUrl,
        [string]$EvidenceNote,
        [string]$Confidence
    )

    foreach ($row in $Rows) {
        if ((Clean-Text $row.allocator_id) -ne $AllocatorId) { continue }
        if ((Clean-Text $row.target_fund_id) -ne $TargetFundId) { continue }
        if ((Clean-Text $row.target_vehicle) -ne $TargetVehicle) { continue }
        $row.allocator_name = $AllocatorName
        $row.allocator_type = $AllocatorType
        $row.target_fund_name = $TargetFundName
        $row.relation_type = $RelationType
        $row.amount_usd = $AmountUsd
        $row.year = $Year
        $row.sector_lens = $SectorLens
        $row.region_lens = $RegionLens
        $row.source_url = $SourceUrl
        $row.evidence_note = $EvidenceNote
        $row.confidence = $Confidence
        return $Rows
    }

    return @($Rows) + [pscustomobject]@{
        allocator_id = $AllocatorId
        allocator_name = $AllocatorName
        allocator_type = $AllocatorType
        target_fund_id = $TargetFundId
        target_fund_name = $TargetFundName
        target_vehicle = $TargetVehicle
        relation_type = $RelationType
        amount_usd = $AmountUsd
        year = $Year
        sector_lens = $SectorLens
        region_lens = $RegionLens
        source_url = $SourceUrl
        evidence_note = $EvidenceNote
        confidence = $Confidence
    }
}

$entitiesPath = Join-Path $Root 'canonical\canonical_entities.csv'
$manualEntitiesPath = Join-Path $Root 'canonical\manual_canonical_entities.csv'
$allocatorPath = Join-Path $Root 'quality\capital_allocator_edges.csv'

$entities = @(Import-Csv -LiteralPath $entitiesPath)
$manualEntities = @(Import-Csv -LiteralPath $manualEntitiesPath)
$allocatorEdges = @(Import-Csv -LiteralPath $allocatorPath)

$entities = Upsert-Entity -Rows $entities -EntityId 'idb_invest' -EntityType 'investor' -CanonicalName 'IDB Invest' -Slug 'idb-invest' -SourcePresence 'manual_institutional_capital' -QualityFlags 'capital_allocator;development_finance_lp' -ConfidenceScore '0.96'
$manualEntities = Upsert-Entity -Rows $manualEntities -EntityId 'idb_invest' -EntityType 'investor' -CanonicalName 'IDB Invest' -Slug 'idb-invest' -SourcePresence 'manual_institutional_capital' -QualityFlags 'capital_allocator;development_finance_lp' -ConfidenceScore '0.96'

$allocatorEdges = Upsert-AllocatorEdge -Rows $allocatorEdges `
    -AllocatorId 'idb_invest' `
    -AllocatorName 'IDB Invest' `
    -AllocatorType 'development_finance_lp' `
    -TargetFundId 'sp_ventures' `
    -TargetFundName 'SP Ventures' `
    -TargetVehicle 'AgVentures III Fund' `
    -RelationType 'lp_or_institutional_support_to_vc_fund' `
    -AmountUsd '' `
    -Year '2026' `
    -SectorLens 'agtech; foodtech; climate-resilient agriculture; biotechnology' `
    -RegionLens 'Latin America and Caribbean' `
    -SourceUrl 'https://spventures.com.br/wp-content/uploads/2026/04/ESG-Impact-Report-2025-SP-Ventures-EN_Oficial.pdf' `
    -EvidenceNote 'SP Ventures 2025 ESG & Impact Report describes Fund III as receiving continued support from institutions like IDB Invest, plus mission-aligned investors such as SEDF and JICA; modeled as institutional capital/support to AgVentures III rather than a direct startup investment.' `
    -Confidence '0.90'

$entities | Sort-Object entity_id | Export-Csv -LiteralPath $entitiesPath -NoTypeInformation -Encoding UTF8
$manualEntities | Sort-Object entity_id | Export-Csv -LiteralPath $manualEntitiesPath -NoTypeInformation -Encoding UTF8
$allocatorEdges | Export-Csv -LiteralPath $allocatorPath -NoTypeInformation -Encoding UTF8

Write-Output 'IDB Invest capital layer upgraded.'
Write-Output 'Added IDB Invest -> SP Ventures / AgVentures III institutional capital bridge.'
