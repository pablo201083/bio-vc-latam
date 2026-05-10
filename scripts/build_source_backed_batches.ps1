param(
    [string]$PriorityQueuePath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_backed_priority_queue.csv",
    [string]$OutputCsvPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_backed_batch_plan.csv",
    [string]$OutputMdPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_backed_batch_strategy.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $PriorityQueuePath)) {
    throw "Missing priority queue: $PriorityQueuePath"
}

$rows = Import-Csv -LiteralPath $PriorityQueuePath

$batchConfigs = @(
    @{ name = 'Batch 1'; label = 'include_fragile_core'; filter = { param($r) $r.scope_decision -eq 'include' -and $r.quality_band -eq 'fragile' -and $r.macro_theme -in @('food biotech and novel ingredients','computational biology and scientific software','diagnostics and medtech','biomanufacturing and bioindustrial platforms','therapeutics and regenerative medicine') }; size = 20; goal = 'Source acquisition for thesis-core fragile includes' }
    @{ name = 'Batch 2'; label = 'include_fragile_systems'; filter = { param($r) $r.scope_decision -eq 'include' -and $r.quality_band -eq 'fragile' -and $r.macro_theme -in @('climate, energy and resource systems','precision agriculture and resource intelligence','ag biologicals and crop resilience','biobased chemistry and advanced materials','frontier hardware and infrastructure systems') }; size = 20; goal = 'Source acquisition for climate, ag and materials edge cases' }
    @{ name = 'Batch 3'; label = 'include_medium_core'; filter = { param($r) $r.scope_decision -eq 'include' -and $r.quality_band -eq 'medium' -and $r.macro_theme -in @('food biotech and novel ingredients','computational biology and scientific software','diagnostics and medtech','biomanufacturing and bioindustrial platforms','therapeutics and regenerative medicine') }; size = 25; goal = 'Scale source coverage across medium-quality thesis-core startups' }
    @{ name = 'Batch 4'; label = 'include_medium_systems'; filter = { param($r) $r.scope_decision -eq 'include' -and $r.quality_band -eq 'medium' -and $r.macro_theme -in @('climate, energy and resource systems','precision agriculture and resource intelligence','ag biologicals and crop resilience','biobased chemistry and advanced materials','frontier hardware and infrastructure systems') }; size = 25; goal = 'Scale source coverage across systems, materials and infrastructure startups' }
    @{ name = 'Batch 5'; label = 'exclude_fast_cleanup'; filter = { param($r) $r.scope_decision -eq 'exclude' -and $r.macro_theme -eq 'peripheral or non-core digital ventures' }; size = 30; goal = 'Fast external-source confirmation for excluded full-digital startups' }
)

$usedKeys = [System.Collections.Generic.HashSet[string]]::new()
$planned = [System.Collections.Generic.List[object]]::new()

foreach ($config in $batchConfigs) {
    $selected = @(
        $rows |
            Where-Object { -not $usedKeys.Contains([string]$_.startup_id) } |
            Where-Object { & $config.filter $_ } |
            Sort-Object @{ Expression = { [int]$_.priority }; Descending = $true }, @{ Expression = 'startup_name'; Descending = $false } |
            Select-Object -First $config.size
    )

    $rank = 1
    foreach ($row in $selected) {
        $null = $usedKeys.Add([string]$row.startup_id)
        $planned.Add([PSCustomObject]@{
            batch_name = $config.name
            batch_label = $config.label
            batch_goal = $config.goal
            batch_rank = $rank
            startup_id = [string]$row.startup_id
            startup_name = [string]$row.startup_name
            scope_decision = [string]$row.scope_decision
            macro_theme = [string]$row.macro_theme
            review_status = [string]$row.review_status
            quality_band = [string]$row.quality_band
            priority = [string]$row.priority
            current_summary = [string]$row.current_summary
        }) | Out-Null
        $rank += 1
    }
}

$planned | Export-Csv -LiteralPath $OutputCsvPath -NoTypeInformation -Encoding UTF8

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Source-Backed Batch Strategy') | Out-Null
$lines.Add('') | Out-Null
$lines.Add(("Generated at: {0}" -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))) | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Why larger batches') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('- Use large batches for `source acquisition` only: find external URLs and minimal evidence fast.') | Out-Null
$lines.Add('- Use smaller follow-up passes for `editorial hardening`: refine summary, scope note and taxonomy adjustments.') | Out-Null
$lines.Add('- This keeps quality high while increasing throughput.') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('## Batches') | Out-Null
$lines.Add('') | Out-Null

foreach ($group in ($planned | Group-Object batch_name)) {
    $first = $group.Group | Select-Object -First 1
    $lines.Add(("### {0}" -f $first.batch_name)) | Out-Null
    $lines.Add(("- Goal: {0}" -f $first.batch_goal)) | Out-Null
    $lines.Add(("- Size: {0}" -f $group.Count)) | Out-Null
    $lines.Add(("- Composition: {0}" -f (($group.Group | Group-Object macro_theme | Sort-Object Count -Descending | ForEach-Object { '{0} ({1})' -f $_.Name, $_.Count }) -join '; '))) | Out-Null
    $lines.Add('') | Out-Null
}

$lines.Add('## Recommended rhythm') | Out-Null
$lines.Add('') | Out-Null
$lines.Add('- Run one big batch of 20-25 startups for source acquisition.') | Out-Null
$lines.Add('- Then do one smaller pass of 8-10 startups to harden summaries and taxonomy where needed.') | Out-Null
$lines.Add('- Repeat until `include without source` falls below 50.') | Out-Null

Set-Content -LiteralPath $OutputMdPath -Value $lines -Encoding UTF8

Write-Output "Source-backed batch plan built:"
Write-Output "  CSV: $OutputCsvPath"
Write-Output "  MD: $OutputMdPath"
