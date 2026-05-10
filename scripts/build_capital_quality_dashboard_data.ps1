param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack",
    [string]$AtlasDataPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\capital-atlas-data.js",
    [string]$OutputJsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\capital-quality-data.js"
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

function Percent {
    param([int]$Ready, [int]$Total)
    if ($Total -le 0) { return 0.0 }
    return [Math]::Round(($Ready / [double]$Total) * 100, 1)
}

function Add-Count {
    param([hashtable]$Map, [string]$Key, [int]$Increment = 1)
    $safe = if (Clean-Text $Key) { Clean-Text $Key } else { 'sin dato' }
    if (-not $Map.ContainsKey($safe)) { $Map[$safe] = 0 }
    $Map[$safe] = [int]$Map[$safe] + $Increment
}

function Count-Rows {
    param([object[]]$Rows)
    return @($Rows).Count
}

function Evidence-Level {
    param([object]$Edge)
    $value = To-Number $Edge.capital_evidence_level -Default -1
    if ($value -ge 0) { return [int]$value }
    if ($Edge.evidence_tier -eq 'public_url' -or $Edge.audited -eq $true) { return 2 }
    return 1
}

function Evidence-Label {
    param([object]$Edge)
    $label = Clean-Text $Edge.capital_evidence_label
    if ($label) { return $label }
    if ((Evidence-Level $Edge) -ge 2) { return 'fund_portfolio_page' }
    return 'historical_graph'
}

if (-not (Test-Path -LiteralPath $AtlasDataPath)) {
    throw "Missing capital atlas data: $AtlasDataPath"
}

$raw = Get-Content -LiteralPath $AtlasDataPath -Raw -Encoding UTF8
$json = $raw -replace '^\s*window\.CAPITAL_ATLAS_DATA\s*=\s*', ''
$json = $json -replace ';\s*$', ''
$atlas = $json | ConvertFrom-Json

$nodes = @($atlas.nodes)
$edges = @($atlas.edges)
$nodesById = @{}
foreach ($node in $nodes) { $nodesById[$node.id] = $node }

$startups = @($nodes | Where-Object { $_.type -eq 'startup' })
$includeStartups = @($startups | Where-Object { $_.scope_decision -eq 'include' })
$funds = @($nodes | Where-Object { $_.type -eq 'fund' })
$allocators = @($nodes | Where-Object { $_.type -eq 'allocator' })
$investmentEdges = @($edges | Where-Object { $nodesById.ContainsKey($_.source) -and $nodesById.ContainsKey($_.target) -and $nodesById[$_.source].type -eq 'fund' -and $nodesById[$_.target].type -eq 'startup' })
$allocatorEdges = @($edges | Where-Object {
    $nodesById.ContainsKey($_.source) -and
    $nodesById.ContainsKey($_.target) -and
    $nodesById[$_.target].type -eq 'fund' -and
    (
        $nodesById[$_.source].type -eq 'allocator' -or
        (Clean-Text $_.type) -match 'fund_of_funds'
    )
})
$includeInvestmentEdges = @($investmentEdges | Where-Object { $nodesById[$_.target].scope_decision -eq 'include' })

$includeWithCapitalIds = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($edge in $includeInvestmentEdges) { [void]$includeWithCapitalIds.Add([string]$edge.target) }
$includeWithCapital = @($includeStartups | Where-Object { $includeWithCapitalIds.Contains([string]$_.id) })
$includeWithoutCapital = @($includeStartups | Where-Object { -not $includeWithCapitalIds.Contains([string]$_.id) })

$publicEdges = @($edges | Where-Object { $_.evidence_tier -eq 'public_url' -or $_.audited -eq $true })
$publicInvestmentEdges = @($includeInvestmentEdges | Where-Object { $_.evidence_tier -eq 'public_url' -or $_.audited -eq $true })
$specificEvidenceEdges = @($includeInvestmentEdges | Where-Object { (Evidence-Level $_) -ge 3 })
$announcementEvidenceEdges = @($includeInvestmentEdges | Where-Object { (Evidence-Level $_) -ge 4 })
$highConfidenceEdges = @($includeInvestmentEdges | Where-Object { (To-Number $_.confidence) -ge 0.9 })
$mediumConfidenceEdges = @($includeInvestmentEdges | Where-Object { (To-Number $_.confidence) -ge 0.75 -and (To-Number $_.confidence) -lt 0.9 })
$weakEdges = @($includeInvestmentEdges | Where-Object { (To-Number $_.confidence) -lt 0.75 -or (Evidence-Level $_) -lt 3 })

$connectivityNodeIds = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($fund in $funds) { [void]$connectivityNodeIds.Add([string]$fund.id) }
foreach ($allocator in $allocators) { [void]$connectivityNodeIds.Add([string]$allocator.id) }
foreach ($startup in $includeStartups) { [void]$connectivityNodeIds.Add([string]$startup.id) }
foreach ($fund in $funds) {
    $qualityFlags = if ($fund.PSObject.Properties.Name -contains 'quality_flags') { Clean-Text $fund.quality_flags } else { '' }
    if ($qualityFlags -match 'capital_core_hidden_exclude_only|capital_core_sidecar_broad_low_priority') {
        [void]$connectivityNodeIds.Remove([string]$fund.id)
    }
}
$adjacency = @{}
foreach ($id in $connectivityNodeIds) {
    $adjacency[$id] = New-Object 'System.Collections.Generic.HashSet[string]'
}
foreach ($edge in $includeInvestmentEdges) {
    $sourceId = [string]$edge.source
    $targetId = [string]$edge.target
    if (-not $adjacency.ContainsKey($sourceId) -or -not $adjacency.ContainsKey($targetId)) { continue }
    $sourceFlags = if ($nodesById[$sourceId].PSObject.Properties.Name -contains 'quality_flags') { Clean-Text $nodesById[$sourceId].quality_flags } else { '' }
    $targetFlags = if ($nodesById[$targetId].PSObject.Properties.Name -contains 'quality_flags') { Clean-Text $nodesById[$targetId].quality_flags } else { '' }
    if (($sourceFlags + ';' + $targetFlags) -match 'capital_core_hidden_exclude_only|capital_core_sidecar_broad_low_priority') { continue }
    [void]$adjacency[$sourceId].Add($targetId)
    [void]$adjacency[$targetId].Add($sourceId)
}
foreach ($edge in $allocatorEdges) {
    $sourceId = [string]$edge.source
    $targetId = [string]$edge.target
    if (-not $adjacency.ContainsKey($sourceId) -or -not $adjacency.ContainsKey($targetId)) { continue }
    $sourceFlags = if ($nodesById[$sourceId].PSObject.Properties.Name -contains 'quality_flags') { Clean-Text $nodesById[$sourceId].quality_flags } else { '' }
    $targetFlags = if ($nodesById[$targetId].PSObject.Properties.Name -contains 'quality_flags') { Clean-Text $nodesById[$targetId].quality_flags } else { '' }
    if (($sourceFlags + ';' + $targetFlags) -match 'capital_core_hidden_exclude_only|capital_core_sidecar_broad_low_priority') { continue }
    [void]$adjacency[$sourceId].Add($targetId)
    [void]$adjacency[$targetId].Add($sourceId)
}
$visitedConnectivity = New-Object 'System.Collections.Generic.HashSet[string]'
$capitalComponents = @()
foreach ($id in $connectivityNodeIds) {
    if ($visitedConnectivity.Contains($id)) { continue }
    $queue = New-Object 'System.Collections.Generic.Queue[string]'
    $componentIds = New-Object 'System.Collections.Generic.List[string]'
    [void]$visitedConnectivity.Add($id)
    $queue.Enqueue($id)
    while ($queue.Count -gt 0) {
        $current = $queue.Dequeue()
        $componentIds.Add($current)
        foreach ($next in $adjacency[$current]) {
            if ($visitedConnectivity.Contains($next)) { continue }
            [void]$visitedConnectivity.Add($next)
            $queue.Enqueue($next)
        }
    }
    $componentNodes = @($componentIds | ForEach-Object { $nodesById[$_] } | Where-Object { $null -ne $_ })
    $componentFunds = @($componentNodes | Where-Object { $_.type -eq 'fund' })
    $componentAllocators = @($componentNodes | Where-Object { $_.type -eq 'allocator' })
    $componentStartups = @($componentNodes | Where-Object { $_.type -eq 'startup' })
    $capitalComponents += [pscustomobject]@{
        nodes = $componentNodes.Count
        funds = $componentFunds.Count
        allocators = $componentAllocators.Count
        startups = $componentStartups.Count
        fund_names = @($componentFunds | ForEach-Object { $_.label }) -join ', '
        allocator_names = @($componentAllocators | ForEach-Object { $_.label }) -join ', '
        startup_names = @($componentStartups | Select-Object -First 12 | ForEach-Object { $_.label }) -join ', '
    }
}
$capitalComponents = @($capitalComponents | Sort-Object @{ Expression = 'nodes'; Descending = $true }, @{ Expression = 'funds'; Descending = $true })
$largestCapitalComponent = if ($capitalComponents.Count) { $capitalComponents[0] } else { $null }
$largestComponentNodes = if ($largestCapitalComponent) { [int]$largestCapitalComponent.nodes } else { 0 }
$mainContinentSharePct = Percent -Ready $largestComponentNodes -Total $connectivityNodeIds.Count
$floatingComponents = @($capitalComponents | Where-Object { $_.nodes -gt 1 } | Select-Object -Skip 1)
$floatingComponentNodes = if ($floatingComponents.Count) { [int](($floatingComponents | Measure-Object -Property nodes -Sum).Sum) } else { 0 }

$fundStats = @()
$fundIdsWithIncludePortfolio = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($fund in $funds) {
    $portfolioEdges = @($includeInvestmentEdges | Where-Object { $_.source -eq $fund.id })
    if ($portfolioEdges.Count -gt 0) { [void]$fundIdsWithIncludePortfolio.Add([string]$fund.id) }
    $portfolioStartups = @($portfolioEdges | ForEach-Object { $nodesById[$_.target] } | Where-Object { $null -ne $_ })
    $publicCount = @($portfolioEdges | Where-Object { $_.evidence_tier -eq 'public_url' -or $_.audited -eq $true }).Count
    $specificCount = @($portfolioEdges | Where-Object { (Evidence-Level $_) -ge 3 }).Count
    $avgConfidence = if ($portfolioEdges.Count) { [Math]::Round((@($portfolioEdges | ForEach-Object { To-Number $_.confidence }) | Measure-Object -Average).Average, 2) } else { 0.0 }
    $themeCount = @($portfolioStartups | ForEach-Object { Clean-Text $_.theme } | Where-Object { $_ } | Select-Object -Unique).Count
    $countryCount = @($portfolioStartups | ForEach-Object { Clean-Text $_.country } | Where-Object { $_ } | Select-Object -Unique).Count
    $sourceCoverage = Percent -Ready $publicCount -Total $portfolioEdges.Count
    $specificCoverage = Percent -Ready $specificCount -Total $portfolioEdges.Count
    $portfolioDepthScore = [Math]::Min(100, [Math]::Round(($portfolioEdges.Count / 20.0) * 100, 1))
    $diversityScore = [Math]::Min(100, [Math]::Round((($themeCount * 12) + ($countryCount * 5)), 1))
    $qualityScore = [Math]::Round(($sourceCoverage * 0.22) + ($specificCoverage * 0.24) + (($avgConfidence * 100) * 0.26) + ($portfolioDepthScore * 0.18) + ($diversityScore * 0.10), 1)
    $fundStats += [pscustomobject]@{
        fund_id = $fund.id
        fund_name = $fund.label
        portfolio_include = $portfolioEdges.Count
        public_edges = $publicCount
        specific_edges = $specificCount
        source_coverage_pct = $sourceCoverage
        specific_edge_pct = $specificCoverage
        avg_confidence = $avgConfidence
        theme_count = $themeCount
        country_count = $countryCount
        quality_score = $qualityScore
        source_presence = Clean-Text $fund.source_presence
        investor_subtype = Clean-Text $fund.investor_subtype
    }
}

$themeRows = @()
$themeKeys = @($includeStartups | ForEach-Object { Clean-Text $_.theme } | Where-Object { $_ } | Select-Object -Unique)
foreach ($theme in $themeKeys) {
    $themeStartups = @($includeStartups | Where-Object { (Clean-Text $_.theme) -eq $theme })
    $mapped = @($themeStartups | Where-Object { $includeWithCapitalIds.Contains([string]$_.id) })
    $themeEdges = @($includeInvestmentEdges | Where-Object { (Clean-Text $nodesById[$_.target].theme) -eq $theme })
    $publicThemeEdges = @($themeEdges | Where-Object { $_.evidence_tier -eq 'public_url' -or $_.audited -eq $true })
    $themeRows += [pscustomobject]@{
        theme = $theme
        startups = $themeStartups.Count
        mapped = $mapped.Count
        gaps = $themeStartups.Count - $mapped.Count
        coverage_pct = Percent -Ready $mapped.Count -Total $themeStartups.Count
        edges = $themeEdges.Count
        public_edges = $publicThemeEdges.Count
        public_edge_pct = Percent -Ready $publicThemeEdges.Count -Total $themeEdges.Count
    }
}

$countryRows = @()
$countryKeys = @($includeStartups | ForEach-Object { Clean-Text $_.country } | Where-Object { $_ } | Select-Object -Unique)
foreach ($country in $countryKeys) {
    $countryStartups = @($includeStartups | Where-Object { (Clean-Text $_.country) -eq $country })
    $mapped = @($countryStartups | Where-Object { $includeWithCapitalIds.Contains([string]$_.id) })
    $countryRows += [pscustomobject]@{
        country = $country
        startups = $countryStartups.Count
        mapped = $mapped.Count
        gaps = $countryStartups.Count - $mapped.Count
        coverage_pct = Percent -Ready $mapped.Count -Total $countryStartups.Count
    }
}

$edgeTypeCounts = @(
    $edges |
        Group-Object type |
        Sort-Object Count -Descending |
        ForEach-Object { [pscustomobject]@{ type = $_.Name; count = $_.Count } }
)

$evidenceLadderRows = @(
    0..4 | ForEach-Object {
        $level = $_
        $rows = @($includeInvestmentEdges | Where-Object { (Evidence-Level $_) -eq $level })
        $label = switch ($level) {
            0 { 'Sin fuente publica' }
            1 { 'Grafo historico / interno' }
            2 { 'URL publica de fondo/portfolio' }
            3 { 'Relacion publica startup-fondo' }
            4 { 'Anuncio de inversion / ronda' }
        }
        [pscustomobject]@{
            level = $level
            label = $label
            edges = $rows.Count
            pct = Percent -Ready $rows.Count -Total $includeInvestmentEdges.Count
            next_action = switch ($level) {
                0 { 'Agregar fuente publica o descartar.' }
                1 { 'Reemplazar por portfolio publico.' }
                2 { 'Confirmar que la startup aparece explicitamente.' }
                3 { 'Buscar anuncio de inversion si existe.' }
                4 { 'Mantener como edge premium.' }
            }
        }
    }
)

$sourceTierCounts = @(
    $edges |
        Group-Object evidence_tier |
        Sort-Object Count -Descending |
        ForEach-Object { [pscustomobject]@{ tier = if ($_.Name) { $_.Name } else { 'sin dato' }; count = $_.Count } }
)

$gapQueue = @(
    $includeWithoutCapital |
        ForEach-Object {
            $theme = Clean-Text $_.theme
            $country = Clean-Text $_.country
            $themeFundCount = @($fundStats | Where-Object { $_.portfolio_include -gt 0 } | ForEach-Object {
                $fundId = $_.fund_id
                $matches = @($includeInvestmentEdges | Where-Object { $_.source -eq $fundId -and (Clean-Text $nodesById[$_.target].theme) -eq $theme }).Count
                if ($matches -gt 0) { $fundId }
            }).Count
            [pscustomobject]@{
                startup_id = $_.id
                startup_name = $_.label
                theme = $theme
                country = $country
                source_url = Clean-Text $_.source_url
                summary = Clean-Text $_.summary
                candidate_fund_pool = $themeFundCount
                priority_score = [Math]::Round((20 + [Math]::Min(45, $themeFundCount * 3) + $(if ($country) { 10 } else { 0 }) + $(if (Clean-Text $_.source_url) { 12 } else { 0 })), 1)
                suggested_action = 'Buscar portfolio/investor pages y press releases de fondos con cartera similar.'
            }
        } |
        Sort-Object @{ Expression = 'priority_score'; Descending = $true }, startup_name |
        Select-Object -First 60
)

$edgeUpgradeQueue = @(
    $weakEdges |
        ForEach-Object {
            $fund = $nodesById[$_.source]
            $startup = $nodesById[$_.target]
            [pscustomobject]@{
                fund_name = $fund.label
                startup_name = $startup.label
                theme = Clean-Text $startup.theme
                country = Clean-Text $startup.country
                relation_type = Clean-Text $_.type
                confidence = To-Number $_.confidence
                evidence_tier = Clean-Text $_.evidence_tier
                evidence_level = Evidence-Level $_
                evidence_label = Evidence-Label $_
                source_url = Clean-Text $_.source_url
                priority_score = [Math]::Round((100 - ((To-Number $_.confidence) * 40) + $(if ((Evidence-Level $_) -lt 2) { 35 } elseif ((Evidence-Level $_) -lt 3) { 18 } else { 0 })), 1)
                suggested_action = if ((Evidence-Level $_) -lt 2) { 'Buscar URL publica de fondo/portfolio.' } elseif ((Evidence-Level $_) -lt 3) { 'Verificar que la startup figure explicitamente en la fuente.' } else { 'Buscar anuncio de inversion o ronda para edge premium.' }
            }
        } |
        Sort-Object @{ Expression = 'priority_score'; Descending = $true }, fund_name, startup_name |
        Select-Object -First 80
)

$fundSpecificEvidenceQueue = @(
    $fundStats |
        Where-Object { $_.portfolio_include -ge 3 } |
        Sort-Object @{ Expression = 'specific_edge_pct'; Ascending = $true }, @{ Expression = 'portfolio_include'; Descending = $true } |
        Select-Object -First 18 |
        ForEach-Object {
            [pscustomobject]@{
                fund_id = $_.fund_id
                fund_name = $_.fund_name
                portfolio_include = $_.portfolio_include
                public_edges = $_.public_edges
                specific_edges = $_.specific_edges
                source_coverage_pct = $_.source_coverage_pct
                specific_edge_pct = $_.specific_edge_pct
                priority_score = [Math]::Round((($_.portfolio_include * 1.5) + (100 - $_.specific_edge_pct) + $(if ($_.source_coverage_pct -ge 80) { 12 } else { 0 })), 1)
                suggested_action = 'Auditar portfolio oficial y convertir URL generica en evidencia startup-fondo explicita.'
            }
        } |
        Sort-Object @{ Expression = 'priority_score'; Descending = $true }
)

$coveragePct = Percent -Ready $includeWithCapital.Count -Total $includeStartups.Count
$publicEdgePct = Percent -Ready $publicInvestmentEdges.Count -Total $includeInvestmentEdges.Count
$specificEdgePct = Percent -Ready $specificEvidenceEdges.Count -Total $includeInvestmentEdges.Count
$announcementEdgePct = Percent -Ready $announcementEvidenceEdges.Count -Total $includeInvestmentEdges.Count
$highConfidencePct = Percent -Ready $highConfidenceEdges.Count -Total $includeInvestmentEdges.Count
$allocatorCoveragePct = Percent -Ready $allocatorEdges.Count -Total ([Math]::Max(1, $funds.Count))
$fundsWithPortfolio = @($fundStats | Where-Object { $_.portfolio_include -gt 0 }).Count
$activeFundPct = Percent -Ready $fundsWithPortfolio -Total $funds.Count
$coInvestableStartups = @($includeStartups | Where-Object {
    $id = $_.id
    @($includeInvestmentEdges | Where-Object { $_.target -eq $id }).Count -ge 2
}).Count
$coInvestablePct = Percent -Ready $coInvestableStartups -Total $includeStartups.Count
$topFundEdges = @($fundStats | Sort-Object portfolio_include -Descending | Select-Object -First 1)
$topFundSharePct = if ($includeInvestmentEdges.Count -and $topFundEdges.Count) { [Math]::Round(($topFundEdges[0].portfolio_include / [double]$includeInvestmentEdges.Count) * 100, 1) } else { 0 }
$concentrationHealthPct = [Math]::Max(0, [Math]::Round(100 - $topFundSharePct, 1))
$overallReadiness = [Math]::Round(($coveragePct * 0.28) + ($publicEdgePct * 0.23) + ($highConfidencePct * 0.17) + ($activeFundPct * 0.12) + ($coInvestablePct * 0.10) + ($concentrationHealthPct * 0.10), 1)

$singleStartupGaps = @($capitalComponents | Where-Object { $_.nodes -eq 1 -and $_.startups -eq 1 -and $_.funds -eq 0 -and $_.allocators -eq 0 })
$fundOnlySidecars = @($capitalComponents | Where-Object { $_.startups -eq 0 -and ($_.funds -gt 0 -or $_.allocators -gt 0) })
$relevantFloatingComponents = @($capitalComponents | Select-Object -Skip 1 | Where-Object { $_.startups -gt 0 -and ($_.funds -gt 0 -or $_.allocators -gt 0) })

$summary = [ordered]@{
    generated_at = (Get-Date).ToString('s')
    capital_readiness_pct = $overallReadiness
    nodes_total = $nodes.Count
    funds_total = $funds.Count
    allocators_total = $allocators.Count
    include_startups_total = $includeStartups.Count
    include_with_capital = $includeWithCapital.Count
    include_without_capital = $includeWithoutCapital.Count
    capital_coverage_pct = $coveragePct
    investment_edges = $includeInvestmentEdges.Count
    public_investment_edges = $publicInvestmentEdges.Count
    public_edge_pct = $publicEdgePct
    specific_investment_edges = $specificEvidenceEdges.Count
    specific_edge_pct = $specificEdgePct
    announcement_investment_edges = $announcementEvidenceEdges.Count
    announcement_edge_pct = $announcementEdgePct
    high_confidence_edges = $highConfidenceEdges.Count
    high_confidence_edge_pct = $highConfidencePct
    active_funds = $fundsWithPortfolio
    active_fund_pct = $activeFundPct
    allocator_edges = $allocatorEdges.Count
    co_investable_startups = $coInvestableStartups
    co_investable_pct = $coInvestablePct
    top_fund_share_pct = $topFundSharePct
    connected_components = $capitalComponents.Count
    floating_components = $floatingComponents.Count
    largest_component_nodes = $largestComponentNodes
    floating_component_nodes = $floatingComponentNodes
    main_continent_share_pct = $mainContinentSharePct
    single_startup_gaps = $singleStartupGaps.Count
    fund_only_sidecars = $fundOnlySidecars.Count
    relevant_floating_components = $relevantFloatingComponents.Count
}

$progress = @(
    [pscustomobject]@{ dimension = 'Cobertura capital BIO'; pct = $coveragePct; ready = $includeWithCapital.Count; total = $includeStartups.Count; note = 'Startups include con al menos una arista de capital.' }
    [pscustomobject]@{ dimension = 'Evidencia publica de aristas'; pct = $publicEdgePct; ready = $publicInvestmentEdges.Count; total = $includeInvestmentEdges.Count; note = 'Aristas con URL publica auditable.' }
    [pscustomobject]@{ dimension = 'Evidencia especifica startup-fondo'; pct = $specificEdgePct; ready = $specificEvidenceEdges.Count; total = $includeInvestmentEdges.Count; note = 'Aristas donde la fuente parece respaldar la relacion, no solo el fondo.' }
    [pscustomobject]@{ dimension = 'Confianza alta de aristas'; pct = $highConfidencePct; ready = $highConfidenceEdges.Count; total = $includeInvestmentEdges.Count; note = 'Aristas con confidence >= 0.90.' }
    [pscustomobject]@{ dimension = 'Fondos activos'; pct = $activeFundPct; ready = $fundsWithPortfolio; total = $funds.Count; note = 'Fondos con portfolio BIO include mapeado.' }
    [pscustomobject]@{ dimension = 'Startups coinvertibles'; pct = $coInvestablePct; ready = $coInvestableStartups; total = $includeStartups.Count; note = 'Startups con 2+ inversores; clave para estructura fondo-fondo.' }
    [pscustomobject]@{ dimension = 'Continente principal'; pct = $mainContinentSharePct; ready = $largestComponentNodes; total = $connectivityNodeIds.Count; note = 'Startups BIO + fondos + allocators conectados en la mayor componente del grafo.' }
    [pscustomobject]@{ dimension = 'Islas relevantes pendientes'; pct = [Math]::Max(0, [Math]::Round(100 - ($relevantFloatingComponents.Count * 20), 1)); ready = [Math]::Max(0, 5 - $relevantFloatingComponents.Count); total = 5; note = 'Componentes con fondo + startups BIO que todavia no conectan al continente principal.' }
    [pscustomobject]@{ dimension = 'Menor dependencia de un hub'; pct = $concentrationHealthPct; ready = [Math]::Round(100 - $topFundSharePct, 1); total = 100; note = 'Penaliza si una sola cartera explica demasiado del grafo.' }
)

$payload = [ordered]@{
    summary = $summary
    progress = $progress
    theme_coverage = @($themeRows | Sort-Object @{ Expression = 'gaps'; Descending = $true }, @{ Expression = 'startups'; Descending = $true })
    country_coverage = @($countryRows | Sort-Object @{ Expression = 'gaps'; Descending = $true }, @{ Expression = 'startups'; Descending = $true })
    fund_quality = @($fundStats | Sort-Object @{ Expression = 'quality_score'; Descending = $true }, @{ Expression = 'portfolio_include'; Descending = $true } | Select-Object -First 40)
    fund_risk = @($fundStats | Where-Object { $_.portfolio_include -gt 0 } | Sort-Object source_coverage_pct, avg_confidence, @{ Expression = 'portfolio_include'; Descending = $true } | Select-Object -First 30)
    gap_queue = $gapQueue
    edge_upgrade_queue = $edgeUpgradeQueue
    fund_specific_evidence_queue = $fundSpecificEvidenceQueue
    evidence_ladder = $evidenceLadderRows
    capital_components = @($capitalComponents | Select-Object -First 20)
    edge_type_counts = $edgeTypeCounts
    source_tier_counts = $sourceTierCounts
    strategy = @(
        [pscustomobject]@{ step = '1. Cubrir gaps'; description = 'Priorizar themes con mas startups include sin capital y buscar fondos candidatos por cartera similar.' }
        [pscustomobject]@{ step = '2. Subir evidencia'; description = 'Reemplazar aristas canonical_internal por URL publica: portfolio page, press release o anuncio institucional.' }
        [pscustomobject]@{ step = '3. Mejorar estructura'; description = 'Buscar coinversiones y fondos medianos para reducir dependencia de hubs y revelar comunidades.' }
        [pscustomobject]@{ step = '4. Medir explicatividad'; description = 'Mirar cobertura por theme/pais, co-investable share y concentracion antes de tocar layout visual.' }
    )
}

$jsonOut = $payload | ConvertTo-Json -Depth 12
"window.CAPITAL_QUALITY_DATA = $jsonOut;" | Set-Content -LiteralPath $OutputJsPath -Encoding UTF8
Write-Output "Capital quality dashboard data built: $OutputJsPath"
Write-Output "Capital readiness: $overallReadiness%"
