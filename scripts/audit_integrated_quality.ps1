param(
    [string]$IntegratedDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\integrated",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$entities = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_entities.csv')
$aliases = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_aliases.csv')
$relations = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_relations.csv')
$reviewQueue = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_review_queue.csv')
$provenance = Import-Csv -LiteralPath (Join-Path $IntegratedDir 'integrated_provenance.csv')

$entityTypeCoverage = $entities |
    Group-Object integrated_type |
    Sort-Object Count -Descending |
    Select-Object @{Name='entity_type';Expression={$_.Name}}, Count

$relationCoverage = $relations |
    Group-Object relation_type |
    Sort-Object Count -Descending |
    Select-Object @{Name='relation_type';Expression={$_.Name}}, Count

$flagCoverage = $entities |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_.quality_flags) } |
    ForEach-Object {
        foreach ($flag in (@($_.quality_flags -split '\|' | Where-Object { $_ }))) {
            [PSCustomObject]@{ quality_flag = $flag }
        }
    } |
    Group-Object quality_flag |
    Sort-Object Count -Descending |
    Select-Object @{Name='quality_flag';Expression={$_.Name}}, Count

$institutionReview = $entities |
    Where-Object {
        $_.integrated_type -eq 'institution' -and (
            $_.canonical_name -match '\($' -or
            $_.canonical_name -match '\.[A-Z]$' -or
            $_.canonical_name -match 'Tecnolog$|Investigaci$|Biolog$|Tucum$|San Andr$|del Pac$|de la Rep$|de Santiago de Chile \(USACH$|de Palermo \(UP$|Nacional de C$|Nacional de R$|Nacional de Asunci$|de San Mart$'
        )
    } |
    Sort-Object canonical_name |
    Select-Object entity_id, canonical_name, canonical_type, confidence_score, integrated_sources, quality_flags

$topInstitutionRelations = $relations |
    Where-Object { $_.relation_type -ne 'funded_by' } |
    Sort-Object relation_type, source_entity_id, target_entity_id |
    Select-Object source_entity_id, target_entity_id, relation_type, confidence, source_kind, notes

$summaryLines = @(
    '# Audit de calidad integrada'
    ''
    '## Resumen'
    "- Entidades: $(@($entities).Count)"
    "- Aliases: $(@($aliases).Count)"
    "- Relaciones: $(@($relations).Count)"
    "- Procedencias: $(@($provenance).Count)"
    "- Review queue: $(@($reviewQueue).Count)"
    ''
    '## Cobertura por tipo'
)

foreach ($row in $entityTypeCoverage) {
    $summaryLines += "- $($row.entity_type): $($row.Count)"
}

$summaryLines += ''
$summaryLines += '## Cobertura por relacion'
foreach ($row in $relationCoverage) {
    $summaryLines += "- $($row.relation_type): $($row.Count)"
}

$summaryLines += ''
$summaryLines += '## Flags de calidad'
if (@($flagCoverage).Count -eq 0) {
    $summaryLines += '- sin flags activos'
} else {
    foreach ($row in $flagCoverage) {
        $summaryLines += "- $($row.quality_flag): $($row.Count)"
    }
}

$summaryLines += ''
$summaryLines += '## Focos para la siguiente iteracion'
$summaryLines += '- revisar instituciones truncadas o incompletas en institution_review_queue.csv'
$summaryLines += '- expandir relaciones institucionales reales mas alla de funded_by'
$summaryLines += '- completar aliases de branding y codificacion pendiente'

$summaryLines | Set-Content -LiteralPath (Join-Path $OutputDir 'integrated_quality_audit.md') -Encoding UTF8

$entityTypeCoverage | Export-Csv -LiteralPath (Join-Path $OutputDir 'entity_type_coverage.csv') -NoTypeInformation -Encoding UTF8
$relationCoverage | Export-Csv -LiteralPath (Join-Path $OutputDir 'relation_type_coverage.csv') -NoTypeInformation -Encoding UTF8
$flagCoverage | Export-Csv -LiteralPath (Join-Path $OutputDir 'quality_flag_coverage.csv') -NoTypeInformation -Encoding UTF8
$institutionReview | Export-Csv -LiteralPath (Join-Path $OutputDir 'institution_review_queue.csv') -NoTypeInformation -Encoding UTF8
$topInstitutionRelations | Export-Csv -LiteralPath (Join-Path $OutputDir 'non_funding_relations.csv') -NoTypeInformation -Encoding UTF8

Write-Output "Integrated quality audit complete: $OutputDir"
