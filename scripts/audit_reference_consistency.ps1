param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack",
    [string]$OutputPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\reference_consistency_audit.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Has-Value {
    param([object]$Value)
    return -not [string]::IsNullOrWhiteSpace([string]$Value)
}

$master = Import-Csv (Join-Path $Root 'startup_master_dataset.csv')
$coverage = Import-Csv (Join-Path $Root 'quality\source_backed_coverage.csv')
$profiles = Import-Csv (Join-Path $Root 'startup_profiles_minimum_viable.csv')

$masterWithUrl = @($master | Where-Object { Has-Value $_.source_url }).Count
$masterInclude = @($master | Where-Object { $_.scope_decision -eq 'include' }).Count
$masterIncludeWithUrl = @($master | Where-Object { $_.scope_decision -eq 'include' -and (Has-Value $_.source_url) }).Count
$masterSeeded = @($master | Where-Object { $_.review_status -eq 'seeded' }).Count
$masterSeededWithUrl = @($master | Where-Object { $_.review_status -eq 'seeded' -and (Has-Value $_.source_url) }).Count

$coverageWithUrl = @($coverage | Where-Object { $_.has_external_source -eq 'True' }).Count
$coverageIncludeWithUrl = @($coverage | Where-Object { $_.scope_decision -eq 'include' -and $_.has_external_source -eq 'True' }).Count
$coverageSeeded = @($coverage | Where-Object { $_.source_backed_status -eq 'source_backed_seeded' }).Count

$profileSeeded = @($profiles | Where-Object { $_.review_status -eq 'seeded' }).Count
$profileWithUrl = @($profiles | Where-Object { Has-Value $_.source_url }).Count
$profileSeededWithUrl = @($profiles | Where-Object { $_.review_status -eq 'seeded' -and (Has-Value $_.source_url) }).Count
$masterBlankReviewStatus = @($master | Where-Object { -not (Has-Value $_.review_status) }).Count

$isAligned = ($masterWithUrl -eq $coverageWithUrl) -and ($masterIncludeWithUrl -eq $coverageIncludeWithUrl) -and ($masterSeededWithUrl -eq $coverageSeeded) -and ($masterWithUrl -eq $profileWithUrl) -and ($masterSeeded -eq $profileSeeded) -and ($masterBlankReviewStatus -eq 0)

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Reference Consistency Audit') | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("Generated at: {0}" -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))) | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("Overall alignment: {0}" -f ($(if ($isAligned) { 'OK' } else { 'MISMATCH' })))) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Master dataset') | Out-Null
$lines.Add(("- with_url: {0}" -f $masterWithUrl)) | Out-Null
$lines.Add(("- include_total: {0}" -f $masterInclude)) | Out-Null
$lines.Add(("- include_with_url: {0}" -f $masterIncludeWithUrl)) | Out-Null
$lines.Add(("- seeded: {0}" -f $masterSeeded)) | Out-Null
$lines.Add(("- seeded_with_url: {0}" -f $masterSeededWithUrl)) | Out-Null
$lines.Add(("- blank_review_status: {0}" -f $masterBlankReviewStatus)) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Coverage tracker') | Out-Null
$lines.Add(("- with_url: {0}" -f $coverageWithUrl)) | Out-Null
$lines.Add(("- include_with_url: {0}" -f $coverageIncludeWithUrl)) | Out-Null
$lines.Add(("- source_backed_seeded: {0}" -f $coverageSeeded)) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Profiles') | Out-Null
$lines.Add(("- with_url: {0}" -f $profileWithUrl)) | Out-Null
$lines.Add(("- seeded: {0}" -f $profileSeeded)) | Out-Null
$lines.Add(("- seeded_with_url: {0}" -f $profileSeededWithUrl)) | Out-Null

Set-Content -LiteralPath $OutputPath -Value $lines -Encoding UTF8
Write-Output "Reference consistency audit built: $OutputPath"
