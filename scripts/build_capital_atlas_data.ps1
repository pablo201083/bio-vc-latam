param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack",
    [string]$OutputPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\capital-atlas-data.js",
    [string]$SemanticAssignmentsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_single_level_assignments.csv"
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

function Normalize-Key {
    param([object]$Value)
    $text = (Clean-Text $Value).ToLowerInvariant()
    if (-not $text) { return '' }
    $normalized = $text.Normalize([Text.NormalizationForm]::FormD)
    $chars = foreach ($char in $normalized.ToCharArray()) {
        if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($char) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            $char
        }
    }
    return ((-join $chars) -replace '[^a-z0-9]+', '')
}

function To-Number {
    param([object]$Value, [double]$Default = 0)
    $text = Clean-Text $Value
    if (-not $text) { return $Default }
    $parsed = 0.0
    if ([double]::TryParse($text, [Globalization.NumberStyles]::Any, [Globalization.CultureInfo]::InvariantCulture, [ref]$parsed)) {
        return $parsed
    }
    return $Default
}

function Edge-Kind {
    param([string]$Raw)
    $value = (Clean-Text $Raw).ToLowerInvariant()
    if ($value -match 'direct') { return 'direct_investment' }
    if ($value -match 'official_portfolio') { return 'portfolio_investment' }
    if ($value -match 'accelerator|membership') { return 'portfolio_or_acceleration' }
    return 'investment_or_membership'
}

function Get-Capital-Evidence {
    param(
        [string]$SourceUrl,
        [string]$Notes,
        [string]$RelationType
    )

    $source = Clean-Text $SourceUrl
    $notesText = (Clean-Text $Notes).ToLowerInvariant()
    $relation = (Clean-Text $RelationType).ToLowerInvariant()
    $hasUrl = $source -match '^https?://'

    if (-not $hasUrl) {
        if ($source -match 'graphml|edgeseco|csv') {
            return [pscustomobject]@{
                Level = 1
                Label = 'historical_graph'
                Tier = 'canonical_internal'
                Note = 'Historical graph or canonical CSV source; useful signal, not publicly auditable edge evidence.'
            }
        }
        return [pscustomobject]@{
            Level = 0
            Label = 'missing_or_internal'
            Tier = 'canonical_internal'
            Note = 'No public URL attached to this capital relation.'
        }
    }

    $looksLikeAnnouncement = ($source -match 'news|press|blog|noticia|announcement|announces|crunchbase|pitchbook|dealroom|latamlist|startups\.com|startupeable') -or ($notesText -match 'announc|investment round|raised|led by|participated|invested in|backed by')
    if ($looksLikeAnnouncement) {
        return [pscustomobject]@{
            Level = 4
            Label = 'investment_announcement'
            Tier = 'public_url'
            Note = 'Public source appears to describe an investment, round or backer relation explicitly.'
        }
    }

    $looksStartupSpecific = ($relation -match 'official_direct|official_portfolio|direct_investment') -or ($notesText -match 'lists .* as|lists .* direct|official .* lists|portfolio .* lists|listed .* portfolio|direct/strategic investment')
    if ($looksStartupSpecific) {
        return [pscustomobject]@{
            Level = 3
            Label = 'startup_specific_public'
            Tier = 'public_url'
            Note = 'Public source appears tied to a specific startup-fund relationship.'
        }
    }

    return [pscustomobject]@{
        Level = 2
        Label = 'fund_portfolio_page'
        Tier = 'public_url'
        Note = 'Public fund or portfolio URL attached; next step is checking startup-specific evidence.'
    }
}

$entities = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_entities.csv')
$investmentEdges = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_investment_edges.csv')
$allocatorEdges = Import-Csv -LiteralPath (Join-Path $Root 'quality\capital_allocator_edges.csv')
$taxonomyRows = Import-Csv -LiteralPath (Join-Path $Root 'startup_taxonomy_assignments_v1.csv')
$semanticRows = if (Test-Path -LiteralPath $SemanticAssignmentsPath) { Import-Csv -LiteralPath $SemanticAssignmentsPath } else { @() }
$profileRows = Import-Csv -LiteralPath (Join-Path $Root 'startup_profiles_minimum_viable.csv')
$masterRows = if (Test-Path -LiteralPath (Join-Path $Root 'startup_master_dataset.csv')) { Import-Csv -LiteralPath (Join-Path $Root 'startup_master_dataset.csv') } else { @() }
$aliasPath = Join-Path $Root 'quality\canonical_startup_aliases.csv'
$startupAliasRows = if (Test-Path -LiteralPath $aliasPath) { Import-Csv -LiteralPath $aliasPath } else { @() }

$entityById = @{}
foreach ($entity in $entities) {
    $entityById[$entity.entity_id] = $entity
}

$startupAliasById = @{}
$startupAliasByName = @{}
foreach ($alias in $startupAliasRows) {
    $aliasId = Clean-Text $alias.alias_startup_id
    $canonicalId = Clean-Text $alias.canonical_startup_id
    if (-not $aliasId -or -not $canonicalId) { continue }
    $startupAliasById[$aliasId] = $canonicalId
    $aliasKey = Normalize-Key $aliasId
    if ($aliasKey) { $startupAliasByName[$aliasKey] = $canonicalId }
}

function Resolve-Startup-Alias {
    param([string]$StartupId)
    $value = Clean-Text $StartupId
    if (-not $value) { return '' }
    if ($startupAliasById.ContainsKey($value)) { return $startupAliasById[$value] }
    $key = Normalize-Key $value
    if ($key -and $startupAliasByName.ContainsKey($key)) { return $startupAliasByName[$key] }
    return $value
}

$canonicalStartupIdByName = @{}
foreach ($entity in $entities) {
    if ((Clean-Text $entity.entity_type) -ne 'startup') { continue }
    $nameKey = Normalize-Key $entity.canonical_name
    if ($nameKey -and -not $canonicalStartupIdByName.ContainsKey($nameKey)) {
        $canonicalStartupIdByName[$nameKey] = Clean-Text $entity.entity_id
    }
}

$taxonomyById = @{}
$taxonomyByName = @{}
foreach ($row in $taxonomyRows) {
    $taxonomyById[$row.startup_id] = $row
    $nameKey = Normalize-Key $row.startup_name
    if ($nameKey -and -not $taxonomyByName.ContainsKey($nameKey)) { $taxonomyByName[$nameKey] = $row }
}

$semanticById = @{}
$semanticByName = @{}
foreach ($row in $semanticRows) {
    $canonicalId = Resolve-Startup-Alias (Clean-Text $row.startup_id)
    if ($canonicalId) { $semanticById[$canonicalId] = $row }
    $nameKey = Normalize-Key $row.startup_name
    if ($nameKey -and -not $semanticByName.ContainsKey($nameKey)) { $semanticByName[$nameKey] = $row }
}

$profileById = @{}
$profileByName = @{}
foreach ($row in $profileRows) {
    $profileById[$row.startup_id] = $row
    $nameKey = Normalize-Key $row.startup_name
    if ($nameKey -and -not $profileByName.ContainsKey($nameKey)) { $profileByName[$nameKey] = $row }
}

$masterById = @{}
$masterByName = @{}
foreach ($row in $masterRows) {
    $masterById[$row.startup_id] = $row
    $nameKey = Normalize-Key $row.startup_name
    if ($nameKey -and -not $masterByName.ContainsKey($nameKey)) { $masterByName[$nameKey] = $row }
}

function Resolve-StartupRecord {
    param(
        [string]$StartupId,
        [hashtable]$EntityById,
        [hashtable]$MasterById,
        [hashtable]$MasterByName
    )

    $StartupId = Resolve-Startup-Alias $StartupId
    $entity = if ($EntityById.ContainsKey($StartupId)) { $EntityById[$StartupId] } else { $null }
    $entityName = if ($entity) { Clean-Text $entity.canonical_name } else { '' }
    $startupNameKey = Normalize-Key $(if ($entityName) { $entityName } else { $StartupId })
    $master = if ($MasterById.ContainsKey($StartupId)) {
        $MasterById[$StartupId]
    } elseif ($startupNameKey -and $MasterByName.ContainsKey($startupNameKey)) {
        $MasterByName[$startupNameKey]
    } else {
        $null
    }

    $resolvedId = if ($master) { Clean-Text $master.startup_id } else { $StartupId }
    $resolvedLabel = if ($master) {
        Clean-Text $master.startup_name
    } elseif ($entity) {
        $entityName
    } else {
        $StartupId
    }
    $resolvedNameKey = Normalize-Key $resolvedLabel

    return [pscustomobject]@{
        Id = $resolvedId
        Label = $resolvedLabel
        NameKey = $resolvedNameKey
        Entity = $entity
        Master = $master
    }
}

$nodeMap = @{}
$edgeMap = @{}

function Ensure-Node {
    param(
        [hashtable]$NodeMap,
        [string]$Id,
        [string]$Type,
        [string]$Label,
        [hashtable]$Extra = @{}
    )
    if (-not $Id) { return }
    if (-not $NodeMap.ContainsKey($Id)) {
        $node = [ordered]@{
            id = $Id
            type = $Type
            label = $Label
        }
        foreach ($key in $Extra.Keys) { $node[$key] = $Extra[$key] }
        $NodeMap[$Id] = $node
    } else {
        foreach ($key in $Extra.Keys) {
            if (-not $NodeMap[$Id].Contains($key) -or -not $NodeMap[$Id][$key]) {
                $NodeMap[$Id][$key] = $Extra[$key]
            }
        }
    }
}

foreach ($edge in $investmentEdges) {
    $investorId = Clean-Text $edge.investor_id
    $startupId = Resolve-Startup-Alias (Clean-Text $edge.startup_id)
    if (-not $investorId -or -not $startupId) { continue }
    if (-not $entityById.ContainsKey($investorId)) { continue }

    $investor = $entityById[$investorId]
    if ((Clean-Text $investor.entity_type) -ne 'investor') { continue }

    $resolvedStartup = Resolve-StartupRecord -StartupId $startupId -EntityById $entityById -MasterById $masterById -MasterByName $masterByName
    if (-not $resolvedStartup.Master -and $resolvedStartup.Entity -and (Clean-Text $resolvedStartup.Entity.entity_type) -ne 'startup') { continue }
    if (-not $resolvedStartup.Master -and -not $resolvedStartup.Entity) { continue }

    $startupId = $resolvedStartup.Id
    $startupLabel = $resolvedStartup.Label
    $startupNameKey = $resolvedStartup.NameKey
    if ($startupNameKey -and -not $resolvedStartup.Master -and $canonicalStartupIdByName.ContainsKey($startupNameKey)) {
        $startupId = $canonicalStartupIdByName[$startupNameKey]
        $resolvedStartup = Resolve-StartupRecord -StartupId $startupId -EntityById $entityById -MasterById $masterById -MasterByName $masterByName
        $startupLabel = $resolvedStartup.Label
        $startupNameKey = $resolvedStartup.NameKey
    }
    $taxonomy = if ($taxonomyById.ContainsKey($startupId)) { $taxonomyById[$startupId] } elseif ($taxonomyByName.ContainsKey($startupNameKey)) { $taxonomyByName[$startupNameKey] } else { $null }
    $semantic = if ($semanticById.ContainsKey($startupId)) { $semanticById[$startupId] } elseif ($semanticByName.ContainsKey($startupNameKey)) { $semanticByName[$startupNameKey] } else { $null }
    $profile = if ($profileById.ContainsKey($startupId)) { $profileById[$startupId] } elseif ($profileByName.ContainsKey($startupNameKey)) { $profileByName[$startupNameKey] } else { $null }
    $master = if ($resolvedStartup.Master) { $resolvedStartup.Master } elseif ($masterById.ContainsKey($startupId)) { $masterById[$startupId] } elseif ($masterByName.ContainsKey($startupNameKey)) { $masterByName[$startupNameKey] } else { $null }
    $confidence = To-Number $edge.confidence_score 0.6
    $kind = Edge-Kind $edge.relation_type_raw
    $sourceUrl = Clean-Text $edge.source_file
    $capitalEvidence = Get-Capital-Evidence -SourceUrl $sourceUrl -Notes $edge.notes -RelationType $edge.relation_type_raw
    $hasPublicSource = $capitalEvidence.Level -ge 2

    Ensure-Node -NodeMap $nodeMap -Id $investorId -Type 'fund' -Label (Clean-Text $investor.canonical_name) -Extra @{
        source_presence = Clean-Text $investor.source_presence
        quality_flags = Clean-Text $investor.quality_flags
        entity_confidence = To-Number $investor.confidence_score 0.6
        investor_subtype = if ((Clean-Text $investor.quality_flags) -match 'fund_of_funds') { 'fund_of_funds' } else { 'vc_or_investor' }
    }

    Ensure-Node -NodeMap $nodeMap -Id $startupId -Type 'startup' -Label $startupLabel -Extra @{
        country = if ($taxonomy) { Clean-Text $taxonomy.structured_country } else { '' }
        theme = if ($semantic) { Clean-Text $semantic.semantic_single_theme } elseif ($taxonomy) { Clean-Text $taxonomy.macro_theme } else { '' }
        legacy_macro_theme = if ($taxonomy) { Clean-Text $taxonomy.macro_theme } else { '' }
        emergent_theme = if ($taxonomy) { Clean-Text $taxonomy.emergent_theme } else { '' }
        semantic_single_theme = if ($semantic) { Clean-Text $semantic.semantic_single_theme } else { '' }
        semantic_single_confidence = if ($semantic) { Clean-Text $semantic.semantic_single_confidence } else { '' }
        semantic_single_score = if ($semantic) { Clean-Text $semantic.semantic_single_score } else { '' }
        scope_decision = if ($taxonomy) { Clean-Text $taxonomy.scope_decision } else { '' }
        thesis_fit = if ($taxonomy) { Clean-Text $taxonomy.thesis_fit } else { '' }
        source_url = if ($profile) { Clean-Text $profile.source_url } else { '' }
        review_status = if ($profile) { Clean-Text $profile.review_status } else { '' }
        summary = if ($profile) { Clean-Text $profile.startup_summary_v1 } else { '' }
        bio_lens_tags = if ($master) { Clean-Text $master.bio_lens_tags } else { '' }
        domain_tags = if ($master) { Clean-Text $master.domain_tags } else { '' }
        technology_tags = if ($master) { Clean-Text $master.technology_tags } else { '' }
        scale_tags = if ($master) { Clean-Text $master.scale_tags } else { '' }
    }

    $edgeId = "$investorId->$startupId|$kind|$(Clean-Text $edge.source_file)"
    if (-not $edgeMap.ContainsKey($edgeId)) {
        $edgeMap[$edgeId] = [ordered]@{
            id = $edge.investment_id
            source = $investorId
            target = $startupId
            type = $kind
            confidence = [math]::Round($confidence, 2)
            source_url = $sourceUrl
            evidence = Clean-Text $edge.notes
            audited = $hasPublicSource
            evidence_tier = $capitalEvidence.Tier
            capital_evidence_level = $capitalEvidence.Level
            capital_evidence_label = $capitalEvidence.Label
            capital_evidence_note = $capitalEvidence.Note
            weight = [math]::Round((0.8 + $confidence * 1.6), 2)
        }
    }
}

$startupNodeIdByName = @{}
foreach ($node in $nodeMap.Values) {
    if ($node.type -eq 'startup') {
        $nameKey = Normalize-Key $node.label
        if ($nameKey -and -not $startupNodeIdByName.ContainsKey($nameKey)) {
            $startupNodeIdByName[$nameKey] = $node.id
        }
    }
}

foreach ($row in $taxonomyRows) {
    $startupId = Clean-Text $row.startup_id
    if ((Resolve-Startup-Alias $startupId) -ne $startupId) { continue }
    $startupLabel = Clean-Text $row.startup_name
    if (-not $startupId -or -not $startupLabel) { continue }
    $startupNameKey = Normalize-Key $startupLabel
    $nodeId = if ($startupNameKey -and $startupNodeIdByName.ContainsKey($startupNameKey)) { $startupNodeIdByName[$startupNameKey] } else { $startupId }
    $profile = if ($profileById.ContainsKey($startupId)) { $profileById[$startupId] } elseif ($profileByName.ContainsKey($startupNameKey)) { $profileByName[$startupNameKey] } else { $null }
    $master = if ($masterById.ContainsKey($startupId)) { $masterById[$startupId] } elseif ($masterByName.ContainsKey($startupNameKey)) { $masterByName[$startupNameKey] } else { $null }
    $semantic = if ($semanticById.ContainsKey($startupId)) { $semanticById[$startupId] } elseif ($semanticByName.ContainsKey($startupNameKey)) { $semanticByName[$startupNameKey] } else { $null }

    Ensure-Node -NodeMap $nodeMap -Id $nodeId -Type 'startup' -Label $startupLabel -Extra @{
        country = Clean-Text $row.structured_country
        theme = if ($semantic) { Clean-Text $semantic.semantic_single_theme } else { Clean-Text $row.macro_theme }
        legacy_macro_theme = Clean-Text $row.macro_theme
        emergent_theme = Clean-Text $row.emergent_theme
        semantic_single_theme = if ($semantic) { Clean-Text $semantic.semantic_single_theme } else { '' }
        semantic_single_confidence = if ($semantic) { Clean-Text $semantic.semantic_single_confidence } else { '' }
        semantic_single_score = if ($semantic) { Clean-Text $semantic.semantic_single_score } else { '' }
        scope_decision = Clean-Text $row.scope_decision
        thesis_fit = Clean-Text $row.thesis_fit
        source_url = if ($profile) { Clean-Text $profile.source_url } else { Clean-Text $row.trl_current_source_url }
        review_status = if ($profile) { Clean-Text $profile.review_status } else { Clean-Text $row.assignment_method }
        summary = if ($profile) { Clean-Text $profile.startup_summary_v1 } else { Clean-Text $row.notes }
        taxonomy_source = Clean-Text $row.taxonomy_source
        evidence_source = Clean-Text $row.evidence_source
        bio_lens_tags = if ($master) { Clean-Text $master.bio_lens_tags } else { '' }
        domain_tags = if ($master) { Clean-Text $master.domain_tags } else { '' }
        technology_tags = if ($master) { Clean-Text $master.technology_tags } else { '' }
        scale_tags = if ($master) { Clean-Text $master.scale_tags } else { '' }
    }
}

foreach ($edge in $allocatorEdges) {
    $allocatorId = Clean-Text $edge.allocator_id
    $targetFundId = Clean-Text $edge.target_fund_id
    if (-not $allocatorId -or -not $targetFundId) { continue }
    $allocatorLabel = Clean-Text $edge.allocator_name
    $targetLabel = Clean-Text $edge.target_fund_name
    Ensure-Node -NodeMap $nodeMap -Id $allocatorId -Type 'allocator' -Label $allocatorLabel -Extra @{
        investor_subtype = Clean-Text $edge.allocator_type
        source_presence = 'capital_allocator_edges'
        entity_confidence = To-Number $edge.confidence 0.85
    }
    Ensure-Node -NodeMap $nodeMap -Id $targetFundId -Type 'fund' -Label $targetLabel -Extra @{
        investor_subtype = 'vc_or_investor'
        source_presence = 'capital_allocator_edges'
        entity_confidence = To-Number $edge.confidence 0.85
    }
    $edgeId = "$allocatorId->$targetFundId|allocator"
    if (-not $edgeMap.ContainsKey($edgeId)) {
        $edgeMap[$edgeId] = [ordered]@{
            id = "$allocatorId-$targetFundId"
            source = $allocatorId
            target = $targetFundId
            type = Clean-Text $edge.relation_type
            confidence = [math]::Round((To-Number $edge.confidence 0.85), 2)
            source_url = Clean-Text $edge.source_url
            evidence = Clean-Text $edge.evidence_note
            audited = $true
            evidence_tier = 'public_url'
            weight = 2.4
            amount_usd = To-Number $edge.amount_usd 0
            year = Clean-Text $edge.year
            sector_lens = Clean-Text $edge.sector_lens
        }
    }
}

$nodes = @($nodeMap.Values)
$edges = @($edgeMap.Values)

$degree = @{}
foreach ($node in $nodes) { $degree[$node.id] = 0 }
foreach ($edge in $edges) {
    if ($degree.ContainsKey($edge.source)) { $degree[$edge.source]++ }
    if ($degree.ContainsKey($edge.target)) { $degree[$edge.target]++ }
}
foreach ($node in $nodes) {
    $node['degree'] = $degree[$node.id]
    if ($node.type -eq 'startup') {
        $node['capital_status'] = if ($degree[$node.id] -gt 0) { 'capital_mapped' } else { 'no_capital_edge' }
    }
}

$funds = @($nodes | Where-Object { $_.type -eq 'fund' })
$startups = @($nodes | Where-Object { $_.type -eq 'startup' })
$allocators = @($nodes | Where-Object { $_.type -eq 'allocator' })
$includeStartups = @($startups | Where-Object { $_.scope_decision -eq 'include' })
$confirmedSourceBacked = @($includeStartups | Where-Object { Clean-Text $_.source_url })

$payload = [ordered]@{
    generated_at = (Get-Date).ToString('s')
    summary = [ordered]@{
        nodes_total = $nodes.Count
        funds_total = $funds.Count
        startups_total = $startups.Count
        allocators_total = $allocators.Count
        edges_total = $edges.Count
        include_startups_total = $includeStartups.Count
        source_backed_include_startups_total = $confirmedSourceBacked.Count
        public_source_edges_total = @($edges | Where-Object { $_.audited }).Count
    }
    nodes = $nodes
    edges = $edges
}

$json = $payload | ConvertTo-Json -Depth 12
"window.CAPITAL_ATLAS_DATA = $json;" | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Host "Wrote $OutputPath"
Write-Host "Nodes: $($nodes.Count) Edges: $($edges.Count)"
