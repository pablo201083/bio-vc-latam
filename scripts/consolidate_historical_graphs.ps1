param(
    [string]$DesktopPath = [Environment]::GetFolderPath('Desktop'),
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\historical_consolidation"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function New-Slug {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
    $slug = $Text.ToLowerInvariant()
    $slug = $slug -replace 'Ã¤','a'
    $slug = $slug -replace '[^a-z0-9]+', '-'
    $slug = $slug.Trim('-')
    return $slug
}

function Add-Entity {
    param(
        [hashtable]$Store,
        [System.Collections.Generic.List[object]]$Provenance,
        [string]$EntityId,
        [string]$Label,
        [string]$EntityType,
        [string]$SourceFile,
        [string]$ExtractionMethod,
        [string]$Notes
    )

    if ([string]::IsNullOrWhiteSpace($EntityId) -and [string]::IsNullOrWhiteSpace($Label)) { return }
    $key = if (-not [string]::IsNullOrWhiteSpace($EntityId)) { $EntityId } else { "label::" + $Label }
    if (-not $Store.ContainsKey($key)) {
        $Store[$key] = [PSCustomObject]@{
            entity_key = $key
            entity_id_raw = $EntityId
            canonical_name_candidate = $Label
            slug_candidate = New-Slug -Text $Label
            entity_type_candidate = $EntityType
            source_count = 0
            sources = ''
            extraction_methods = ''
            notes = ''
        }
    }

    $item = $Store[$key]
    $item.source_count = [int]$item.source_count + 1
    $item.sources = (@($item.sources -split '\|' | Where-Object { $_ }) + $SourceFile | Select-Object -Unique) -join '|'
    $item.extraction_methods = (@($item.extraction_methods -split '\|' | Where-Object { $_ }) + $ExtractionMethod | Select-Object -Unique) -join '|'
    $item.notes = (@($item.notes -split '\|' | Where-Object { $_ }) + $Notes | Select-Object -Unique) -join '|'

    $Provenance.Add([PSCustomObject]@{
        record_type = 'entity'
        entity_key = $key
        entity_id_raw = $EntityId
        label = $Label
        entity_type = $EntityType
        source_file = $SourceFile
        extraction_method = $ExtractionMethod
        notes = $Notes
    }) | Out-Null
}

function Add-Relation {
    param(
        [System.Collections.Generic.List[object]]$Store,
        [string]$SourceId,
        [string]$TargetId,
        [string]$RelationType,
        [string]$SourceFile,
        [string]$ExtractionMethod,
        [string]$Confidence,
        [string]$Notes
    )
    if ([string]::IsNullOrWhiteSpace($SourceId) -or [string]::IsNullOrWhiteSpace($TargetId)) { return }
    $Store.Add([PSCustomObject]@{
        source_id = $SourceId
        target_id = $TargetId
        relation_type = $RelationType
        source_file = $SourceFile
        extraction_method = $ExtractionMethod
        confidence = $Confidence
        notes = $Notes
    }) | Out-Null
}

Ensure-Dir -Path $OutputDir

$entityStore = @{}
$entityProvenance = New-Object System.Collections.Generic.List[object]
$relations = New-Object System.Collections.Generic.List[object]
$fileInventory = New-Object System.Collections.Generic.List[object]
$stringSignals = New-Object System.Collections.Generic.List[object]

# Core known files
$nodesCsvPath = Join-Path $DesktopPath 'nodoseco.csv'
$edgesCsvPath = Join-Path $DesktopPath 'edgeseco.csv'
$coinvestGraphPath = Join-Path $DesktopPath 'latam_coinvest_network_v3.graphml'

if (Test-Path -LiteralPath $nodesCsvPath) {
    $nodesCsv = Import-Csv -LiteralPath $nodesCsvPath
    foreach ($row in $nodesCsv) {
        Add-Entity -Store $entityStore -Provenance $entityProvenance `
            -EntityId ([string]$row.Id) `
            -Label ([string]$row.Label) `
            -EntityType ([string]$row.'0') `
            -SourceFile 'nodoseco.csv' `
            -ExtractionMethod 'csv_node_table' `
            -Notes 'core_capital_graph'
    }
    $fileInventory.Add([PSCustomObject]@{ file='nodoseco.csv'; category='core'; extracted=@($nodesCsv).Count; notes='node table with graph metrics' }) | Out-Null
}

if (Test-Path -LiteralPath $edgesCsvPath) {
    $edgesCsv = Import-Csv -LiteralPath $edgesCsvPath
    foreach ($row in $edgesCsv) {
        Add-Relation -Store $relations `
            -SourceId ([string]$row.Source) `
            -TargetId ([string]$row.Target) `
            -RelationType ([string]$row.'1') `
            -SourceFile 'edgeseco.csv' `
            -ExtractionMethod 'csv_edge_table' `
            -Confidence 'high' `
            -Notes 'direction_as_recorded_needs_canonical_mapping'
    }
    $fileInventory.Add([PSCustomObject]@{ file='edgeseco.csv'; category='core'; extracted=@($edgesCsv).Count; notes='edge table with investment relations' }) | Out-Null
}

if (Test-Path -LiteralPath $coinvestGraphPath) {
    $xml = [xml](Get-Content -LiteralPath $coinvestGraphPath -Raw)
    $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
    $ns.AddNamespace('g', 'http://graphml.graphdrawing.org/xmlns')
    $graphNodes = $xml.SelectNodes('//g:node', $ns)
    $graphEdges = $xml.SelectNodes('//g:edge', $ns)

    foreach ($node in $graphNodes) {
        $labelNode = $node.SelectSingleNode("g:data[@key='d0']", $ns)
        $typeNode = $node.SelectSingleNode("g:data[@key='d1']", $ns)
        $label = if ($labelNode) { [string]$labelNode.InnerText } else { [string]$node.id }
        $type = if ($typeNode) { [string]$typeNode.InnerText } else { '' }

        Add-Entity -Store $entityStore -Provenance $entityProvenance `
            -EntityId ([string]$node.id) `
            -Label $label `
            -EntityType $type `
            -SourceFile 'latam_coinvest_network_v3.graphml' `
            -ExtractionMethod 'graphml_nodes' `
            -Notes 'core_coinvest_graph'
    }

    foreach ($edge in $graphEdges) {
        Add-Relation -Store $relations `
            -SourceId ([string]$edge.source) `
            -TargetId ([string]$edge.target) `
            -RelationType 'investment_or_membership' `
            -SourceFile 'latam_coinvest_network_v3.graphml' `
            -ExtractionMethod 'graphml_edges' `
            -Confidence 'medium' `
            -Notes 'graphml_direction_reverse_for_some_edges'
    }

    $fileInventory.Add([PSCustomObject]@{ file='latam_coinvest_network_v3.graphml'; category='core'; extracted=@($graphNodes).Count + @($graphEdges).Count; notes='graphml with startup/investor nodes and edges' }) | Out-Null
}

# Historical gephi and graph data
$historicalFiles = Get-ChildItem $DesktopPath -File | Where-Object {
    $_.Extension -in '.gephi','.graphml','.csv' -and
    $_.Name -match 'Ecosistema|Mapa|grafo|Universidades|nodos|edges|modularidad|videos'
}

foreach ($file in $historicalFiles) {
    if ($file.Name -in @('nodoseco.csv','edgeseco.csv','latam_coinvest_network_v3.graphml','grafo_elgatylacaja.graphml')) {
        continue
    }

    if ($file.Extension -eq '.csv') {
        $csv = Import-Csv -LiteralPath $file.FullName
        if (@($csv).Count -gt 0) {
            $headers = $csv[0].PSObject.Properties.Name
            $fileInventory.Add([PSCustomObject]@{
                file = $file.Name
                category = 'historical_csv'
                extracted = @($csv).Count
                notes = ($headers -join ', ')
            }) | Out-Null
        }
        continue
    }

    if ($file.Extension -eq '.graphml') {
        try {
            $xml = [xml](Get-Content -LiteralPath $file.FullName -Raw)
            $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
            $ns.AddNamespace('g', 'http://graphml.graphdrawing.org/xmlns')
            $nodes = $xml.SelectNodes('//g:node', $ns)
            foreach ($node in $nodes) {
                Add-Entity -Store $entityStore -Provenance $entityProvenance `
                    -EntityId ([string]$node.id) `
                    -Label ([string]$node.id) `
                    -EntityType 'unknown' `
                    -SourceFile $file.Name `
                    -ExtractionMethod 'historical_graphml_node_ids' `
                    -Notes 'non_capital_graphml'
            }
            $fileInventory.Add([PSCustomObject]@{ file=$file.Name; category='historical_graphml'; extracted=@($nodes).Count; notes='node ids extracted' }) | Out-Null
        } catch {
            $fileInventory.Add([PSCustomObject]@{ file=$file.Name; category='historical_graphml'; extracted=0; notes='parse_error' }) | Out-Null
        }
        continue
    }

    if ($file.Extension -eq '.gephi' -and $file.Length -gt 0) {
        try {
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $zip = [IO.Compression.ZipFile]::OpenRead($file.FullName)
            $entry = $zip.Entries | Where-Object { $_.FullName -eq 'Workspace_1_graphstore_bytes' }
            if ($entry) {
                $stream = $entry.Open()
                $bytes = New-Object byte[] $entry.Length
                [void]$stream.Read($bytes, 0, $bytes.Length)
                $stream.Close()
                $text = [System.Text.Encoding]::UTF8.GetString($bytes)

                $entityPatterns = @(
                    'Universidad[^|]{4,60}',
                    'Instituto[^|]{4,60}',
                    'CONICET[^|]{0,40}',
                    'INTA[^|]{0,40}',
                    'ITBA[^|]{0,30}',
                    'IAE Business School',
                    'UCEMA',
                    'UdeSA[^|]{0,30}',
                    'Draper University',
                    'Techstars',
                    'Y Combinator',
                    '500 Startups',
                    'Wayra Hispam',
                    'Brinc',
                    'IndieBio',
                    'GridX',
                    'CITES',
                    'Air Capital',
                    'Antom',
                    'Draper Cygnus',
                    'Nxtp Labs',
                    'Stämm',
                    'Stamm',
                    'Michroma',
                    'Puna Bio',
                    'Beeflow',
                    'Bioeutectics',
                    'Feedvax',
                    'Cell Farm',
                    'Onco Precision',
                    'Tomorrow Foods',
                    'Vexxel Biotech',
                    'Ubique Bio',
                    'Kresko RNAtech',
                    'Kresko RNATech',
                    'Satellogic',
                    'Auth0',
                    'Kilimo'
                )

                foreach ($pattern in $entityPatterns) {
                    [regex]::Matches($text, $pattern) | ForEach-Object {
                        $value = $_.Value.Trim()
                        $etype = if ($value -match 'Universidad|Instituto|CONICET|INTA|ITBA|IAE|UCEMA|UdeSA') { 'institution_candidate' }
                                 elseif ($value -match 'GridX|CITES|Air Capital|Antom|Draper|Nxtp|IndieBio|Wayra|Techstars|Y Combinator|500 Startups|Brinc') { 'capital_candidate' }
                                 else { 'startup_candidate' }

                        Add-Entity -Store $entityStore -Provenance $entityProvenance `
                            -EntityId '' `
                            -Label $value `
                            -EntityType $etype `
                            -SourceFile $file.Name `
                            -ExtractionMethod 'gephi_string_signal' `
                            -Notes 'historical_rich_graph_signal'
                    }
                }

                $relationPatterns = @(
                    'funded_by',
                    'has_founder',
                    'studied_at',
                    'researched_at',
                    'member_of',
                    'graduated_from',
                    'accelerated_at',
                    'incubated_at',
                    'spin_off_from',
                    'collaborates_with',
                    'built_by'
                )

                foreach ($pattern in $relationPatterns) {
                    $count = ([regex]::Matches($text, $pattern)).Count
                    if ($count -gt 0) {
                        $stringSignals.Add([PSCustomObject]@{
                            source_file = $file.Name
                            signal_type = 'relation_taxonomy'
                            value = $pattern
                            occurrences = $count
                        }) | Out-Null
                    }
                }

                $typePatterns = @(
                    'University',
                    'Research Institute',
                    'Accelerator',
                    'Corporate',
                    'Corporate VC',
                    'Investor4',
                    'Startup4',
                    'Founder4',
                    'Knowledge Hub4'
                )

                foreach ($pattern in $typePatterns) {
                    $count = ([regex]::Matches($text, $pattern)).Count
                    if ($count -gt 0) {
                        $stringSignals.Add([PSCustomObject]@{
                            source_file = $file.Name
                            signal_type = 'node_type_signal'
                            value = $pattern
                            occurrences = $count
                        }) | Out-Null
                    }
                }

                $fileInventory.Add([PSCustomObject]@{
                    file = $file.Name
                    category = 'historical_gephi_strings'
                    extracted = ([regex]::Matches($text, '[A-Za-z0-9]')).Count
                    notes = 'string signals extracted from graphstore bytes'
                }) | Out-Null
            } else {
                $fileInventory.Add([PSCustomObject]@{ file=$file.Name; category='historical_gephi_strings'; extracted=0; notes='graphstore_bytes_missing' }) | Out-Null
            }
            $zip.Dispose()
        } catch {
            $fileInventory.Add([PSCustomObject]@{ file=$file.Name; category='historical_gephi_strings'; extracted=0; notes='read_error' }) | Out-Null
        }
    }
}

$entityStore.Values |
    Sort-Object entity_type_candidate, canonical_name_candidate |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'historical_entities_candidates.csv') -NoTypeInformation -Encoding UTF8

$entityProvenance |
    Sort-Object source_file, label |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'historical_entity_provenance.csv') -NoTypeInformation -Encoding UTF8

$relations |
    Sort-Object source_file, relation_type, source_id, target_id |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'historical_relations_raw.csv') -NoTypeInformation -Encoding UTF8

$stringSignals |
    Sort-Object source_file, signal_type, value |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'historical_string_signals.csv') -NoTypeInformation -Encoding UTF8

$fileInventory |
    Sort-Object file |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'historical_file_inventory.csv') -NoTypeInformation -Encoding UTF8

$summary = @(
    [PSCustomObject]@{ metric='entity_candidates'; value=[int]$entityStore.Values.Count }
    [PSCustomObject]@{ metric='entity_provenance_rows'; value=[int]$entityProvenance.Count }
    [PSCustomObject]@{ metric='raw_relations'; value=[int]$relations.Count }
    [PSCustomObject]@{ metric='string_signals'; value=[int]$stringSignals.Count }
    [PSCustomObject]@{ metric='files_inventory'; value=[int]$fileInventory.Count }
)

$summary |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'historical_consolidation_summary.csv') -NoTypeInformation -Encoding UTF8

Write-Output "Historical consolidation complete: $OutputDir"
