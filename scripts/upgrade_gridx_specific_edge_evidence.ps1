param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack",
    [string]$OfficialPortfolioUrl = "https://www.gridexponential.com/portfolio"
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

$edgePath = Join-Path $Root 'canonical\canonical_investment_edges.csv'
$taxonomyOverridePath = Join-Path $Root 'quality\manual_startup_taxonomy_overrides.csv'

$edges = Import-Csv -LiteralPath $edgePath
$gridxOverrides = Import-Csv -LiteralPath $taxonomyOverridePath |
    Where-Object { (Clean-Text $_.scope_source) -eq 'gridx_portfolio_official' }

$officialGridxByKey = @{}
foreach ($row in $gridxOverrides) {
    foreach ($candidate in @($row.startup_id, $row.startup_name)) {
        $key = Normalize-Key $candidate
        if ($key -and -not $officialGridxByKey.ContainsKey($key)) {
            $officialGridxByKey[$key] = $row
        }
    }
}

$updated = 0
foreach ($edge in $edges) {
    if ((Clean-Text $edge.investor_id) -ne 'GridX') { continue }
    $startupKey = Normalize-Key $edge.startup_id
    if (-not $startupKey -or -not $officialGridxByKey.ContainsKey($startupKey)) { continue }

    $override = $officialGridxByKey[$startupKey]
    $startupName = if (Clean-Text $override.startup_name) { Clean-Text $override.startup_name } else { Clean-Text $edge.startup_id }
    $overrideNote = Clean-Text $override.notes
    $edge.source_file = $OfficialPortfolioUrl
    $edge.relation_type_raw = 'official_portfolio_investment'
    $edge.direction_status = 'validated_investor_to_startup'
    $edge.confidence_score = '0.96'
    $edge.notes = "GridX official portfolio lists $startupName. $overrideNote"
    $updated++
}

$portfolioLeadUpdates = 0
foreach ($edge in $edges) {
    if ((Clean-Text $edge.investor_id) -ne 'GridX') { continue }
    if ((Clean-Text $edge.startup_id) -eq '0') { continue }
    if ((Clean-Text $edge.source_file) -match '^https?://' -and (Clean-Text $edge.relation_type_raw) -ne 'portfolio_page_lead') { continue }

    $edge.source_file = $OfficialPortfolioUrl
    $edge.relation_type_raw = 'portfolio_page_lead'
    $edge.direction_status = 'validated_investor_to_startup'
    $edge.confidence_score = '0.90'
    $existingNote = Clean-Text $edge.notes
    $edge.notes = if ($existingNote) {
        "$existingNote | GridX official portfolio page is used as public fund-level evidence for this mapped GridX relationship; keep in the specific-evidence queue until startup-level page/text is confirmed."
    } else {
        'GridX official portfolio page is used as public fund-level evidence for this mapped GridX relationship; keep in the specific-evidence queue until startup-level page/text is confirmed.'
    }
    $portfolioLeadUpdates++
}

$edges |
    Sort-Object investor_id, startup_id, source_file, investment_id |
    Export-Csv -LiteralPath $edgePath -NoTypeInformation -Encoding UTF8

Write-Output "GridX specific edge evidence upgrade: $updated canonical rows updated."
Write-Output "GridX public portfolio lead upgrade: $portfolioLeadUpdates canonical rows updated."
