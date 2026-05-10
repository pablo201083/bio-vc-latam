param(
    [string]$IntegratedDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\integrated",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\hub_audits"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$entities = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_entities.csv')
$relations = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_relations.csv')
$aliases = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_aliases.csv')

$entityMap = @{}
foreach ($entity in $entities) {
    $entityMap[$entity.entity_id] = $entity
}

function Normalize-Name {
    param([string]$Name)
    if ([string]::IsNullOrWhiteSpace($Name)) { return '' }
    return (($Name.ToLowerInvariant()) -replace '[^a-z0-9]+','')
}

$capitalSummary = foreach ($capital in ($entities | Where-Object { $_.integrated_type -eq 'capital' })) {
    $funded = @($relations | Where-Object { $_.source_entity_id -eq $capital.entity_id -and $_.relation_type -eq 'funded_by' })
    $uniqueTargets = @($funded | Select-Object -ExpandProperty target_entity_id -Unique)
    [PSCustomObject]@{
        entity_id = $capital.entity_id
        canonical_name = $capital.canonical_name
        funded_edges = $funded.Count
        unique_target_ids = $uniqueTargets.Count
        duplicate_edges = $funded.Count - $uniqueTargets.Count
        integrated_sources = $capital.integrated_sources
        confidence_score = $capital.confidence_score
    }
}

$capitalSummary |
    Sort-Object unique_target_ids -Descending |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'capital_hub_summary.csv') -NoTypeInformation -Encoding UTF8

$topHubs = @($capitalSummary | Sort-Object unique_target_ids -Descending | Select-Object -First 10)

foreach ($hub in $topHubs) {
    $funded = @($relations | Where-Object { $_.source_entity_id -eq $hub.entity_id -and $_.relation_type -eq 'funded_by' })
    $rows = foreach ($rel in $funded) {
        $target = $entityMap[$rel.target_entity_id]
        [PSCustomObject]@{
            source_entity_id = $rel.source_entity_id
            source_name = $hub.canonical_name
            target_entity_id = $rel.target_entity_id
            target_name = if ($null -ne $target) { $target.canonical_name } else { '' }
            target_norm = if ($null -ne $target) { Normalize-Name $target.canonical_name } else { '' }
            source_kind = $rel.source_kind
            confidence = $rel.confidence
            notes = $rel.notes
        }
    }

    $safeName = ($hub.canonical_name.ToLowerInvariant() -replace '[^a-z0-9]+','-').Trim('-')
    $rows | Sort-Object target_name, source_kind | Export-Csv -LiteralPath (Join-Path $OutputDir ($safeName + '_funding_edges.csv')) -NoTypeInformation -Encoding UTF8
}

$gridxRows = Import-Csv -LiteralPath (Join-Path $OutputDir 'gridx_funding_edges.csv')
$gridxReview = $gridxRows |
    Group-Object target_norm |
    Where-Object { $_.Count -gt 1 } |
    ForEach-Object {
        [PSCustomObject]@{
            normalized_name = $_.Name
            edge_rows = $_.Count
            target_names = ($_.Group | Select-Object -ExpandProperty target_name -Unique) -join ' | '
            target_ids = ($_.Group | Select-Object -ExpandProperty target_entity_id -Unique) -join ' | '
            source_kinds = ($_.Group | Select-Object -ExpandProperty source_kind -Unique) -join ' | '
        }
    }

$gridxReview |
    Sort-Object @{Expression='edge_rows';Descending=$true}, @{Expression='normalized_name';Descending=$false} |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'gridx_duplicate_candidates.csv') -NoTypeInformation -Encoding UTF8

$aliasRows = foreach ($alias in $aliases) {
    $entity = $entityMap[$alias.entity_id]
    [PSCustomObject]@{
        entity_id = $alias.entity_id
        canonical_name = if ($null -ne $entity) { $entity.canonical_name } else { '' }
        alias = $alias.alias
        alias_type = $alias.alias_type
        source_kind = $alias.source_kind
        notes = $alias.notes
    }
}

$aliasRows |
    Sort-Object canonical_name, alias |
    Export-Csv -LiteralPath (Join-Path $OutputDir 'alias_inventory.csv') -NoTypeInformation -Encoding UTF8

$summary = @"
Auditoria de hubs

Archivos:
- capital_hub_summary.csv
- gridx_funding_edges.csv
- gridx_duplicate_candidates.csv
- alias_inventory.csv

Notas:
- capital_hub_summary usa cantidad de startups unicas por hub
- gridx_duplicate_candidates marca grupos que todavia merecen revision manual
- alias_inventory sirve para revisar merges aplicados y pendientes
"@

Set-Content -LiteralPath (Join-Path $OutputDir 'README.md') -Value $summary -Encoding UTF8

Write-Output "Hub audit complete: $OutputDir"
