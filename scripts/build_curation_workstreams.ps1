param(
    [string]$MasterPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$SemanticPriorityPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_curation_priority_current.csv",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality"
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

function Get-WordCount {
    param([string]$Text)
    $value = Clean-Text $Text
    if (-not $value) { return 0 }
    return @(($value -replace '[^\p{L}\p{N}\- ]', ' ' -split '\s+') | Where-Object { $_ }).Count
}

function Is-OfficialSource {
    param([string]$SourceType)
    $value = (Clean-Text $SourceType).ToLowerInvariant()
    return ($value -match 'official_website|official_company|official_public|official_profile')
}

function Has-StructuredProfile {
    param($Row)
    return (
        (Get-WordCount $Row.startup_summary_v1) -ge 55 -and
        (Clean-Text $Row.business_one_liner) -and
        (Clean-Text $Row.problem_addressed) -and
        (Clean-Text $Row.technical_approach) -and
        (Clean-Text $Row.thesis_scope_note)
    )
}

function Get-RowValue {
    param(
        [object]$Row,
        [string]$PropertyName
    )
    if ($null -eq $Row) { return '' }
    if ($Row.PSObject.Properties.Name -contains $PropertyName) {
        return Clean-Text $Row.$PropertyName
    }
    return ''
}

function New-QueueRow {
    param(
        $Row,
        [string]$Workstream,
        [string]$Action,
        [string]$Reason,
        [string]$Effort = 'low',
        [string]$ExpectedImpact = 'medium'
    )

    [pscustomobject]@{
        workstream = $Workstream
        startup_id = $Row.startup_id
        startup_name = $Row.startup_name
        scope_decision = $Row.scope_decision
        current_theme = if (Get-RowValue $Row 'semantic_single_theme') { Get-RowValue $Row 'semantic_single_theme' } else { Get-RowValue $Row 'emergent_theme' }
        quality_band = $Row.quality_band
        review_status = $Row.review_status
        source_type = $Row.source_type
        source_url = $Row.source_url
        summary_words = Get-WordCount $Row.startup_summary_v1
        data_quality_score_10 = $Row.data_quality_score_10
        action = $Action
        reason = $Reason
        effort = $Effort
        expected_impact = $ExpectedImpact
        current_summary = $Row.startup_summary_v1
    }
}

if (-not (Test-Path -LiteralPath $MasterPath)) {
    throw "Missing master dataset: $MasterPath"
}
if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$masterRows = Import-Csv -LiteralPath $MasterPath
$semanticRows = if (Test-Path -LiteralPath $SemanticPriorityPath) { Import-Csv -LiteralPath $SemanticPriorityPath } else { @() }

$semanticByName = @{}
foreach ($row in $semanticRows) {
    $semanticByName[[string]$row.startup_name] = $row
}

$includeRows = @($masterRows | Where-Object { $_.scope_decision -eq 'include' })
$excludeRows = @($masterRows | Where-Object { $_.scope_decision -eq 'exclude' })
$masterByName = @{}
foreach ($row in $masterRows) {
    $masterByName[[string]$row.startup_name] = $row
}

$easyReviewPromotions = @(
    $includeRows |
        Where-Object {
            $_.review_status -eq 'seeded' -and
            (Is-OfficialSource $_.source_type) -and
            (Has-StructuredProfile $_)
        } |
        Sort-Object @{ Expression = { if ($_.quality_band -eq 'high') { 0 } else { 1 } } }, startup_name |
        ForEach-Object {
            New-QueueRow -Row $_ -Workstream 'easy_review_promotions' -Action 'promote_to_reviewed_after_spot_check' -Reason 'Official source plus complete structured profile already meet review threshold.' -Effort 'very_low' -ExpectedImpact 'high'
        }
)

$sourceUpgradeBatch = @(
    $includeRows |
        Where-Object {
            $_.review_status -eq 'seeded' -and
            -not (Is-OfficialSource $_.source_type)
        } |
        Sort-Object @{ Expression = { if ($_.source_type -match 'candidate|portfolio') { 0 } else { 1 } } }, startup_name |
        ForEach-Object {
            New-QueueRow -Row $_ -Workstream 'source_upgrade_batch' -Action 'find_or_confirm_official_source_then_rewrite' -Reason 'Still seeded with portfolio, candidate, external or weak source.' -Effort 'medium' -ExpectedImpact 'high'
        }
)

$officialSeededEnrichment = @(
    $includeRows |
        Where-Object {
            $_.review_status -eq 'seeded' -and
            (Is-OfficialSource $_.source_type) -and
            -not (Has-StructuredProfile $_)
        } |
        Sort-Object @{ Expression = { if ($_.quality_band -eq 'high') { 0 } else { 1 } } }, @{ Expression = { Get-WordCount $_.startup_summary_v1 } }, startup_name |
        ForEach-Object {
            New-QueueRow -Row $_ -Workstream 'official_seeded_enrichment' -Action 'rewrite_from_official_source_using_template' -Reason 'Official source exists, but summary/structured fields are too thin to promote automatically.' -Effort 'low' -ExpectedImpact 'high'
        }
)

$semanticConflictBatch = @(
    $semanticRows |
        Where-Object { $_.semantic_confidence -in @('low', 'medium') } |
        Select-Object -First 120 |
        ForEach-Object {
            $name = $_.startup_name
            $master = if ($masterByName.ContainsKey($name)) { $masterByName[$name] } else { $null }
            if ($null -eq $master) { return }
            New-QueueRow -Row $master -Workstream 'semantic_conflict_batch' -Action 'enrich_or_reclassify_semantic_fit' -Reason ("Semantic confidence {0} with margin {1}; current theme: {2}" -f $_.semantic_confidence, $_.semantic_margin, $_.current_theme) -Effort 'medium' -ExpectedImpact 'medium'
        }
)

$excludeDefenseBatch = @(
    $excludeRows |
        Where-Object {
            $_.quality_band -in @('fragile', 'poor', '') -or
            $_.review_status -ne 'reviewed' -or
            -not (Clean-Text $_.source_url)
        } |
        Sort-Object @{ Expression = { if ($_.quality_band -eq 'fragile') { 0 } elseif ($_.quality_band -eq 'poor') { 1 } else { 2 } } }, startup_name |
        ForEach-Object {
            New-QueueRow -Row $_ -Workstream 'exclude_defense_batch' -Action 'add_external_source_and_defensible_exclude_reason' -Reason 'Exclude frontier needs auditable evidence to defend universe boundary.' -Effort 'low' -ExpectedImpact 'medium'
        }
)

$summary = @(
    [pscustomobject]@{ workstream = 'easy_review_promotions'; count = @($easyReviewPromotions).Count; purpose = 'Cheap reviewed gains from already complete official-source records.'; output = 'quality\easy_review_promotions.csv' }
    [pscustomobject]@{ workstream = 'official_seeded_enrichment'; count = @($officialSeededEnrichment).Count; purpose = 'Official-source include records that only need template rewrite and structured-field completion.'; output = 'quality\official_seeded_enrichment.csv' }
    [pscustomobject]@{ workstream = 'source_upgrade_batch'; count = @($sourceUpgradeBatch).Count; purpose = 'Find direct sources for seeded include records still backed by portfolio/external/candidate evidence.'; output = 'quality\source_upgrade_batch.csv' }
    [pscustomobject]@{ workstream = 'semantic_conflict_batch'; count = @($semanticConflictBatch).Count; purpose = 'Good or medium records whose semantic placement remains uncertain.'; output = 'quality\semantic_conflict_batch.csv' }
    [pscustomobject]@{ workstream = 'exclude_defense_batch'; count = @($excludeDefenseBatch).Count; purpose = 'Weak excludes to close the boundary of the BIO universe.'; output = 'quality\exclude_defense_batch.csv' }
)

$easyReviewPromotions | Export-Csv -LiteralPath (Join-Path $OutputDir 'easy_review_promotions.csv') -NoTypeInformation -Encoding UTF8
$officialSeededEnrichment | Export-Csv -LiteralPath (Join-Path $OutputDir 'official_seeded_enrichment.csv') -NoTypeInformation -Encoding UTF8
$sourceUpgradeBatch | Export-Csv -LiteralPath (Join-Path $OutputDir 'source_upgrade_batch.csv') -NoTypeInformation -Encoding UTF8
$semanticConflictBatch | Export-Csv -LiteralPath (Join-Path $OutputDir 'semantic_conflict_batch.csv') -NoTypeInformation -Encoding UTF8
$excludeDefenseBatch | Export-Csv -LiteralPath (Join-Path $OutputDir 'exclude_defense_batch.csv') -NoTypeInformation -Encoding UTF8
$summary | Export-Csv -LiteralPath (Join-Path $OutputDir 'curation_workstream_summary.csv') -NoTypeInformation -Encoding UTF8

Write-Output "Curation workstreams built:"
$summary | ForEach-Object { Write-Output ("  {0}: {1}" -f $_.workstream, $_.count) }
