param(
    [string]$IntegratedDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\integrated",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\gephi_export"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Escape-Xml {
    param([AllowNull()][string]$Value)

    if ($null -eq $Value) { return '' }
    return [System.Security.SecurityElement]::Escape([string]$Value)
}

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$entities = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_entities.csv')
$relations = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_relations.csv')
$provenance = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_provenance.csv')

$neighbors = @{}
foreach ($relation in $relations) {
    if (-not $neighbors.ContainsKey($relation.source_entity_id)) {
        $neighbors[$relation.source_entity_id] = New-Object System.Collections.Generic.HashSet[string]
    }
    if (-not $neighbors.ContainsKey($relation.target_entity_id)) {
        $neighbors[$relation.target_entity_id] = New-Object System.Collections.Generic.HashSet[string]
    }
    [void]$neighbors[$relation.source_entity_id].Add([string]$relation.target_entity_id)
    [void]$neighbors[$relation.target_entity_id].Add([string]$relation.source_entity_id)
}

$degree = @{}
foreach ($entityId in $neighbors.Keys) {
    $degree[$entityId] = $neighbors[$entityId].Count
}

$provenanceCount = @{}
foreach ($row in $provenance) {
    if (-not $provenanceCount.ContainsKey($row.entity_id)) { $provenanceCount[$row.entity_id] = 0 }
    $provenanceCount[$row.entity_id]++
}

$nodes = foreach ($entity in $entities) {
    $d = if ($degree.ContainsKey($entity.entity_id)) { [int]$degree[$entity.entity_id] } else { 0 }
    $size =
        if ($entity.integrated_type -eq 'capital') { [Math]::Min(60, 10 + $d * 1.2) }
        elseif ($entity.integrated_type -eq 'institution') { [Math]::Min(42, 8 + $d * 0.9) }
        else { [Math]::Min(18, 4 + $d * 0.3) }

    $r = if ($entity.integrated_type -eq 'capital') { 37 } elseif ($entity.integrated_type -eq 'institution') { 255 } else { 124 }
    $g = if ($entity.integrated_type -eq 'capital') { 182 } elseif ($entity.integrated_type -eq 'institution') { 123 } else { 131 }
    $b = if ($entity.integrated_type -eq 'capital') { 106 } elseif ($entity.integrated_type -eq 'institution') { 44 } else { 253 }

    [PSCustomObject]@{
        Id = $entity.entity_id
        Label = $entity.canonical_name
        Type = $entity.integrated_type
        CanonicalType = $entity.canonical_type
        Degree = $d
        Size = [Math]::Round($size, 2)
        Confidence = $entity.confidence_score
        Sources = $entity.integrated_sources
        SourcePresence = $entity.source_presence
        ProvenanceRows = if ($provenanceCount.ContainsKey($entity.entity_id)) { $provenanceCount[$entity.entity_id] } else { 0 }
        QualityFlags = $entity.quality_flags
        Slug = $entity.slug
        r = $r
        g = $g
        b = $b
    }
}

$edgeRows = @()
$seen = @{}
foreach ($relation in $relations) {
    $key = "$($relation.source_entity_id)|$($relation.target_entity_id)|$($relation.relation_type)|$($relation.source_kind)"
    if ($seen.ContainsKey($key)) { continue }
    $seen[$key] = $true

    $weight =
        if ($relation.relation_type -eq 'funded_by') { 2.0 }
        elseif ($relation.relation_type -in @('researched_at', 'studied_at')) { 1.5 }
        else { 1.0 }

    $edgeRows += [PSCustomObject]@{
        Source = $relation.source_entity_id
        Target = $relation.target_entity_id
        Type = "Undirected"
        Weight = $weight
        RelationType = $relation.relation_type
        Confidence = $relation.confidence
        SourceKind = $relation.source_kind
        Notes = $relation.notes
    }
}

$graphMlLines = [System.Collections.Generic.List[string]]::new()
$null = $graphMlLines.Add('<?xml version="1.0" encoding="UTF-8"?>')
$null = $graphMlLines.Add('<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:viz="http://www.gephi.org/gexf/viz" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">')
$null = $graphMlLines.Add('  <key id="label" for="node" attr.name="label" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="type" for="node" attr.name="type" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="canonical_type" for="node" attr.name="canonical_type" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="degree" for="node" attr.name="degree" attr.type="int"/>')
$null = $graphMlLines.Add('  <key id="size" for="node" attr.name="size" attr.type="double"/>')
$null = $graphMlLines.Add('  <key id="confidence" for="node" attr.name="confidence" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="sources" for="node" attr.name="sources" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="source_presence" for="node" attr.name="source_presence" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="provenance_rows" for="node" attr.name="provenance_rows" attr.type="int"/>')
$null = $graphMlLines.Add('  <key id="quality_flags" for="node" attr.name="quality_flags" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="slug" for="node" attr.name="slug" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>')
$null = $graphMlLines.Add('  <key id="relation_type" for="edge" attr.name="relation_type" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="edge_confidence" for="edge" attr.name="confidence" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="source_kind" for="edge" attr.name="source_kind" attr.type="string"/>')
$null = $graphMlLines.Add('  <key id="notes" for="edge" attr.name="notes" attr.type="string"/>')
$null = $graphMlLines.Add('  <graph id="ecosystem" edgedefault="undirected">')
$null = $graphMlLines.Add('    <nodes>')

foreach ($node in ($nodes | Sort-Object Type, Label)) {
    $null = $graphMlLines.Add("      <node id=""$(Escape-Xml $node.Id)"">")
    $null = $graphMlLines.Add("        <data key=""label"">$(Escape-Xml $node.Label)</data>")
    $null = $graphMlLines.Add("        <data key=""type"">$(Escape-Xml $node.Type)</data>")
    $null = $graphMlLines.Add("        <data key=""canonical_type"">$(Escape-Xml $node.CanonicalType)</data>")
    $null = $graphMlLines.Add("        <data key=""degree"">$(Escape-Xml $node.Degree)</data>")
    $null = $graphMlLines.Add("        <data key=""size"">$(Escape-Xml $node.Size)</data>")
    $null = $graphMlLines.Add("        <data key=""confidence"">$(Escape-Xml $node.Confidence)</data>")
    $null = $graphMlLines.Add("        <data key=""sources"">$(Escape-Xml $node.Sources)</data>")
    $null = $graphMlLines.Add("        <data key=""source_presence"">$(Escape-Xml $node.SourcePresence)</data>")
    $null = $graphMlLines.Add("        <data key=""provenance_rows"">$(Escape-Xml $node.ProvenanceRows)</data>")
    $null = $graphMlLines.Add("        <data key=""quality_flags"">$(Escape-Xml $node.QualityFlags)</data>")
    $null = $graphMlLines.Add("        <data key=""slug"">$(Escape-Xml $node.Slug)</data>")
    $null = $graphMlLines.Add("        <viz:color r=""$(Escape-Xml $node.r)"" g=""$(Escape-Xml $node.g)"" b=""$(Escape-Xml $node.b)""/>")
    $null = $graphMlLines.Add("        <viz:size value=""$(Escape-Xml $node.Size)""/>")
    $null = $graphMlLines.Add('      </node>')
}

$null = $graphMlLines.Add('    </nodes>')
$null = $graphMlLines.Add('    <edges>')

$edgeId = 0
foreach ($edge in ($edgeRows | Sort-Object RelationType, Source, Target)) {
    $null = $graphMlLines.Add("      <edge id=""$edgeId"" source=""$(Escape-Xml $edge.Source)"" target=""$(Escape-Xml $edge.Target)"">")
    $null = $graphMlLines.Add("        <data key=""weight"">$(Escape-Xml $edge.Weight)</data>")
    $null = $graphMlLines.Add("        <data key=""relation_type"">$(Escape-Xml $edge.RelationType)</data>")
    $null = $graphMlLines.Add("        <data key=""edge_confidence"">$(Escape-Xml $edge.Confidence)</data>")
    $null = $graphMlLines.Add("        <data key=""source_kind"">$(Escape-Xml $edge.SourceKind)</data>")
    $null = $graphMlLines.Add("        <data key=""notes"">$(Escape-Xml $edge.Notes)</data>")
    $null = $graphMlLines.Add('      </edge>')
    $edgeId++
}

$null = $graphMlLines.Add('    </edges>')
$null = $graphMlLines.Add('  </graph>')
$null = $graphMlLines.Add('</graphml>')

$nodes |
    Sort-Object Type, Label |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'nodes.csv') -NoTypeInformation -Encoding UTF8

$edgeRows |
    Sort-Object RelationType, Source, Target |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'edges.csv') -NoTypeInformation -Encoding UTF8

Set-Content -LiteralPath (Join-Path $OutputDir 'ecosystem.graphml') -Value $graphMlLines -Encoding UTF8

$summary = @"
Export para Gephi

Archivos:
- nodes.csv
- edges.csv
- ecosystem.graphml

Columnas clave en nodes.csv:
- Id
- Label
- Type
- CanonicalType
- Degree
- Size
- Confidence
- Sources
- ProvenanceRows
- QualityFlags
- r/g/b

Columnas clave en edges.csv:
- Source
- Target
- Type
- Weight
- RelationType
- Confidence
- SourceKind
- Notes

Resumen:
- Nodes: $(@($nodes).Count)
- Edges: $(@($edgeRows).Count)
- Capital nodes: $(@($nodes | Where-Object { $_.Type -eq 'capital' }).Count)
- Institution nodes: $(@($nodes | Where-Object { $_.Type -eq 'institution' }).Count)
- Startup nodes: $(@($nodes | Where-Object { $_.Type -eq 'startup' }).Count)
"@

Set-Content -LiteralPath (Join-Path $OutputDir 'README.txt') -Value $summary -Encoding UTF8

Write-Output "Gephi export complete: $OutputDir"
