param(
    [string]$AssignmentsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_beta_assignments.csv",
    [string]$OutputJsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\semantic-beta-assignments-data.js"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $AssignmentsPath)) {
    throw "Missing semantic beta assignments CSV: $AssignmentsPath"
}

$rows = Import-Csv -LiteralPath $AssignmentsPath
$assignmentsById = [ordered]@{}

foreach ($row in $rows) {
    $startupId = [string]$row.startup_id
    if ([string]::IsNullOrWhiteSpace($startupId)) { continue }

    $assignmentsById[$startupId] = [ordered]@{
        startup_id = $row.startup_id
        startup_name = $row.startup_name
        current_macro_theme = $row.current_macro_theme
        current_emergent_theme = $row.current_emergent_theme
        semantic_beta_theme = $row.semantic_beta_theme
        semantic_beta_score = $row.semantic_beta_score
        semantic_beta_margin = $row.semantic_beta_margin
        semantic_beta_confidence = $row.semantic_beta_confidence
        gridx_match = $row.gridx_match
        antom_match = $row.antom_match
        matched_signals = $row.matched_signals
        source_url = $row.source_url
        source_type = $row.source_type
        review_status = $row.review_status
        evidence_excerpt = $row.evidence_excerpt
        startup_summary_v1 = $row.startup_summary_v1
    }
}

$payload = [ordered]@{
    assignmentsById = $assignmentsById
}

$json = $payload | ConvertTo-Json -Depth 8
$content = "window.SEMANTIC_BETA_ASSIGNMENTS = $json;"
Set-Content -LiteralPath $OutputJsPath -Value $content -Encoding UTF8

Write-Output "Semantic beta assignments JS built: $OutputJsPath"
