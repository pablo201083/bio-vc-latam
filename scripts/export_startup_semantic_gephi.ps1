param(
    [string]$MasterCsv = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$AssignmentsCsv = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_single_level_assignments.csv",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\gephi_export\startup_semantic"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Escape-Xml {
    param([AllowNull()][string]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Security.SecurityElement]::Escape([string]$Value)
}

function Normalize-Text {
    param([AllowNull()][string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
    $normalized = $Text.ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD)
    $builder = New-Object System.Text.StringBuilder
    foreach ($char in $normalized.ToCharArray()) {
        if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($char) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            [void]$builder.Append($char)
        }
    }
    $normalized = $builder.ToString()
    $normalized = [regex]::Replace($normalized, "entra en tesis.*$", " ")
    $normalized = [regex]::Replace($normalized, "official site describes|official site presents|official site states|linkedin company profile describes|linkedin company profile states that|gridx describes|f6s profile describes", " ")
    $normalized = [regex]::Replace($normalized, "[^a-z0-9\s-]+", " ")
    $normalized = [regex]::Replace($normalized, "\s+", " ").Trim()
    return $normalized
}

function New-TokenSet {
    param([AllowNull()][string]$Text, [System.Collections.Generic.HashSet[string]]$StopSet)
    $set = [System.Collections.Generic.HashSet[string]]::new()
    if ([string]::IsNullOrWhiteSpace($Text)) { return $set }
    foreach ($token in (Normalize-Text $Text).Split(" ")) {
        if ($token.Length -ge 4 -and -not $StopSet.Contains($token)) {
            [void]$set.Add($token)
        }
    }
    return $set
}

function New-FacetSet {
    param([AllowNull()][string]$Text)
    $set = [System.Collections.Generic.HashSet[string]]::new()
    $value = Normalize-Text $Text
    if ([string]::IsNullOrWhiteSpace($value)) { return $set }

    $rules = @(
        @{ Label = "human_health"; Patterns = @("clinical","medical","diagnostic","therapeut","regenerative","health","drug","pharma","patient") },
        @{ Label = "ag_systems"; Patterns = @("crop","agric","agri","pollination","livestock","farm","soil","seed","animal protein") },
        @{ Label = "food_systems"; Patterns = @("food","ingredient","nutrition","beverage","dairy","protein") },
        @{ Label = "bioindustrial"; Patterns = @("industrial","bioprocess","enzyme","fermentation","molecular","manufacturing","bioindustrial") },
        @{ Label = "climate_resource"; Patterns = @("carbon","resource","climate","water","energy","remediation","circular","recovery","waste") },
        @{ Label = "monitor_trace"; Patterns = @("trace","monitor","intelligence","analytics","mrv","market","token","sensor") },
        @{ Label = "intervention"; Patterns = @("intervention","therapeut","diagnostic","input","delivery","device") },
        @{ Label = "platform"; Patterns = @("platform","software","model","screening","discovery","simulation") }
    )

    foreach ($rule in $rules) {
        foreach ($pattern in $rule.Patterns) {
            if ($value.Contains($pattern)) {
                [void]$set.Add($rule.Label)
                break
            }
        }
    }

    return $set
}

function Jaccard {
    param(
        [System.Collections.Generic.HashSet[string]]$SetA,
        [System.Collections.Generic.HashSet[string]]$SetB
    )
    if ($SetA.Count -eq 0 -or $SetB.Count -eq 0) { return 0.0 }
    $intersection = 0
    $smaller = if ($SetA.Count -le $SetB.Count) { $SetA } else { $SetB }
    $larger = if ($SetA.Count -le $SetB.Count) { $SetB } else { $SetA }
    foreach ($token in $smaller) {
        if ($larger.Contains($token)) { $intersection++ }
    }
    $union = $SetA.Count + $SetB.Count - $intersection
    if ($union -eq 0) { return 0.0 }
    return [double]$intersection / [double]$union
}

function Composite-Similarity {
    param(
        [System.Collections.Generic.HashSet[string]]$TextA,
        [System.Collections.Generic.HashSet[string]]$TextB,
        [System.Collections.Generic.HashSet[string]]$FacetA,
        [System.Collections.Generic.HashSet[string]]$FacetB
    )
    $textSim = Jaccard $TextA $TextB
    $facetSim = Jaccard $FacetA $FacetB
    $healthBonus = if ($FacetA.Contains("human_health") -and $FacetB.Contains("human_health")) { 0.14 } else { 0.0 }
    $agBonus = if ($FacetA.Contains("ag_systems") -and $FacetB.Contains("ag_systems")) { 0.08 } else { 0.0 }
    $industrialBonus = if ($FacetA.Contains("bioindustrial") -and $FacetB.Contains("bioindustrial")) { 0.08 } else { 0.0 }
    $climateBonus = if ($FacetA.Contains("climate_resource") -and $FacetB.Contains("climate_resource")) { 0.08 } else { 0.0 }
    $score = ($textSim * 0.62) + ($facetSim * 0.38) + $healthBonus + $agBonus + $industrialBonus + $climateBonus
    return [Math]::Min(1.0, $score)
}

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
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

$stopSet = [System.Collections.Generic.HashSet[string]]::new()
@(
    "startup","startups","company","empresa","platform","plataforma","technology","solution","solutions",
    "biotech","biology","bio","life","health","food","agriculture","official","site","describes","presents",
    "states","with","from","into","para","con","por","una","uno","their","this","that","using","used","based"
) | ForEach-Object { [void]$stopSet.Add($_) }

$master = Import-Csv -LiteralPath $MasterCsv
$assignments = Import-Csv -LiteralPath $AssignmentsCsv
$assignmentsById = @{}
foreach ($assignment in $assignments) {
    $assignmentsById[$assignment.startup_id] = $assignment
}

$rows = foreach ($row in $master) {
    if ($row.scope_decision -ne "include") { continue }
    if ($row.scope_status -ne "confirmed") { continue }
    if (-not $assignmentsById.ContainsKey($row.startup_id)) { continue }
    $assignment = $assignmentsById[$row.startup_id]
    $text = @(
        $row.startup_summary_v1,
        $row.business_one_liner,
        $row.market_label,
        $row.transition_function,
        $row.technical_stack,
        $row.industry_destination
    ) -join " "
    $facetText = @(
        $row.market_label,
        $row.transition_function,
        $row.technical_stack,
        $row.industry_destination,
        $assignment.semantic_single_theme
    ) -join " "
    $tokens = New-TokenSet -Text $text -StopSet $stopSet
    $facets = New-FacetSet -Text $facetText
    $theme = $assignment.semantic_single_theme
    $color = if ($themeColors.ContainsKey($theme)) { $themeColors[$theme] } else { @{ r = 160; g = 160; b = 160 } }
    [PSCustomObject]@{
        Id = $row.startup_id
        Label = $row.startup_name
        Theme = $theme
        ClusterId = $assignment.semantic_single_cluster_id
        Country = $row.structured_country
        QualityBand = $row.quality_band
        QualityScore = $row.data_quality_score_10
        ReviewStatus = $row.review_status
        SourceUrl = $row.source_url
        SourceType = $row.source_type
        MarketLabel = $row.market_label
        TransitionFunction = $row.transition_function
        TechnicalStack = $row.technical_stack
        IndustryDestination = $row.industry_destination
        Summary = $row.startup_summary_v1
        OneLiner = $row.business_one_liner
        SemanticScore = $assignment.semantic_single_score
        SemanticMargin = $assignment.semantic_single_margin
        SemanticConfidence = $assignment.semantic_single_confidence
        Tokens = $tokens
        Facets = $facets
        r = $color.r
        g = $color.g
        b = $color.b
    }
}

$nodeRows = @($rows | Sort-Object Theme, Label)

$edgeRows = New-Object System.Collections.Generic.List[object]
$seenEdges = [System.Collections.Generic.HashSet[string]]::new()
foreach ($node in $nodeRows) {
    $neighbors = @(
        foreach ($other in $nodeRows) {
            if ($node.Id -eq $other.Id) { continue }
            $sim = Composite-Similarity -TextA $node.Tokens -TextB $other.Tokens -FacetA $node.Facets -FacetB $other.Facets
            if ($sim -lt 0.08) { continue }
            [PSCustomObject]@{
                Target = $other.Id
                Similarity = $sim
                SameTheme = ($node.Theme -eq $other.Theme)
            }
        }
    ) | Sort-Object Similarity -Descending | Select-Object -First 6

    foreach ($neighbor in $neighbors) {
        $pair = @($node.Id, $neighbor.Target) | Sort-Object
        $edgeKey = "$($pair[0])|$($pair[1])"
        if ($seenEdges.Contains($edgeKey)) { continue }
        [void]$seenEdges.Add($edgeKey)
        $edgeRows.Add([PSCustomObject]@{
            Source = $pair[0]
            Target = $pair[1]
            Type = "Undirected"
            Weight = [Math]::Round([double]$neighbor.Similarity, 4)
            SameTheme = if ($neighbor.SameTheme) { "yes" } else { "no" }
        })
    }
}

$csvNodes = $nodeRows | ForEach-Object {
    [PSCustomObject]@{
        Id = $_.Id
        Label = $_.Label
        Theme = $_.Theme
        ClusterId = $_.ClusterId
        Country = $_.Country
        QualityBand = $_.QualityBand
        QualityScore = $_.QualityScore
        ReviewStatus = $_.ReviewStatus
        SourceUrl = $_.SourceUrl
        SourceType = $_.SourceType
        MarketLabel = $_.MarketLabel
        TransitionFunction = $_.TransitionFunction
        TechnicalStack = $_.TechnicalStack
        IndustryDestination = $_.IndustryDestination
        Summary = $_.Summary
        OneLiner = $_.OneLiner
        SemanticScore = $_.SemanticScore
        SemanticMargin = $_.SemanticMargin
        SemanticConfidence = $_.SemanticConfidence
        Size = [Math]::Round((6 + [double]$_.QualityScore * 0.8), 2)
        r = $_.r
        g = $_.g
        b = $_.b
    }
}

$graphMl = [System.Collections.Generic.List[string]]::new()
$null = $graphMl.Add('<?xml version="1.0" encoding="UTF-8"?>')
$null = $graphMl.Add('<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:viz="http://www.gephi.org/gexf/viz" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">')
$null = $graphMl.Add('  <key id="label" for="node" attr.name="label" attr.type="string"/>')
$null = $graphMl.Add('  <key id="theme" for="node" attr.name="theme" attr.type="string"/>')
$null = $graphMl.Add('  <key id="cluster_id" for="node" attr.name="cluster_id" attr.type="string"/>')
$null = $graphMl.Add('  <key id="country" for="node" attr.name="country" attr.type="string"/>')
$null = $graphMl.Add('  <key id="quality_band" for="node" attr.name="quality_band" attr.type="string"/>')
$null = $graphMl.Add('  <key id="quality_score" for="node" attr.name="quality_score" attr.type="double"/>')
$null = $graphMl.Add('  <key id="review_status" for="node" attr.name="review_status" attr.type="string"/>')
$null = $graphMl.Add('  <key id="source_url" for="node" attr.name="source_url" attr.type="string"/>')
$null = $graphMl.Add('  <key id="source_type" for="node" attr.name="source_type" attr.type="string"/>')
$null = $graphMl.Add('  <key id="market_label" for="node" attr.name="market_label" attr.type="string"/>')
$null = $graphMl.Add('  <key id="transition_function" for="node" attr.name="transition_function" attr.type="string"/>')
$null = $graphMl.Add('  <key id="technical_stack" for="node" attr.name="technical_stack" attr.type="string"/>')
$null = $graphMl.Add('  <key id="industry_destination" for="node" attr.name="industry_destination" attr.type="string"/>')
$null = $graphMl.Add('  <key id="summary" for="node" attr.name="summary" attr.type="string"/>')
$null = $graphMl.Add('  <key id="one_liner" for="node" attr.name="one_liner" attr.type="string"/>')
$null = $graphMl.Add('  <key id="semantic_score" for="node" attr.name="semantic_score" attr.type="double"/>')
$null = $graphMl.Add('  <key id="semantic_margin" for="node" attr.name="semantic_margin" attr.type="double"/>')
$null = $graphMl.Add('  <key id="semantic_confidence" for="node" attr.name="semantic_confidence" attr.type="string"/>')
$null = $graphMl.Add('  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>')
$null = $graphMl.Add('  <key id="same_theme" for="edge" attr.name="same_theme" attr.type="string"/>')
$null = $graphMl.Add('  <graph id="startup_semantic" edgedefault="undirected">')
$null = $graphMl.Add('    <nodes>')

foreach ($node in $csvNodes) {
    $null = $graphMl.Add("      <node id=""$(Escape-Xml $node.Id)"">")
    $null = $graphMl.Add("        <data key=""label"">$(Escape-Xml $node.Label)</data>")
    $null = $graphMl.Add("        <data key=""theme"">$(Escape-Xml $node.Theme)</data>")
    $null = $graphMl.Add("        <data key=""cluster_id"">$(Escape-Xml $node.ClusterId)</data>")
    $null = $graphMl.Add("        <data key=""country"">$(Escape-Xml $node.Country)</data>")
    $null = $graphMl.Add("        <data key=""quality_band"">$(Escape-Xml $node.QualityBand)</data>")
    $null = $graphMl.Add("        <data key=""quality_score"">$(Escape-Xml $node.QualityScore)</data>")
    $null = $graphMl.Add("        <data key=""review_status"">$(Escape-Xml $node.ReviewStatus)</data>")
    $null = $graphMl.Add("        <data key=""source_url"">$(Escape-Xml $node.SourceUrl)</data>")
    $null = $graphMl.Add("        <data key=""source_type"">$(Escape-Xml $node.SourceType)</data>")
    $null = $graphMl.Add("        <data key=""market_label"">$(Escape-Xml $node.MarketLabel)</data>")
    $null = $graphMl.Add("        <data key=""transition_function"">$(Escape-Xml $node.TransitionFunction)</data>")
    $null = $graphMl.Add("        <data key=""technical_stack"">$(Escape-Xml $node.TechnicalStack)</data>")
    $null = $graphMl.Add("        <data key=""industry_destination"">$(Escape-Xml $node.IndustryDestination)</data>")
    $null = $graphMl.Add("        <data key=""summary"">$(Escape-Xml $node.Summary)</data>")
    $null = $graphMl.Add("        <data key=""one_liner"">$(Escape-Xml $node.OneLiner)</data>")
    $null = $graphMl.Add("        <data key=""semantic_score"">$(Escape-Xml $node.SemanticScore)</data>")
    $null = $graphMl.Add("        <data key=""semantic_margin"">$(Escape-Xml $node.SemanticMargin)</data>")
    $null = $graphMl.Add("        <data key=""semantic_confidence"">$(Escape-Xml $node.SemanticConfidence)</data>")
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
    $null = $graphMl.Add("        <data key=""same_theme"">$(Escape-Xml $edge.SameTheme)</data>")
    $null = $graphMl.Add('      </edge>')
    $edgeId++
}
$null = $graphMl.Add('    </edges>')
$null = $graphMl.Add('  </graph>')
$null = $graphMl.Add('</graphml>')

$csvNodes | Export-Csv -LiteralPath (Join-Path $OutputDir 'startup_nodes.csv') -NoTypeInformation -Encoding UTF8
$edgeRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'startup_edges.csv') -NoTypeInformation -Encoding UTF8
Set-Content -LiteralPath (Join-Path $OutputDir 'startup_semantic.graphml') -Value $graphMl -Encoding UTF8

$summary = @"
Startup semantic export for Gephi

Files:
- startup_nodes.csv
- startup_edges.csv
- startup_semantic.graphml

Universe:
- include + confirmed only
- adopted semantic taxonomy k=7
- similarity edges based on text + functional/system facets

Counts:
- Nodes: $($csvNodes.Count)
- Edges: $($edgeRows.Count)

Suggested Gephi starting points:
- Layout: ForceAtlas2 or Fruchterman Reingold
- Node color: existing viz color / theme
- Node size: existing viz size / quality score
- Edge weight: Weight
- Label: Label
- Filter weak edges only if graph feels too dense
"@

Set-Content -LiteralPath (Join-Path $OutputDir 'README.txt') -Value $summary -Encoding UTF8
Write-Output "Startup semantic Gephi export complete: $OutputDir"
