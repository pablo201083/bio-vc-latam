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

function Add-Flag {
    param([string]$Existing, [string]$Flag)
    $parts = @((Clean-Text $Existing) -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($parts -notcontains $Flag) { $parts += $Flag }
    return ($parts -join ';')
}

function Remove-Flag {
    param([string]$Existing, [string]$Flag)
    $parts = @((Clean-Text $Existing) -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ -and $_ -ne $Flag })
    return ($parts -join ';')
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

function Upsert-InvestmentEdge {
    param(
        [object[]]$Rows,
        [string]$InvestmentId,
        [string]$InvestorId,
        [string]$StartupId,
        [string]$InvestorLabel = '1200 VC',
        [string]$StartupLabel = 'General Biological',
        [string]$RelationType,
        [string]$SourceFile,
        [string]$Notes,
        [string]$Confidence
    )

    foreach ($row in $Rows) {
        if (($row.PSObject.Properties.Name -contains 'investment_id') -and (Clean-Text $row.investment_id) -eq $InvestmentId) {
            $row.investor_id = $InvestorId
            $row.startup_id = $StartupId
            $row.relation_type_raw = $RelationType
            $row.direction_status = 'validated_investor_to_startup'
            $row.confidence_score = $Confidence
            $row.source_file = $SourceFile
            $row.notes = $Notes
            return $Rows
        }
        if (($row.PSObject.Properties.Name -contains 'raw_edge_id') -and (Clean-Text $row.raw_edge_id) -eq $InvestmentId) {
            $row.source_id = $InvestorLabel
            $row.target_id = $StartupLabel
            $row.source_file = $SourceFile
            $row.relation_type_raw = $RelationType
            $row.direction_status = 'validated_investor_to_startup'
            $row.investor_id_candidate = $InvestorId
            $row.startup_id_candidate = $StartupId
            $row.confidence_score = $Confidence
            $row.notes = $Notes
            return $Rows
        }
    }

    if ($Rows.Count -and ($Rows[0].PSObject.Properties.Name -contains 'raw_edge_id')) {
        return @($Rows) + [pscustomobject]@{
            raw_edge_id = $InvestmentId
            source_id = $InvestorLabel
            target_id = $StartupLabel
            source_file = $SourceFile
            relation_type_raw = $RelationType
            direction_status = 'validated_investor_to_startup'
            investor_id_candidate = $InvestorId
            startup_id_candidate = $StartupId
            confidence_score = $Confidence
            notes = $Notes
        }
    }

    return @($Rows) + [pscustomobject]@{
        investment_id = $InvestmentId
        investor_id = $InvestorId
        startup_id = $StartupId
        relation_type_raw = $RelationType
        direction_status = 'validated_investor_to_startup'
        confidence_score = $Confidence
        source_file = $SourceFile
        notes = $Notes
    }
}

$entitiesPath = Join-Path $Root 'canonical\canonical_entities.csv'
$manualEntitiesPath = Join-Path $Root 'canonical\manual_canonical_entities.csv'
$allocatorPath = Join-Path $Root 'quality\capital_allocator_edges.csv'
$canonicalEdgesPath = Join-Path $Root 'canonical\canonical_investment_edges.csv'
$manualEdgesPath = Join-Path $Root 'canonical\manual_canonical_investment_edges.csv'

$entities = @(Import-Csv -LiteralPath $entitiesPath)
$manualEntities = @(Import-Csv -LiteralPath $manualEntitiesPath)
$allocatorEdges = @(Import-Csv -LiteralPath $allocatorPath)
$canonicalEdges = @(Import-Csv -LiteralPath $canonicalEdgesPath)
$manualEdges = @(Import-Csv -LiteralPath $manualEdgesPath)

$sourceUrl = 'https://www.twelvehundred.vc/investments'

$funds = @(
    [pscustomobject]@{ Id = 'third_sphere'; Name = 'Third Sphere'; Slug = 'third-sphere'; Lens = 'climate tech; urban tech; hardware; systems climate'; Note = '1200 VC official investments page lists Third Sphere, described as supporting rapid and scalable ClimateTech startups.' },
    [pscustomobject]@{ Id = 'lowercarbon_capital'; Name = 'Lowercarbon Capital'; Slug = 'lowercarbon-capital'; Lens = 'climate tech; carbon capture; clean energy; sustainability'; Note = '1200 VC official investments page lists Lowercarbon Capital, described as backing climate-change solutions across clean energy, carbon capture and sustainability.' },
    [pscustomobject]@{ Id = 'endurance_28'; Name = 'Endurance 28'; Slug = 'endurance-28'; Lens = 'climate; health; digital economy; US and LatAm'; Note = '1200 VC official investments page lists Endurance 28, described as backing founders in climate, health and digital economy across US and LatAm.' },
    [pscustomobject]@{ Id = 'cantos'; Name = 'Cantos'; Slug = 'cantos'; Lens = 'frontier science; energy; space; AI; bio'; Note = '1200 VC official investments page lists Cantos, described as first-check investor in near-frontier science and engineering ventures building energy, space, AI and bio.' },
    [pscustomobject]@{ Id = 'onevc'; Name = 'OneVC'; Slug = 'onevc'; Lens = 'Brazil; seed; fintech; SaaS; logistics; healthcare'; Note = '1200 VC official investments page lists OneVC, described as backing ambitious Brazilian founders across fintech, SaaS, logistics and healthcare.' }
)

foreach ($fund in $funds) {
    $entities = Upsert-Entity -Rows $entities -EntityId $fund.Id -EntityType 'investor' -CanonicalName $fund.Name -Slug $fund.Slug -SourcePresence 'manual_1200vc_public_portfolio' -QualityFlags 'fund_of_funds_target' -ConfidenceScore '0.90'
    $manualEntities = Upsert-Entity -Rows $manualEntities -EntityId $fund.Id -EntityType 'investor' -CanonicalName $fund.Name -Slug $fund.Slug -SourcePresence 'manual_1200vc_public_portfolio' -QualityFlags 'fund_of_funds_target' -ConfidenceScore '0.90'
    $allocatorEdges = Upsert-AllocatorEdge -Rows $allocatorEdges `
        -AllocatorId '1200_vc' `
        -AllocatorName '1200 VC' `
        -AllocatorType 'fund_of_funds_and_direct_investor' `
        -TargetFundId $fund.Id `
        -TargetFundName $fund.Name `
        -TargetVehicle $fund.Name `
        -RelationType 'fund_of_funds_commitment_or_exposure' `
        -AmountUsd '' `
        -Year '' `
        -SectorLens $fund.Lens `
        -RegionLens 'United States; Latin America; global' `
        -SourceUrl $sourceUrl `
        -EvidenceNote $fund.Note `
        -Confidence '0.90'
}

$entities = Upsert-Entity -Rows $entities -EntityId 'general_biological' -EntityType 'startup' -CanonicalName 'General Biological' -Slug 'general-biological' -SourcePresence 'manual_1200vc_public_portfolio' -QualityFlags 'non_latam_bio_reference' -ConfidenceScore '0.88'
$manualEntities = Upsert-Entity -Rows $manualEntities -EntityId 'general_biological' -EntityType 'startup' -CanonicalName 'General Biological' -Slug 'general-biological' -SourcePresence 'manual_1200vc_public_portfolio' -QualityFlags 'non_latam_bio_reference' -ConfidenceScore '0.88'
$canonicalEdges = Upsert-InvestmentEdge -Rows $canonicalEdges `
    -InvestmentId 'manual-1200-vc-general-biological' `
    -InvestorId '1200_vc' `
    -StartupId 'general_biological' `
    -RelationType 'official_direct_investment' `
    -SourceFile $sourceUrl `
    -Notes '1200 VC official investments page lists General Biological and describes it as enabling the shift from petrochemical to biological production through scalable fermentation infrastructure for industrial biotechnology; included as non-LATAM BIO reference edge.' `
    -Confidence '0.90'
$manualEdges = Upsert-InvestmentEdge -Rows $manualEdges `
    -InvestmentId 'manual-1200-vc-general-biological' `
    -InvestorId '1200_vc' `
    -StartupId 'general_biological' `
    -RelationType 'official_direct_investment' `
    -SourceFile $sourceUrl `
    -Notes '1200 VC official investments page lists General Biological and describes it as enabling the shift from petrochemical to biological production through scalable fermentation infrastructure for industrial biotechnology; included as non-LATAM BIO reference edge.' `
    -Confidence '0.90'

$enduranceStartupEdges = @(
    [pscustomobject]@{
        InvestmentId = 'manual-endurance28-biomakers'
        StartupId = 'biomakers'
        StartupLabel = 'Biomakers'
        SourceUrl = 'https://www.endurance28.com/biomakers/'
        Notes = 'Endurance28 official startup page lists Biomakers; Biomakers also publicly lists Endurance28 among its investors.'
    },
    [pscustomobject]@{
        InvestmentId = 'manual-endurance28-oncoliq'
        StartupId = 'oncoliq'
        StartupLabel = 'Oncoliq'
        SourceUrl = 'https://www.endurance28.com/oncoliq/'
        Notes = 'Endurance28 official startup page lists Oncoliq; third-party funding profiles also identify Endurance28 as an Oncoliq seed investor.'
    }
)

foreach ($edge in $enduranceStartupEdges) {
    $canonicalEdges = Upsert-InvestmentEdge -Rows $canonicalEdges `
        -InvestmentId $edge.InvestmentId `
        -InvestorId 'endurance_28' `
        -StartupId $edge.StartupId `
        -InvestorLabel 'Endurance 28' `
        -StartupLabel $edge.StartupLabel `
        -RelationType 'official_portfolio_investment' `
        -SourceFile $edge.SourceUrl `
        -Notes $edge.Notes `
        -Confidence '0.93'
    $manualEdges = Upsert-InvestmentEdge -Rows $manualEdges `
        -InvestmentId $edge.InvestmentId `
        -InvestorId 'endurance_28' `
        -StartupId $edge.StartupId `
        -InvestorLabel 'Endurance 28' `
        -StartupLabel $edge.StartupLabel `
        -RelationType 'official_portfolio_investment' `
        -SourceFile $edge.SourceUrl `
        -Notes $edge.Notes `
        -Confidence '0.93'
}

foreach ($table in @($entities, $manualEntities)) {
    foreach ($entity in $table) {
        if ((Clean-Text $entity.entity_id) -eq '1200_vc') {
            $entity.quality_flags = Remove-Flag -Existing $entity.quality_flags -Flag 'capital_core_hidden_exclude_only'
            $entity.quality_flags = Add-Flag -Existing $entity.quality_flags -Flag 'fund_of_funds_and_direct_investor'
            $entity.confidence_score = '0.92'
            $entity.source_presence = 'manual_1200vc_public_portfolio'
        }
    }
}

$entities | Sort-Object entity_id | Export-Csv -LiteralPath $entitiesPath -NoTypeInformation -Encoding UTF8
$manualEntities | Sort-Object entity_id | Export-Csv -LiteralPath $manualEntitiesPath -NoTypeInformation -Encoding UTF8
$allocatorEdges | Export-Csv -LiteralPath $allocatorPath -NoTypeInformation -Encoding UTF8
$canonicalEdges | Export-Csv -LiteralPath $canonicalEdgesPath -NoTypeInformation -Encoding UTF8
$manualEdges | Export-Csv -LiteralPath $manualEdgesPath -NoTypeInformation -Encoding UTF8

Write-Output '1200 VC capital layer upgraded.'
Write-Output 'Added fund-of-funds edges and one non-LATAM BIO reference direct edge.'
