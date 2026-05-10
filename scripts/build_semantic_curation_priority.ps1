param(
  [string]$MasterPath = "startup_master_dataset.csv",
  [string]$SemanticAssignmentsPath = "quality\semantic_single_level_assignments.csv",
  [string]$OutputPath = "quality\semantic_curation_priority_current.csv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $MasterPath)) {
  throw "Missing master dataset: $MasterPath"
}
if (-not (Test-Path $SemanticAssignmentsPath)) {
  throw "Missing semantic assignments: $SemanticAssignmentsPath"
}

$master = Import-Csv $MasterPath
$semanticRows = Import-Csv $SemanticAssignmentsPath

$semanticByName = @{}
foreach ($row in $semanticRows) {
  $semanticByName[[string]$row.startup_name] = $row
}

$rows = foreach ($row in ($master | Where-Object { $_.scope_decision -eq "include" })) {
  $semantic = $semanticByName[[string]$row.startup_name]
  $priority = 999
  $reasons = @()

  if (-not $row.quality_band) {
    $priority -= 300
    $reasons += "missing_quality_band"
  }
  if ($semantic.semantic_single_confidence -eq "low") {
    $priority -= 250
    $reasons += "low_semantic_confidence"
  } elseif ($semantic.semantic_single_confidence -eq "medium") {
    $priority -= 150
    $reasons += "medium_semantic_confidence"
  }
  if ($row.review_status -eq "seeded") {
    $priority -= 100
    $reasons += "seeded_not_reviewed"
  }
  if ($row.source_type -match "portfolio|listing") {
    $priority -= 35
    $reasons += "fund_profile_needs_startup_source_check"
  }
  if ($row.source_type -match "linkedin|external_profile|f6s") {
    $priority -= 50
    $reasons += "weak_or_secondary_source"
  }
  if ($row.startup_summary_v1 -match "Entra en tesis|Startup|Plataforma|produccion|agricultura|biotecnologica") {
    $priority -= 20
    $reasons += "summary_not_normalized_to_english"
  }

  [pscustomobject]@{
    priority_rank_score = $priority
    startup_name = $row.startup_name
    current_theme = $semantic.semantic_single_theme
    semantic_confidence = $semantic.semantic_single_confidence
    semantic_margin = $semantic.semantic_single_margin
    data_quality_score_10 = $row.data_quality_score_10
    quality_band = $row.quality_band
    review_status = $row.review_status
    source_type = $row.source_type
    source_url = $row.source_url
    curation_reasons = ($reasons -join "; ")
    current_one_liner = $row.business_one_liner
    current_summary = $row.startup_summary_v1
    evidence_excerpt = $row.evidence_excerpt
    suggested_action = if (-not $row.quality_band) {
      "add quality score/band and rewrite source-backed English summary"
    } elseif ($semantic.semantic_single_confidence -in @("low", "medium")) {
      "verify cluster fit and enrich description with technology, biology/materiality, market"
    } elseif ($row.review_status -eq "seeded") {
      "upgrade from seeded to reviewed using official startup/product source"
    } else {
      "spot-check"
    }
  }
}

$rows |
  Sort-Object priority_rank_score, @{ Expression = { if ($_.semantic_margin) { [double]($_.semantic_margin -replace ",", ".") } else { 9999 } } } |
  Export-Csv $OutputPath -NoTypeInformation -Encoding UTF8

Write-Host "Wrote $OutputPath"
