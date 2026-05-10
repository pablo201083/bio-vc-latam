param(
    [string]$ProfilesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$QueuePath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_profiles_research_queue.csv",
    [string]$OutputJsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\startup-profiles-data.js"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $ProfilesPath)) {
    throw "Missing profiles file: $ProfilesPath"
}

$profiles = Import-Csv -LiteralPath $ProfilesPath
$queue = if (Test-Path -LiteralPath $QueuePath) { Import-Csv -LiteralPath $QueuePath } else { @() }

$summary = [PSCustomObject]@{
    generated_at = (Get-Date).ToString('s')
    total = @($profiles).Count
    with_summary = @($profiles | Where-Object { -not [string]::IsNullOrWhiteSpace($_.startup_summary_v1) }).Count
    with_external_source = @($profiles | Where-Object { -not [string]::IsNullOrWhiteSpace($_.source_url) }).Count
    confirmed_scope = @($profiles | Where-Object { $_.scope_status -eq 'confirmed' }).Count
    provisional_scope = @($profiles | Where-Object { $_.scope_status -eq 'provisional' }).Count
    include_with_external_source = @($profiles | Where-Object { $_.scope_decision -eq 'include' -and -not [string]::IsNullOrWhiteSpace($_.source_url) }).Count
    include_without_external_source = @($profiles | Where-Object { $_.scope_decision -eq 'include' -and [string]::IsNullOrWhiteSpace($_.source_url) }).Count
    include_confirmed_scope = @($profiles | Where-Object { $_.scope_decision -eq 'include' -and $_.scope_status -eq 'confirmed' }).Count
    include_provisional_scope = @($profiles | Where-Object { $_.scope_decision -eq 'include' -and $_.scope_status -eq 'provisional' }).Count
    seeded = @($profiles | Where-Object { $_.review_status -eq 'seeded' }).Count
    taxonomy_stub = @($profiles | Where-Object { $_.review_status -eq 'taxonomy_stub' }).Count
    needs_research = @($profiles | Where-Object { $_.review_status -eq 'needs_research' }).Count
    verified = @($profiles | Where-Object { $_.review_status -eq 'verified' }).Count
    reviewed = @($profiles | Where-Object { $_.review_status -eq 'reviewed' }).Count
}

$sourceBackedCounts = @(
    [PSCustomObject]@{
        label = 'source_backed_reviewed'
        count = @($profiles | Where-Object { -not [string]::IsNullOrWhiteSpace($_.source_url) -and $_.review_status -eq 'reviewed' }).Count
    }
    [PSCustomObject]@{
        label = 'source_backed_seeded'
        count = @($profiles | Where-Object { -not [string]::IsNullOrWhiteSpace($_.source_url) -and $_.review_status -eq 'seeded' }).Count
    }
    [PSCustomObject]@{
        label = 'source_backed_minimum'
        count = @($profiles | Where-Object { -not [string]::IsNullOrWhiteSpace($_.source_url) -and $_.review_status -notin @('reviewed','seeded') }).Count
    }
    [PSCustomObject]@{
        label = 'missing_external_source'
        count = @($profiles | Where-Object { [string]::IsNullOrWhiteSpace($_.source_url) }).Count
    }
)

$sourceCounts = @(
    $profiles | Group-Object source_type | Sort-Object Count -Descending | ForEach-Object {
        [PSCustomObject]@{
            source_type = if ([string]::IsNullOrWhiteSpace($_.Name)) { 'none' } else { $_.Name }
            count = $_.Count
        }
    }
)

$reviewCounts = @(
    $profiles | Group-Object review_status | Sort-Object Count -Descending | ForEach-Object {
        [PSCustomObject]@{
            review_status = $_.Name
            count = $_.Count
        }
    }
)

$scopeCounts = @(
    $profiles | Group-Object scope_decision | Sort-Object Count -Descending | ForEach-Object {
        [PSCustomObject]@{
            scope_decision = $_.Name
            count = $_.Count
        }
    }
)

$scopeStatusCounts = @(
    $profiles | Group-Object scope_status | Sort-Object Count -Descending | ForEach-Object {
        [PSCustomObject]@{
            scope_status = $_.Name
            count = $_.Count
        }
    }
)

$qualityCounts = @(
    $profiles | Group-Object quality_band | Sort-Object Count -Descending | ForEach-Object {
        [PSCustomObject]@{
            quality_band = if ([string]::IsNullOrWhiteSpace($_.Name)) { 'unknown' } else { $_.Name }
            count = $_.Count
        }
    }
)

$macroThemeCounts = @(
    $profiles |
        Where-Object { $_.scope_decision -eq 'include' } |
        Group-Object macro_theme |
        Sort-Object Count -Descending |
        ForEach-Object {
            [PSCustomObject]@{
                macro_theme = $_.Name
                count = $_.Count
            }
        }
)

$payload = [PSCustomObject]@{
    summary = $summary
    profiles = $profiles
    queue = $queue
    source_counts = $sourceCounts
    review_counts = $reviewCounts
    scope_counts = $scopeCounts
    scope_status_counts = $scopeStatusCounts
    source_backed_counts = $sourceBackedCounts
    quality_counts = $qualityCounts
    macro_theme_counts = $macroThemeCounts
}

$js = "window.STARTUP_PROFILES_DATA = " + ($payload | ConvertTo-Json -Depth 8) + ";"
Set-Content -LiteralPath $OutputJsPath -Value $js -Encoding UTF8

Write-Output "Startup profiles dashboard data built: $OutputJsPath"
