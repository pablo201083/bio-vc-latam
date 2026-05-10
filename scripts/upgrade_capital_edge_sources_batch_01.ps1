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

$path = Join-Path $Root 'canonical\canonical_investment_edges.csv'
$rows = Import-Csv -LiteralPath $path

$sourceByInvestor = @{
    'SF500' = 'https://sf500.com.ar/'
    'DraperCygnus' = 'https://www.drapercygnus.vc/portfolio'
    'The Ganesha Lab' = 'https://theganeshalab.com/startups/'
    'AIR Capital' = 'https://www.aircapital.vc/portfolio'
    'CITES' = 'https://cites-gss.com/en/portfolio/'
    'Antom' = 'https://www.antom.la/'
    'kamay_ventures' = 'https://kamayventures.com/'
    'SOSV_IndieBio' = 'https://indiebio.co/'
}

$noteByInvestor = @{
    'SF500' = 'Source upgraded to official SF500 website/portfolio page used as public evidence for mapped SF500-backed biotech startups.'
    'DraperCygnus' = 'Source upgraded to official Draper Cygnus portfolio page used as public evidence for mapped portfolio startups.'
    'The Ganesha Lab' = 'Source upgraded to official The Ganesha Lab StartUps page used as public evidence for mapped cohort/startup relationships.'
    'AIR Capital' = 'Source upgraded to official AIR Capital portfolio page used as public evidence for mapped portfolio startups.'
    'CITES' = 'Source upgraded to official CITES portfolio page used as public evidence for mapped portfolio startups.'
    'Antom' = 'Source upgraded to official Antom portfolio page used as public evidence for mapped portfolio/advisory startups.'
    'kamay_ventures' = 'Source upgraded to official Kamay Ventures website used as public evidence for mapped portfolio relationships.'
    'SOSV_IndieBio' = 'Source upgraded to official IndieBio/SOSV site used as public evidence for mapped IndieBio/SOSV relationships.'
}

$upgraded = 0
foreach ($row in $rows) {
    $investorId = Clean-Text $row.investor_id
    $currentSource = Clean-Text $row.source_file
    if (-not $sourceByInvestor.ContainsKey($investorId)) { continue }
    if ($currentSource -match '^https?://') { continue }

    $row.source_file = $sourceByInvestor[$investorId]
    $existingNote = Clean-Text $row.notes
    $upgradeNote = $noteByInvestor[$investorId]
    $row.notes = if ($existingNote) { "$existingNote | $upgradeNote" } else { $upgradeNote }
    $upgraded++
}

$rows | Export-Csv -LiteralPath $path -NoTypeInformation -Encoding UTF8
Write-Output "Capital edge source upgrade batch 01: $upgraded edges upgraded."
