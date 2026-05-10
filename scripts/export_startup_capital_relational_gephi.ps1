param(
    [string]$IntegratedDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\integrated",
    [string]$MasterCsv = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$AssignmentsCsv = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_single_level_assignments.csv",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\gephi_export\startup_capital_relational"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Escape-Xml {
    param([AllowNull()][string]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Security.SecurityElement]::Escape([string]$Value)
}

function Normalize-Confidence {
    param([AllowNull()][string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return 1.0 }
    $parsed = 0.0
    if ([double]::TryParse($Value, [ref]$parsed)) {
        return [Math]::Round($parsed, 3)
    }
    switch ($Value.ToLowerInvariant()) {
        "high" { return 0.9 }
        "medium" { return 0.7 }
        "low" { return 0.45 }
        default { return 1.0 }
    }
}

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$entities = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_entities.csv')
$relations = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_relations.csv')
$master = Import-Csv -LiteralPath $MasterCsv
$assignments = Import-Csv -LiteralPath $AssignmentsCsv

$masterById = @{}
foreach ($row in $master) { $masterById[$row.startup_id] = $row }

$assignmentById = @{}
foreach ($row in $assignments) { $assignmentById[$row.startup_id] = $row }

$entityById = @{}
foreach ($entity in $entities) { $entityById[$entity.entity_id] = $entity }

$fundedBy = @($relations | Where-Object { $_.relation_type -eq 'funded_by' })

$usedNodeIds = [System.Collections.Generic.HashSet[string]]::new()
foreach ($edge in $fundedBy) {
    [void]$usedNodeIds.Add([string]$edge.source_entity_id)
    [void]$usedNodeIds.Add([string]$edge.target_entity_id)
}

$themeColors = @{
    "ag biologicals and crop resilience" = @{ r = 126; g = 87; b = 194 }
    "food ingredients and biofactories" = @{ r = 11; g = 181; b = 214 }
    "industrial enzymes and bioprocess platforms" = @{ r = 139; g = 195; b = 74 }
    "agri intelligence and traceable markets" = @{ r = 217; g = 112; b = 179 }
    "clinical diagnostics and medical devices" = @{ r = 31; g = 78; b = 108 }
    "therapeutics and regenerative bio" = @{ r = 38; g = 166; b = 154 }
    "climate and resource intelligence platforms" = @{ r = 255; g = 112; b = 67 }
}

$nodes = foreach ($nodeId in ($usedNodeIds | Sort-Object)) {
    if (-not $entityById.ContainsKey($nodeId)) { continue }
    $entity = $entityById[$nodeId]
    $isStartup = $entity.integrated_type -eq 'startup'
    $masterRow = if ($isStartup -and $masterById.ContainsKey($nodeId)) { $masterById[$nodeId] } else { $null }
    $assignment = if ($isStartup -and $assignmentById.ContainsKey($nodeId)) { $assignmentById[$nodeId] } else { $null }
    $theme = if ($assignment) { $assignment.semantic_single_theme } else { "" }
    $color =
        if ($entity.integrated_type -eq 'capital') { @{ r = 37; g = 182; b = 106 } }
        elseif ($theme -and $themeColors.ContainsKey($theme)) { $themeColors[$theme] }
        else { @{ r = 150; g = 150; b = 150 } }
    $size =
        if ($entity.integrated_type -eq 'capital') { 18 }
        elseif ($masterRow) { [Math]::Round((6 + [double]$masterRow.data_quality_score_10 * 0.8), 2) }
        else { 7 }

    [PSCustomObject]@{
        Id = $entity.entity_id
        Label = $entity.canonical_name
        NodeType = $entity.integrated_type
        CanonicalType = $entity.canonical_type
        Slug = $entity.slug
        IntegratedSources = $entity.integrated_sources
        SourcePresence = $entity.source_presence
        EntityConfidence = $entity.confidence_score
        ScopeDecision = if ($masterRow) { $masterRow.scope_decision } else { "" }
        ScopeStatus = if ($masterRow) { $masterRow.scope_status } else { "" }
        QualityBand = if ($masterRow) { $masterRow.quality_band } else { "" }
        QualityScore = if ($masterRow) { $masterRow.data_quality_score_10 } else { "" }
        SourceUrl = if ($masterRow) { $masterRow.source_url } else { "" }
        SemanticTheme = $theme
        SemanticClusterId = if ($assignment) { $assignment.semantic_single_cluster_id } else { "" }
        SemanticConfidence = if ($assignment) { $assignment.semantic_single_confidence } else { "" }
        Summary = if ($masterRow) { $masterRow.startup_summary_v1 } else { "" }
        OneLiner = if ($masterRow) { $masterRow.business_one_liner } else { "" }
        Country = if ($masterRow) { $masterRow.structured_country } else { "" }
        r = $color.r
        g = $color.g
        b = $color.b
        Size = $size
    }
}

$edgeRows = foreach ($relation in ($fundedBy | Sort-Object source_entity_id, target_entity_id)) {
    [PSCustomObject]@{
        Source = $relation.source_entity_id
        Target = $relation.target_entity_id
        Type = "Directed"
        Weight = Normalize-Confidence $relation.confidence
        RelationType = $relation.relation_type
        Confidence = $relation.confidence
        SourceKind = $relation.source_kind
        Notes = $relation.notes
    }
}

$nodes | Export-Csv -LiteralPath (Join-Path $OutputDir 'nodes.csv') -NoTypeInformation -Encoding UTF8
$edgeRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'edges.csv') -NoTypeInformation -Encoding UTF8

$graphMl = [System.Collections.Generic.List[string]]::new()
$null = $graphMl.Add('<?xml version="1.0" encoding="UTF-8"?>')
$null = $graphMl.Add('<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:viz="http://www.gephi.org/gexf/viz" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">')
$null = $graphMl.Add('  <key id="label" for="node" attr.name="label" attr.type="string"/>')
$null = $graphMl.Add('  <key id="node_type" for="node" attr.name="node_type" attr.type="string"/>')
$null = $graphMl.Add('  <key id="canonical_type" for="node" attr.name="canonical_type" attr.type="string"/>')
$null = $graphMl.Add('  <key id="slug" for="node" attr.name="slug" attr.type="string"/>')
$null = $graphMl.Add('  <key id="integrated_sources" for="node" attr.name="integrated_sources" attr.type="string"/>')
$null = $graphMl.Add('  <key id="source_presence" for="node" attr.name="source_presence" attr.type="string"/>')
$null = $graphMl.Add('  <key id="entity_confidence" for="node" attr.name="entity_confidence" attr.type="double"/>')
$null = $graphMl.Add('  <key id="scope_decision" for="node" attr.name="scope_decision" attr.type="string"/>')
$null = $graphMl.Add('  <key id="scope_status" for="node" attr.name="scope_status" attr.type="string"/>')
$null = $graphMl.Add('  <key id="quality_band" for="node" attr.name="quality_band" attr.type="string"/>')
$null = $graphMl.Add('  <key id="quality_score" for="node" attr.name="quality_score" attr.type="double"/>')
$null = $graphMl.Add('  <key id="source_url" for="node" attr.name="source_url" attr.type="string"/>')
$null = $graphMl.Add('  <key id="semantic_theme" for="node" attr.name="semantic_theme" attr.type="string"/>')
$null = $graphMl.Add('  <key id="semantic_cluster_id" for="node" attr.name="semantic_cluster_id" attr.type="string"/>')
$null = $graphMl.Add('  <key id="semantic_confidence" for="node" attr.name="semantic_confidence" attr.type="string"/>')
$null = $graphMl.Add('  <key id="summary" for="node" attr.name="summary" attr.type="string"/>')
$null = $graphMl.Add('  <key id="one_liner" for="node" attr.name="one_liner" attr.type="string"/>')
$null = $graphMl.Add('  <key id="country" for="node" attr.name="country" attr.type="string"/>')
$null = $graphMl.Add('  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>')
$null = $graphMl.Add('  <key id="relation_type" for="edge" attr.name="relation_type" attr.type="string"/>')
$null = $graphMl.Add('  <key id="confidence" for="edge" attr.name="confidence" attr.type="double"/>')
$null = $graphMl.Add('  <key id="source_kind" for="edge" attr.name="source_kind" attr.type="string"/>')
$null = $graphMl.Add('  <key id="notes" for="edge" attr.name="notes" attr.type="string"/>')
$null = $graphMl.Add('  <graph id="startup_capital_relational" edgedefault="directed">')
$null = $graphMl.Add('    <nodes>')

foreach ($node in ($nodes | Sort-Object NodeType, Label)) {
    $null = $graphMl.Add("      <node id=""$(Escape-Xml $node.Id)"">")
    $null = $graphMl.Add("        <data key=""label"">$(Escape-Xml $node.Label)</data>")
    $null = $graphMl.Add("        <data key=""node_type"">$(Escape-Xml $node.NodeType)</data>")
    $null = $graphMl.Add("        <data key=""canonical_type"">$(Escape-Xml $node.CanonicalType)</data>")
    $null = $graphMl.Add("        <data key=""slug"">$(Escape-Xml $node.Slug)</data>")
    $null = $graphMl.Add("        <data key=""integrated_sources"">$(Escape-Xml $node.IntegratedSources)</data>")
    $null = $graphMl.Add("        <data key=""source_presence"">$(Escape-Xml $node.SourcePresence)</data>")
    $null = $graphMl.Add("        <data key=""entity_confidence"">$(Escape-Xml $node.EntityConfidence)</data>")
    $null = $graphMl.Add("        <data key=""scope_decision"">$(Escape-Xml $node.ScopeDecision)</data>")
    $null = $graphMl.Add("        <data key=""scope_status"">$(Escape-Xml $node.ScopeStatus)</data>")
    $null = $graphMl.Add("        <data key=""quality_band"">$(Escape-Xml $node.QualityBand)</data>")
    $null = $graphMl.Add("        <data key=""quality_score"">$(Escape-Xml $node.QualityScore)</data>")
    $null = $graphMl.Add("        <data key=""source_url"">$(Escape-Xml $node.SourceUrl)</data>")
    $null = $graphMl.Add("        <data key=""semantic_theme"">$(Escape-Xml $node.SemanticTheme)</data>")
    $null = $graphMl.Add("        <data key=""semantic_cluster_id"">$(Escape-Xml $node.SemanticClusterId)</data>")
    $null = $graphMl.Add("        <data key=""semantic_confidence"">$(Escape-Xml $node.SemanticConfidence)</data>")
    $null = $graphMl.Add("        <data key=""summary"">$(Escape-Xml $node.Summary)</data>")
    $null = $graphMl.Add("        <data key=""one_liner"">$(Escape-Xml $node.OneLiner)</data>")
    $null = $graphMl.Add("        <data key=""country"">$(Escape-Xml $node.Country)</data>")
    $null = $graphMl.Add("        <viz:color r=""$(Escape-Xml $node.r)"" g=""$(Escape-Xml $node.g)"" b=""$(Escape-Xml $node.b)""/>")
    $null = $graphMl.Add("        <viz:size value=""$(Escape-Xml $node.Size)""/>")
    $null = $graphMl.Add('      </node>')
}

$null = $graphMl.Add('    </nodes>')
$null = $graphMl.Add('    <edges>')
$edgeId = 0
foreach ($edge in $edgeRows) {
    $null = $graphMl.Add("      <edge id=""$edgeId"" source=""$(Escape-Xml $edge.Source)"" target=""$(Escape-Xml $edge.Target)"">")
    $null = $graphMl.Add("        <data key=""weight"">$(Escape-Xml $edge.Weight)</data>")
    $null = $graphMl.Add("        <data key=""relation_type"">$(Escape-Xml $edge.RelationType)</data>")
    $null = $graphMl.Add("        <data key=""confidence"">$(Escape-Xml $edge.Confidence)</data>")
    $null = $graphMl.Add("        <data key=""source_kind"">$(Escape-Xml $edge.SourceKind)</data>")
    $null = $graphMl.Add("        <data key=""notes"">$(Escape-Xml $edge.Notes)</data>")
    $null = $graphMl.Add('      </edge>')
    $edgeId++
}
$null = $graphMl.Add('    </edges>')
$null = $graphMl.Add('  </graph>')
$null = $graphMl.Add('</graphml>')

Set-Content -LiteralPath (Join-Path $OutputDir 'startup_capital_relational.graphml') -Value $graphMl -Encoding UTF8

$summary = @"
Startup-capital relational export for Gephi

Files:
- nodes.csv
- edges.csv
- startup_capital_relational.graphml

Scope:
- only capital nodes
- only startup nodes that participate in funded_by relations
- only funded_by edges

Counts:
- Nodes: $(@($nodes).Count)
- Capital nodes: $(@($nodes | Where-Object { $_.NodeType -eq 'capital' }).Count)
- Startup nodes: $(@($nodes | Where-Object { $_.NodeType -eq 'startup' }).Count)
- Edges: $(@($edgeRows).Count)

Useful Gephi filters:
- node_type
- scope_decision
- scope_status
- semantic_theme
- quality_band
"@

Set-Content -LiteralPath (Join-Path $OutputDir 'README.txt') -Value $summary -Encoding UTF8
Write-Output "Startup-capital relational Gephi export complete: $OutputDir"
