param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$steps = @(
    'upgrade_startup_quality_credibility_batch.ps1',
    'upgrade_semantic_text_batch_01.ps1',
    'upgrade_semantic_text_batch_02.ps1',
    'upgrade_semantic_text_batch_03.ps1',
    'upgrade_semantic_text_batch_04.ps1',
    'upgrade_semantic_text_batch_05.ps1',
    'upgrade_semantic_text_batch_06.ps1',
    'upgrade_semantic_text_batch_07.ps1',
    'build_startup_taxonomy_layer.ps1',
    'build_startup_profiles_minimum_viable.ps1',
    'build_startup_data_quality_audit.ps1',
    'build_startup_master_dataset.ps1',
    'build_source_backed_tracker.ps1',
    'build_source_registry.ps1',
    'build_reference_base_status.ps1',
    'build_startup_profiles_dashboard_data.ps1',
    'build_semantic_single_level_sweep.ps1',
    'build_fund_portfolio_observations.ps1',
    'build_canonical_layer.ps1',
    'validate_reference_base.ps1',
    'build_curation_workstreams.ps1',
    'build_quality_dashboard_data.ps1',
    'build_semantic_quality_queue.ps1',
    'build_fund_analytics_data.ps1',
    'build_matchmaking_recommendations.ps1',
    'upgrade_capital_edge_sources_batch_01.ps1',
    'upgrade_capital_edge_sources_batch_02_specific.ps1',
    'upgrade_capital_edge_sources_batch_03_structure.ps1',
    'upgrade_capital_edge_sources_batch_04_portfolio_depth.ps1',
    'upgrade_bidlab_capital_layer.ps1',
    'upgrade_capital_island_triage.ps1',
    'upgrade_1200vc_capital_layer.ps1',
    'upgrade_idb_invest_capital_layer.ps1',
    'upgrade_gridx_specific_edge_evidence.ps1',
    'validate_reference_base.ps1',
    'build_capital_atlas_data.ps1',
    'build_capital_quality_dashboard_data.ps1',
    'build_semantic_taxonomy_beta.ps1',
    'build_semantic_beta_assignments_data.ps1',
    'build_semantic_taxonomy_beta_dashboard_data.ps1'
)

foreach ($step in $steps) {
    $path = Join-Path $Root ("scripts\" + $step)
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing pipeline step: $path"
    }
    Write-Output ("Running {0}..." -f $step)
    & powershell -ExecutionPolicy Bypass -File $path
}

Write-Output "Reference pipeline rebuilt sequentially."
