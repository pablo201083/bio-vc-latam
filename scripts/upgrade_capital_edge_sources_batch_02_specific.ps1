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

function Add-VerifiedName {
    param(
        [hashtable]$Map,
        [string]$FundId,
        [string]$FundName,
        [string]$Name,
        [string]$Url,
        [string]$EvidenceNote
    )
    $key = Normalize-Key $Name
    if (-not $key) { return }
    if (-not $Map.ContainsKey($FundId)) { $Map[$FundId] = @{} }
    $Map[$FundId][$key] = [pscustomobject]@{
        FundName = $FundName
        StartupName = $Name
        Url = $Url
        EvidenceNote = $EvidenceNote
    }
}

$edgePath = Join-Path $Root 'canonical\canonical_investment_edges.csv'
$entityPath = Join-Path $Root 'canonical\canonical_entities.csv'
$masterPath = Join-Path $Root 'startup_master_dataset.csv'

$edges = Import-Csv -LiteralPath $edgePath
$entities = Import-Csv -LiteralPath $entityPath
$masterRows = Import-Csv -LiteralPath $masterPath

$entityById = @{}
foreach ($entity in $entities) {
    $key = Clean-Text $entity.entity_id
    if ($key) { $entityById[$key] = $entity }
}
$masterById = @{}
foreach ($row in $masterRows) {
    $key = Clean-Text $row.startup_id
    if ($key) { $masterById[$key] = $row }
}

$verified = @{}

$sf500Url = 'https://sf500.com.ar/portfolio/'
$sf500Names = @(
    'Oncoliq','Limay Biosciences','MultiplAI Health','Tell','Dharma BioScience','Exomas','Mesenchyal-T','Libera',
    'Spectrum','Biotalife','Pill.AR','Gameet','Eureka','Trebe Biotech','Mycorium Biotech','Tintte','INMET',
    'UNIBAIO','M4Life','BEAM CropTech','Eirú','SoyGREEN','BioMetallum','NotFossil'
)
foreach ($name in $sf500Names) {
    Add-VerifiedName $verified 'SF500' 'SF500' $name $sf500Url 'SF500 official portfolio page lists this startup in its portfolio.'
}

$airUrl = 'https://www.aircapital.vc/portfolio'
$airNames = @(
    'Stämm','Gigablue','Outpost','Skyloom','Puna Bio','Beeflow','Novo Space','Ayuvant','Ethos','ArgenTAG',
    'Lemon','Egg','Inner Cosmos','Starlight Ventures','Tissue Dynamics','Branch Energy','Menta Tickets',
    'Onco Precision','Laurus','Oncoliq','Blerify','FeedVax','Done Properly','Ergo Foods','Sylvarum','Cellva',
    'Arcomed','Calice','Satellites On Fire','Aplife Biotech','Alma Space','Ammobia','Antarka','Aptos Orbital',
    'Bioeutectics','BioOrbit','CellCo','CellRep','Dogma Biotech','Fork & Good','Giraffe Bio','GlycoX',
    'MetaBIX Biotech','Momentum Therapeutics','Power Matrix','/q99','Semion Bio'
)
foreach ($name in $airNames) {
    Add-VerifiedName $verified 'AIR Capital' 'AIR Capital' $name $airUrl 'AIR Capital official portfolio page lists this startup.'
}

$ganeshaUrl = 'https://theganeshalab.com/startups/'
$ganeshaNames = @(
    'TELL','Patagon Fiber','Nanotransfer','Eywa','Amplify Dynamics','Trears Biomarkers','Innovai','Delee',
    'Biogea','Aquit','Synergic Bio Solutions','arcomedLab','Aictive','Vali','Bleps Vision','Biome Resources',
    'Metabix Biotech','Bifidice','UNIBAIO','Risas Pendientes','The Earth Says','Farmtastica','Smart Tissues',
    'Pannex','Luyef','GlucoLib','Soleit','Tensor Care','Bee Technology','EcoAustralis','SciPhage','Retidiag',
    'Botanical Solutions','Purple Dental','CuperScience'
)
foreach ($name in $ganeshaNames) {
    Add-VerifiedName $verified 'the-ganesha-lab' 'The Ganesha Lab' $name $ganeshaUrl 'The Ganesha Lab official startups page lists this startup.'
    Add-VerifiedName $verified 'The Ganesha Lab' 'The Ganesha Lab' $name $ganeshaUrl 'The Ganesha Lab official startups page lists this startup.'
}

$antomUrl = 'https://www.antom.la/portfolio-projects-en'
$antomNames = @('Kilimo','Ruuts','Nideport','Kigui','Huiro','Satellites On Fire','Conciencia','CIRCCLO','Eirú','Agrojusto')
foreach ($name in $antomNames) {
    Add-VerifiedName $verified 'Antom' 'Antom' $name $antomUrl 'Antom official portfolio page lists this project.'
}

$draperSpecific = @(
    @{ Name = 'Stämm'; Url = 'https://www.drapercygnus.vc/startups/stamm'; Note = 'Draper Cygnus official startup page profiles Stamm.' },
    @{ Name = 'ArgenTAG'; Url = 'https://www.drapercygnus.vc/startups/argentag'; Note = 'Draper Cygnus official startup page profiles ArgenTAG.' },
    @{ Name = 'Microterra'; Url = 'https://www.drapercygnus.vc/startups/microterra'; Note = 'Draper Cygnus official startup page profiles Microterra.' },
    @{ Name = 'Satellites On Fire'; Url = 'https://www.drapercygnus.vc/startups/satellites-on-fire'; Note = 'Draper Cygnus official startup page profiles Satellites On Fire.' }
)
foreach ($item in $draperSpecific) {
    Add-VerifiedName $verified 'DraperCygnus' 'DraperCygnus' $item.Name $item.Url $item.Note
}

$citesSpecific = @(
    @{ Name = 'Ardan'; Url = 'https://cites-gss.com/en/portfolio/ardan-en/'; Note = 'CITES official portfolio page profiles Ardan.' },
    @{ Name = 'Ardan Pharma'; Url = 'https://cites-gss.com/en/portfolio/ardan-en/'; Note = 'CITES official portfolio page profiles Ardan Pharma.' },
    @{ Name = 'Bioseek'; Url = 'https://cites-gss.com/en/portfolio/bioseek-2/'; Note = 'CITES official portfolio page profiles Bioseek.' }
)
foreach ($item in $citesSpecific) {
    Add-VerifiedName $verified 'CITES' 'CITES' $item.Name $item.Url $item.Note
}

$updated = 0
$updatedByFund = @{}
foreach ($edge in $edges) {
    $fundId = Clean-Text $edge.investor_id
    if (-not $verified.ContainsKey($fundId)) { continue }

    $startupId = Clean-Text $edge.startup_id
    $candidateKeys = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($candidate in @($startupId)) {
        $key = Normalize-Key $candidate
        if ($key) { [void]$candidateKeys.Add($key) }
    }
    if ($entityById.ContainsKey($startupId)) {
        $key = Normalize-Key $entityById[$startupId].canonical_name
        if ($key) { [void]$candidateKeys.Add($key) }
    }
    if ($masterById.ContainsKey($startupId)) {
        $key = Normalize-Key $masterById[$startupId].startup_name
        if ($key) { [void]$candidateKeys.Add($key) }
    }

    $match = $null
    foreach ($key in $candidateKeys) {
        if ($verified[$fundId].ContainsKey($key)) {
            $match = $verified[$fundId][$key]
            break
        }
    }
    if (-not $match) { continue }

    $edge.source_file = $match.Url
    $edge.relation_type_raw = 'official_portfolio_investment'
    $edge.direction_status = 'validated_investor_to_startup'
    $edge.confidence_score = '0.96'
    $edge.notes = "$($match.EvidenceNote) Matched as $($match.StartupName)."
    $updated++
    if (-not $updatedByFund.ContainsKey($fundId)) { $updatedByFund[$fundId] = 0 }
    $updatedByFund[$fundId] = [int]$updatedByFund[$fundId] + 1
}

$edges |
    Sort-Object investor_id, startup_id, source_file, investment_id |
    Export-Csv -LiteralPath $edgePath -NoTypeInformation -Encoding UTF8

Write-Output "Capital edge specific evidence upgrade batch 02: $updated canonical rows updated."
$updatedByFund.GetEnumerator() |
    Sort-Object Name |
    ForEach-Object { Write-Output "$($_.Name): $($_.Value)" }
