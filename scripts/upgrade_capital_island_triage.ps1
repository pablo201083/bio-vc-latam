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

function Add-Flag {
    param([string]$Existing, [string]$Flag)
    $parts = @((Clean-Text $Existing) -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($parts -notcontains $Flag) { $parts += $Flag }
    return ($parts -join ';')
}

$entitiesPath = Join-Path $Root 'canonical\canonical_entities.csv'
$manualEntitiesPath = Join-Path $Root 'canonical\manual_canonical_entities.csv'
$allocatorPath = Join-Path $Root 'quality\capital_allocator_edges.csv'

$entities = @(Import-Csv -LiteralPath $entitiesPath)
$manualEntities = @(Import-Csv -LiteralPath $manualEntitiesPath)
$allocatorEdges = @(Import-Csv -LiteralPath $allocatorPath)

foreach ($table in @($entities, $manualEntities)) {
    foreach ($entity in $table) {
        if ((Clean-Text $entity.entity_id) -eq '1200_vc') {
            $entity.quality_flags = Add-Flag -Existing $entity.quality_flags -Flag 'capital_core_hidden_exclude_only'
        }
        if ((Clean-Text $entity.entity_id) -eq 'kptl') {
            $entity.quality_flags = Add-Flag -Existing $entity.quality_flags -Flag 'bioeconomy_fund'
        }
        if ((Clean-Text $entity.entity_id) -eq 'aceleradora_litoral') {
            $entity.quality_flags = Add-Flag -Existing $entity.quality_flags -Flag 'capital_island_keep_priority_bio'
        }
        if ((Clean-Text $entity.entity_id) -in @('newtopia_vc', 'chileglobal_ventures')) {
            $entity.quality_flags = Add-Flag -Existing $entity.quality_flags -Flag 'capital_core_sidecar_broad_low_priority'
        }
    }
}

$kptlSource = 'https://kptl.com.br/active-listening-ancestral-wisdom-and-the-voices-of-the-forest/?lang=en'
$allocatorEdges = Upsert-AllocatorEdge -Rows $allocatorEdges `
    -AllocatorId 'idb_lab' `
    -AllocatorName 'IDB Lab' `
    -AllocatorType 'development_venture_capital_lp' `
    -TargetFundId 'kptl' `
    -TargetFundName 'KPTL' `
    -TargetVehicle 'Amazonia Regenerate Accelerator and Investment Fund' `
    -RelationType 'bioeconomy_fund_support' `
    -AmountUsd '' `
    -Year '2024' `
    -SectorLens 'Amazon bioeconomy; biodiversity; climate; regenerative economy; sustainable agriculture' `
    -RegionLens 'Amazon basin; Latin America' `
    -SourceUrl $kptlSource `
    -EvidenceNote 'KPTL describes an Amazonia Regenerate accelerator and investment fund supported by IDB Lab and focused on startups linked to the Amazon bioeconomy and climate/biodiversity outcomes.' `
    -Confidence '0.90'

$entities | Export-Csv -LiteralPath $entitiesPath -NoTypeInformation -Encoding UTF8
$manualEntities | Export-Csv -LiteralPath $manualEntitiesPath -NoTypeInformation -Encoding UTF8
$allocatorEdges | Export-Csv -LiteralPath $allocatorPath -NoTypeInformation -Encoding UTF8

Write-Output 'Capital island triage applied.'
Write-Output 'Connected KPTL through IDB Lab; flagged 1200 VC as hidden; flagged Aceleradora Litoral as keep-priority island; flagged Newtopia VC and ChileGlobal Ventures as broad sidecars.'
