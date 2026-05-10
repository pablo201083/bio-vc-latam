param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack",
    [string]$ReportCsvPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\product_surface_validation.csv",
    [string]$ReportMdPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\product_surface_validation.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$targets = @(
    'pilot\index.html',
    'pilot\startup-themes.html',
    'pilot\startup-themes.js',
    'pilot\capital-atlas.html',
    'pilot\capital-atlas.js',
    'pilot\matchmaking.html',
    'pilot\matchmaking.js'
)

$forbidden = @(
    'evidencia a reforzar',
    'tesis concentra',
    'grado base',
    'taxonomy_stub',
    'macrotheme',
    'microcluster',
    'semantic edge cases'
)

$rows = New-Object System.Collections.Generic.List[object]
foreach ($relative in $targets) {
    $path = Join-Path $Root $relative
    if (-not (Test-Path -LiteralPath $path)) {
        $rows.Add([pscustomobject]@{
            file = $relative
            status = 'missing'
            forbidden_term = ''
            line = ''
            excerpt = ''
        }) | Out-Null
        continue
    }
    $lineNumber = 0
    foreach ($line in [IO.File]::ReadLines($path)) {
        $lineNumber++
        foreach ($term in $forbidden) {
            if ($line.IndexOf($term, [StringComparison]::OrdinalIgnoreCase) -lt 0) { continue }
            $rows.Add([pscustomobject]@{
                file = $relative
                status = 'warn'
                forbidden_term = $term
                line = $lineNumber
                excerpt = $line.Trim()
            }) | Out-Null
        }
    }
}

if ($rows.Count -eq 0) {
    $rows.Add([pscustomobject]@{
        file = 'product_surface'
        status = 'pass'
        forbidden_term = ''
        line = ''
        excerpt = 'No internal/backoffice labels found in product-facing surfaces.'
    }) | Out-Null
}

$rows | Export-Csv -LiteralPath $ReportCsvPath -NoTypeInformation -Encoding UTF8

$warnings = @($rows | Where-Object { $_.status -eq 'warn' }).Count
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# Product Surface Validation') | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("Generated at: {0}" -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))) | Out-Null
$lines.Add(("Warnings: {0}" -f $warnings)) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('Scans product-facing pages for internal/backoffice labels that should stay in quality trackers.') | Out-Null
$lines.Add('') | Out-Null
foreach ($row in $rows) {
    $lines.Add(("- {0}: {1} {2} {3}" -f $row.status, $row.file, $row.forbidden_term, $row.line)) | Out-Null
}
[IO.File]::WriteAllLines($ReportMdPath, $lines, [Text.Encoding]::UTF8)

Write-Output "Product surface validation built:"
Write-Output "  CSV: $ReportCsvPath"
Write-Output "  MD: $ReportMdPath"
Write-Output "  Warnings: $warnings"
