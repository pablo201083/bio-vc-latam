param(
    [string]$MasterDatasetPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$OutputCsvPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\reference_base_status.csv",
    [string]$OutputMdPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\reference_base_status.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $MasterDatasetPath)) {
    throw "Missing master dataset: $MasterDatasetPath"
}

$rows = Import-Csv -LiteralPath $MasterDatasetPath

$metrics = [System.Collections.Generic.List[object]]::new()

function Add-Metric {
    param(
        [System.Collections.Generic.List[object]]$List,
        [string]$Metric,
        [object]$Value
    )

    $List.Add([PSCustomObject]@{
        metric = $Metric
        value = $Value
    }) | Out-Null
}

Add-Metric -List $metrics -Metric 'startup_total_unique' -Value (@($rows).Count)
Add-Metric -List $metrics -Metric 'duplicates_by_startup_name' -Value (@($rows | Group-Object startup_name | Where-Object { $_.Count -gt 1 }).Count)
Add-Metric -List $metrics -Metric 'source_backed::with_external_source' -Value (@($rows | Where-Object { -not [string]::IsNullOrWhiteSpace($_.source_url) }).Count)
Add-Metric -List $metrics -Metric 'source_backed::missing_external_source' -Value (@($rows | Where-Object { [string]::IsNullOrWhiteSpace($_.source_url) }).Count)

foreach ($group in ($rows | Group-Object scope_decision | Sort-Object Name)) {
    Add-Metric -List $metrics -Metric ("scope::{0}" -f $group.Name) -Value $group.Count
}

foreach ($group in ($rows | Group-Object review_status | Sort-Object Name)) {
    Add-Metric -List $metrics -Metric ("review_status::{0}" -f $group.Name) -Value $group.Count
}

$includeRows = @($rows | Where-Object { $_.scope_decision -eq 'include' })
foreach ($group in ($includeRows | Group-Object review_status | Sort-Object Name)) {
    Add-Metric -List $metrics -Metric ("include_review_status::{0}" -f $group.Name) -Value $group.Count
}
Add-Metric -List $metrics -Metric 'include_source_backed::with_external_source' -Value (@($includeRows | Where-Object { -not [string]::IsNullOrWhiteSpace($_.source_url) }).Count)
Add-Metric -List $metrics -Metric 'include_source_backed::missing_external_source' -Value (@($includeRows | Where-Object { [string]::IsNullOrWhiteSpace($_.source_url) }).Count)

foreach ($group in ($includeRows | Group-Object macro_theme | Sort-Object Count -Descending | Select-Object -First 10)) {
    Add-Metric -List $metrics -Metric ("include_macro_theme::{0}" -f $group.Name) -Value $group.Count
}

$metrics | Export-Csv -LiteralPath $OutputCsvPath -NoTypeInformation -Encoding UTF8

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Reference Base Status') | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("Generated at: {0}" -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Core Metrics') | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("- Unique startups: {0}" -f (@($rows).Count))) | Out-Null
$lines.Add(("- Duplicates by startup_name: {0}" -f (@($rows | Group-Object startup_name | Where-Object { $_.Count -gt 1 }).Count))) | Out-Null
$lines.Add(("- Include: {0}" -f (@($rows | Where-Object { $_.scope_decision -eq 'include' }).Count))) | Out-Null
$lines.Add(("- Exclude: {0}" -f (@($rows | Where-Object { $_.scope_decision -eq 'exclude' }).Count))) | Out-Null
$lines.Add(("- Review: {0}" -f (@($rows | Where-Object { $_.scope_decision -eq 'review' }).Count))) | Out-Null
$lines.Add(("- With external source URL: {0}" -f (@($rows | Where-Object { -not [string]::IsNullOrWhiteSpace($_.source_url) }).Count))) | Out-Null
$lines.Add(("- Missing external source URL: {0}" -f (@($rows | Where-Object { [string]::IsNullOrWhiteSpace($_.source_url) }).Count))) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Profile Coverage') | Out-Null
$lines.Add('') | Out-Null
foreach ($group in ($rows | Group-Object review_status | Sort-Object Count -Descending)) {
    $lines.Add(("- {0}: {1}" -f $group.Name, $group.Count)) | Out-Null
}
$lines.Add('') | Out-Null
$lines.Add('## Include Universe Coverage') | Out-Null
$lines.Add('') | Out-Null
foreach ($group in ($includeRows | Group-Object review_status | Sort-Object Count -Descending)) {
    $lines.Add(("- {0}: {1}" -f $group.Name, $group.Count)) | Out-Null
}
$lines.Add(("- with_external_source: {0}" -f (@($includeRows | Where-Object { -not [string]::IsNullOrWhiteSpace($_.source_url) }).Count))) | Out-Null
$lines.Add(("- missing_external_source: {0}" -f (@($includeRows | Where-Object { [string]::IsNullOrWhiteSpace($_.source_url) }).Count))) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Top Include Macro Themes') | Out-Null
$lines.Add('') | Out-Null
foreach ($group in ($includeRows | Group-Object macro_theme | Sort-Object Count -Descending | Select-Object -First 10)) {
    $lines.Add(("- {0}: {1}" -f $group.Name, $group.Count)) | Out-Null
}

Set-Content -LiteralPath $OutputMdPath -Value $lines -Encoding UTF8

Write-Output "Reference base status built:"
Write-Output "  CSV: $OutputCsvPath"
Write-Output "  MD: $OutputMdPath"
