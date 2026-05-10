param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack",
    [string]$OutputPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\matchmaking-data.js"
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

function Split-Tags {
    param([object]$Value)
    $text = Clean-Text $Value
    if (-not $text) { return @() }
    return @(
        $text -split ';' |
            ForEach-Object { Clean-Text $_ } |
            Where-Object { $_ } |
            ForEach-Object { Normalize-Key $_ }
    )
}

function Read-FundAnalytics {
    param([string]$Path)
    $raw = Get-Content -LiteralPath $Path -Raw
    $json = $raw -replace '^\s*window\.FUND_ANALYTICS_DATA\s*=\s*', ''
    $json = $json -replace ';\s*$', ''
    return $json | ConvertFrom-Json
}

function Get-Theme-Share {
    param([object]$Fund, [string]$Theme)
    $theme = Clean-Text $Theme
    if (-not $theme -or -not $Fund.theme_mix) { return 0.0 }
    $total = [Math]::Max(1, [int]$Fund.include_confirmed_count)
    foreach ($row in @($Fund.theme_mix)) {
        if ((Clean-Text $row.theme) -eq $theme) {
            return [double]$row.count / $total
        }
    }
    return 0.0
}

function Get-Country-Share {
    param([object]$Fund, [string]$Country)
    $country = Clean-Text $Country
    if (-not $country -or -not $Fund.country_mix) { return 0.0 }
    $total = [Math]::Max(1, [int]$Fund.include_confirmed_count)
    foreach ($row in @($Fund.country_mix)) {
        if ((Clean-Text $row.country) -eq $country) {
            return [double]$row.count / $total
        }
    }
    return 0.0
}

function Get-Startup-Tags {
    param([object]$Startup)
    $tags = New-Object System.Collections.Generic.HashSet[string]
    foreach ($field in @('bio_lens_tags', 'domain_tags', 'technology_tags', 'scale_tags')) {
        foreach ($tag in (Split-Tags $Startup.$field)) {
            [void]$tags.Add($tag)
        }
    }
    return $tags
}

function Get-Overlap-Count {
    param(
        [System.Collections.Generic.HashSet[string]]$Left,
        [System.Collections.Generic.HashSet[string]]$Right
    )
    if ($null -eq $Left -or $null -eq $Right) { return 0 }
    $count = 0
    foreach ($tag in $Left) {
        if ($Right.Contains($tag)) { $count += 1 }
    }
    return $count
}

function Score-Label {
    param([double]$Score)
    if ($Score -ge 78) { return 'very_high' }
    if ($Score -ge 62) { return 'high' }
    if ($Score -ge 46) { return 'medium' }
    return 'exploratory'
}

function Add-Reason {
    param(
        [System.Collections.Generic.List[object]]$Reasons,
        [string]$Kind,
        [string]$Text,
        [double]$Weight
    )
    if (-not (Clean-Text $Text)) { return }
    $Reasons.Add([PSCustomObject]@{
        kind = $Kind
        text = $Text
        weight = [Math]::Round($Weight, 1)
    })
}

$fundDataPath = Join-Path $Root 'pilot\fund-analytics-data.js'
if (-not (Test-Path -LiteralPath $fundDataPath)) {
    throw "Missing fund analytics data: $fundDataPath. Run scripts\build_fund_analytics_data.ps1 first."
}

$master = Import-Csv -LiteralPath (Join-Path $Root 'startup_master_dataset.csv')
$semanticRows = Import-Csv -LiteralPath (Join-Path $Root 'quality\semantic_single_level_assignments.csv')
$canonicalEdges = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_investment_edges.csv')
$canonicalEntities = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_entities.csv')
$fundPayload = Read-FundAnalytics -Path $fundDataPath
$funds = @($fundPayload.funds)

$semanticById = @{}
foreach ($row in $semanticRows) {
    $semanticById[[string]$row.startup_id] = $row
}

$startupById = @{}
$startupLookup = @{}
foreach ($row in $master) {
    $startupById[[string]$row.startup_id] = $row
    $startupLookup[(Normalize-Key ([string]$row.startup_id))] = [string]$row.startup_id
    $startupLookup[(Normalize-Key ([string]$row.startup_name))] = [string]$row.startup_id
}

$investorById = @{}
$investorLookup = @{}
foreach ($row in ($canonicalEntities | Where-Object { $_.entity_type -eq 'investor' })) {
    $investorById[[string]$row.entity_id] = $row
    $investorLookup[(Normalize-Key ([string]$row.entity_id))] = [string]$row.entity_id
    $investorLookup[(Normalize-Key ([string]$row.canonical_name))] = [string]$row.entity_id
}
foreach ($fund in $funds) {
    $investorLookup[(Normalize-Key ([string]$fund.investor_id))] = [string]$fund.investor_id
    $investorLookup[(Normalize-Key ([string]$fund.investor_name))] = [string]$fund.investor_id
}

$fundById = @{}
foreach ($fund in $funds) {
    $fundById[[string]$fund.investor_id] = $fund
}

$investorsByStartup = @{}
foreach ($edge in $canonicalEdges) {
    $startupId = if ($startupById.ContainsKey([string]$edge.startup_id)) {
        [string]$edge.startup_id
    } else {
        $startupLookup[(Normalize-Key ([string]$edge.startup_id))]
    }
    $investorId = if ($fundById.ContainsKey([string]$edge.investor_id)) {
        [string]$edge.investor_id
    } else {
        $investorLookup[(Normalize-Key ([string]$edge.investor_id))]
    }
    if (-not $startupId -or -not $investorId) { continue }
    if (-not $fundById.ContainsKey($investorId)) { continue }
    if (-not $investorsByStartup.ContainsKey($startupId)) {
        $investorsByStartup[$startupId] = New-Object System.Collections.Generic.HashSet[string]
    }
    [void]$investorsByStartup[$startupId].Add($investorId)
}

$startupProfiles = @{}
foreach ($row in $master) {
    $id = [string]$row.startup_id
    $semantic = if ($semanticById.ContainsKey($id)) { $semanticById[$id] } else { $null }
    $theme = if ($null -ne $semantic -and (Clean-Text $semantic.semantic_single_theme)) { Clean-Text $semantic.semantic_single_theme } else { Clean-Text $row.macro_theme }
    $tags = Get-Startup-Tags -Startup $row
    $startupProfiles[$id] = [PSCustomObject]@{
        startup_id = $id
        startup_name = Clean-Text $row.startup_name
        scope_decision = Clean-Text $row.scope_decision
        scope_status = Clean-Text $row.scope_status
        country = Clean-Text $row.structured_country
        theme = $theme
        semantic_confidence = if ($null -ne $semantic) { Clean-Text $semantic.semantic_single_confidence } else { '' }
        quality_score = To-Number $row.data_quality_score_10
        quality_band = Clean-Text $row.quality_band
        source_url = Clean-Text $row.source_url
        one_liner = Clean-Text $row.business_one_liner
        summary = Clean-Text $row.startup_summary_v1
        tags = $tags
    }
}

$fundTagProfiles = @{}
foreach ($fund in $funds) {
    $tags = New-Object System.Collections.Generic.HashSet[string]
    foreach ($startup in @($fund.startups)) {
        $sid = [string]$startup.startup_id
        if (-not $startupProfiles.ContainsKey($sid)) { continue }
        foreach ($tag in $startupProfiles[$sid].tags) {
            [void]$tags.Add($tag)
        }
    }
    $fundTagProfiles[[string]$fund.investor_id] = $tags
}

$startupRecommendations = New-Object System.Collections.Generic.List[object]
$eligibleStartups = @(
    $startupProfiles.Values |
        Where-Object { $_.scope_decision -eq 'include' -and $_.scope_status -eq 'confirmed' } |
        Sort-Object startup_name
)

foreach ($startup in $eligibleStartups) {
    $currentInvestorIds = if ($investorsByStartup.ContainsKey($startup.startup_id)) { @($investorsByStartup[$startup.startup_id]) } else { @() }
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($fund in $funds) {
        $fundId = [string]$fund.investor_id
        if ($currentInvestorIds -contains $fundId) { continue }
        if ([int]$fund.include_confirmed_count -lt 2) { continue }

        $themeShare = Get-Theme-Share -Fund $fund -Theme $startup.theme
        $countryShare = Get-Country-Share -Fund $fund -Country $startup.country
        $tagOverlap = Get-Overlap-Count -Left $startup.tags -Right $fundTagProfiles[$fundId]
        $sourceCoverage = [double]$fund.source_coverage_pct / 100.0
        $portfolioStrength = [Math]::Min(1.0, [double]$fund.include_confirmed_count / 25.0)
        $roleBoost = switch ([string]$fund.bio_role) {
            'anchor_bio_platform' { 1.0 }
            'diversified_bio_investor' { 0.82 }
            'specialized_bio_investor' { 0.76 }
            'emerging_bio_signal' { 0.58 }
            default { 0.35 }
        }

        $score = 0.0
        $score += 35.0 * [Math]::Min(1.0, $themeShare / 0.45)
        $score += 16.0 * [Math]::Min(1.0, $countryShare / 0.35)
        $score += 18.0 * [Math]::Min(1.0, [double]$tagOverlap / 4.0)
        $score += 14.0 * $portfolioStrength
        $score += 9.0 * $roleBoost
        $score += 8.0 * $sourceCoverage
        $score = [Math]::Min(100.0, $score)

        $reasons = New-Object System.Collections.Generic.List[object]
        if ($themeShare -gt 0) {
            Add-Reason -Reasons $reasons -Kind 'theme_fit' -Text ("{0:P0} de su cartera BIO confirmada esta en {1}" -f $themeShare, $startup.theme) -Weight (35.0 * [Math]::Min(1.0, $themeShare / 0.45))
        }
        if ($countryShare -gt 0) {
            Add-Reason -Reasons $reasons -Kind 'country_fit' -Text ("Tiene senal en {0}: {1:P0} de cartera confirmada" -f $startup.country, $countryShare) -Weight (16.0 * [Math]::Min(1.0, $countryShare / 0.35))
        }
        if ($tagOverlap -gt 0) {
            Add-Reason -Reasons $reasons -Kind 'tag_overlap' -Text ("Comparte {0} etiquetas BIO/tecnologia/dominio con la cartera" -f $tagOverlap) -Weight (18.0 * [Math]::Min(1.0, [double]$tagOverlap / 4.0))
        }
        Add-Reason -Reasons $reasons -Kind 'portfolio_depth' -Text ("{0} startups include+confirmed en cartera mapeada" -f $fund.include_confirmed_count) -Weight (14.0 * $portfolioStrength)
        if ($sourceCoverage -gt 0.7) {
            Add-Reason -Reasons $reasons -Kind 'evidence_quality' -Text ("Alta cobertura de fuente en cartera: {0}%" -f $fund.source_coverage_pct) -Weight (8.0 * $sourceCoverage)
        }

        $examples = @(
            @($fund.startups) |
                Where-Object { $_.scope_decision -eq 'include' -and $_.scope_status -eq 'confirmed' -and ((Clean-Text $_.semantic_single_theme) -eq $startup.theme -or (Clean-Text $_.macro_theme) -eq $startup.theme) } |
                Select-Object -First 4 |
                ForEach-Object {
                    [PSCustomObject]@{
                        startup_id = $_.startup_id
                        startup_name = $_.startup_name
                        theme = if (Clean-Text $_.semantic_single_theme) { Clean-Text $_.semantic_single_theme } else { Clean-Text $_.macro_theme }
                    }
                }
        )

        if ($score -ge 32) {
            $rows.Add([PSCustomObject]@{
                investor_id = $fundId
                investor_name = Clean-Text $fund.investor_name
                actor_label = Clean-Text $fund.actor_label
                bio_role = Clean-Text $fund.bio_role
                score = [Math]::Round($score, 1)
                score_label = Score-Label $score
                theme_share = [Math]::Round($themeShare, 3)
                country_share = [Math]::Round($countryShare, 3)
                tag_overlap = $tagOverlap
                source_coverage_pct = [double]$fund.source_coverage_pct
                portfolio_size = [int]$fund.portfolio_size
                include_confirmed_count = [int]$fund.include_confirmed_count
                dominant_theme = Clean-Text $fund.dominant_theme
                reasons = @($reasons | Sort-Object weight -Descending | Select-Object -First 4)
                comparable_startups = $examples
            })
        }
    }

    $topRows = @(
        $rows |
            Sort-Object @{ Expression = { [double]$_.score }; Descending = $true }, @{ Expression = { [string]$_.investor_name }; Descending = $false } |
            Select-Object -First 12
    )

    $startupRecommendations.Add([PSCustomObject]@{
        startup_id = $startup.startup_id
        startup_name = $startup.startup_name
        country = $startup.country
        theme = $startup.theme
        quality_score = [Math]::Round($startup.quality_score, 1)
        quality_band = $startup.quality_band
        source_url = $startup.source_url
        one_liner = $startup.one_liner
        current_investors = @(
            $currentInvestorIds |
                Where-Object { $fundById.ContainsKey($_) } |
                ForEach-Object {
                    [PSCustomObject]@{
                        investor_id = $_
                        investor_name = Clean-Text $fundById[$_].investor_name
                    }
                } |
                Sort-Object investor_name
        )
        recommendations = $topRows
    })
}

$fundRecommendations = New-Object System.Collections.Generic.List[object]
foreach ($fund in $funds) {
    if ([int]$fund.include_confirmed_count -lt 2) { continue }
    $fundId = [string]$fund.investor_id
    $portfolioIds = New-Object System.Collections.Generic.HashSet[string]
    foreach ($startup in @($fund.startups)) {
        [void]$portfolioIds.Add([string]$startup.startup_id)
    }

    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($startup in $eligibleStartups) {
        if ($portfolioIds.Contains($startup.startup_id)) { continue }

        $themeShare = Get-Theme-Share -Fund $fund -Theme $startup.theme
        $countryShare = Get-Country-Share -Fund $fund -Country $startup.country
        $tagOverlap = Get-Overlap-Count -Left $startup.tags -Right $fundTagProfiles[$fundId]
        $qualityBoost = [Math]::Min(1.0, [double]$startup.quality_score / 8.0)
        $sourceBoost = if ($startup.source_url) { 1.0 } else { 0.15 }

        $score = 0.0
        $score += 40.0 * [Math]::Min(1.0, $themeShare / 0.45)
        $score += 12.0 * [Math]::Min(1.0, $countryShare / 0.35)
        $score += 22.0 * [Math]::Min(1.0, [double]$tagOverlap / 4.0)
        $score += 16.0 * $qualityBoost
        $score += 10.0 * $sourceBoost
        $score = [Math]::Min(100.0, $score)

        if ($score -lt 36) { continue }

        $reasons = New-Object System.Collections.Generic.List[object]
        if ($themeShare -gt 0) {
            Add-Reason -Reasons $reasons -Kind 'theme_fit' -Text ("Encaja con {0:P0} de la cartera BIO confirmada del fondo" -f $themeShare) -Weight (40.0 * [Math]::Min(1.0, $themeShare / 0.45))
        }
        if ($countryShare -gt 0) {
            Add-Reason -Reasons $reasons -Kind 'country_fit' -Text ("Mismo pais con senal previa en cartera: {0}" -f $startup.country) -Weight (12.0 * [Math]::Min(1.0, $countryShare / 0.35))
        }
        if ($tagOverlap -gt 0) {
            Add-Reason -Reasons $reasons -Kind 'tag_overlap' -Text ("Comparte {0} etiquetas con la cartera actual" -f $tagOverlap) -Weight (22.0 * [Math]::Min(1.0, [double]$tagOverlap / 4.0))
        }
        Add-Reason -Reasons $reasons -Kind 'data_quality' -Text ("Calidad de datos {0}/10; fuente {1}" -f ([Math]::Round($startup.quality_score, 1)), $(if ($startup.source_url) { 'disponible' } else { 'pendiente' })) -Weight ((16.0 * $qualityBoost) + (10.0 * $sourceBoost))

        $examples = @(
            @($fund.startups) |
                Where-Object { $_.scope_decision -eq 'include' -and $_.scope_status -eq 'confirmed' -and ((Clean-Text $_.semantic_single_theme) -eq $startup.theme -or (Clean-Text $_.macro_theme) -eq $startup.theme) } |
                Select-Object -First 4 |
                ForEach-Object {
                    [PSCustomObject]@{
                        startup_id = $_.startup_id
                        startup_name = $_.startup_name
                    }
                }
        )

        $rows.Add([PSCustomObject]@{
            startup_id = $startup.startup_id
            startup_name = $startup.startup_name
            country = $startup.country
            theme = $startup.theme
            score = [Math]::Round($score, 1)
            score_label = Score-Label $score
            quality_score = [Math]::Round($startup.quality_score, 1)
            quality_band = $startup.quality_band
            source_url = $startup.source_url
            one_liner = $startup.one_liner
            reasons = @($reasons | Sort-Object weight -Descending | Select-Object -First 4)
            comparable_portfolio = $examples
        })
    }

    $fundRecommendations.Add([PSCustomObject]@{
        investor_id = $fundId
        investor_name = Clean-Text $fund.investor_name
        actor_label = Clean-Text $fund.actor_label
        bio_role = Clean-Text $fund.bio_role
        dominant_theme = Clean-Text $fund.dominant_theme
        include_confirmed_count = [int]$fund.include_confirmed_count
        source_coverage_pct = [double]$fund.source_coverage_pct
        recommendations = @(
            $rows |
                Sort-Object @{ Expression = { [double]$_.score }; Descending = $true }, @{ Expression = { [string]$_.startup_name }; Descending = $false } |
                Select-Object -First 24
        )
    })
}

$summary = [PSCustomObject]@{
    generated_at = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    startups_with_recommendations = @($startupRecommendations | Where-Object { @($_.recommendations).Count -gt 0 }).Count
    funds_with_recommendations = @($fundRecommendations | Where-Object { @($_.recommendations).Count -gt 0 }).Count
    eligible_startups = @($eligibleStartups).Count
    eligible_funds = @($funds | Where-Object { [int]$_.include_confirmed_count -ge 2 }).Count
    method = 'explainable_theme_country_tag_quality_graph_adjacency_v1'
}

$payload = [PSCustomObject]@{
    summary = $summary
    startup_recommendations = $startupRecommendations
    fund_recommendations = $fundRecommendations
}

$js = "window.MATCHMAKING_DATA = " + ($payload | ConvertTo-Json -Depth 12 -Compress) + ";"
Set-Content -LiteralPath $OutputPath -Value $js -Encoding UTF8

Write-Output "Matchmaking recommendations built: $OutputPath"
