param(
    [string]$MasterDatasetPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$CoverageCsvPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_backed_coverage.csv",
    [string]$CoverageMdPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_backed_coverage.md",
    [string]$PriorityQueuePath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_backed_priority_queue.csv"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $MasterDatasetPath)) {
    throw "Missing master dataset: $MasterDatasetPath"
}

$rows = Import-Csv -LiteralPath $MasterDatasetPath

function Has-Value {
    param([string]$Text)
    return -not [string]::IsNullOrWhiteSpace([string]$Text)
}

function Get-SourceBackedStatus {
    param([object]$Row)

    $hasUrl = Has-Value -Text ([string]$Row.source_url)
    $reviewStatus = [string]$Row.review_status

    if (-not $hasUrl) {
        return 'missing_external_source'
    }

    switch ($reviewStatus) {
        'reviewed' { return 'source_backed_reviewed' }
        'seeded' { return 'source_backed_seeded' }
        'verified' { return 'source_backed_reviewed' }
        default { return 'source_backed_minimum' }
    }
}

function Get-QueuePriority {
    param([object]$Row)

    $scope = [string]$Row.scope_decision
    $quality = [string]$Row.quality_band
    $hasUrl = Has-Value -Text ([string]$Row.source_url)
    $base = 1

    if ($scope -eq 'include') { $base += 50 }
    elseif ($scope -eq 'review') { $base += 20 }

    switch ($quality) {
        'fragile' { $base += 20 }
        'medium' { $base += 12 }
        'high' { $base += 6 }
    }

    if (-not $hasUrl) { $base += 40 }
    if ([string]$Row.review_status -eq 'taxonomy_stub') { $base += 12 }

    return $base
}

$coverageRows = foreach ($row in $rows) {
    $status = Get-SourceBackedStatus -Row $row
    $hasUrl = Has-Value -Text ([string]$row.source_url)
    $isStubEvidence = [string]$row.evidence_excerpt -like 'Resumen provisional generado*'
    [PSCustomObject]@{
        startup_id = [string]$row.startup_id
        startup_name = [string]$row.startup_name
        scope_decision = [string]$row.scope_decision
        macro_theme = [string]$row.macro_theme
        review_status = [string]$row.review_status
        quality_band = [string]$row.quality_band
        source_backed_status = $status
        has_external_source = $hasUrl
        source_url = [string]$row.source_url
        source_type = [string]$row.source_type
        source_date = [string]$row.source_date
        evidence_is_stub = $isStubEvidence
        data_quality_score_10 = [string]$row.data_quality_score_10
    }
}

$coverageRows | Export-Csv -LiteralPath $CoverageCsvPath -NoTypeInformation -Encoding UTF8

$priorityQueue = @(
    $rows |
        Where-Object { -not (Has-Value -Text ([string]$_.source_url)) } |
        ForEach-Object {
            [PSCustomObject]@{
                startup_id = [string]$_.startup_id
                startup_name = [string]$_.startup_name
                scope_decision = [string]$_.scope_decision
                macro_theme = [string]$_.macro_theme
                review_status = [string]$_.review_status
                quality_band = [string]$_.quality_band
                data_quality_score_10 = [string]$_.data_quality_score_10
                priority = Get-QueuePriority -Row $_
                current_summary = [string]$_.startup_summary_v1
            }
        } |
        Sort-Object @{ Expression = 'priority'; Descending = $true }, @{ Expression = 'startup_name'; Descending = $false }
)

$priorityQueue | Export-Csv -LiteralPath $PriorityQueuePath -NoTypeInformation -Encoding UTF8

$total = @($rows).Count
$withUrl = @($rows | Where-Object { Has-Value -Text ([string]$_.source_url) }).Count
$includeRows = @($rows | Where-Object { $_.scope_decision -eq 'include' })
$includeWithUrl = @($includeRows | Where-Object { Has-Value -Text ([string]$_.source_url) }).Count
$reviewedWithUrl = @($rows | Where-Object { (Get-SourceBackedStatus -Row $_) -eq 'source_backed_reviewed' }).Count
$seededWithUrl = @($rows | Where-Object { (Get-SourceBackedStatus -Row $_) -eq 'source_backed_seeded' }).Count
$minimumWithUrl = @($rows | Where-Object { (Get-SourceBackedStatus -Row $_) -eq 'source_backed_minimum' }).Count
$missingUrl = @($rows | Where-Object { (Get-SourceBackedStatus -Row $_) -eq 'missing_external_source' }).Count

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Source-Backed Coverage') | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("Generated at: {0}" -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Coverage') | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("- Total startups: {0}" -f $total)) | Out-Null
$lines.Add(("- With external source URL: {0}" -f $withUrl)) | Out-Null
$lines.Add(("- Missing external source URL: {0}" -f $missingUrl)) | Out-Null
$lines.Add(("- Include startups: {0}" -f @($includeRows).Count)) | Out-Null
$lines.Add(("- Include with external source URL: {0}" -f $includeWithUrl)) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Source-Backed Status') | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("- source_backed_reviewed: {0}" -f $reviewedWithUrl)) | Out-Null
$lines.Add(("- source_backed_seeded: {0}" -f $seededWithUrl)) | Out-Null
$lines.Add(("- source_backed_minimum: {0}" -f $minimumWithUrl)) | Out-Null
$lines.Add(("- missing_external_source: {0}" -f $missingUrl)) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Priority') | Out-Null
$lines.Add('') | Out-Null
if ($includeWithUrl -eq @($includeRows).Count) {
    $lines.Add('All `include` startups have `source_url`. The next work queue should prioritize include rows that are still `seeded`, `fragile`, missing country/base, or backed only by broad portfolio pages.') | Out-Null
} else {
    $lines.Add('The next work queue should prioritize `include` startups without `source_url`, especially `fragile` and `taxonomy_stub` rows.') | Out-Null
}

Set-Content -LiteralPath $CoverageMdPath -Value $lines -Encoding UTF8

Write-Output "Source-backed tracker built:"
Write-Output "  Coverage CSV: $CoverageCsvPath"
Write-Output "  Coverage MD: $CoverageMdPath"
Write-Output "  Priority Queue: $PriorityQueuePath"
