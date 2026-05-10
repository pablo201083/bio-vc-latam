param(
    [string]$GephiPath = "C:\Users\Pablo A\Desktop\Ecosistema Startups Materiales Universidades Fondos Startups 426112025.gephi",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\structured_gephi"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($GephiPath)
$entry = $zip.Entries | Where-Object { $_.FullName -eq 'Workspace_1_graphstore_bytes' }
if (-not $entry) {
    throw "Workspace_1_graphstore_bytes not found in $GephiPath"
}

$stream = $entry.Open()
$bytes = New-Object byte[] $entry.Length
[void]$stream.Read($bytes, 0, $bytes.Length)
$stream.Close()
$zip.Dispose()

$tokens = New-Object System.Collections.Generic.List[object]
for ($i = 0; $i -lt $bytes.Length - 2; $i++) {
    if ($bytes[$i] -eq 0x67) {
        $len = [int]$bytes[$i + 1]
        if ($len -ge 1 -and $len -le 80 -and $i + 2 + $len -le $bytes.Length) {
            [byte[]]$slice = $bytes[($i + 2)..($i + 1 + $len)]
            $text = [System.Text.Encoding]::UTF8.GetString($slice)
            if ($text -match '^[A-Za-z0-9_ /().,+-]{1,80}$') {
                $tokens.Add([PSCustomObject]@{
                    offset = $i
                    len = $len
                    text = $text
                }) | Out-Null
            }
        }
    }
}

$relationNames = @('funded_by','has_founder','studied_at','researched_at','member_of','graduated_from','accelerated_at','incubated_at','spin_off_from','collaborates_with','built_by')
$firstRelationOffset = ($tokens | Where-Object { $_.text -in $relationNames } | Sort-Object offset | Select-Object -First 1).offset
if (-not $firstRelationOffset) {
    throw "Could not find relation section in graphstore bytes"
}

$nodeTokens = @($tokens | Where-Object { $_.offset -lt $firstRelationOffset -and $_.offset -gt 1200 })

function Is-SlugLike {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
    return $Text -match '^[a-z0-9_]+$'
}

function Is-GenericValue {
    param([string]$Text)
    return $Text -in @(
        'Startup','Investor','Investor4','Startup4','University','Research Institute','Accelerator','Corporate','Corporate VC',
        'Knowledge Hub4','Knowledge Hub','Digital Economy','Other / Unclassified','nan','Angel','VC','CVC','PE'
    )
}

$nodes = New-Object System.Collections.Generic.List[object]

for ($i = 0; $i -lt $nodeTokens.Count - 6; $i++) {
    $t0 = $nodeTokens[$i]
    $t1 = $nodeTokens[$i + 1]
    $t2 = $nodeTokens[$i + 2]

    if (-not (Is-SlugLike $t0.text)) { continue }
    if ($t1.text -ne $t0.text) { continue }
    if (Is-SlugLike $t2.text) { continue }
    if ($t2.text -match '^(java|PROPERTY|DATA|DOUBLE|PageRank|Label|Id|Interval|type|country|trl|gridx_vertical|valuation_tier|scientist|origin|inst_type|inv_type)$') { continue }

    $attrs = @()
    for ($j = $i + 3; $j -lt [Math]::Min($i + 9, $nodeTokens.Count); $j++) {
        $candidate = $nodeTokens[$j].text
        if ((Is-SlugLike $candidate) -and $j + 1 -lt $nodeTokens.Count -and $nodeTokens[$j + 1].text -eq $candidate) {
            break
        }
        $attrs += $candidate
    }

    $type = ($attrs | Where-Object { $_ -in @('Startup','Investor','University','Research Institute','Accelerator','Corporate','Corporate VC','Knowledge Hub4') } | Select-Object -First 1)
    $country = ($attrs | Where-Object { $_ -match '^[A-Z]{2}(/[A-Z]{2,})*$|^[A-Z][A-Za-z]+/[A-Z][A-Za-z]+$' -or $_ -eq 'nan' } | Select-Object -First 1)
    $sector = ($attrs | Where-Object { -not (Is-GenericValue $_) -and $_ -notmatch '^[A-Z]{2}(/[A-Z]{2,})*$|^[A-Z][A-Za-z]+/[A-Z][A-Za-z]+$' } | Select-Object -First 1)

    $nodes.Add([PSCustomObject]@{
        slug = $t0.text
        label = $t2.text
        inferred_type = if ($type) { $type } else { '' }
        inferred_country = if ($country) { $country } else { '' }
        inferred_sector = if ($sector -and $sector -ne $t2.text) { $sector } else { '' }
        offset = $t0.offset
        raw_attrs = ($attrs -join '|')
    }) | Out-Null
}

$deduped = $nodes |
    Group-Object slug |
    ForEach-Object { $_.Group | Sort-Object {[string]::IsNullOrWhiteSpace($_.inferred_type)}, {[string]::IsNullOrWhiteSpace($_.inferred_country)} | Select-Object -First 1 } |
    Sort-Object slug

$deduped | Export-Csv -LiteralPath (Join-Path $OutputDir 'structured_nodes_426112025.csv') -NoTypeInformation -Encoding UTF8

$summaryRows = @(
    [PSCustomObject]@{ metric = 'token_count'; value = [int]($tokens | Measure-Object | Select-Object -ExpandProperty Count) }
    [PSCustomObject]@{ metric = 'first_relation_offset'; value = [int]$firstRelationOffset }
    [PSCustomObject]@{ metric = 'structured_node_candidates'; value = [int]($nodes | Measure-Object | Select-Object -ExpandProperty Count) }
    [PSCustomObject]@{ metric = 'structured_nodes_deduped'; value = [int]($deduped | Measure-Object | Select-Object -ExpandProperty Count) }
)
$summaryRows | Export-Csv -LiteralPath (Join-Path $OutputDir 'structured_nodes_summary.csv') -NoTypeInformation -Encoding UTF8

Write-Output "Structured Gephi nodes extracted: $OutputDir"
