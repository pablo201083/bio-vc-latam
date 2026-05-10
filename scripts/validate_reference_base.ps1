param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack",
    [string]$ReportCsvPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\reference_validation_report.csv",
    [string]$ReportMdPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\reference_validation_report.md"
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
    return (($builder.ToString().ToLowerInvariant()) -replace '[^a-z0-9]+', '').Trim()
}

function Add-Check {
    param(
        [System.Collections.Generic.List[object]]$Checks,
        [string]$CheckId,
        [string]$Severity,
        [string]$Status,
        [int]$Count,
        [string]$Message
    )
    $Checks.Add([PSCustomObject]@{
        check_id = $CheckId
        severity = $Severity
        status = $Status
        count = $Count
        message = $Message
    }) | Out-Null
}

$master = Import-Csv -LiteralPath (Join-Path $Root 'startup_master_dataset.csv')
$entities = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_entities.csv')
$aliases = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_aliases.csv')
$edges = Import-Csv -LiteralPath (Join-Path $Root 'canonical\canonical_investment_edges.csv')
$sourceRegistryPath = Join-Path $Root 'quality\source_registry.csv'
$sourceRegistry = if (Test-Path -LiteralPath $sourceRegistryPath) { Import-Csv -LiteralPath $sourceRegistryPath } else { @() }

$checks = New-Object System.Collections.Generic.List[object]

$includeRows = @($master | Where-Object { $_.scope_decision -eq 'include' })
$includeMissingSource = @($includeRows | Where-Object { -not (Clean-Text $_.source_url) })
Add-Check $checks 'include_source_url' 'error' ($(if ($includeMissingSource.Count -eq 0) { 'pass' } else { 'fail' })) $includeMissingSource.Count 'Include rows must have an auditable source_url.'

$duplicateStartups = @(
    $master |
        Group-Object { Normalize-Key $_.startup_name } |
        Where-Object { $_.Name -and $_.Count -gt 1 }
)
Add-Check $checks 'duplicate_startup_names' 'error' ($(if ($duplicateStartups.Count -eq 0) { 'pass' } else { 'fail' })) $duplicateStartups.Count 'Startup names should not duplicate after normalization.'

$investorDuplicates = @(
    $entities |
        Where-Object { $_.entity_type -eq 'investor' } |
        Group-Object { Normalize-Key $_.canonical_name } |
        Where-Object { $_.Name -and $_.Count -gt 1 }
)
Add-Check $checks 'duplicate_investor_names' 'error' ($(if ($investorDuplicates.Count -eq 0) { 'pass' } else { 'fail' })) $investorDuplicates.Count 'Investor names should not duplicate after normalization.'

$startupIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
foreach ($row in $master) { $startupIds.Add([string]$row.startup_id) | Out-Null }
$startupLookup = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
foreach ($row in $master) {
    $startupLookup[(Normalize-Key ([string]$row.startup_id))] = [string]$row.startup_id
    $startupLookup[(Normalize-Key ([string]$row.startup_name))] = [string]$row.startup_id
}
foreach ($alias in $aliases) {
    $key = Normalize-Key ([string]$alias.alias)
    if ($key -and $startupIds.Contains([string]$alias.entity_id)) {
        $startupLookup[$key] = [string]$alias.entity_id
    }
}
$investorIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
foreach ($row in ($entities | Where-Object { $_.entity_type -eq 'investor' })) { $investorIds.Add([string]$row.entity_id) | Out-Null }
$canonicalStartupIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
foreach ($row in ($entities | Where-Object { $_.entity_type -eq 'startup' })) { $canonicalStartupIds.Add([string]$row.entity_id) | Out-Null }

$unresolvedInvestors = @($edges | Where-Object { -not $investorIds.Contains([string]$_.investor_id) })
$externalCanonicalStartups = New-Object System.Collections.Generic.List[object]
$unresolvedStartups = @(
    $edges | Where-Object {
        $rawStartupId = [string]$_.startup_id
        if ($startupIds.Contains($rawStartupId) -or $startupLookup.ContainsKey((Normalize-Key $rawStartupId))) {
            return $false
        }
        if ($canonicalStartupIds.Contains($rawStartupId)) {
            $externalCanonicalStartups.Add($_) | Out-Null
            return $false
        }
        return $true
    }
)
Add-Check $checks 'canonical_edge_investor_resolution' 'error' ($(if ($unresolvedInvestors.Count -eq 0) { 'pass' } else { 'fail' })) $unresolvedInvestors.Count 'Canonical investment edges must point to canonical investor ids.'
Add-Check $checks 'canonical_edge_startup_resolution' 'warning' ($(if ($unresolvedStartups.Count -eq 0) { 'pass' } else { 'warn' })) $unresolvedStartups.Count 'Canonical investment edges must resolve to master startups, aliases, or tracked external canonical startup nodes.'
Add-Check $checks 'canonical_edge_external_startups' 'info' ($(if ($externalCanonicalStartups.Count -gt 0) { 'warn' } else { 'pass' })) $externalCanonicalStartups.Count 'Canonical investment edges pointing to startup nodes outside the master dataset; review as expansion candidates or keep as capital-network context.'

$includeMissingCountry = @($includeRows | Where-Object { -not (Clean-Text $_.structured_country) })
Add-Check $checks 'include_country_coverage' 'warning' ($(if ($includeMissingCountry.Count -eq 0) { 'pass' } else { 'warn' })) $includeMissingCountry.Count 'Include rows should have structured_country for regional coverage analysis.'

$includeFragile = @($includeRows | Where-Object { $_.quality_band -eq 'fragile' -or $_.review_status -eq 'taxonomy_stub' })
Add-Check $checks 'include_fragile_or_stub' 'warning' ($(if ($includeFragile.Count -eq 0) { 'pass' } else { 'warn' })) $includeFragile.Count 'Include rows should be moved from fragile/taxonomy_stub to source-backed seeded or reviewed.'

$tier1Sources = @($sourceRegistry | Where-Object { [int]$_.trust_tier -eq 1 }).Count
Add-Check $checks 'source_registry_tier1' 'info' ($(if ($tier1Sources -gt 0) { 'pass' } else { 'warn' })) $tier1Sources 'Source registry should contain tier 1 official sources.'

$checks | Export-Csv -LiteralPath $ReportCsvPath -NoTypeInformation -Encoding UTF8

$errorCount = @($checks | Where-Object { $_.severity -eq 'error' -and $_.status -eq 'fail' }).Count
$warningCount = @($checks | Where-Object { $_.severity -eq 'warning' -and $_.status -eq 'warn' }).Count

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# Reference Validation Report') | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("Generated at: {0}" -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))) | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("Errors: {0}" -f $errorCount)) | Out-Null
$lines.Add(("Warnings: {0}" -f $warningCount)) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Checks') | Out-Null
$lines.Add('') | Out-Null
foreach ($check in $checks) {
    $lines.Add(("- {0} [{1}/{2}]: {3} ({4})" -f $check.check_id, $check.severity, $check.status, $check.message, $check.count)) | Out-Null
}

Set-Content -LiteralPath $ReportMdPath -Value $lines -Encoding UTF8

Write-Output "Reference validation report built:"
Write-Output "  CSV: $ReportCsvPath"
Write-Output "  MD: $ReportMdPath"
if ($errorCount -gt 0) {
    throw "Reference validation failed with $errorCount error check(s). See $ReportMdPath"
}
