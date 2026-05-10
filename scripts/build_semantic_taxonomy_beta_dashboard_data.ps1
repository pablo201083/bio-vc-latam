param(
    [string]$AssignmentsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_beta_assignments.csv",
    [string]$ThemesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_beta_themes.csv",
    [string]$MasterPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$OutputPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\semantic-taxonomy-beta-data.js"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function To-Int($value) {
    if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) { return 0 }
    return [int]$value
}

if (-not (Test-Path -LiteralPath $AssignmentsPath)) { throw "Missing semantic beta assignments: $AssignmentsPath" }
if (-not (Test-Path -LiteralPath $ThemesPath)) { throw "Missing semantic beta themes: $ThemesPath" }
if (-not (Test-Path -LiteralPath $MasterPath)) { throw "Missing master dataset: $MasterPath" }

$assignments = Import-Csv -LiteralPath $AssignmentsPath
$themes = Import-Csv -LiteralPath $ThemesPath
$master = Import-Csv -LiteralPath $MasterPath

$include = @($master | Where-Object { $_.scope_decision -eq 'include' })
$confirmedInclude = @($include | Where-Object { $_.scope_status -eq 'confirmed' })

$confidenceCounts = @(
    $assignments | Group-Object semantic_beta_confidence | Sort-Object Count -Descending | ForEach-Object {
        [pscustomobject]@{
            confidence = $_.Name
            count = $_.Count
        }
    }
)

$microclusterCounts = @(
    $assignments | Group-Object semantic_cluster_id | Sort-Object Count -Descending | ForEach-Object {
        $group = @($_.Group)
        [pscustomobject]@{
            semantic_cluster_id = $group[0].semantic_cluster_id
            startup_count = $_.Count
            macrotheme = $group[0].semantic_beta_theme
            dominant_current_macro_theme = (($group | Group-Object current_macro_theme | Sort-Object Count -Descending | Select-Object -First 1).Name)
            avg_margin = [math]::Round((($group | ForEach-Object { [double]($_.semantic_beta_margin) } | Measure-Object -Average).Average), 2)
            low_confidence_count = @($group | Where-Object { $_.semantic_beta_confidence -eq 'low' }).Count
            representative_startups = (@($group | Sort-Object { [double]($_.semantic_beta_score) } -Descending | Select-Object -First 3 -ExpandProperty startup_name) -join '; ')
        }
    }
)

$themeCoverage = @(
    $themes | Sort-Object {[int]$_.startup_count} -Descending | ForEach-Object {
        $themeName = $_.semantic_beta_theme
        $members = @($assignments | Where-Object { $_.semantic_beta_theme -eq $themeName })
        $microclusters = @($members | Group-Object semantic_cluster_id | Sort-Object Count -Descending)
        $avgMargin = if ($members.Count -gt 0) {
            [math]::Round((($members | ForEach-Object { [double]($_.semantic_beta_margin) } | Measure-Object -Average).Average), 2)
        } else { 0 }
        $avgScore = if ($members.Count -gt 0) {
            [math]::Round((($members | ForEach-Object { [double]($_.semantic_beta_score) } | Measure-Object -Average).Average), 2)
        } else { 0 }
        $microclusterCount = $microclusters.Count
        $compressionRatio = if ($microclusterCount -gt 0) {
            [math]::Round(([double](To-Int $_.startup_count) / [double]$microclusterCount), 2)
        } else { 0 }
        $microclusterBreakdown = @(
            $microclusters | ForEach-Object {
                $group = @($_.Group)
                [pscustomobject]@{
                    semantic_cluster_id = $group[0].semantic_cluster_id
                    startup_count = $_.Count
                    avg_margin = [math]::Round((($group | ForEach-Object { [double]($_.semantic_beta_margin) } | Measure-Object -Average).Average), 2)
                    low_confidence_count = @($group | Where-Object { $_.semantic_beta_confidence -eq 'low' }).Count
                    dominant_current_macro_theme = (($group | Group-Object current_macro_theme | Sort-Object Count -Descending | Select-Object -First 1).Name)
                    representative_startups = (@($group | Sort-Object { [double]($_.semantic_beta_score) } -Descending | Select-Object -First 3 -ExpandProperty startup_name) -join '; ')
                }
            }
        )

        [pscustomobject]@{
            theme = $themeName
            startup_count = To-Int $_.startup_count
            low_confidence_count = To-Int $_.low_confidence_count
            majority_current_macro_theme = $_.majority_current_macro_theme
            gridx_match = $_.gridx_match
            antom_match = $_.antom_match
            representative_startups = $_.representative_startups
            top_tokens = $_.top_tokens
            theme_description = $_.theme_description
            microcluster_count = $microclusterCount
            compression_ratio = $compressionRatio
            avg_margin = $avgMargin
            avg_score = $avgScore
            microclusters = $microclusterBreakdown
            explanatory_signal = if ((To-Int $_.low_confidence_count) -eq 0) {
                'strong'
            } elseif ((To-Int $_.low_confidence_count) -le 2) {
                'promising'
            } else {
                'noisy'
            }
        }
    }
)

$summary = [pscustomobject]@{
    generated_at = (Get-Date).ToString('s')
    startups_total = $master.Count
    include_total = $include.Count
    confirmed_include_total = $confirmedInclude.Count
    proto_themes = $themes.Count
    microclusters_total = (($assignments.semantic_cluster_id | Select-Object -Unique).Count)
    macrothemes_total = $themes.Count
    global_compression_ratio = if ($themes.Count -gt 0) { [math]::Round(((($assignments.semantic_cluster_id | Select-Object -Unique).Count) / [double]$themes.Count), 2) } else { 0 }
    confirmed_include_coverage_pct = if ($include.Count -gt 0) { [math]::Round(($confirmedInclude.Count / $include.Count) * 100, 1) } else { 0 }
    uncertain_cluster_size = @($assignments | Where-Object { $_.semantic_beta_theme -eq 'uncertain source-backed edge cases' }).Count
    low_confidence_assignments = @($assignments | Where-Object { $_.semantic_beta_confidence -eq 'low' }).Count
}

$themeCounts = @(
    $assignments | Group-Object semantic_beta_theme | Sort-Object Count -Descending | ForEach-Object {
        [pscustomobject]@{
            theme = $_.Name
            count = $_.Count
        }
    }
)

$currentMacroCounts = @(
    $assignments | Group-Object current_macro_theme | Sort-Object Count -Descending | ForEach-Object {
        [pscustomobject]@{
            macro_theme = $_.Name
            count = $_.Count
        }
    }
)

$uncertainAssignments = @(
    $assignments |
    Where-Object { $_.semantic_beta_theme -eq 'uncertain source-backed edge cases' } |
    Select-Object startup_name, current_macro_theme, source_url, source_type, semantic_beta_confidence |
    Sort-Object startup_name
)

$data = [pscustomobject]@{
    summary = $summary
    confidence_counts = $confidenceCounts
    microcluster_counts = $microclusterCounts
    theme_counts = $themeCounts
    theme_coverage = $themeCoverage
    current_macro_counts = $currentMacroCounts
    uncertain_assignments = $uncertainAssignments
}

$json = $data | ConvertTo-Json -Depth 8
$content = "window.SEMANTIC_TAXONOMY_BETA_DATA = $json;"
Set-Content -LiteralPath $OutputPath -Value $content -Encoding UTF8

Write-Output "Semantic taxonomy beta dashboard data built: $OutputPath"
