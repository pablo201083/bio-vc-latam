param(
    [string]$DesktopPath = [Environment]::GetFolderPath('Desktop'),
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function New-DirIfMissing {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function New-Slug {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
    $slug = $Text.ToLowerInvariant()
    $slug = $slug -replace '[^a-z0-9]+', '-'
    $slug = $slug.Trim('-')
    return $slug
}

function Get-ConfidenceFromSources {
    param(
        [bool]$InNodesCsv,
        [bool]$InGraphMl
    )
    if ($InNodesCsv -and $InGraphMl) { return 0.9 }
    if ($InNodesCsv -or $InGraphMl) { return 0.6 }
    return 0.2
}

New-DirIfMissing -Path $OutputDir

$nodesCsvPath = Join-Path $DesktopPath 'nodoseco.csv'
$edgesCsvPath = Join-Path $DesktopPath 'edgeseco.csv'
$graphMlPath = Join-Path $DesktopPath 'latam_coinvest_network_v3.graphml'

$issues = New-Object System.Collections.Generic.List[object]
$entities = @{}
$metrics = New-Object System.Collections.Generic.List[object]
$edgePairs = New-Object System.Collections.Generic.HashSet[string]
$investmentEdges = New-Object System.Collections.Generic.List[object]

if (-not (Test-Path -LiteralPath $nodesCsvPath)) {
    throw "Missing required file: $nodesCsvPath"
}
if (-not (Test-Path -LiteralPath $edgesCsvPath)) {
    throw "Missing required file: $edgesCsvPath"
}
if (-not (Test-Path -LiteralPath $graphMlPath)) {
    throw "Missing required file: $graphMlPath"
}

$nodesCsv = Import-Csv -LiteralPath $nodesCsvPath
foreach ($row in $nodesCsv) {
    $entityId = [string]$row.Id
    $label = [string]$row.Label
    $entityType = [string]$row.'0'
    if ([string]::IsNullOrWhiteSpace($entityId)) {
        $issues.Add([PSCustomObject]@{
            issue_type = 'missing_entity_id'
            entity_id = ''
            context = 'nodoseco.csv'
            severity = 'high'
            notes = 'Row without Id in nodes CSV'
        })
        continue
    }

    if (-not $entities.ContainsKey($entityId)) {
        $entities[$entityId] = [PSCustomObject]@{
            entity_id = $entityId
            canonical_name = $label
            slug = New-Slug -Text $label
            entity_type_raw = $entityType
            in_nodes_csv = $true
            in_graphml = $false
            name_from_nodes_csv = $label
            name_from_graphml = ''
            quality_flags = ''
            confidence_score = 0.0
        }
    }

    $metrics.Add([PSCustomObject]@{
        entity_id = $entityId
        source_name = 'nodoseco.csv'
        pagerank = $row.pageranks
        indegree = $row.indegree
        outdegree = $row.outdegree
        degree_total = $row.Degree
        weighted_indegree = $row.'weighted indegree'
        weighted_outdegree = $row.'weighted outdegree'
        weighted_degree = $row.'Weighted Degree'
    })
}

$xml = [xml](Get-Content -LiteralPath $graphMlPath -Raw)
$ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
$ns.AddNamespace('g', 'http://graphml.graphdrawing.org/xmlns')
$graphNodes = $xml.SelectNodes('//g:node', $ns)
$graphEdges = $xml.SelectNodes('//g:edge', $ns)

foreach ($node in $graphNodes) {
    $entityId = [string]$node.id
    $labelNode = $node.SelectSingleNode("g:data[@key='d0']", $ns)
    $typeNode = $node.SelectSingleNode("g:data[@key='d1']", $ns)
    $label = if ($labelNode) { [string]$labelNode.InnerText } else { '' }
    $entityType = if ($typeNode) { [string]$typeNode.InnerText } else { '' }

    if (-not $entities.ContainsKey($entityId)) {
        $entities[$entityId] = [PSCustomObject]@{
            entity_id = $entityId
            canonical_name = $label
            slug = New-Slug -Text $label
            entity_type_raw = $entityType
            in_nodes_csv = $false
            in_graphml = $true
            name_from_nodes_csv = ''
            name_from_graphml = $label
            quality_flags = ''
            confidence_score = 0.0
        }
    } else {
        $existing = $entities[$entityId]
        $existing.in_graphml = $true
        $existing.name_from_graphml = $label
        if ([string]::IsNullOrWhiteSpace($existing.canonical_name) -and -not [string]::IsNullOrWhiteSpace($label)) {
            $existing.canonical_name = $label
            $existing.slug = New-Slug -Text $label
        }
        if ([string]::IsNullOrWhiteSpace($existing.entity_type_raw) -and -not [string]::IsNullOrWhiteSpace($entityType)) {
            $existing.entity_type_raw = $entityType
        }
    }
}

foreach ($graphEdge in $graphEdges) {
    $sourceId = [string]$graphEdge.source
    $targetId = [string]$graphEdge.target
    $pairKey = "$sourceId->$targetId"
    if (-not $edgePairs.Contains($pairKey)) {
        [void]$edgePairs.Add($pairKey)
        $investmentEdges.Add([PSCustomObject]@{
            raw_edge_id = [string]$graphEdge.id
            source_id = $sourceId
            target_id = $targetId
            source_file = 'latam_coinvest_network_v3.graphml'
            relation_type_raw = 'investment_or_membership'
            direction_status = 'needs_review'
            investor_id_candidate = ''
            startup_id_candidate = ''
            confidence_score = 0.4
            notes = 'GraphML edge direction is not assumed canonical'
        })
    }
}

$edgesCsv = Import-Csv -LiteralPath $edgesCsvPath
foreach ($row in $edgesCsv) {
    $sourceId = [string]$row.Source
    $targetId = [string]$row.Target
    $edgeType = [string]$row.'1'
    $pairKey = "$sourceId->$targetId"
    if (-not $edgePairs.Contains($pairKey)) {
        [void]$edgePairs.Add($pairKey)
        $investmentEdges.Add([PSCustomObject]@{
            raw_edge_id = [string]$row.Id
            source_id = $sourceId
            target_id = $targetId
            source_file = 'edgeseco.csv'
            relation_type_raw = $edgeType
            direction_status = 'candidate_investor_to_startup'
            investor_id_candidate = $sourceId
            startup_id_candidate = $targetId
            confidence_score = 0.7
            notes = 'CSV suggests investor to startup direction but must be validated against canonical entity types'
        })
    }
}

foreach ($key in $entities.Keys) {
    $entity = $entities[$key]
    $flags = New-Object System.Collections.Generic.List[string]

    if ([string]::IsNullOrWhiteSpace($entity.canonical_name)) {
        $flags.Add('missing_name')
    }
    if ([string]::IsNullOrWhiteSpace($entity.entity_type_raw)) {
        $flags.Add('missing_type')
    }
    if ($entity.in_nodes_csv -and $entity.in_graphml) {
        if ($entity.name_from_nodes_csv -ne $entity.name_from_graphml -and `
            -not [string]::IsNullOrWhiteSpace($entity.name_from_nodes_csv) -and `
            -not [string]::IsNullOrWhiteSpace($entity.name_from_graphml)) {
            $flags.Add('name_mismatch_between_sources')
        }
    }
    if ($entity.canonical_name -match 'Ã|�') {
        $flags.Add('encoding_issue')
    }
    if ($entity.canonical_name -match 'sillicon') {
        $flags.Add('possible_typo')
    }
    if ($entity.entity_type_raw -notin @('startup', 'investor')) {
        $flags.Add('unknown_type_for_current_import')
    }

    $entity.quality_flags = ($flags -join '|')
    $entity.confidence_score = Get-ConfidenceFromSources -InNodesCsv:$entity.in_nodes_csv -InGraphMl:$entity.in_graphml

    foreach ($flag in $flags) {
        $issues.Add([PSCustomObject]@{
            issue_type = $flag
            entity_id = $entity.entity_id
            context = 'entity'
            severity = if ($flag -in @('missing_name', 'missing_type')) { 'high' } else { 'medium' }
            notes = $entity.canonical_name
        })
    }
}

foreach ($edge in $investmentEdges) {
    $sourceEntity = if ($entities.ContainsKey($edge.source_id)) { $entities[$edge.source_id] } else { $null }
    $targetEntity = if ($entities.ContainsKey($edge.target_id)) { $entities[$edge.target_id] } else { $null }

    if ($sourceEntity -and $targetEntity) {
        if ($sourceEntity.entity_type_raw -eq 'investor' -and $targetEntity.entity_type_raw -eq 'startup') {
            $edge.direction_status = 'validated_investor_to_startup'
            $edge.investor_id_candidate = $edge.source_id
            $edge.startup_id_candidate = $edge.target_id
            $edge.confidence_score = [Math]::Max([double]$edge.confidence_score, 0.95)
        } elseif ($sourceEntity.entity_type_raw -eq 'startup' -and $targetEntity.entity_type_raw -eq 'investor') {
            $edge.direction_status = 'validated_startup_to_investor_reverse'
            $edge.investor_id_candidate = $edge.target_id
            $edge.startup_id_candidate = $edge.source_id
            $edge.confidence_score = [Math]::Max([double]$edge.confidence_score, 0.9)
        } else {
            $issues.Add([PSCustomObject]@{
                issue_type = 'edge_direction_ambiguous'
                entity_id = "$($edge.source_id)->$($edge.target_id)"
                context = $edge.source_file
                severity = 'medium'
                notes = 'Could not infer investor/startup direction from entity types'
            })
        }
    } else {
        $issues.Add([PSCustomObject]@{
            issue_type = 'edge_references_missing_entity'
            entity_id = "$($edge.source_id)->$($edge.target_id)"
            context = $edge.source_file
            severity = 'high'
            notes = 'Edge source or target not found in extracted entities'
        })
    }
}

$entities.Values |
    Sort-Object entity_type_raw, canonical_name |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'entities_raw.csv') -NoTypeInformation -Encoding UTF8

$metrics |
    Sort-Object entity_id |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'graph_metrics_raw.csv') -NoTypeInformation -Encoding UTF8

$investmentEdges |
    Sort-Object source_file, source_id, target_id |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'investment_edges_raw.csv') -NoTypeInformation -Encoding UTF8

$issues |
    Sort-Object severity, issue_type, entity_id |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'import_issues.csv') -NoTypeInformation -Encoding UTF8

$summary = @(
    [PSCustomObject]@{metric='entities_total'; value=$entities.Count}
    [PSCustomObject]@{metric='entities_from_nodes_csv'; value=@($entities.Values | Where-Object { $_.in_nodes_csv }).Count}
    [PSCustomObject]@{metric='entities_from_graphml'; value=@($entities.Values | Where-Object { $_.in_graphml }).Count}
    [PSCustomObject]@{metric='raw_edges_total'; value=$investmentEdges.Count}
    [PSCustomObject]@{metric='issues_total'; value=$issues.Count}
    [PSCustomObject]@{metric='validated_investor_to_startup'; value=@($investmentEdges | Where-Object { $_.direction_status -eq 'validated_investor_to_startup' }).Count}
    [PSCustomObject]@{metric='validated_reverse_edges'; value=@($investmentEdges | Where-Object { $_.direction_status -eq 'validated_startup_to_investor_reverse' }).Count}
    [PSCustomObject]@{metric='needs_review_edges'; value=@($investmentEdges | Where-Object { $_.direction_status -like 'needs_review*' }).Count}
)

$summary |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'staging_summary.csv') -NoTypeInformation -Encoding UTF8

Write-Output "Staging extraction complete: $OutputDir"
