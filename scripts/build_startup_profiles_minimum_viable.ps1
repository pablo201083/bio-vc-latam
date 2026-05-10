param(
    [string]$TaxonomyPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_taxonomy_assignments_v1.csv",
    [string]$CorpusSeedPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_corpus_seed.csv",
    [string]$ManualOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\manual_startup_taxonomy_overrides.csv",
    [string]$ManualProfileOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\manual_startup_profile_overrides.csv",
    [string]$AliasOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\manual_alias_overrides.csv",
    [string]$TrlSeedPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_trl_current_seed.csv",
    [string]$QualityScoresPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\startup_data_quality_scores.csv",
    [string]$OutputProfilesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_profiles_minimum_viable.csv",
    [string]$OutputQueuePath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_profiles_research_queue.csv"
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
    param([string]$Text)
    $value = Clean-Text $Text
    if (-not $value) { return '' }
    $value = $value.ToLowerInvariant()
    $value = $value.Replace([char]0x00B7, ' ')
    $value = [regex]::Replace($value, '[^a-z0-9]+', '')
    return $value
}

$script:MojibakeMarkers = @([char]0x00C3, [char]0x00C2, [char]0x00E2)

function Get-MojibakeScore {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return 0 }
    $score = 0
    foreach ($marker in $script:MojibakeMarkers) {
        $score += @($Text.ToCharArray() | Where-Object { $_ -eq $marker }).Count
    }
    return $score
}

function Repair-Mojibake {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return '' }

    $value = $Text
    $encodings = @(
        [System.Text.Encoding]::GetEncoding('ISO-8859-1'),
        [System.Text.Encoding]::GetEncoding(1252)
    )

    for ($i = 0; $i -lt 2; $i++) {
        $currentScore = Get-MojibakeScore $value
        if ($currentScore -eq 0) { break }

        foreach ($encoding in $encodings) {
            try {
                $candidate = [System.Text.Encoding]::UTF8.GetString($encoding.GetBytes($value))
                if ((Get-MojibakeScore $candidate) -lt $currentScore) {
                    $value = $candidate
                    break
                }
            } catch {}
        }
    }

    return $value
}

function Clean-Text {
    param([object]$Value)
    if ($null -eq $Value) { return '' }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return '' }
    if ($text.Trim().ToLowerInvariant() -eq 'nan') { return '' }
    return (Repair-Mojibake $text).Trim()
}

function Add-Lookup {
    param(
        [hashtable]$Table,
        [string]$Id,
        [string]$Name,
        [object]$Value,
        [hashtable]$AliasMap = $null
    )

    $keys = @((Normalize-Key $Id), (Normalize-Key $Name))
    if ($null -ne $AliasMap) {
        $nameKey = Normalize-Key $Name
        if ($nameKey -and $AliasMap.ContainsKey($nameKey)) {
            $keys += Normalize-Key ([string]$AliasMap[$nameKey])
        }
    }

    foreach ($key in ($keys | Where-Object { $_ } | Select-Object -Unique)) {
        $Table[$key] = $Value
    }
}

function Get-Lookup {
    param(
        [hashtable]$Table,
        [string]$Id,
        [string]$Name
    )

    foreach ($key in @((Normalize-Key $Id), (Normalize-Key $Name)) | Where-Object { $_ }) {
        if ($Table.ContainsKey($key)) {
            return $Table[$key]
        }
    }
    return $null
}

function To-TitleCase {
    param([string]$Text)
    $value = Clean-Text $Text
    if (-not $value) { return '' }
    return ($value -replace '[_-]+', ' ')
}

function Get-RowValue {
    param(
        [object]$Row,
        [string]$PropertyName
    )

    if ($null -eq $Row) { return '' }
    $property = $Row.PSObject.Properties[$PropertyName]
    if ($null -eq $property) { return '' }
    return Clean-Text $property.Value
}

function Get-MaterialitySignal {
    param(
        [string]$ScopeDecision,
        [string]$MacroTheme
    )

    if ($ScopeDecision -eq 'exclude') { return 'low' }
    if ($MacroTheme -match 'climate|materials|ag biologicals|biomanufacturing|food biotech|therapeutics|precision agriculture|diagnostics') { return 'high' }
    if ($ScopeDecision -eq 'review') { return 'medium' }
    return 'medium'
}

function Get-ScopeNote {
    param(
        [string]$ScopeDecision,
        [string]$ScopeReason,
        [string]$MacroTheme
    )

    switch ($ScopeDecision) {
        'include' { return "Entra en tesis por $MacroTheme." }
        'exclude' { return "Queda afuera por $ScopeReason." }
        'review' { return "Permanece en revision por $ScopeReason." }
        default { return "Scope todavia no estabilizado." }
    }
}

function Build-ProvisionalOneLiner {
    param(
        [string]$MarketLabel,
        [string]$IndustryDestination,
        [string]$MacroTheme,
        [string]$ScopeDecision
    )

    $label = Clean-Text $MarketLabel
    $industry = Clean-Text $IndustryDestination
    $macro = Clean-Text $MacroTheme

    if (-not $label) {
        $label = if ($macro) { $macro } else { 'startup' }
    }

    if ($industry) {
        return ("{0} para {1}." -f $label, $industry)
    }

    if ($ScopeDecision -eq 'exclude') {
        return ("Empresa o plataforma de {0}." -f $label)
    }

    return ("Startup enfocada en {0}." -f $label)
}

if (-not (Test-Path -LiteralPath $TaxonomyPath)) {
    throw "Missing taxonomy file: $TaxonomyPath"
}

$taxonomyRows = Import-Csv -LiteralPath $TaxonomyPath
$corpusRows = if (Test-Path -LiteralPath $CorpusSeedPath) { Import-Csv -LiteralPath $CorpusSeedPath } else { @() }
$overrideRows = if (Test-Path -LiteralPath $ManualOverridesPath) { Import-Csv -LiteralPath $ManualOverridesPath } else { @() }
$manualProfileRows = if (Test-Path -LiteralPath $ManualProfileOverridesPath) { Import-Csv -LiteralPath $ManualProfileOverridesPath } else { @() }
$aliasRows = if (Test-Path -LiteralPath $AliasOverridesPath) { Import-Csv -LiteralPath $AliasOverridesPath } else { @() }
$trlRows = if (Test-Path -LiteralPath $TrlSeedPath) { Import-Csv -LiteralPath $TrlSeedPath } else { @() }
$qualityRows = if (Test-Path -LiteralPath $QualityScoresPath) { Import-Csv -LiteralPath $QualityScoresPath } else { @() }

$aliasMap = @{}
foreach ($row in $aliasRows) {
    $aliasName = Clean-Text $row.alias_name
    $canonicalName = Clean-Text $row.canonical_name
    if ($aliasName -and $canonicalName) {
        $aliasMap[(Normalize-Key $aliasName)] = $canonicalName
    }
}

$corpusByKey = @{}
foreach ($row in $corpusRows) {
    Add-Lookup -Table $corpusByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -Value $row -AliasMap $aliasMap
}

$overrideByKey = @{}
foreach ($row in $overrideRows) {
    Add-Lookup -Table $overrideByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -Value $row -AliasMap $aliasMap
}

$manualProfileByKey = @{}
foreach ($row in $manualProfileRows) {
    Add-Lookup -Table $manualProfileByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -Value $row -AliasMap $aliasMap
}

$trlByKey = @{}
foreach ($row in $trlRows) {
    Add-Lookup -Table $trlByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -Value $row -AliasMap $aliasMap
}

$qualityByKey = @{}
foreach ($row in $qualityRows) {
    Add-Lookup -Table $qualityByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -Value $row -AliasMap $aliasMap
}

$profiles = foreach ($row in $taxonomyRows) {
    $corpus = Get-Lookup -Table $corpusByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name)
    $override = Get-Lookup -Table $overrideByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name)
    $manualProfile = Get-Lookup -Table $manualProfileByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name)
    $trl = Get-Lookup -Table $trlByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name)
    $quality = Get-Lookup -Table $qualityByKey -Id ([string]$row.startup_id) -Name ([string]$row.startup_name)

    $startupSummary = ''
    $businessOneLiner = ''
    $problemAddressed = Clean-Text $row.transition_function
    $technicalApproach = Clean-Text $row.technical_stack
    $industryDestination = Clean-Text $row.industry_destination
    $materialitySignal = Get-MaterialitySignal -ScopeDecision (Clean-Text $row.scope_decision) -MacroTheme (Clean-Text $row.macro_theme)
    $scopeNote = Get-ScopeNote -ScopeDecision (Clean-Text $row.scope_decision) -ScopeReason (Clean-Text $row.scope_reason) -MacroTheme (Clean-Text $row.macro_theme)
    $sourceUrl = ''
    $sourceType = ''
    $sourceDate = ''
    $evidenceExcerpt = ''
    $summaryConfidence = 'low'
    $reviewStatus = 'needs_research'
    $lastReviewedAt = (Get-Date).ToString('yyyy-MM-dd')

    if ($null -ne $manualProfile) {
        $startupSummary = Get-RowValue -Row $manualProfile -PropertyName 'startup_summary_v1'
        $businessOneLiner = Get-RowValue -Row $manualProfile -PropertyName 'business_one_liner'
        $manualProblemAddressed = Get-RowValue -Row $manualProfile -PropertyName 'problem_addressed'
        $manualTechnicalApproach = Get-RowValue -Row $manualProfile -PropertyName 'technical_approach'
        $manualIndustryDestination = Get-RowValue -Row $manualProfile -PropertyName 'industry_destination'
        $manualMaterialitySignal = Get-RowValue -Row $manualProfile -PropertyName 'materiality_signal'
        $manualScopeNote = Get-RowValue -Row $manualProfile -PropertyName 'thesis_scope_note'
        $sourceUrl = Get-RowValue -Row $manualProfile -PropertyName 'source_url'
        $sourceType = Get-RowValue -Row $manualProfile -PropertyName 'source_type'
        $sourceDate = Get-RowValue -Row $manualProfile -PropertyName 'source_date'
        $evidenceExcerpt = Get-RowValue -Row $manualProfile -PropertyName 'evidence_excerpt'
        $manualSummaryConfidence = Get-RowValue -Row $manualProfile -PropertyName 'summary_confidence'
        $manualReviewStatus = Get-RowValue -Row $manualProfile -PropertyName 'review_status'
        $manualLastReviewedAt = Get-RowValue -Row $manualProfile -PropertyName 'last_reviewed_at'

        if ($manualProblemAddressed) { $problemAddressed = $manualProblemAddressed }
        if ($manualTechnicalApproach) { $technicalApproach = $manualTechnicalApproach }
        if ($manualIndustryDestination) { $industryDestination = $manualIndustryDestination }
        if ($manualMaterialitySignal) { $materialitySignal = $manualMaterialitySignal }
        if ($manualScopeNote) { $scopeNote = $manualScopeNote }
        $summaryConfidence = if ($manualSummaryConfidence) { $manualSummaryConfidence } else { 'high' }
        $reviewStatus = if ($manualReviewStatus) { $manualReviewStatus } else { 'reviewed' }
        if ($manualLastReviewedAt) { $lastReviewedAt = $manualLastReviewedAt }
    } elseif ($null -ne $corpus) {
        $businessOneLiner = Clean-Text $corpus.text_clean
        $sourceUrl = Clean-Text $corpus.source_url
        $sourceType = Clean-Text $corpus.source_type
        $sourceDate = Clean-Text $corpus.source_date
        $evidenceExcerpt = Clean-Text $corpus.text_clean
        $summaryConfidence = 'medium'
        $reviewStatus = 'seeded'
    } elseif ($null -ne $override) {
        $businessOneLiner = ("{0} para {1}." -f (To-TitleCase $override.market_label), (Clean-Text $override.industry_destination))
        $sourceType = 'portfolio_or_official_override'
        $sourceDate = (Get-Date).ToString('yyyy-MM-dd')
        $evidenceExcerpt = Clean-Text $override.notes
        $summaryConfidence = 'medium'
        $reviewStatus = 'seeded'
    } else {
        $businessOneLiner = ''
    }

    $trlClause = ''
    if ($null -ne $trl) {
        $trlValue = Clean-Text $trl.trl_current
        if ($trlValue) {
            $trlClause = " TRL actual inferido: $trlValue."
            if (-not $sourceUrl) {
                $sourceUrl = Clean-Text $trl.trl_current_source_url
                $sourceType = 'trl_seed'
                $sourceDate = Clean-Text $trl.trl_current_last_checked
            }
            if ($summaryConfidence -eq 'low') {
                $summaryConfidence = 'medium'
            }
            if ($reviewStatus -eq 'needs_research') { $reviewStatus = 'seeded' }
        }
    }

    if (-not $startupSummary -and $businessOneLiner) {
        $startupSummary = "$businessOneLiner $scopeNote$trlClause".Trim()
    }

    if (-not $startupSummary) {
        $businessOneLiner = Build-ProvisionalOneLiner -MarketLabel (Clean-Text $row.market_label) -IndustryDestination $industryDestination -MacroTheme (Clean-Text $row.macro_theme) -ScopeDecision (Clean-Text $row.scope_decision)
        $startupSummary = "$businessOneLiner $scopeNote$trlClause".Trim()
        if (-not $sourceType) { $sourceType = 'taxonomy_stub' }
        if (-not $sourceDate) { $sourceDate = (Get-Date).ToString('yyyy-MM-dd') }
        if (-not $evidenceExcerpt) {
            $evidenceExcerpt = "Resumen provisional generado desde taxonomia, scope y atributos estructurados."
        }
        if ($summaryConfidence -eq 'low') {
            $summaryConfidence = 'low'
        }
        if ($reviewStatus -eq 'needs_research') {
            $reviewStatus = 'taxonomy_stub'
        }
    }

    $qualityBand = if ($null -ne $quality) { Clean-Text $quality.quality_band } else { '' }
    if ($qualityBand -eq 'high') {
        $summaryConfidence = 'high'
    } elseif ($qualityBand -eq 'poor' -and -not $businessOneLiner) {
        $summaryConfidence = 'low'
    }

    [PSCustomObject]@{
        startup_id = [string]$row.startup_id
        startup_name = Clean-Text $row.startup_name
        startup_summary_v1 = $startupSummary
        business_one_liner = $businessOneLiner
        problem_addressed = $problemAddressed
        technical_approach = $technicalApproach
        industry_destination = $industryDestination
        materiality_signal = $materialitySignal
        thesis_scope_note = $scopeNote
        source_url = $sourceUrl
        source_type = $sourceType
        source_date = $sourceDate
        evidence_excerpt = $evidenceExcerpt
        summary_confidence = $summaryConfidence
        last_reviewed_at = $lastReviewedAt
        review_status = $reviewStatus
    }
}

$profilesByKey = @{}
foreach ($profile in @($profiles)) {
    Add-Lookup -Table $profilesByKey -Id ([string]$profile.startup_id) -Name ([string]$profile.startup_name) -Value $profile -AliasMap $aliasMap
}

foreach ($manualProfile in $manualProfileRows) {
    $fallbackProfile = Get-Lookup -Table $profilesByKey -Id ([string]$manualProfile.startup_id) -Name ([string]$manualProfile.startup_name)
    $mergedProfile = [PSCustomObject]@{
        startup_id = if ((Get-RowValue -Row $manualProfile -PropertyName 'startup_id')) { Get-RowValue -Row $manualProfile -PropertyName 'startup_id' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'startup_id' }
        startup_name = if ((Get-RowValue -Row $manualProfile -PropertyName 'startup_name')) { Get-RowValue -Row $manualProfile -PropertyName 'startup_name' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'startup_name' }
        startup_summary_v1 = if ((Get-RowValue -Row $manualProfile -PropertyName 'startup_summary_v1')) { Get-RowValue -Row $manualProfile -PropertyName 'startup_summary_v1' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'startup_summary_v1' }
        business_one_liner = if ((Get-RowValue -Row $manualProfile -PropertyName 'business_one_liner')) { Get-RowValue -Row $manualProfile -PropertyName 'business_one_liner' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'business_one_liner' }
        problem_addressed = if ((Get-RowValue -Row $manualProfile -PropertyName 'problem_addressed')) { Get-RowValue -Row $manualProfile -PropertyName 'problem_addressed' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'problem_addressed' }
        technical_approach = if ((Get-RowValue -Row $manualProfile -PropertyName 'technical_approach')) { Get-RowValue -Row $manualProfile -PropertyName 'technical_approach' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'technical_approach' }
        industry_destination = if ((Get-RowValue -Row $manualProfile -PropertyName 'industry_destination')) { Get-RowValue -Row $manualProfile -PropertyName 'industry_destination' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'industry_destination' }
        materiality_signal = if ((Get-RowValue -Row $manualProfile -PropertyName 'materiality_signal')) { Get-RowValue -Row $manualProfile -PropertyName 'materiality_signal' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'materiality_signal' }
        thesis_scope_note = if ((Get-RowValue -Row $manualProfile -PropertyName 'thesis_scope_note')) { Get-RowValue -Row $manualProfile -PropertyName 'thesis_scope_note' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'thesis_scope_note' }
        source_url = if ((Get-RowValue -Row $manualProfile -PropertyName 'source_url')) { Get-RowValue -Row $manualProfile -PropertyName 'source_url' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'source_url' }
        source_type = if ((Get-RowValue -Row $manualProfile -PropertyName 'source_type')) { Get-RowValue -Row $manualProfile -PropertyName 'source_type' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'source_type' }
        source_date = if ((Get-RowValue -Row $manualProfile -PropertyName 'source_date')) { Get-RowValue -Row $manualProfile -PropertyName 'source_date' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'source_date' }
        evidence_excerpt = if ((Get-RowValue -Row $manualProfile -PropertyName 'evidence_excerpt')) { Get-RowValue -Row $manualProfile -PropertyName 'evidence_excerpt' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'evidence_excerpt' }
        summary_confidence = if ((Get-RowValue -Row $manualProfile -PropertyName 'summary_confidence')) { Get-RowValue -Row $manualProfile -PropertyName 'summary_confidence' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'summary_confidence' }
        last_reviewed_at = if ((Get-RowValue -Row $manualProfile -PropertyName 'last_reviewed_at')) { Get-RowValue -Row $manualProfile -PropertyName 'last_reviewed_at' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'last_reviewed_at' }
        review_status = if ((Get-RowValue -Row $manualProfile -PropertyName 'review_status')) { Get-RowValue -Row $manualProfile -PropertyName 'review_status' } else { Get-RowValue -Row $fallbackProfile -PropertyName 'review_status' }
    }
    Add-Lookup -Table $profilesByKey -Id ([string]$mergedProfile.startup_id) -Name ([string]$mergedProfile.startup_name) -Value $mergedProfile -AliasMap $aliasMap
}

$profiles = @($profilesByKey.Values | Sort-Object startup_name -Unique)
$profiles | Export-Csv -LiteralPath $OutputProfilesPath -NoTypeInformation -Encoding UTF8

$queue = @(
    foreach ($profile in $profiles) {
        $taxonomy = Get-Lookup -Table $qualityByKey -Id ([string]$profile.startup_id) -Name ([string]$profile.startup_name)
        [PSCustomObject]@{
            startup_id = $profile.startup_id
            startup_name = $profile.startup_name
            scope_decision = if ($null -ne $taxonomy) { Clean-Text $taxonomy.scope_decision } else { '' }
            quality_band = if ($null -ne $taxonomy) { Clean-Text $taxonomy.quality_band } else { '' }
            research_priority = if ($null -ne $taxonomy) { Clean-Text $taxonomy.research_priority } else { '' }
            has_summary = [bool](Clean-Text $profile.startup_summary_v1)
            review_status = $profile.review_status
            source_type = $profile.source_type
        }
    }
) | Where-Object {
    ($_.scope_decision -eq 'include' -and $_.review_status -ne 'reviewed') -or -not $_.has_summary
} | Sort-Object @{ Expression = 'research_priority'; Descending = $true }, startup_name

$queue | Export-Csv -LiteralPath $OutputQueuePath -NoTypeInformation -Encoding UTF8

Write-Output "Startup profiles minimum viable built:"
Write-Output "  Profiles: $OutputProfilesPath"
Write-Output "  Queue: $OutputQueuePath"

