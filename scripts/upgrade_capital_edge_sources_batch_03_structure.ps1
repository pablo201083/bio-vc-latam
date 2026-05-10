param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Clean-Text {
    param([object]$Value)
    if ($null -eq $Value) { return '' }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return '' }
    if ($text.Trim().ToLowerInvariant() -eq 'nan') { return '' }
    return $text.Trim()
}

function Normalize-Key {
    param([object]$Value)
    $text = (Clean-Text $Value).ToLowerInvariant()
    if (-not $text) { return '' }
    $normalized = $text.Normalize([Text.NormalizationForm]::FormD)
    $chars = foreach ($char in $normalized.ToCharArray()) {
        if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($char) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            $char
        }
    }
    return ((-join $chars) -replace '[^a-z0-9]+', '')
}

function Set-EdgeEvidence {
    param(
        [object]$Row,
        [string]$Relation,
        [string]$Source,
        [string]$Notes,
        [string]$Confidence = '0.96'
    )
    $Row.relation_type_raw = $Relation
    $Row.direction_status = 'validated_investor_to_startup'
    $Row.confidence_score = $Confidence
    $Row.source_file = $Source
    $Row.notes = $Notes
}

function Add-Or-Update-CanonicalEdge {
    param(
        [object[]]$Rows,
        [string]$InvestmentId,
        [string]$InvestorId,
        [string]$StartupId,
        [string]$Relation,
        [string]$Source,
        [string]$Notes,
        [string]$Confidence = '0.96'
    )
    $existing = @($Rows | Where-Object { $_.investment_id -eq $InvestmentId } | Select-Object -First 1)
    if ($existing.Count) {
        Set-EdgeEvidence -Row $existing[0] -Relation $Relation -Source $Source -Notes $Notes -Confidence $Confidence
        return $Rows
    }
    $row = [pscustomobject]@{
        investment_id = $InvestmentId
        investor_id = $InvestorId
        startup_id = $StartupId
        relation_type_raw = $Relation
        direction_status = 'validated_investor_to_startup'
        confidence_score = $Confidence
        source_file = $Source
        notes = $Notes
    }
    return @($Rows) + $row
}

function Add-Or-Update-ManualEdge {
    param(
        [object[]]$Rows,
        [string]$RawEdgeId,
        [string]$SourceId,
        [string]$TargetId,
        [string]$SourceFile,
        [string]$Relation,
        [string]$InvestorId,
        [string]$StartupId,
        [string]$Notes,
        [string]$Confidence = '0.96'
    )
    $existing = @($Rows | Where-Object { $_.raw_edge_id -eq $RawEdgeId } | Select-Object -First 1)
    if ($existing.Count) {
        $row = $existing[0]
        $row.source_id = $SourceId
        $row.target_id = $TargetId
        $row.source_file = $SourceFile
        $row.relation_type_raw = $Relation
        $row.direction_status = 'validated_investor_to_startup'
        $row.investor_id_candidate = $InvestorId
        $row.startup_id_candidate = $StartupId
        $row.confidence_score = $Confidence
        $row.notes = $Notes
        return $Rows
    }
    $row = [pscustomobject]@{
        raw_edge_id = $RawEdgeId
        source_id = $SourceId
        target_id = $TargetId
        source_file = $SourceFile
        relation_type_raw = $Relation
        direction_status = 'validated_investor_to_startup'
        investor_id_candidate = $InvestorId
        startup_id_candidate = $StartupId
        confidence_score = $Confidence
        notes = $Notes
    }
    return @($Rows) + $row
}

$canonicalPath = Join-Path $Root 'canonical\canonical_investment_edges.csv'
$manualPath = Join-Path $Root 'canonical\manual_canonical_investment_edges.csv'
$canonicalRows = @(Import-Csv -LiteralPath $canonicalPath)
$manualRows = @(Import-Csv -LiteralPath $manualPath)

$updates = 0

$innventureSource = 'https://www.lanacion.com.ar/economia/campo/nuevas-tecnologias-un-fondo-del-agro-junto-us28-millones-e-invirtio-en-10-empresas-nid20122024/'
$innventureStartups = @{
    'deepagro' = 'DeepAgro'
    'eiwa' = 'Eiwa'
    'zoomagri' = 'ZoomAgri'
    'siloreal' = 'Silo Real'
    'sensify' = 'Sensify'
    'calice' = 'Calice'
    'elytronbiotech' = 'Elytron'
    'satellitesonfire' = 'Satelites on Fire'
    'tracestory' = 'Tracestory'
    'unibaio' = 'Unibaio'
}
foreach ($row in $canonicalRows) {
    if ((Clean-Text $row.investor_id) -ne 'inventure') { continue }
    $key = Normalize-Key $row.startup_id
    if (-not $innventureStartups.ContainsKey($key)) { continue }
    Set-EdgeEvidence -Row $row `
        -Relation 'investment_announcement' `
        -Source $innventureSource `
        -Confidence '0.98' `
        -Notes "LA NACION reports Innventure invested in $($innventureStartups[$key]) as part of a 10-company agtech portfolio; upgraded from historical graph to public investment announcement evidence."
    $updates += 1
}

$aceleradoraSource = 'https://www.aceleradoralitoral.com.ar/portfolio/'
$aceleradoraNames = @{
    'bioheuris' = 'Bioheuris'
    'biosynaptica' = 'BioSynaptica'
    'inbioar' = 'Inbioar'
    'infira' = 'Infira'
    'nairotech' = 'Nairotech'
    'seedmatriz' = 'SeedMatriz'
    'untech' = 'UnTech'
}
foreach ($row in $canonicalRows) {
    if ((Clean-Text $row.investor_id) -ne 'aceleradora_litoral') { continue }
    $key = Normalize-Key $row.startup_id
    if (-not $aceleradoraNames.ContainsKey($key)) { continue }
    Set-EdgeEvidence -Row $row `
        -Relation 'official_portfolio_investment' `
        -Source $aceleradoraSource `
        -Confidence '0.96' `
        -Notes "Aceleradora Litoral official portfolio page lists $($aceleradoraNames[$key]); upgraded from historical graph to official portfolio evidence."
    $updates += 1
}

$kamayKilimoSource = 'https://tekiosmag.com/2022/12/07/kamay-ventures-invierte-en-la-agtech-argentina-kilimo-experta-en-optimizar-la-utilizacion-del-agua/'
foreach ($row in $canonicalRows) {
    if ((Clean-Text $row.investor_id) -ne 'kamay_ventures') { continue }
    if ((Normalize-Key $row.startup_id) -ne 'kilimo') { continue }
    Set-EdgeEvidence -Row $row `
        -Relation 'investment_announcement' `
        -Source $kamayKilimoSource `
        -Confidence '0.98' `
        -Notes 'Tekios reports Kamay Ventures invested in Kilimo, an Argentine agtech focused on water-use optimization; upgraded to investment announcement evidence.'
    $updates += 1
}

$glocalSource = 'https://www.glocalmanagers.com/pt/startups-2/'
$glocalEdges = @(
    [pscustomobject]@{
        InvestmentId = 'manual-glocal-puna-bio'
        StartupId = 'Puna Bio'
        TargetId = 'Puna Bio'
        Label = 'Puna Bio'
        Notes = "GLOCAL official startups page includes a Puna Bio founder quote describing Puna Bio as part of GLOCAL's portfolio."
    },
    [pscustomobject]@{
        InvestmentId = 'manual-glocal-done-properly'
        StartupId = 'Done Properly'
        TargetId = 'Done Properly'
        Label = 'Done Properly'
        Notes = "GLOCAL official startups page includes a Done Properly founder quote describing Done Properly as part of GLOCAL's portfolio."
    }
)
foreach ($edge in $glocalEdges) {
    $before = $canonicalRows.Count
    $canonicalRows = Add-Or-Update-CanonicalEdge `
        -Rows $canonicalRows `
        -InvestmentId $edge.InvestmentId `
        -InvestorId 'glocal' `
        -StartupId $edge.StartupId `
        -Relation 'official_portfolio_investment' `
        -Source $glocalSource `
        -Confidence '0.96' `
        -Notes $edge.Notes
    if ($canonicalRows.Count -gt $before) { $updates += 1 }
    $manualRows = Add-Or-Update-ManualEdge `
        -Rows $manualRows `
        -RawEdgeId $edge.InvestmentId `
        -SourceId 'GLOCAL' `
        -TargetId $edge.TargetId `
        -SourceFile $glocalSource `
        -Relation 'official_portfolio_investment' `
        -InvestorId 'glocal' `
        -StartupId $edge.StartupId `
        -Confidence '0.96' `
        -Notes $edge.Notes
}

$canonicalRows | Export-Csv -LiteralPath $canonicalPath -NoTypeInformation -Encoding UTF8
$manualRows | Export-Csv -LiteralPath $manualPath -NoTypeInformation -Encoding UTF8

Write-Output "Capital structure evidence batch 03 completed."
Write-Output "Rows updated or added: $updates"
