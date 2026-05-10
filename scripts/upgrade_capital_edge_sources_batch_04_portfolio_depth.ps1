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

function Set-FundLevelEvidence {
    param(
        [object]$Row,
        [string]$Source,
        [string]$Notes,
        [string]$Confidence = '0.86'
    )
    $Row.relation_type_raw = 'portfolio_page_lead'
    $Row.direction_status = 'validated_investor_to_startup'
    $Row.confidence_score = $Confidence
    $Row.source_file = $Source
    $Row.notes = $Notes
}

$canonicalPath = Join-Path $Root 'canonical\canonical_investment_edges.csv'
$rows = @(Import-Csv -LiteralPath $canonicalPath)
$updates = 0

$citesLabels = @{
    'abastra' = 'Abastra'
    'bionirs' = 'Bionirs'
    'circatherapeutics' = 'Circa Therapeutics'
    'clover' = 'Clover'
    'crinsurance' = 'Crinsurance'
    'eolopharma' = 'Eolo Pharma'
    'epiliquid' = 'Epiliquid'
    'ergobioscience' = 'Ergo Bioscience'
    'gbot' = 'Gbot'
    'imvalv' = 'Imvalv'
    'limaybiosciences' = 'Limay Biosciences'
    'pepton' = 'Pepton'
    'phylumtech' = 'Phylumtech'
    'radbio' = 'RadBio'
    'singlestrandbiotech' = 'Single Strand Biotech'
    'stradot' = 'Stradot'
    'teramot' = 'Teramot'
    'viewmind' = 'ViewMind'
}
$citesSource = 'https://cites-gss.com/en/portfolio/'

$sosvSources = @{
    'argentag' = @{ Label = 'ArgenTAG'; Url = 'https://indiebio.co/company/argentag/' }
    'beeflow' = @{ Label = 'Beeflow'; Url = 'https://indiebio.co/company/beeflow/' }
    'michroma' = @{ Label = 'Michroma'; Url = 'https://indiebio.co/company/michroma/' }
    'microgenesis' = @{ Label = 'Microgenesis'; Url = 'https://indiebio.co/company/microgenesis/' }
    'oncoprecision' = @{ Label = 'OncoPrecision'; Url = 'https://indiebio.co/company/oncoprecision/' }
    'punabio' = @{ Label = 'Puna Bio'; Url = 'https://indiebio.co/company/puna-bio/' }
    'stamm' = @{ Label = 'STAMM'; Url = 'https://indiebio.co/company/stamm/' }
}

$yieldSources = @{
    'agree' = @{ Label = 'Agree'; Url = 'https://theyieldlablatam.com/companies/agree/' }
    'agroforte' = @{ Label = 'Agroforte'; Url = 'https://theyieldlablatam.com/companies/agroforte/' }
    'auravant' = @{ Label = 'Auravant'; Url = 'https://theyieldlablatam.com/companies/auravant/' }
    'circular' = @{ Label = 'Circular'; Url = 'https://theyieldlablatam.com/companies/circular/' }
    'courageousland' = @{ Label = 'Courageous Land'; Url = 'https://theyieldlablatam.com/companies/courageous-land/' }
    'eiwa' = @{ Label = 'Eiwa'; Url = 'https://theyieldlablatam.com/companies/eiwa/' }
    'heartbest' = @{ Label = 'Heartbest'; Url = 'https://theyieldlablatam.com/companies/heartbest/' }
    'tech' = @{ Label = '@Tech'; Url = 'https://theyieldlablatam.com/companies/atech/' }
}

$kamayLabels = @{
    'aerialoop' = 'Aerialoop'
    'altscore' = 'AltScore'
    'arqlite' = 'Arqlite'
    'auravant' = 'Auravant'
    'bacu' = 'Bacu'
    'ini' = 'Ini'
    'logshare' = 'Logshare'
    'muta' = 'Muta'
    'nude' = 'Nude'
    'retrypay' = 'RetryPay'
    'ruedata' = 'Ruedata'
    'sensei' = 'Sensei'
    'sensify' = 'Sensify'
    'solfium' = 'Solfium'
    'webee' = 'Webee'
    'wiagro' = 'Wiagro'
    'wisy' = 'Wisy'
    'zipnova' = 'Zipnova'
}
$kamaySource = 'https://kamayventures.com/'

foreach ($row in $rows) {
    $investor = Clean-Text $row.investor_id
    $startupKey = Normalize-Key $row.startup_id

    if ($investor -eq 'CITES' -and $citesLabels.ContainsKey($startupKey)) {
        Set-EdgeEvidence -Row $row `
            -Relation 'official_portfolio_investment' `
            -Source $citesSource `
            -Confidence '0.96' `
            -Notes "CITES official portfolio page lists $($citesLabels[$startupKey]); upgraded to explicit official portfolio evidence."
        $updates += 1
        continue
    }

    if ($investor -eq 'SOSV_IndieBio' -and $sosvSources.ContainsKey($startupKey)) {
        $source = $sosvSources[$startupKey]
        Set-EdgeEvidence -Row $row `
            -Relation 'official_portfolio_investment' `
            -Source $source.Url `
            -Confidence '0.97' `
            -Notes "IndieBio/SOSV official company page profiles $($source.Label); upgraded from generic IndieBio URL to startup-specific portfolio evidence."
        $updates += 1
        continue
    }

    if ($investor -eq 'the_yield_lab_latam' -and $yieldSources.ContainsKey($startupKey)) {
        $source = $yieldSources[$startupKey]
        Set-EdgeEvidence -Row $row `
            -Relation 'official_portfolio_investment' `
            -Source $source.Url `
            -Confidence '0.96' `
            -Notes "The Yield Lab Latam official company page profiles $($source.Label); upgraded from historical graph to startup-specific portfolio evidence."
        $updates += 1
        continue
    }

    if ($investor -eq 'kamay_ventures' -and $kamayLabels.ContainsKey($startupKey) -and (Clean-Text $row.relation_type_raw) -ne 'investment_announcement') {
        Set-FundLevelEvidence -Row $row `
            -Source $kamaySource `
            -Confidence '0.86' `
            -Notes "Kamay Ventures official website has an Our portfolio section, but current auditable HTML does not expose $($kamayLabels[$startupKey]) as text; keep as public portfolio lead pending startup-specific confirmation."
        $updates += 1
        continue
    }
}

$rows | Export-Csv -LiteralPath $canonicalPath -NoTypeInformation -Encoding UTF8
Write-Output "Capital portfolio depth upgrade batch 04 completed."
Write-Output "Rows updated: $updates"
