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

    $found = $false
    foreach ($row in $Rows) {
        if ((Clean-Text $row.entity_id) -ne $EntityId) { continue }
        $row.entity_type = $EntityType
        $row.canonical_name = $CanonicalName
        $row.slug = $Slug
        $row.source_presence = $SourcePresence
        $row.quality_flags = $QualityFlags
        $row.confidence_score = $ConfidenceScore
        $row.staging_entity_id = $EntityId
        $found = $true
        break
    }
    if ($found) { return $Rows }

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

    $found = $false
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
        $found = $true
        break
    }
    if ($found) { return $Rows }

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

$canonicalPath = Join-Path $Root 'canonical\canonical_entities.csv'
$manualPath = Join-Path $Root 'canonical\manual_canonical_entities.csv'
$allocatorPath = Join-Path $Root 'quality\capital_allocator_edges.csv'

$canonicalEntities = @(Import-Csv -LiteralPath $canonicalPath)
$manualEntities = @(Import-Csv -LiteralPath $manualPath)
$allocatorEdges = @(Import-Csv -LiteralPath $allocatorPath)

$institutionalEntities = @(
    [pscustomobject]@{ Id = 'idb_natural_capital_lab'; Name = 'IDB Natural Capital Lab'; Slug = 'idb-natural-capital-lab'; Presence = 'manual_institutional_capital'; Flags = 'capital_allocator'; Confidence = '0.90' },
    [pscustomobject]@{ Id = 'gef'; Name = 'Global Environment Facility'; Slug = 'global-environment-facility'; Presence = 'manual_institutional_capital'; Flags = 'capital_allocator'; Confidence = '0.92' },
    [pscustomobject]@{ Id = 'kaete_investimentos'; Name = 'Kaete Investimentos'; Slug = 'kaete-investimentos'; Presence = 'manual_institutional_capital'; Flags = ''; Confidence = '0.88' }
)

foreach ($entity in $institutionalEntities) {
    $canonicalEntities = Upsert-Entity -Rows $canonicalEntities -EntityId $entity.Id -EntityType 'investor' -CanonicalName $entity.Name -Slug $entity.Slug -SourcePresence $entity.Presence -QualityFlags $entity.Flags -ConfidenceScore $entity.Confidence
    $manualEntities = Upsert-Entity -Rows $manualEntities -EntityId $entity.Id -EntityType 'investor' -CanonicalName $entity.Name -Slug $entity.Slug -SourcePresence $entity.Presence -QualityFlags $entity.Flags -ConfidenceScore $entity.Confidence
}

$bidlabGridxSource = 'https://bidlab.org/es/noticias/bid-lab-aprueba-inversion-para-impulsar-emprendimientos-deeptech-en-america-latina'
$yieldLabSource = 'https://theyieldlablatam.com/2024/09/30/the-yield-lab-latam-announces-advancement-of-its-third-agrifoodtech-fund-with-new-investment-from-the-global-environment-facility/'
$regenerateSource = 'https://www.iadb.org/en/project/RG-Q0093'

$allocatorEdges = @(
    $allocatorEdges | Where-Object {
        -not (
            ((Clean-Text $_.allocator_id) -in @('idb_lab', 'idb_natural_capital_lab')) -and
            ((Clean-Text $_.target_fund_id) -eq 'kptl') -and
            ((Clean-Text $_.target_vehicle) -eq 'Amazonia Regenerate Accelerator and Investment Fund')
        )
    }
)

$allocatorEdges = Upsert-AllocatorEdge -Rows $allocatorEdges `
    -AllocatorId 'idb_lab' `
    -AllocatorName 'IDB Lab' `
    -AllocatorType 'development_venture_capital_lp' `
    -TargetFundId 'GridX' `
    -TargetFundName 'GridX' `
    -TargetVehicle 'GridX II' `
    -RelationType 'lp_commitment_to_vc_fund' `
    -AmountUsd '3000000' `
    -Year '2022' `
    -SectorLens 'deeptech; biotechnology; climate; health; science-based ventures; bio-revolution' `
    -RegionLens 'Latin America and Caribbean' `
    -SourceUrl $bidlabGridxSource `
    -EvidenceNote 'BID Lab approved a $3M investment in GridX II to promote science-based deeptech ventures with a special focus on biotechnology, climate and health across Latin America.' `
    -Confidence '0.97'

$allocatorEdges = Upsert-AllocatorEdge -Rows $allocatorEdges `
    -AllocatorId 'idb_lab' `
    -AllocatorName 'IDB Lab' `
    -AllocatorType 'development_venture_capital_lp' `
    -TargetFundId 'the_yield_lab_latam' `
    -TargetFundName 'The Yield Lab LATAM' `
    -TargetVehicle 'The Yield Lab Opportunity Fund' `
    -RelationType 'lp_commitment_to_vc_fund' `
    -AmountUsd '' `
    -Year '2023' `
    -SectorLens 'agrifoodtech; food systems; agriculture; climate-smart agriculture; sustainable food value chains' `
    -RegionLens 'Latin America and Caribbean' `
    -SourceUrl $yieldLabSource `
    -EvidenceNote 'The Yield Lab LATAM states that IDB Lab is an investor in its Opportunity Fund, a regional agrifoodtech VC fund targeting 30 Latin American food and agriculture technology companies.' `
    -Confidence '0.94'

$allocatorEdges = Upsert-AllocatorEdge -Rows $allocatorEdges `
    -AllocatorId 'gef' `
    -AllocatorName 'Global Environment Facility' `
    -AllocatorType 'multilateral_environmental_lp' `
    -TargetFundId 'the_yield_lab_latam' `
    -TargetFundName 'The Yield Lab LATAM' `
    -TargetVehicle 'The Yield Lab Opportunity Fund' `
    -RelationType 'lp_commitment_to_vc_fund' `
    -AmountUsd '6000000' `
    -Year '2024' `
    -SectorLens 'decarbonized food systems; sustainable agriculture; climate adaptation; restoration' `
    -RegionLens 'Latin America and Caribbean' `
    -SourceUrl $yieldLabSource `
    -EvidenceNote 'The Yield Lab LATAM announced a $6M GEF commitment through the Inter-American Development Bank for the Opportunity Fund, alongside IDB Lab and other institutional investors.' `
    -Confidence '0.94'

$allocatorEdges = Upsert-AllocatorEdge -Rows $allocatorEdges `
    -AllocatorId 'idb_lab' `
    -AllocatorName 'IDB Lab' `
    -AllocatorType 'development_venture_capital_lp' `
    -TargetFundId 'kaete_investimentos' `
    -TargetFundName 'Kaete Investimentos' `
    -TargetVehicle 'Amazonia ReGenerate Accelerator and Investment Trust' `
    -RelationType 'anchor_support_to_bioeconomy_fund' `
    -AmountUsd '2000000' `
    -Year '2021' `
    -SectorLens 'Amazon bioeconomy; biodiversity; circular economy; climate; forest restoration; sustainable agriculture' `
    -RegionLens 'Amazon basin; Brazil; Ecuador; Bolivia; Peru; Colombia; Guyana; Suriname' `
    -SourceUrl $regenerateSource `
    -EvidenceNote 'The official IDB project page says IDB Lab approved $2M for the Amazonia ReGenerate Accelerator and Investment Trust, partnering with Kaete Investimentos to support regenerative-economy ventures in the Amazon basin.' `
    -Confidence '0.96'

$allocatorEdges = Upsert-AllocatorEdge -Rows $allocatorEdges `
    -AllocatorId 'idb_natural_capital_lab' `
    -AllocatorName 'IDB Natural Capital Lab' `
    -AllocatorType 'development_nature_capital_platform' `
    -TargetFundId 'kaete_investimentos' `
    -TargetFundName 'Kaete Investimentos' `
    -TargetVehicle 'Amazonia ReGenerate Accelerator and Investment Trust' `
    -RelationType 'strategic_capital_support_to_bioeconomy_fund' `
    -AmountUsd '' `
    -Year '2021' `
    -SectorLens 'natural capital; biodiversity; Amazon bioeconomy; climate; forest systems' `
    -RegionLens 'Amazon basin; Latin America' `
    -SourceUrl $regenerateSource `
    -EvidenceNote 'The official IDB project page identifies IDB Natural Capital Lab as partner in structuring and operating the Amazonia ReGenerate trust and accelerator with Kaete Investimentos.' `
    -Confidence '0.92'

$canonicalEntities | Sort-Object entity_id | Export-Csv -LiteralPath $canonicalPath -NoTypeInformation -Encoding UTF8
$manualEntities | Sort-Object entity_id | Export-Csv -LiteralPath $manualPath -NoTypeInformation -Encoding UTF8
$allocatorEdges | Export-Csv -LiteralPath $allocatorPath -NoTypeInformation -Encoding UTF8

Write-Output 'BID Lab / IDB institutional capital layer upgraded.'
Write-Output "Allocator edges total: $($allocatorEdges.Count)"
