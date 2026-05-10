param(
  [int]$Limit = 80,
  [string]$PriorityPath = "quality\semantic_curation_priority_current.csv",
  [string]$OutputPath = "quality\summary_enrichment_batch_01.csv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PriorityPath)) {
  throw "Missing priority queue: $PriorityPath. Build quality\semantic_curation_priority_current.csv first."
}

$rows = Import-Csv $PriorityPath

$batch = foreach ($row in ($rows | Select-Object -First $Limit)) {
  $wordCount = 0
  if ($row.current_summary) {
    $wordCount = @(($row.current_summary -replace '[^\p{L}\p{N}\- ]', ' ' -split '\s+') | Where-Object { $_ }).Count
  }

  $needs = @()
  if (-not $row.quality_band) {
    $needs += "assign_quality_band"
  }
  if ($row.semantic_confidence -in @("low", "medium")) {
    $needs += "clarify_semantic_fit"
  }
  if ($row.review_status -eq "seeded") {
    $needs += "upgrade_seeded_to_reviewed"
  }
  if ($row.source_type -match "portfolio|listing") {
    $needs += "find_official_startup_or_product_source"
  }
  if ($row.source_type -match "linkedin|external") {
    $needs += "replace_secondary_source_if_possible"
  }

  $targetWords = if (($row.semantic_confidence -in @("low", "medium")) -or (-not $row.quality_band)) {
    "55-75 words"
  } else {
    "45-60 words"
  }

  [pscustomobject]@{
    startup_name = $row.startup_name
    current_theme = $row.current_theme
    semantic_confidence = $row.semantic_confidence
    semantic_margin = $row.semantic_margin
    current_words = $wordCount
    target_words = $targetWords
    quality_band = $row.quality_band
    review_status = $row.review_status
    source_type = $row.source_type
    source_url = $row.source_url
    action_needed = ($needs -join "; ")
    rewrite_prompt = "Rewrite in English using only auditable source evidence. Include: product, technology/mechanism, market/use case, bio/material/planetary-boundary relevance, and why it belongs in BIO VC LATAM."
    current_one_liner = $row.current_one_liner
    current_summary = $row.current_summary
    evidence_excerpt = $row.evidence_excerpt
  }
}

$batch | Export-Csv $OutputPath -NoTypeInformation -Encoding UTF8
Write-Host "Wrote $OutputPath with $($batch.Count) rows."
