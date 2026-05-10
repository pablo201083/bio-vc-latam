param(
    [string]$CanonicalDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\canonical",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\data"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$entities = Import-Csv -LiteralPath (Join-Path $CanonicalDir 'canonical_entities.csv')
$aliases = Import-Csv -LiteralPath (Join-Path $CanonicalDir 'canonical_aliases.csv')
$edges = Import-Csv -LiteralPath (Join-Path $CanonicalDir 'canonical_investment_edges.csv')
$review = Import-Csv -LiteralPath (Join-Path $CanonicalDir 'canonical_review_queue.csv')
$summary = Import-Csv -LiteralPath (Join-Path $CanonicalDir 'canonical_summary.csv')

$entityById = @{}
foreach ($entity in $entities) {
    $entityById[$entity.entity_id] = $entity
}

$investorStats = @{}
$startupStats = @{}

foreach ($edge in $edges) {
    if (-not $investorStats.ContainsKey($edge.investor_id)) {
        $investorStats[$edge.investor_id] = 0
    }
    if (-not $startupStats.ContainsKey($edge.startup_id)) {
        $startupStats[$edge.startup_id] = 0
    }
    $investorStats[$edge.investor_id]++
    $startupStats[$edge.startup_id]++
}

$topInvestors = $investorStats.GetEnumerator() |
    Sort-Object Value -Descending |
    Select-Object -First 20 |
    ForEach-Object {
        [PSCustomObject]@{
            entity_id = $_.Key
            canonical_name = $entityById[$_.Key].canonical_name
            investment_count = $_.Value
            source_presence = $entityById[$_.Key].source_presence
            confidence_score = $entityById[$_.Key].confidence_score
        }
    }

$topStartups = $startupStats.GetEnumerator() |
    Sort-Object Value -Descending |
    Select-Object -First 20 |
    ForEach-Object {
        [PSCustomObject]@{
            entity_id = $_.Key
            canonical_name = $entityById[$_.Key].canonical_name
            investor_count = $_.Value
            source_presence = $entityById[$_.Key].source_presence
            confidence_score = $entityById[$_.Key].confidence_score
        }
    }

$pilotSummary = [PSCustomObject]@{
    entities_total = @($entities).Count
    investors_total = @($entities | Where-Object { $_.entity_type -eq 'investor' }).Count
    startups_total = @($entities | Where-Object { $_.entity_type -eq 'startup' }).Count
    investment_edges_total = @($edges).Count
    aliases_total = @($aliases).Count
    review_queue_total = @($review).Count
}

$graphInvestorIds = $investorStats.GetEnumerator() |
    Sort-Object Value -Descending |
    Select-Object -First 12 |
    ForEach-Object { $_.Key }

$graphEdgeList = $edges |
    Where-Object { $graphInvestorIds -contains $_.investor_id } |
    Sort-Object investor_id, startup_id

$graphStartupIds = $graphEdgeList |
    Group-Object startup_id |
    Sort-Object Count -Descending |
    Select-Object -First 48 |
    ForEach-Object { $_.Name }

$graphEdgeList = $graphEdgeList |
    Where-Object { $graphStartupIds -contains $_.startup_id }

$graphNodes = @()

foreach ($investorId in $graphInvestorIds) {
    if ($entityById.ContainsKey($investorId)) {
        $investorDegree = if ($investorStats.ContainsKey($investorId)) { $investorStats[$investorId] } else { 0 }
        $graphNodes += [PSCustomObject]@{
            id = $investorId
            label = $entityById[$investorId].canonical_name
            type = 'investor'
            degree = $investorDegree
            source_presence = $entityById[$investorId].source_presence
            confidence_score = $entityById[$investorId].confidence_score
        }
    }
}

foreach ($startupId in $graphStartupIds) {
    if ($entityById.ContainsKey($startupId)) {
        $startupDegree = if ($startupStats.ContainsKey($startupId)) { $startupStats[$startupId] } else { 0 }
        $graphNodes += [PSCustomObject]@{
            id = $startupId
            label = $entityById[$startupId].canonical_name
            type = 'startup'
            degree = $startupDegree
            source_presence = $entityById[$startupId].source_presence
            confidence_score = $entityById[$startupId].confidence_score
        }
    }
}

$graphNodeArray = $graphNodes
$graphEdgeArray = @(
    $graphEdgeList | ForEach-Object {
        [PSCustomObject]@{
            id = $_.investment_id
            source = $_.investor_id
            target = $_.startup_id
            confidence_score = $_.confidence_score
            source_file = $_.source_file
        }
    }
)

$graphData = [PSCustomObject]@{
    generated_at = (Get-Date).ToString('s')
    description = 'Subgrafo bipartito de inversores top y startups conectadas'
    nodes = $graphNodeArray
    edges = $graphEdgeArray
}

$dashboard = [PSCustomObject]@{
    generated_at = (Get-Date).ToString('s')
    summary = $pilotSummary
    top_investors = @($topInvestors)
    top_startups = @($topStartups)
    source_summary = @($summary)
}

$dashboard | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDir 'dashboard.json') -Encoding UTF8
$entities | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDir 'entities.json') -Encoding UTF8
$aliases | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDir 'aliases.json') -Encoding UTF8
$edges | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDir 'investment_edges.json') -Encoding UTF8
$review | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDir 'review_queue.json') -Encoding UTF8
$graphData | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDir 'graph.json') -Encoding UTF8

$embedded = [PSCustomObject]@{
    dashboard = $dashboard
    entities = $entities
    aliases = $aliases
    investment_edges = $edges
    review_queue = $review
    graph = $graphData
}

$embeddedJs = "window.PILOT_DATA = " + ($embedded | ConvertTo-Json -Depth 8) + ";"
Set-Content -LiteralPath (Join-Path $OutputDir 'embedded-data.js') -Value $embeddedJs -Encoding UTF8

Write-Output "Pilot data built: $OutputDir"
