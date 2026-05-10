param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $Root 'scripts\build_semantic_quality_queue.js'
if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Missing semantic quality queue script: $scriptPath"
}

Push-Location $Root
try {
    & node $scriptPath
} finally {
    Pop-Location
}
