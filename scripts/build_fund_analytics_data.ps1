param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack",
    [string]$OutputPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\fund-analytics-data.js",
    [string]$CapitalAllocatorEdgesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\capital_allocator_edges.csv",
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
    param([string]$Value)
    $text = Clean-Text $Value
    if (-not $text) { return '' }
    $decomposed = $text.Normalize([Text.NormalizationForm]::FormD)
    $builder = New-Object System.Text.StringBuilder
    foreach ($char in $decomposed.ToCharArray()) {
        $category = [Globalization.CharUnicodeInfo]::GetUnicodeCategory($char)
        if ($category -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            [void]$builder.Append($char)
        }
    }
    return (($builder.ToString().ToLowerInvariant()) -replace '[^a-z0-9]+', '-').Trim('-')
}

function To-Number {
    param([object]$Value)
    $result = 0.0
    [void][double]::TryParse((Clean-Text $Value), [ref]$result)
    return $result
}

function Classify-CapitalActor {
    param(
        [object]$Investor,
        [int]$PortfolioSize,
        [int]$IncludeConfirmedCount,
        [bool]$HasCapitalBackers
    )

    $name = (Clean-Text $Investor.canonical_name).ToLowerInvariant()
    $source = (Clean-Text $Investor.source_presence).ToLowerInvariant()
    $flags = (Clean-Text $Investor.quality_flags).ToLowerInvariant()

    if ($flags -match 'fund_of_funds|allocator|lp' -or $name -match 'idb|bid|jica|svb|fund of funds|fondo de fondos') {
        return [PSCustomObject]@{ actor_type = 'allocator_or_lp'; actor_label = 'Allocator / LP'; actor_rank = 5 }
    }
    if ($name -match 'university|universidad|draper university|litoral|cites|fundacion|foundation|institut|research|consortium') {
        return [PSCustomObject]@{ actor_type = 'research_builder_or_accelerator'; actor_label = 'Builder / accelerator / research'; actor_rank = 3 }
    }
    if ($name -match 'eatable|ganesha|gridx|sf500|indiebio|sosv|brinc|accelerator|aceleradora|venture studio|company builder|builder') {
        return [PSCustomObject]@{ actor_type = 'company_builder_or_accelerator'; actor_label = 'Company builder / accelerator'; actor_rank = 2 }
    }
    if ($name -match 'bago|insud|corporate|grupo|company|international|conservation|happiness|duhau|familia|flia') {
        return [PSCustomObject]@{ actor_type = 'corporate_or_strategic'; actor_label = 'Corporate / strategic'; actor_rank = 4 }
    }
    if ($name -match 'venture debt|partners for growth|debt|lending') {
        return [PSCustomObject]@{ actor_type = 'venture_debt_or_growth'; actor_label = 'Venture debt / growth'; actor_rank = 6 }
    }
    if ($source -match 'manual_external|external_fund_map_delta|nodes_csv|graphml' -or $PortfolioSize -gt 0 -or $HasCapitalBackers) {
        return [PSCustomObject]@{ actor_type = 'vc_or_investor'; actor_label = 'VC / investor'; actor_rank = 1 }
    }

    return [PSCustomObject]@{ actor_type = 'capital_actor_review'; actor_label = 'Capital actor review'; actor_rank = 7 }
}

function Classify-FundBioRole {
    param([int]$IncludeConfirmedCount, [int]$PortfolioSize, [int]$UniqueThemes, [double]$Concentration)
    if ($IncludeConfirmedCount -ge 25) { return 'anchor_bio_platform' }
    if ($IncludeConfirmedCount -ge 10 -and $UniqueThemes -ge 4) { return 'diversified_bio_investor' }
    if ($IncludeConfirmedCount -ge 6 -and $Concentration -ge 0.45) { return 'specialized_bio_investor' }
    if ($IncludeConfirmedCount -ge 3) { return 'emerging_bio_signal' }
    if ($PortfolioSize -gt 0) { return 'peripheral_or_discovery_signal' }
    return 'capital_context_only'
}

$canonicalEntities = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_entities.csv')
$canonicalAliases = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_aliases.csv')
$canonicalEdges = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_investment_edges.csv')
$master = Import-Csv -LiteralPath (Join-Path $Root 'startup_master_dataset.csv')
$capitalAllocatorEdges = if (Test-Path -LiteralPath $CapitalAllocatorEdgesPath) { @(Import-Csv -LiteralPath $CapitalAllocatorEdgesPath) } else { @() }
$semanticRows = if (Test-Path -LiteralPath $SemanticAssignmentsPath) { Import-Csv -LiteralPath $SemanticAssignmentsPath } else { @() }

$semanticById = @{}
foreach ($row in $semanticRows) {
    $semanticById[[string]$row.startup_id] = $row
}

$investorsById = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)
$investorLookup = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
foreach ($row in ($canonicalEntities | Where-Object { $_.entity_type -eq 'investor' })) {
    $investorsById[[string]$row.entity_id] = $row
    $investorLookup[(Normalize-Key ([string]$row.entity_id))] = [string]$row.entity_id
    $investorLookup[(Normalize-Key ([string]$row.canonical_name))] = [string]$row.entity_id
}

$startupsById = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)
$startupLookup = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
foreach ($row in $master) {
    $startupsById[[string]$row.startup_id] = $row
    $startupLookup[(Normalize-Key ([string]$row.startup_id))] = [string]$row.startup_id
    $startupLookup[(Normalize-Key ([string]$row.startup_name))] = [string]$row.startup_id
}

foreach ($alias in $canonicalAliases) {
    $normalizedAlias = Normalize-Key ([string]$alias.alias)
    if (-not $normalizedAlias) { continue }

    if ($investorsById.ContainsKey([string]$alias.entity_id)) {
        $investorLookup[$normalizedAlias] = [string]$alias.entity_id
    }
    if ($startupsById.ContainsKey([string]$alias.entity_id)) {
        $startupLookup[$normalizedAlias] = [string]$alias.entity_id
    }
}

$capitalByFund = @{}
$capitalByAllocator = @{}
foreach ($edge in $capitalAllocatorEdges) {
    $targetFundId = Clean-Text $edge.target_fund_id
    if (-not $targetFundId) { continue }
    $allocatorId = Clean-Text $edge.allocator_id
    $amount = To-Number $edge.amount_usd
    $edgeRow = [PSCustomObject]@{
        allocator_id = $allocatorId
        allocator_name = Clean-Text $edge.allocator_name
        allocator_type = Clean-Text $edge.allocator_type
        target_fund_id = $targetFundId
        target_fund_name = Clean-Text $edge.target_fund_name
        target_vehicle = Clean-Text $edge.target_vehicle
        relation_type = Clean-Text $edge.relation_type
        amount_usd = if ($amount -gt 0) { [int64]$amount } else { 0 }
        year = Clean-Text $edge.year
        sector_lens = Clean-Text $edge.sector_lens
        region_lens = Clean-Text $edge.region_lens
        source_url = Clean-Text $edge.source_url
        evidence_note = Clean-Text $edge.evidence_note
        confidence = Clean-Text $edge.confidence
    }

    if (-not $capitalByFund.ContainsKey($targetFundId)) {
        $capitalByFund[$targetFundId] = New-Object System.Collections.Generic.List[object]
    }
    $capitalByFund[$targetFundId].Add($edgeRow)

    if (-not $capitalByAllocator.ContainsKey($allocatorId)) {
        $capitalByAllocator[$allocatorId] = New-Object System.Collections.Generic.List[object]
    }
    $capitalByAllocator[$allocatorId].Add($edgeRow)
}

$portfolioByInvestor = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)
$investorEdgeCounts = New-Object 'System.Collections.Generic.Dictionary[string,int]' ([System.StringComparer]::Ordinal)

foreach ($edge in $canonicalEdges) {
    $rawInvestorId = [string]$edge.investor_id
    $rawStartupId = [string]$edge.startup_id

    $investorId = if ($investorsById.ContainsKey($rawInvestorId)) {
        $rawInvestorId
    } else {
        $investorLookup[(Normalize-Key $rawInvestorId)]
    }

    $startupId = if ($startupsById.ContainsKey($rawStartupId)) {
        $rawStartupId
    } else {
        $startupLookup[(Normalize-Key $rawStartupId)]
    }

    if (-not $investorId -or -not $investorsById.ContainsKey($investorId)) { continue }
    if (-not $startupId -or -not $startupsById.ContainsKey($startupId)) { continue }

    if (-not $portfolioByInvestor.ContainsKey($investorId)) {
        $portfolioByInvestor[$investorId] = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)
    }
    $portfolioByInvestor[$investorId][$startupId] = $startupsById[$startupId]

    $current = if ($investorEdgeCounts.ContainsKey($investorId)) { [int]$investorEdgeCounts[$investorId] } else { 0 }
    $investorEdgeCounts[$investorId] = $current + 1
}

$fundRows = New-Object System.Collections.Generic.List[object]

foreach ($investorId in $investorsById.Keys) {
    $investor = $investorsById[$investorId]
    $hasMappedPortfolio = $portfolioByInvestor.ContainsKey($investorId)
    $hasCapitalBackers = $capitalByFund.ContainsKey([string]$investorId)
    if (-not $hasMappedPortfolio -and -not $hasCapitalBackers -and ([string]$investor.source_presence -notmatch 'manual_external')) {
        continue
    }

    $portfolioRows = if ($hasMappedPortfolio) { @($portfolioByInvestor[$investorId].Values) } else { @() }
    $portfolioStartups = @(
        $portfolioRows |
            Sort-Object @{ Expression = { [int](($_.scope_decision -eq 'include') -and ($_.scope_status -eq 'confirmed')) }; Descending = $true }, `
                        @{ Expression = { To-Number $_.data_quality_score_10 }; Descending = $true }, `
                        @{ Expression = { Clean-Text $_.startup_name }; Descending = $false } |
            ForEach-Object {
                [PSCustomObject]@{
                    startup_id = $_.startup_id
                    startup_name = $_.startup_name
                    scope_decision = $_.scope_decision
                    scope_status = $_.scope_status
                    macro_theme = $_.macro_theme
                    semantic_single_theme = if ($semanticById.ContainsKey([string]$_.startup_id)) { $semanticById[[string]$_.startup_id].semantic_single_theme } else { $_.macro_theme }
                    semantic_single_confidence = if ($semanticById.ContainsKey([string]$_.startup_id)) { $semanticById[[string]$_.startup_id].semantic_single_confidence } else { '' }
                    emergent_theme = $_.emergent_theme
                    structured_country = $_.structured_country
                    data_quality_score_10 = $_.data_quality_score_10
                    quality_band = $_.quality_band
                    review_status = $_.review_status
                    source_url = $_.source_url
                    source_type = $_.source_type
                    materiality_signal = $_.materiality_signal
                    bio_lens_tags = $_.bio_lens_tags
                    domain_tags = $_.domain_tags
                    technology_tags = $_.technology_tags
                    scale_tags = $_.scale_tags
                }
            }
    )

    $includeRows = @($portfolioRows | Where-Object { $_.scope_decision -eq 'include' })
    $includeConfirmedRows = @($portfolioRows | Where-Object { $_.scope_decision -eq 'include' -and $_.scope_status -eq 'confirmed' })
    $excludeRows = @($portfolioRows | Where-Object { $_.scope_decision -eq 'exclude' })
    $sourceBackedRows = @($portfolioRows | Where-Object { Clean-Text $_.source_url })
    $investorKey = [string]$investorId
    $capitalBackers = @()
    if ($capitalByFund.ContainsKey($investorKey)) {
        $capitalBackers = @($capitalByFund[$investorKey].ToArray())
    }

    $countryCounts = @{}
    $themeCounts = @{}
    foreach ($row in $includeConfirmedRows) {
        $country = Clean-Text $row.structured_country
        if (-not $country) { $country = 'n/d' }
        $countryCurrent = if ($countryCounts.ContainsKey($country)) { [int]$countryCounts[$country] } else { 0 }
        $countryCounts[$country] = $countryCurrent + 1

        $theme = if ($semanticById.ContainsKey([string]$row.startup_id)) { Clean-Text $semanticById[[string]$row.startup_id].semantic_single_theme } else { Clean-Text $row.macro_theme }
        if (-not $theme) { $theme = 'semantic edge cases' }
        $themeCurrent = if ($themeCounts.ContainsKey($theme)) { [int]$themeCounts[$theme] } else { 0 }
        $themeCounts[$theme] = $themeCurrent + 1
    }

    $countryMix = @(
        $countryCounts.GetEnumerator() |
            Sort-Object -Property @{ Expression = { [int]$_.Value }; Descending = $true }, @{ Expression = { [string]$_.Name }; Descending = $false } |
            ForEach-Object {
                [PSCustomObject]@{
                    country = $_.Name
                    count = $_.Value
                }
            }
    )

    $themeMix = @(
        $themeCounts.GetEnumerator() |
            Sort-Object -Property @{ Expression = { [int]$_.Value }; Descending = $true }, @{ Expression = { [string]$_.Name }; Descending = $false } |
            ForEach-Object {
                [PSCustomObject]@{
                    theme = $_.Name
                    count = $_.Value
                }
            }
    )

    $concentrationScore = 0.0
    $confirmedTotal = [Math]::Max(1, @($includeConfirmedRows).Count)
    $qualityAverage = @($portfolioRows | ForEach-Object { To-Number $_.data_quality_score_10 } | Measure-Object -Average)
    $qualityAverageValue = if (@($portfolioRows).Count -gt 0 -and $null -ne $qualityAverage.Average) { [double]$qualityAverage.Average } else { 0.0 }
    foreach ($entry in $themeMix) {
        $share = [double]$entry.count / $confirmedTotal
        $concentrationScore += $share * $share
    }
    $actor = Classify-CapitalActor -Investor $investor -PortfolioSize @($portfolioRows).Count -IncludeConfirmedCount @($includeConfirmedRows).Count -HasCapitalBackers $hasCapitalBackers
    $sourceCoveragePct = [Math]::Round((@($sourceBackedRows).Count / [Math]::Max(1, @($portfolioRows).Count)) * 100, 1)
    $bioRole = Classify-FundBioRole -IncludeConfirmedCount @($includeConfirmedRows).Count -PortfolioSize @($portfolioRows).Count -UniqueThemes @($themeMix).Count -Concentration $concentrationScore

    $fundRows.Add([PSCustomObject]@{
        investor_id = $investorId
        investor_name = $investor.canonical_name
        investor_slug = $investor.slug
        source_presence = $investor.source_presence
        actor_type = $actor.actor_type
        actor_label = $actor.actor_label
        actor_rank = $actor.actor_rank
        bio_role = $bioRole
        portfolio_size = @($portfolioRows).Count
        include_count = @($includeRows).Count
        include_confirmed_count = @($includeConfirmedRows).Count
        exclude_count = @($excludeRows).Count
        source_backed_count = @($sourceBackedRows).Count
        source_coverage_pct = $sourceCoveragePct
        average_quality = [Math]::Round($qualityAverageValue, 2)
        theme_concentration_hhi = [Math]::Round($concentrationScore, 3)
        unique_themes = @($themeMix).Count
        edge_count = if ($investorEdgeCounts.ContainsKey($investorId)) { [int]$investorEdgeCounts[$investorId] } else { 0 }
        dominant_theme = if (@($themeMix).Count -gt 0) { $themeMix[0].theme } else { '' }
        country_mix = $countryMix
        theme_mix = $themeMix
        startups = $portfolioStartups
        capital_backers = $capitalBackers
    })
}

$funds = @(
    $fundRows |
        Sort-Object @{ Expression = { [int]$_.actor_rank }; Descending = $false }, `
                    @{ Expression = { [int]$_.include_confirmed_count }; Descending = $true }, `
                    @{ Expression = { [int]$_.portfolio_size }; Descending = $true }, `
                    @{ Expression = { [string]$_.investor_name }; Descending = $false }
)

$overlapRows = New-Object System.Collections.Generic.List[object]
for ($i = 0; $i -lt $funds.Count; $i += 1) {
    for ($j = $i + 1; $j -lt $funds.Count; $j += 1) {
        $left = $funds[$i]
        $right = $funds[$j]
        $leftIds = @($left.startups | Where-Object { $_.scope_decision -eq 'include' -and $_.scope_status -eq 'confirmed' } | ForEach-Object { $_.startup_id })
        $rightIds = @($right.startups | Where-Object { $_.scope_decision -eq 'include' -and $_.scope_status -eq 'confirmed' } | ForEach-Object { $_.startup_id })
        if (-not $leftIds.Count -or -not $rightIds.Count) { continue }

        $leftSet = New-Object System.Collections.Generic.HashSet[string]
        $rightSet = New-Object System.Collections.Generic.HashSet[string]
        foreach ($id in $leftIds) { [void]$leftSet.Add([string]$id) }
        foreach ($id in $rightIds) { [void]$rightSet.Add([string]$id) }

        $shared = @($leftSet | Where-Object { $rightSet.Contains($_) })
        if (-not $shared.Count) { continue }

        $unionCount = ($leftSet.Count + $rightSet.Count - $shared.Count)
        $jaccard = if ($unionCount -gt 0) { [Math]::Round($shared.Count / $unionCount, 3) } else { 0.0 }

        $overlapRows.Add([PSCustomObject]@{
            left_investor_id = $left.investor_id
            left_investor_name = $left.investor_name
            right_investor_id = $right.investor_id
            right_investor_name = $right.investor_name
            shared_count = $shared.Count
            jaccard = $jaccard
            shared_startups = @($shared | ForEach-Object { $startupsById[$_] } | Sort-Object startup_name | Select-Object -First 12 startup_id, startup_name, macro_theme)
        })
    }
}

$topOverlaps = @(
    $overlapRows |
        Sort-Object @{ Expression = { [int]$_.shared_count }; Descending = $true }, `
                    @{ Expression = { [double]$_.jaccard }; Descending = $true }, `
                    @{ Expression = { [string]$_.left_investor_name }; Descending = $false } |
        Select-Object -First 40
)

$startupInvestorCounts = @{}
$startupInvestorNames = @{}
foreach ($fund in $funds) {
    foreach ($startup in ($fund.startups | Where-Object { $_.scope_decision -eq 'include' -and $_.scope_status -eq 'confirmed' })) {
        $sid = [string]$startup.startup_id
        if (-not $startupInvestorCounts.ContainsKey($sid)) { $startupInvestorCounts[$sid] = 0 }
        if (-not $startupInvestorNames.ContainsKey($sid)) { $startupInvestorNames[$sid] = New-Object System.Collections.Generic.List[string] }
        $startupInvestorCounts[$sid] = [int]$startupInvestorCounts[$sid] + 1
        $startupInvestorNames[$sid].Add([string]$fund.investor_name)
    }
}

$topStartups = @(
    $startupInvestorCounts.GetEnumerator() |
        Sort-Object -Property @{ Expression = { [int]$_.Value }; Descending = $true }, @{ Expression = { [string]$_.Name }; Descending = $false } |
        Select-Object -First 40 |
        ForEach-Object {
            $startup = $startupsById[[string]$_.Name]
            [PSCustomObject]@{
                startup_id = $startup.startup_id
                startup_name = $startup.startup_name
                investor_count = $_.Value
                macro_theme = $startup.macro_theme
                semantic_single_theme = if ($semanticById.ContainsKey([string]$startup.startup_id)) { $semanticById[[string]$startup.startup_id].semantic_single_theme } else { $startup.macro_theme }
                structured_country = $startup.structured_country
                source_url = $startup.source_url
                investors = @($startupInvestorNames[[string]$_.Name] | Sort-Object)
            }
        }
)

$themeTotals = @{}
foreach ($fund in $funds) {
    foreach ($item in $fund.theme_mix) {
        $themeKey = [string]$item.theme
        $themeTotalCurrent = if ($themeTotals.ContainsKey($themeKey)) { [int]$themeTotals[$themeKey] } else { 0 }
        $themeTotals[$themeKey] = $themeTotalCurrent + [int]$item.count
    }
}

$capitalAllocatorRows = @(
    $capitalByAllocator.GetEnumerator() |
        ForEach-Object {
            $edgesForAllocator = @($_.Value.ToArray())
            $allocatorAmountMeasure = @($edgesForAllocator | ForEach-Object { [double]$_.amount_usd } | Measure-Object -Sum)
            $allocatorAmount = if ($null -ne $allocatorAmountMeasure.Sum) { [double]$allocatorAmountMeasure.Sum } else { 0.0 }
            [PSCustomObject]@{
                allocator_id = $_.Key
                allocator_name = if ($edgesForAllocator.Count) { $edgesForAllocator[0].allocator_name } else { $_.Key }
                allocator_type = if ($edgesForAllocator.Count) { $edgesForAllocator[0].allocator_type } else { '' }
                fund_count = @($edgesForAllocator | Select-Object -ExpandProperty target_fund_id -Unique).Count
                disclosed_amount_usd = [int64]$allocatorAmount
                sector_lenses = @($edgesForAllocator | ForEach-Object { $_.sector_lens } | Where-Object { $_ } | Select-Object -Unique)
                fund_edges = @($edgesForAllocator | Sort-Object target_fund_name, year)
            }
        } |
        Sort-Object @{ Expression = { [int]$_.fund_count }; Descending = $true }, @{ Expression = { [double]$_.disclosed_amount_usd }; Descending = $true }, allocator_name
)

$disclosedAllocatorCapitalMeasure = @($capitalAllocatorEdges | ForEach-Object { To-Number $_.amount_usd } | Measure-Object -Sum)
$disclosedAllocatorCapital = if ($null -ne $disclosedAllocatorCapitalMeasure.Sum) { [double]$disclosedAllocatorCapitalMeasure.Sum } else { 0.0 }

$actorTypeTotals = @(
    $funds |
        Group-Object actor_type |
        Sort-Object @{ Expression = { [int]$_.Count }; Descending = $true }, @{ Expression = { [string]$_.Name }; Descending = $false } |
        ForEach-Object {
            $sample = $_.Group | Select-Object -First 1
            [PSCustomObject]@{
                actor_type = $_.Name
                actor_label = $sample.actor_label
                count = $_.Count
                include_confirmed_count = @($_.Group | ForEach-Object { [int]$_.include_confirmed_count } | Measure-Object -Sum).Sum
            }
        }
)

$bioRoleTotals = @(
    $funds |
        Group-Object bio_role |
        Sort-Object @{ Expression = { [int]$_.Count }; Descending = $true }, @{ Expression = { [string]$_.Name }; Descending = $false } |
        ForEach-Object {
            [PSCustomObject]@{
                bio_role = $_.Name
                count = $_.Count
                include_confirmed_count = @($_.Group | ForEach-Object { [int]$_.include_confirmed_count } | Measure-Object -Sum).Sum
            }
        }
)

$summary = [PSCustomObject]@{
    generated_at = (Get-Date).ToString('s')
    funds_total = @($funds).Count
    mapped_funds_total = @($funds | Where-Object { [int]$_.portfolio_size -gt 0 }).Count
    startups_mapped_total = @($master).Count
    startups_in_fund_portfolios = @($startupInvestorCounts.Keys).Count
    include_confirmed_total = @($master | Where-Object { $_.scope_decision -eq 'include' -and $_.scope_status -eq 'confirmed' }).Count
    average_confirmed_portfolio_size = if ($funds.Count) { [Math]::Round((@($funds | ForEach-Object { [double]$_.include_confirmed_count } | Measure-Object -Average).Average), 1) } else { 0 }
    top_fund_by_confirmed = if ($funds.Count) { $funds[0].investor_name } else { '' }
    anchor_bio_platforms = @($funds | Where-Object { $_.bio_role -eq 'anchor_bio_platform' }).Count
    vc_or_investor_total = @($funds | Where-Object { $_.actor_type -eq 'vc_or_investor' }).Count
    builders_total = @($funds | Where-Object { $_.actor_type -match 'builder|accelerator' }).Count
    average_source_coverage_pct = if ($funds.Count) { [Math]::Round((@($funds | ForEach-Object { [double]$_.source_coverage_pct } | Measure-Object -Average).Average), 1) } else { 0 }
    capital_allocators_total = @($capitalAllocatorRows).Count
    allocator_edges_total = @($capitalAllocatorEdges).Count
    disclosed_allocator_capital_usd = [int64]$disclosedAllocatorCapital
}

$payload = [PSCustomObject]@{
    summary = $summary
    funds = $funds
    top_overlaps = $topOverlaps
    top_startups = $topStartups
    capital_allocators = $capitalAllocatorRows
    capital_edges = $capitalAllocatorEdges
    actor_type_totals = $actorTypeTotals
    bio_role_totals = $bioRoleTotals
    theme_totals = @(
        $themeTotals.GetEnumerator() |
            Sort-Object -Property @{ Expression = { [int]$_.Value }; Descending = $true }, @{ Expression = { [string]$_.Name }; Descending = $false } |
            ForEach-Object {
                [PSCustomObject]@{
                    theme = $_.Name
                    count = $_.Value
                }
            }
    )
}

$js = "window.FUND_ANALYTICS_DATA = " + ($payload | ConvertTo-Json -Depth 8) + ";"
Set-Content -LiteralPath $OutputPath -Value $js -Encoding UTF8

Write-Output "Fund analytics data built: $OutputPath"
