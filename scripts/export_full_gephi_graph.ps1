param(
    [string]$GephiPath = "C:\Users\Pablo A\Desktop\Ecosistema Startups Materiales Universidades Fondos Startups 426112025.gephi",
    [string]$OutputDir = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\full_gephi_graph"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workspace = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack"
$jarDir = Join-Path $workspace 'tmp\gephi_jars'
if (-not (Test-Path -LiteralPath $jarDir)) {
    New-Item -ItemType Directory -Path $jarDir | Out-Null
}

$sourceJars = @(
    'C:\Program Files\Gephi-0.10.1\gephi\modules\org-gephi-graph-api.jar',
    'C:\Program Files\Gephi-0.10.1\gephi\modules\ext\org.gephi.graph-api\org-gephi\graphstore.jar',
    'C:\Program Files\Gephi-0.10.1\gephi\modules\ext\org.gephi.graph-api\it-unimi-dsi\fastutil.jar',
    'C:\Program Files\Gephi-0.10.1\gephi\modules\ext\org.gephi.graph-api\colt\colt.jar',
    'C:\Program Files\Gephi-0.10.1\gephi\modules\ext\org.gephi.graph-api\concurrent\concurrent.jar',
    'C:\Program Files\Gephi-0.10.1\gephi\modules\ext\org.gephi.graph-api\joda-time\joda-time.jar'
)

foreach ($jar in $sourceJars) {
    Copy-Item -LiteralPath $jar -Destination (Join-Path $jarDir ([IO.Path]::GetFileName($jar))) -Force
}

$cp = @(
    Join-Path $jarDir 'graphstore.jar'
    Join-Path $jarDir 'org-gephi-graph-api.jar'
    Join-Path $jarDir 'fastutil.jar'
    Join-Path $jarDir 'colt.jar'
    Join-Path $jarDir 'concurrent.jar'
    Join-Path $jarDir 'joda-time.jar'
) -join ';'

$jrunscript = 'C:\Program Files\Gephi-0.10.1\jre-x64\jdk-11.0.17+8-jre\bin\jrunscript.exe'
$scriptPath = Join-Path $workspace 'scripts\export_full_gephi_graph.js'

& $jrunscript '-cp' $cp '-f' $scriptPath $GephiPath $OutputDir
