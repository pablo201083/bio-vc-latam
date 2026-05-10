param(
    [string]$TaxonomyPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_taxonomy_assignments_v1.csv",
    [string]$QualityPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\startup_data_quality_scores.csv",
    [string]$ProfilesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_profiles_minimum_viable.csv",
    [string]$AliasOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\manual_alias_overrides.csv",
    [string]$OutputPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv"
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

function Add-RowToMaps {
    param(
        [hashtable]$ById,
        [hashtable]$ByName,
        [string]$Id,
        [string]$Name,
        [object]$Value,
        [hashtable]$AliasMap = @{}
    )

    $idKey = Normalize-Key $Id
    $nameKey = Normalize-Key $Name
    if ($idKey) { $ById[$idKey] = $Value }
    if ($nameKey) { $ByName[$nameKey] = $Value }
    if ($nameKey -and $AliasMap.ContainsKey($nameKey)) {
        $canonicalKey = Normalize-Key ([string]$AliasMap[$nameKey])
        if ($canonicalKey) { $ByName[$canonicalKey] = $Value }
    }
}

function Get-RowFromMaps {
    param(
        [hashtable]$ById,
        [hashtable]$ByName,
        [string]$Id,
        [string]$Name,
        [hashtable]$AliasMap = @{}
    )

    $idKey = Normalize-Key $Id
    $nameKey = Normalize-Key $Name
    if ($idKey -and $ById.ContainsKey($idKey)) {
        return $ById[$idKey]
    }
    if ($nameKey -and $ByName.ContainsKey($nameKey)) {
        return $ByName[$nameKey]
    }
    if ($nameKey -and $AliasMap.ContainsKey($nameKey)) {
        $canonicalKey = Normalize-Key ([string]$AliasMap[$nameKey])
        if ($canonicalKey -and $ByName.ContainsKey($canonicalKey)) {
            return $ByName[$canonicalKey]
        }
    }
    return $null
}

function Test-AnyPattern {
    param(
        [string]$Text,
        [string[]]$Patterns
    )
    if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
    foreach ($pattern in $Patterns) {
        if ($Text -match $pattern) { return $true }
    }
    return $false
}

function Join-Tags {
    param([string[]]$Tags)
    return @($Tags | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique) -join '; '
}

function Get-StrategicTags {
    param(
        [object]$Row,
        [object]$Quality,
        [object]$Profile
    )

    $parts = @(
        $Row.startup_name,
        $Row.macro_theme,
        $Row.emergent_theme,
        $Row.market_label,
        $Row.transition_function,
        $Row.technical_stack,
        $Row.industry_destination,
        $Row.structured_sector
    )
    if ($null -ne $Profile) {
        $parts += @(
            $Profile.business_one_liner,
            $Profile.evidence_excerpt
        )
        if ((Clean-Text $Row.scope_decision) -ne 'exclude') {
            $parts += @(
                $Row.scope_reason,
                $Row.thesis_fit,
                $Profile.startup_summary_v1,
                $Profile.materiality_signal,
                $Profile.thesis_scope_note
            )
        }
    }

    $text = (($parts | ForEach-Object { Clean-Text $_ }) -join ' ').ToLowerInvariant()
    $text = [regex]::Replace($text, '\b(no|not|sin|without)\b[^.]{0,80}\b(bio[- ]?based|biobased|biocentric|biocentrica|regenerative|regenerativa|planetary|materiality|materialidad)\b', ' ')

    $bioLens = @()
    $domain = @()
    $technology = @()
    $scale = @()

    if (Test-AnyPattern $text @('bio[- ]?based','biobased','biomass','biomaterial','biofabric','bio[- ]?ingredient','microbe','microbial','fermentation','enzyme','cell culture','synthetic biology','synbio','biomanufactur','bioindustrial','bioinput','biofertilizer','biostimulant')) {
        $bioLens += 'biobased'
    }
    if (Test-AnyPattern $text @('ecosystem','biodiversity','forest','wildfire','soil','crop','livestock','pollination','regenerative','nature','living system','sistemas vivos','sistema vivo','agroecosystem','agriculture','agricola','agropecuaria')) {
        $bioLens += 'biocentric'
    }
    if (Test-AnyPattern $text @('climate','carbon','water','waste','pollution','remediation','biodiversity','forest','soil','land use','resource efficiency','circular','planetary','fire','wildfire','methane','emissions')) {
        $bioLens += 'planetary-boundary'
    }
    if (Test-AnyPattern $text @('regenerative','regeneration','restoration','restore','soil health','resilience','pollination','restauracion','regenerativa')) {
        $bioLens += 'regenerative'
    }
    if (Test-AnyPattern $text @('circular','waste','residue','recycling','upcycling','valorization','plastic','scrap','byproduct')) {
        $bioLens += 'circular'
    }
    if (Test-AnyPattern $text @('diagnostic','clinical','therapy','therapeutic','medical','medtech','drug','pharma','gene therapy','cell therapy','regenerative medicine','health','biomarker')) {
        $bioLens += 'human-health-bio'
    }
    if (Test-AnyPattern $text @('biomanufactur','bioprocess','bioindustrial','industrial biotech','enzyme','fermentation','cell culture','bioreactor','synthetic biology','protein production')) {
        $bioLens += 'bio-enabled-industrial-transition'
    }

    if (Test-AnyPattern $text @('food','ingredient','protein','crop','livestock','farm','agri','agro','agtech','soil','input','irrigation','agriculture','agricola')) { $domain += 'agri-food' }
    if (Test-AnyPattern $text @('diagnostic','clinical','therapy','therapeutic','medical','medtech','drug','pharma','health','biomarker','regenerative medicine')) { $domain += 'human-health' }
    if (Test-AnyPattern $text @('biomaterial','bio[- ]?material','advanced materials','textile','polymer','packaging','construction material','cosmetic','leather','fabric','plastic')) { $domain += 'biomaterials' }
    if (Test-AnyPattern $text @('biomanufactur','bioprocess','bioreactor','cell culture','fermentation','lab automation','industrial biotech')) { $domain += 'biomanufacturing' }
    if (Test-AnyPattern $text @('climate','carbon','energy','water','waste','remediation','resource efficiency','emissions','methane','circular')) { $domain += 'climate-resource' }
    if (Test-AnyPattern $text @('biodiversity','nature','forest','wildfire','landscape','conservation','restoration','ecosystem')) { $domain += 'biodiversity-nature' }
    if (Test-AnyPattern $text @('enzyme','microbial production','industrial biotech','bioindustrial','bio[- ]?industry')) { $domain += 'industrial-biotech' }
    if (Test-AnyPattern $text @('diagnostic','medical device','medtech','clinical device','pathogen','biomarker')) { $domain += 'diagnostics-medtech' }
    if (Test-AnyPattern $text @('therapeutic','drug discovery','gene therapy','cell therapy','regenerative medicine','pharma','therapy')) { $domain += 'therapeutics-regenerative' }

    if (Test-AnyPattern $text @('\bai\b','artificial intelligence','machine learning','data','analytics','decision intelligence','software','saas','platform')) { $technology += 'ai-data' }
    if (Test-AnyPattern $text @('satellite','remote sensing','drone','geospatial','imaging','imagery','earth observation')) { $technology += 'remote-sensing' }
    if (Test-AnyPattern $text @('\biot\b','sensor','telemetry','connected device','smart tag')) { $technology += 'iot' }
    if (Test-AnyPattern $text @('synthetic biology','synbio','genetic engineering','engineered organism','genome engineering')) { $technology += 'synthetic-biology' }
    if (Test-AnyPattern $text @('fermentation','fermentacion','microbial production')) { $technology += 'fermentation' }
    if (Test-AnyPattern $text @('precision fermentation')) { $technology += 'precision-fermentation' }
    if (Test-AnyPattern $text @('biomanufactur','bioprocess','bioreactor','cell culture','scale[- ]?up','lab automation')) { $technology += 'biomanufacturing' }
    if (Test-AnyPattern $text @('biomaterial','bio[- ]?material','advanced materials','polymer','textile','packaging','construction material','biofabric','plastic')) { $technology += 'biomaterials' }
    if (Test-AnyPattern $text @('diagnostic','biomarker','pathogen detection','test kit','clinical test')) { $technology += 'diagnostics' }
    if (Test-AnyPattern $text @('therapeutic','drug discovery','gene therapy','cell therapy','regenerative medicine','pharma')) { $technology += 'therapeutics' }
    if (Test-AnyPattern $text @('bioinput','biofertilizer','biostimulant','biological control','crop protection','pollination','microbial input')) { $technology += 'bioinputs' }
    if (Test-AnyPattern $text @('enzyme','enzymatic')) { $technology += 'enzymes' }
    if (Test-AnyPattern $text @('carbon mrv','mrv','carbon accounting','carbon measurement','carbon credit')) { $technology += 'carbon-mrv' }
    if (Test-AnyPattern $text @('remediation','pollution','waste treatment','soil treatment','water treatment','fire prevention','wildfire prevention')) { $technology += 'remediation' }

    if (Test-AnyPattern $text @('molecular','\bgene\b','\bgenes\b','genetic','\bcell\b','\bcells\b','microbe','microbial','enzyme','synthetic biology','biomarker')) { $scale += 'molecular-scale' }
    if (Test-AnyPattern $text @('human','clinical','medical','patient','health','personalized medicine','nutrition','therapeutic')) { $scale += 'human-scale' }
    if (Test-AnyPattern $text @('ingredient','biomaterial','bio[- ]?material','advanced materials','\bproduct\b','device','textile','packaging','cosmetic','object','polymer','plastic')) { $scale += 'product-scale' }
    if (Test-AnyPattern $text @('industrial','factory','manufactur','bioprocess','bioreactor','supply chain','infrastructure','scale[- ]?up')) { $scale += 'industrial-scale' }
    if (Test-AnyPattern $text @('farm','crop','livestock','soil','agri','agro','irrigation','pollination','field')) { $scale += 'agroecosystem-scale' }
    if (Test-AnyPattern $text @('forest','wildfire','watershed','landscape','territory','city','urban','mine','land use','biodiversity')) { $scale += 'territorial-scale' }
    if (Test-AnyPattern $text @('climate','planetary','carbon','emissions','biodiversity','global','methane')) { $scale += 'planetary-scale' }

    return [PSCustomObject]@{
        bio_lens_tags = Join-Tags $bioLens
        domain_tags = Join-Tags $domain
        technology_tags = Join-Tags $technology
        scale_tags = Join-Tags $scale
    }
}

if (-not (Test-Path -LiteralPath $TaxonomyPath)) {
    throw "Missing taxonomy file: $TaxonomyPath"
}

$taxonomyRows = Import-Csv -LiteralPath $TaxonomyPath
$qualityRows = if (Test-Path -LiteralPath $QualityPath) { Import-Csv -LiteralPath $QualityPath } else { @() }
$profileRows = if (Test-Path -LiteralPath $ProfilesPath) { Import-Csv -LiteralPath $ProfilesPath } else { @() }
$aliasRows = if (Test-Path -LiteralPath $AliasOverridesPath) { Import-Csv -LiteralPath $AliasOverridesPath } else { @() }

$aliasMap = @{}
foreach ($row in $aliasRows) {
    $aliasName = Clean-Text $row.alias_name
    $canonicalName = Clean-Text $row.canonical_name
    if ($aliasName -and $canonicalName) {
        $aliasMap[(Normalize-Key $aliasName)] = $canonicalName
    }
}

$qualityById = @{}
$qualityByName = @{}
foreach ($row in $qualityRows) {
    Add-RowToMaps -ById $qualityById -ByName $qualityByName -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -Value $row -AliasMap $aliasMap
}

$profilesById = @{}
$profilesByName = @{}
foreach ($row in $profileRows) {
    Add-RowToMaps -ById $profilesById -ByName $profilesByName -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -Value $row -AliasMap $aliasMap
}

$masterRows = foreach ($row in $taxonomyRows) {
    $quality = Get-RowFromMaps -ById $qualityById -ByName $qualityByName -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -AliasMap $aliasMap
    $profile = Get-RowFromMaps -ById $profilesById -ByName $profilesByName -Id ([string]$row.startup_id) -Name ([string]$row.startup_name) -AliasMap $aliasMap
    $strategicTags = Get-StrategicTags -Row $row -Quality $quality -Profile $profile

    [PSCustomObject]@{
        startup_id = [string]$row.startup_id
        startup_name = Clean-Text $row.startup_name
        scope_decision = Clean-Text $row.scope_decision
        scope_status = if ($null -ne $profile -and -not [string]::IsNullOrWhiteSpace((Clean-Text $profile.source_url))) { 'confirmed' } else { 'provisional' }
        scope_basis = if ($null -ne $profile -and -not [string]::IsNullOrWhiteSpace((Clean-Text $profile.source_url))) { 'external_auditable_source' } else { 'internal_structured_inference' }
        scope_reason = Clean-Text $row.scope_reason
        macro_theme = Clean-Text $row.macro_theme
        emergent_theme = Clean-Text $row.emergent_theme
        market_label = Clean-Text $row.market_label
        transition_function = Clean-Text $row.transition_function
        technical_stack = Clean-Text $row.technical_stack
        industry_destination = Clean-Text $row.industry_destination
        thesis_fit = Clean-Text $row.thesis_fit
        assignment_method = Clean-Text $row.assignment_method
        taxonomy_confidence = Clean-Text $row.confidence
        structured_country = Clean-Text $row.structured_country
        structured_sector = Clean-Text $row.structured_sector
        trl_current = Clean-Text $row.trl_current
        trl_current_status = Clean-Text $row.trl_current_status
        valuation_tier = Clean-Text $row.valuation_tier
        data_quality_score_10 = if ($null -ne $quality) { Clean-Text $quality.data_quality_score_10 } else { '' }
        quality_band = if ($null -ne $quality) { Clean-Text $quality.quality_band } else { '' }
        research_priority = if ($null -ne $quality) { Clean-Text $quality.research_priority } else { '' }
        missing_signals = if ($null -ne $quality) { Clean-Text $quality.missing_signals } else { '' }
        startup_summary_v1 = if ($null -ne $profile) { Clean-Text $profile.startup_summary_v1 } else { '' }
        business_one_liner = if ($null -ne $profile) { Clean-Text $profile.business_one_liner } else { '' }
        materiality_signal = if ($null -ne $profile) { Clean-Text $profile.materiality_signal } else { '' }
        thesis_scope_note = if ($null -ne $profile) { Clean-Text $profile.thesis_scope_note } else { '' }
        source_url = if ($null -ne $profile) { Clean-Text $profile.source_url } else { '' }
        source_type = if ($null -ne $profile) { Clean-Text $profile.source_type } else { '' }
        source_date = if ($null -ne $profile) { Clean-Text $profile.source_date } else { '' }
        evidence_excerpt = if ($null -ne $profile) { Clean-Text $profile.evidence_excerpt } else { '' }
        summary_confidence = if ($null -ne $profile) { Clean-Text $profile.summary_confidence } else { '' }
        review_status = if ($null -ne $profile) { Clean-Text $profile.review_status } else { '' }
        last_reviewed_at = if ($null -ne $profile) { Clean-Text $profile.last_reviewed_at } else { '' }
        bio_lens_tags = $strategicTags.bio_lens_tags
        domain_tags = $strategicTags.domain_tags
        technology_tags = $strategicTags.technology_tags
        scale_tags = $strategicTags.scale_tags
    }
}

$masterById = @{}
$masterByName = @{}
foreach ($masterRow in @($masterRows)) {
    Add-RowToMaps -ById $masterById -ByName $masterByName -Id ([string]$masterRow.startup_id) -Name ([string]$masterRow.startup_name) -Value $masterRow -AliasMap $aliasMap
}

foreach ($profile in $profileRows) {
    $existing = Get-RowFromMaps -ById $masterById -ByName $masterByName -Id ([string]$profile.startup_id) -Name ([string]$profile.startup_name) -AliasMap $aliasMap
    if ($null -eq $existing) { continue }

    $merged = [PSCustomObject]@{
        startup_id = [string]$existing.startup_id
        startup_name = Clean-Text $existing.startup_name
        scope_decision = Clean-Text $existing.scope_decision
        scope_status = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.source_url))) { 'confirmed' } else { Clean-Text $existing.scope_status }
        scope_basis = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.source_url))) { 'external_auditable_source' } else { Clean-Text $existing.scope_basis }
        scope_reason = Clean-Text $existing.scope_reason
        macro_theme = Clean-Text $existing.macro_theme
        emergent_theme = Clean-Text $existing.emergent_theme
        market_label = Clean-Text $existing.market_label
        transition_function = Clean-Text $existing.transition_function
        technical_stack = Clean-Text $existing.technical_stack
        industry_destination = Clean-Text $existing.industry_destination
        thesis_fit = Clean-Text $existing.thesis_fit
        assignment_method = Clean-Text $existing.assignment_method
        taxonomy_confidence = Clean-Text $existing.taxonomy_confidence
        structured_country = Clean-Text $existing.structured_country
        structured_sector = Clean-Text $existing.structured_sector
        trl_current = Clean-Text $existing.trl_current
        trl_current_status = Clean-Text $existing.trl_current_status
        valuation_tier = Clean-Text $existing.valuation_tier
        data_quality_score_10 = Clean-Text $existing.data_quality_score_10
        quality_band = Clean-Text $existing.quality_band
        research_priority = Clean-Text $existing.research_priority
        missing_signals = Clean-Text $existing.missing_signals
        startup_summary_v1 = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.startup_summary_v1))) { Clean-Text $profile.startup_summary_v1 } else { Clean-Text $existing.startup_summary_v1 }
        business_one_liner = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.business_one_liner))) { Clean-Text $profile.business_one_liner } else { Clean-Text $existing.business_one_liner }
        materiality_signal = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.materiality_signal))) { Clean-Text $profile.materiality_signal } else { Clean-Text $existing.materiality_signal }
        thesis_scope_note = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.thesis_scope_note))) { Clean-Text $profile.thesis_scope_note } else { Clean-Text $existing.thesis_scope_note }
        source_url = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.source_url))) { Clean-Text $profile.source_url } else { Clean-Text $existing.source_url }
        source_type = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.source_type))) { Clean-Text $profile.source_type } else { Clean-Text $existing.source_type }
        source_date = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.source_date))) { Clean-Text $profile.source_date } else { Clean-Text $existing.source_date }
        evidence_excerpt = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.evidence_excerpt))) { Clean-Text $profile.evidence_excerpt } else { Clean-Text $existing.evidence_excerpt }
        summary_confidence = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.summary_confidence))) { Clean-Text $profile.summary_confidence } else { Clean-Text $existing.summary_confidence }
        review_status = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.review_status))) { Clean-Text $profile.review_status } else { Clean-Text $existing.review_status }
        last_reviewed_at = if (-not [string]::IsNullOrWhiteSpace((Clean-Text $profile.last_reviewed_at))) { Clean-Text $profile.last_reviewed_at } else { Clean-Text $existing.last_reviewed_at }
        bio_lens_tags = Clean-Text $existing.bio_lens_tags
        domain_tags = Clean-Text $existing.domain_tags
        technology_tags = Clean-Text $existing.technology_tags
        scale_tags = Clean-Text $existing.scale_tags
    }
    Add-RowToMaps -ById $masterById -ByName $masterByName -Id ([string]$merged.startup_id) -Name ([string]$merged.startup_name) -Value $merged -AliasMap $aliasMap
}

$masterRows = @($masterById.Values | Sort-Object startup_name -Unique)
$masterRows | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding UTF8

Write-Output "Startup master dataset built: $OutputPath"

