param(
    [string]$MasterPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$OutputAssignmentsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_beta_assignments.csv",
    [string]$OutputThemesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_beta_themes.csv",
    [string]$OutputReportPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_beta_report.md"
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

function Normalize-Text {
    param([string]$Text)
    $value = Clean-Text $Text
    if (-not $value) { return '' }
    $value = $value.ToLowerInvariant()
    $value = $value.Normalize([Text.NormalizationForm]::FormD)
    $chars = foreach ($char in $value.ToCharArray()) {
        if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($char) -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            $char
        }
    }
    return (-join $chars)
}

function Strip-EditorialText {
    param([string]$Text)
    $value = Clean-Text $Text
    if (-not $value) { return '' }
    $patterns = @(
        '(?i)\s+entra en tesis.*$',
        '(?i)\s+queda fuera.*$',
        '(?i)\s+sale de tesis.*$',
        '(?i)\s+la dejamos adentro.*$',
        '(?i)^official site describes\s+',
        '(?i)^official site presents\s+',
        '(?i)^official site states\s+',
        '(?i)^linkedin company profile states that\s+',
        '(?i)^linkedin company profile describes\s+',
        '(?i)^f6s profile describes\s+',
        '(?i)^tecnologico de monterrey describes\s+',
        '(?i)^gridx describes\s+',
        '(?i)^argentina\.gob\.ar describes\s+',
        '(?i)^the yield lab latam portfolio describes\s+'
    )
    foreach ($pattern in $patterns) {
        $value = [regex]::Replace($value, $pattern, '')
    }
    return $value.Trim()
}

function Get-DocumentText {
    param($Row)

    $optional = @{
        startup_summary_v1 = ''
        business_one_liner = ''
        evidence_excerpt = ''
        technical_stack = ''
        transition_function = ''
        industry_destination = ''
        problem_addressed = ''
        market_label = ''
    }
    foreach ($name in @($optional.Keys)) {
        $property = $Row.PSObject.Properties[$name]
        if ($null -ne $property) {
            $optional[$name] = $property.Value
        }
    }

    return @(
        Strip-EditorialText $optional.startup_summary_v1,
        Strip-EditorialText $optional.business_one_liner,
        Strip-EditorialText $optional.technical_stack,
        Strip-EditorialText $optional.industry_destination
    ) -join ' '
}

function Get-Stopwords {
    return @(
        'startup','startups','company','companies','empresa','empresas','platform','platforms','plataforma','plataformas',
        'technology','technologies','tecnologia','tecnologias','solution','solutions','solucion','soluciones',
        'using','uses','used','desarrolla','desarrollo','desarrollar','based','driven','enabled','powered',
        'system','systems','sistema','sistemas','tool','tools','herramienta','herramientas','service','services',
        'improve','improves','improving','improved','mejorar','mejora','mejoras','through','with','from','into',
        'that','this','their','these','those','para','desde','hacia','sobre','entre','con','sin','por','una','uno',
        'and','the','del','las','los','una','uno','ser','estar','como','más','mas','its','our','your','into',
        'industry','industrial','market','markets','mercado','mercados','production','produccion','products','product',
        'health','salud','food','alimentos','agriculture','agricultura','biotech','bio','life','scientific','software',
        'research','clinical','clinico','clinica','biology','biologia','medical','medico','medica','materials','materiales',
        'official','site','describes','entra','tesis','source','sources','based','sourcebacked','reviewed','seeded',
        'portfolio','website','gridx','develops','developing','desarrolla','desarrollando','user','users'
    )
}

function Get-Tokens {
    param(
        [string]$Text,
        [string[]]$Stopwords
    )
    $normalized = Normalize-Text $Text
    if (-not $normalized) { return @() }
    $tokens = [regex]::Matches($normalized, '[a-z]{4,}') | ForEach-Object { $_.Value }
    return @($tokens | Where-Object { $Stopwords -notcontains $_ })
}

function Add-ToVector {
    param(
        [hashtable]$Vector,
        [string]$Key,
        [double]$Value
    )
    if (-not $Vector.ContainsKey($Key)) {
        $Vector[$Key] = 0.0
    }
    $Vector[$Key] = [double]$Vector[$Key] + $Value
}

function Scale-Vector {
    param(
        [hashtable]$Vector,
        [double]$Scale
    )
    $scaled = @{}
    foreach ($key in $Vector.Keys) {
        $scaled[$key] = [double]$Vector[$key] * $Scale
    }
    return $scaled
}

function Get-VectorNorm {
    param([hashtable]$Vector)
    $sumSquares = 0.0
    foreach ($value in $Vector.Values) {
        $sumSquares += ([double]$value * [double]$value)
    }
    return [math]::Sqrt($sumSquares)
}

function Get-CosineSimilarity {
    param(
        [hashtable]$A,
        [hashtable]$B
    )
    if ($A.Count -eq 0 -or $B.Count -eq 0) { return 0.0 }
    $normA = Get-VectorNorm $A
    $normB = Get-VectorNorm $B
    if ($normA -le 0 -or $normB -le 0) { return 0.0 }
    $dot = 0.0
    $small = if ($A.Count -le $B.Count) { $A } else { $B }
    $large = if ($A.Count -le $B.Count) { $B } else { $A }
    foreach ($key in $small.Keys) {
        if ($large.ContainsKey($key)) {
            $dot += ([double]$small[$key] * [double]$large[$key])
        }
    }
    return $dot / ($normA * $normB)
}

function Get-Centroid {
    param(
        [object[]]$Documents,
        [int[]]$Indices
    )
    $centroid = @{}
    if ($Indices.Count -eq 0) { return $centroid }
    foreach ($index in $Indices) {
        foreach ($key in $Documents[$index].vector.Keys) {
            Add-ToVector -Vector $centroid -Key $key -Value ([double]$Documents[$index].vector[$key])
        }
    }
    return (Scale-Vector -Vector $centroid -Scale (1.0 / [double]$Indices.Count))
}

function Get-FarthestFirstSeeds {
    param(
        [object[]]$Documents,
        [int]$K
    )
    $seeds = New-Object System.Collections.Generic.List[int]
    $firstIndex = 0
    $bestTokenCount = -1
    for ($i = 0; $i -lt $Documents.Count; $i++) {
        if ($Documents[$i].token_count -gt $bestTokenCount) {
            $bestTokenCount = $Documents[$i].token_count
            $firstIndex = $i
        }
    }
    $seeds.Add($firstIndex)

    while ($seeds.Count -lt $K) {
        $candidateIndex = -1
        $candidateDistance = -1.0
        for ($i = 0; $i -lt $Documents.Count; $i++) {
            if ($seeds.Contains($i)) { continue }
            $closest = 1.0
            foreach ($seed in $seeds) {
                $similarity = Get-CosineSimilarity -A $Documents[$i].vector -B $Documents[$seed].vector
                $distance = 1.0 - $similarity
                if ($distance -lt $closest) { $closest = $distance }
            }
            if ($closest -gt $candidateDistance) {
                $candidateDistance = $closest
                $candidateIndex = $i
            }
        }
        if ($candidateIndex -ge 0) {
            $seeds.Add($candidateIndex)
        } else {
            break
        }
    }

    return @($seeds.ToArray())
}

function Run-KMeansLike {
    param(
        [object[]]$Documents,
        [int]$K,
        [int]$MaxIterations = 20
    )

    $seedIndices = Get-FarthestFirstSeeds -Documents $Documents -K $K
    $centroids = @()
    foreach ($seed in $seedIndices) {
        $centroids += ,(@{} + $Documents[$seed].vector)
    }

    $assignments = @(-1) * $Documents.Count

    for ($iteration = 0; $iteration -lt $MaxIterations; $iteration++) {
        $changed = $false
        $clusters = @()
        for ($c = 0; $c -lt $K; $c++) { $clusters += ,(New-Object System.Collections.Generic.List[int]) }

        for ($i = 0; $i -lt $Documents.Count; $i++) {
            $bestCluster = 0
            $bestSimilarity = -1.0
            for ($c = 0; $c -lt $K; $c++) {
                $similarity = Get-CosineSimilarity -A $Documents[$i].vector -B $centroids[$c]
                if ($similarity -gt $bestSimilarity) {
                    $bestSimilarity = $similarity
                    $bestCluster = $c
                }
            }
            if ($assignments[$i] -ne $bestCluster) {
                $assignments[$i] = $bestCluster
                $changed = $true
            }
            $clusters[$bestCluster].Add($i)
        }

        foreach ($c in 0..($K - 1)) {
            if ($clusters[$c].Count -eq 0) {
                $farthestIndex = -1
                $farthestDistance = -1.0
                for ($i = 0; $i -lt $Documents.Count; $i++) {
                    $cluster = $assignments[$i]
                    $distance = 1.0 - (Get-CosineSimilarity -A $Documents[$i].vector -B $centroids[$cluster])
                    if ($distance -gt $farthestDistance) {
                        $farthestDistance = $distance
                        $farthestIndex = $i
                    }
                }
                if ($farthestIndex -ge 0) {
                    $assignments[$farthestIndex] = $c
                    $clusters[$c].Add($farthestIndex)
                }
            }
        }

        $newCentroids = @()
        foreach ($c in 0..($K - 1)) {
            $indices = @($clusters[$c].ToArray())
            $newCentroids += ,(Get-Centroid -Documents $Documents -Indices $indices)
        }
        $centroids = $newCentroids

        if (-not $changed -and $iteration -gt 0) { break }
    }

    return [pscustomobject]@{
        assignments = $assignments
        centroids = $centroids
    }
}

function Get-ClusterQuality {
    param(
        [object[]]$Documents,
        [int[]]$Assignments,
        [hashtable[]]$Centroids
    )
    $k = $Centroids.Count
    $clusters = @{}
    for ($c = 0; $c -lt $k; $c++) { $clusters[$c] = New-Object System.Collections.Generic.List[int] }
    for ($i = 0; $i -lt $Assignments.Count; $i++) {
        $clusters[$Assignments[$i]].Add($i)
    }

    $marginSum = 0.0
    $withinSum = 0.0
    $smallClusters = 0
    foreach ($c in 0..($k - 1)) {
        if ($clusters[$c].Count -lt 5) { $smallClusters++ }
    }

    for ($i = 0; $i -lt $Documents.Count; $i++) {
        $own = $Assignments[$i]
        $ownSim = Get-CosineSimilarity -A $Documents[$i].vector -B $Centroids[$own]
        $bestOther = 0.0
        for ($c = 0; $c -lt $k; $c++) {
            if ($c -eq $own) { continue }
            $sim = Get-CosineSimilarity -A $Documents[$i].vector -B $Centroids[$c]
            if ($sim -gt $bestOther) { $bestOther = $sim }
        }
        $marginSum += ($ownSim - $bestOther)
        $withinSum += $ownSim
    }

    $avgMargin = if ($Documents.Count -gt 0) { $marginSum / $Documents.Count } else { 0.0 }
    $avgWithin = if ($Documents.Count -gt 0) { $withinSum / $Documents.Count } else { 0.0 }
    $smallPenalty = ($smallClusters / [double][math]::Max(1, $k)) * 0.08
    $score = $avgMargin + ($avgWithin * 0.35) - $smallPenalty

    return [pscustomobject]@{
        score = [math]::Round($score, 4)
        avg_margin = [math]::Round($avgMargin, 4)
        avg_within = [math]::Round($avgWithin, 4)
        small_clusters = $smallClusters
        clusters = $clusters
    }
}

function Get-TopTokens {
    param(
        [string[]]$Texts,
        [int]$Limit = 8
    )
    $stopwords = Get-Stopwords
    $counts = @{}
    foreach ($text in $Texts) {
        foreach ($token in (Get-Tokens -Text $text -Stopwords $stopwords)) {
            if (-not $counts.ContainsKey($token)) { $counts[$token] = 0 }
            $counts[$token]++
        }
    }
    return @(
        $counts.GetEnumerator() |
        Sort-Object -Property Value, Name -Descending |
        Select-Object -First $Limit |
        ForEach-Object { $_.Name }
    )
}

function Get-Dominant {
    param(
        [object[]]$Rows,
        [string]$Property
    )
    $valid = @($Rows | Where-Object { Clean-Text $_.$Property })
    if ($valid.Count -eq 0) { return '' }
    return (($valid | Group-Object -Property $Property | Sort-Object Count -Descending | Select-Object -First 1).Name)
}

function Get-ThemeLabel {
    param(
        [string]$DominantMacro,
        [string[]]$TopTokens
    )
    $tokenSet = @{}
    foreach ($token in $TopTokens) { $tokenSet[$token] = $true }

    switch ($DominantMacro) {
        'food biotech and novel ingredients' { return 'food ingredients and biofactories' }
        'diagnostics and medtech' { return 'clinical diagnostics and medical devices' }
        'therapeutics and regenerative medicine' { return 'therapeutics and regenerative bio' }
        'biomanufacturing and bioindustrial platforms' { return 'biomanufacturing and molecular platforms' }
        'computational biology and scientific software' { return 'computational biology and genomic intelligence' }
        'ag biologicals and crop resilience' {
            if ($tokenSet.ContainsKey('traceability') -or $tokenSet.ContainsKey('logistics') -or $tokenSet.ContainsKey('grain') -or $tokenSet.ContainsKey('marketplace')) {
                return 'agri intelligence and traceable markets'
            }
            return 'ag biologicals and crop resilience'
        }
        'precision agriculture and resource intelligence' { return 'agri intelligence and traceable markets' }
        'biobased chemistry and advanced materials' {
            if ($tokenSet.ContainsKey('waste') -or $tokenSet.ContainsKey('carbon') -or $tokenSet.ContainsKey('mining') -or $tokenSet.ContainsKey('remediation') -or $tokenSet.ContainsKey('lithium')) {
                return 'resource recovery and remediation'
            }
            return 'biobased chemistry and circular materials'
        }
        'climate, energy and resource systems' {
            if ($tokenSet.ContainsKey('satellite') -or $tokenSet.ContainsKey('wildfire') -or $tokenSet.ContainsKey('marine') -or $tokenSet.ContainsKey('ocean') -or $tokenSet.ContainsKey('monitoring')) {
                return 'planetary monitoring and resilience systems'
            }
            if ($tokenSet.ContainsKey('battery') -or $tokenSet.ContainsKey('renewable') -or $tokenSet.ContainsKey('energy') -or $tokenSet.ContainsKey('grid') -or $tokenSet.ContainsKey('logistics') -or $tokenSet.ContainsKey('emissions')) {
                return 'climate and resource intelligence platforms'
            }
            return 'resource recovery and remediation'
        }
        'frontier hardware and infrastructure systems' { return 'planetary monitoring and resilience systems' }
        default {
            if ($tokenSet.ContainsKey('genomics') -or $tokenSet.ContainsKey('sequencing') -or $tokenSet.ContainsKey('bioinformatics')) { return 'computational biology and genomic intelligence' }
            if ($tokenSet.ContainsKey('ingredient') -or $tokenSet.ContainsKey('proteins') -or $tokenSet.ContainsKey('food')) { return 'food ingredients and biofactories' }
            if ($tokenSet.ContainsKey('therapeutic') -or $tokenSet.ContainsKey('cancer') -or $tokenSet.ContainsKey('regenerative')) { return 'therapeutics and regenerative bio' }
            if ($tokenSet.ContainsKey('diagnostic') -or $tokenSet.ContainsKey('device') -or $tokenSet.ContainsKey('biopsy')) { return 'clinical diagnostics and medical devices' }
            if ($tokenSet.ContainsKey('crop') -or $tokenSet.ContainsKey('soil') -or $tokenSet.ContainsKey('microbial')) { return 'ag biologicals and crop resilience' }
            if ($tokenSet.ContainsKey('traceability') -or $tokenSet.ContainsKey('agronomic') -or $tokenSet.ContainsKey('irrigation')) { return 'agri intelligence and traceable markets' }
            if ($tokenSet.ContainsKey('materials') -or $tokenSet.ContainsKey('biopolymer') -or $tokenSet.ContainsKey('plastic')) { return 'biobased chemistry and circular materials' }
            if ($tokenSet.ContainsKey('energy') -or $tokenSet.ContainsKey('battery') -or $tokenSet.ContainsKey('renewable')) { return 'climate and resource intelligence platforms' }
            if ($tokenSet.ContainsKey('satellite') -or $tokenSet.ContainsKey('ocean') -or $tokenSet.ContainsKey('wildfire')) { return 'planetary monitoring and resilience systems' }
            if ($tokenSet.ContainsKey('recovery') -or $tokenSet.ContainsKey('waste') -or $tokenSet.ContainsKey('remediation')) { return 'resource recovery and remediation' }
            return 'semantic edge cases'
        }
    }
}

function Get-ThemeDescription {
    param([string]$Theme)
    switch ($Theme) {
        'food ingredients and biofactories' { return 'Startups que usan biologia, fermentacion o microorganismos para producir ingredientes, proteinas o mejoras funcionales en sistemas alimentarios.' }
        'ag biologicals and crop resilience' { return 'Startups que intervienen directamente sobre cultivos, bioinsumos, microbiomas, polinizacion o resiliencia agropecuaria con biologia aplicada.' }
        'agri intelligence and traceable markets' { return 'Startups que organizan decision agronomica, trazabilidad, comercializacion o infraestructura transaccional acoplada a cadenas agroalimentarias materiales.' }
        'clinical diagnostics and medical devices' { return 'Startups que diagnostican, detectan o actuan clinicamente sobre sistemas vivos mediante dispositivos, pruebas o plataformas medicas concretas.' }
        'therapeutics and regenerative bio' { return 'Startups que construyen terapias, delivery biologico o medicina regenerativa sobre mecanismos moleculares, celulares o inmunologicos.' }
        'biomanufacturing and molecular platforms' { return 'Startups que habilitan produccion biologica, herramientas moleculares o manufactura biotecnologica escalable.' }
        'biobased chemistry and circular materials' { return 'Startups que reemplazan rutas fosiles o contaminantes por quimica verde, biomateriales o circularidad material.' }
        'computational biology and genomic intelligence' { return 'Startups que amplifican descubrimiento biologico con genomica, bioinformatica, high-throughput biology o software cientifico acoplado a life sciences.' }
        'climate and resource intelligence platforms' { return 'Startups que coordinan despliegue de energia limpia, descarbonizacion operativa o eficiencia material mediante software acoplado a sistemas fisicos de energia, transporte y recursos.' }
        'planetary monitoring and resilience systems' { return 'Startups que miden, anticipan u operan riesgos planetarios y ambientales mediante observacion, monitoreo e inteligencia aplicada a sistemas naturales o infraestructuras criticas.' }
        'resource recovery and remediation' { return 'Startups que recuperan materiales, cierran ciclos o remedian residuos, emisiones y flujos criticos del sistema productivo.' }
        default { return 'Cluster semantico puro basado en proximidad textual dentro del universo include + confirmed.' }
    }
}

function Get-GridxMatch {
    param([string]$Theme)
    switch ($Theme) {
        'food ingredients and biofactories' { return 'Agri-food-land use / Bio-industry' }
        'ag biologicals and crop resilience' { return 'Agri-food-land use' }
        'agri intelligence and traceable markets' { return 'Agri-food-land use' }
        'clinical diagnostics and medical devices' { return 'Human health' }
        'therapeutics and regenerative bio' { return 'Human health' }
        'biomanufacturing and molecular platforms' { return 'Deep-biotech / Bio-industry' }
        'biobased chemistry and circular materials' { return 'Bio-industry' }
        'computational biology and genomic intelligence' { return 'Deep-biotech / Human health' }
        'climate and resource intelligence platforms' { return 'Climate systems / Resource systems' }
        'planetary monitoring and resilience systems' { return 'Agri-food-land use / Climate systems' }
        'resource recovery and remediation' { return 'Bio-industry / Climate systems' }
        default { return 'Mixed / unresolved' }
    }
}

function Get-AntomMatch {
    param([string]$Theme)
    switch ($Theme) {
        'food ingredients and biofactories' { return 'despliegue material' }
        'ag biologicals and crop resilience' { return 'despliegue / intervencion' }
        'agri intelligence and traceable markets' { return 'conexion / despliegue' }
        'clinical diagnostics and medical devices' { return 'intervencion clinica sobre sistemas vivos' }
        'therapeutics and regenerative bio' { return 'biocentrico' }
        'biomanufacturing and molecular platforms' { return 'despliegue material' }
        'biobased chemistry and circular materials' { return 'despliegue material / limites planetarios' }
        'computational biology and genomic intelligence' { return 'conexion' }
        'climate and resource intelligence platforms' { return 'despliegue / coordinacion / mrv' }
        'planetary monitoring and resilience systems' { return 'mrv / transparencia / intervencion' }
        'resource recovery and remediation' { return 'restauracion / despliegue material' }
        default { return 'mixed' }
    }
}

if (-not (Test-Path -LiteralPath $MasterPath)) {
    throw "Missing master dataset: $MasterPath"
}

$rows = Import-Csv -LiteralPath $MasterPath
$confirmedInclude = @(
    $rows | Where-Object {
        (Clean-Text $_.scope_decision) -eq 'include' -and
        (Clean-Text $_.scope_status) -eq 'confirmed'
    }
)

$stopwords = Get-Stopwords
$rawDocs = foreach ($row in $confirmedInclude) {
    $text = Get-DocumentText -Row $row
    $tokens = @(Get-Tokens -Text $text -Stopwords $stopwords)
    [pscustomobject]@{
        row = $row
        text = $text
        tokens = $tokens
        token_count = $tokens.Count
    }
}

$docCount = $rawDocs.Count
$docFrequency = @{}
foreach ($doc in $rawDocs) {
    foreach ($token in ($doc.tokens | Select-Object -Unique)) {
        if (-not $docFrequency.ContainsKey($token)) { $docFrequency[$token] = 0 }
        $docFrequency[$token]++
    }
}

$minDf = [math]::Max(2, [math]::Floor($docCount * 0.015))
$maxDf = [math]::Max($minDf + 1, [math]::Ceiling($docCount * 0.65))
$vocabulary = @(
    $docFrequency.GetEnumerator() |
    Where-Object { $_.Value -ge $minDf -and $_.Value -le $maxDf } |
    Sort-Object Name |
    ForEach-Object { $_.Name }
)

$documents = New-Object System.Collections.Generic.List[object]
foreach ($doc in $rawDocs) {
    $termCounts = @{}
    foreach ($token in $doc.tokens) {
        if ($vocabulary -notcontains $token) { continue }
        if (-not $termCounts.ContainsKey($token)) { $termCounts[$token] = 0 }
        $termCounts[$token]++
    }
    $vector = @{}
    $totalTerms = [double][math]::Max(1, ($termCounts.Values | Measure-Object -Sum).Sum)
    foreach ($token in $termCounts.Keys) {
        $tf = [double]$termCounts[$token] / $totalTerms
        $idf = [math]::Log((1.0 + $docCount) / (1.0 + [double]$docFrequency[$token])) + 1.0
        $vector[$token] = $tf * $idf
    }
    $documents.Add([pscustomobject]@{
        row = $doc.row
        text = $doc.text
        tokens = $doc.tokens
        token_count = $doc.token_count
        vector = $vector
    })
}

$candidateResults = New-Object System.Collections.Generic.List[object]
foreach ($k in 7..10) {
    if ($k -ge $documents.Count) { continue }
    $run = Run-KMeansLike -Documents @($documents.ToArray()) -K $k
    $quality = Get-ClusterQuality -Documents @($documents.ToArray()) -Assignments $run.assignments -Centroids $run.centroids
    $candidateResults.Add([pscustomobject]@{
        k = $k
        run = $run
        quality = $quality
    })
}

$bestResult = $candidateResults | Sort-Object -Property @{ Expression = { $_.quality.score }; Descending = $true }, @{ Expression = 'k'; Descending = $false } | Select-Object -First 1
if (-not $bestResult) {
    throw 'Could not produce semantic clustering candidates.'
}

$assignments = New-Object System.Collections.Generic.List[object]
$clusterThemeNames = @{}

foreach ($clusterId in 0..($bestResult.k - 1)) {
    $memberIndices = @($bestResult.quality.clusters[$clusterId].ToArray())
    if ($memberIndices.Count -eq 0) { continue }
    $memberRows = @($memberIndices | ForEach-Object { $documents[$_].row })
    $memberTexts = @($memberIndices | ForEach-Object { $documents[$_].text })
    $topTokens = @(Get-TopTokens -Texts $memberTexts -Limit 8)
    $dominantMacro = Get-Dominant -Rows $memberRows -Property 'macro_theme'
    $themeName = Get-ThemeLabel -DominantMacro $dominantMacro -TopTokens $topTokens
    if ($clusterThemeNames.ContainsKey($clusterId)) {
        $themeName = $clusterThemeNames[$clusterId]
    } else {
        $clusterThemeNames[$clusterId] = $themeName
    }
}

for ($i = 0; $i -lt $documents.Count; $i++) {
    $clusterId = $bestResult.run.assignments[$i]
    $themeName = $clusterThemeNames[$clusterId]
    $ownCentroid = $bestResult.run.centroids[$clusterId]
    $ownSimilarity = Get-CosineSimilarity -A $documents[$i].vector -B $ownCentroid
    $bestOtherSimilarity = 0.0
    foreach ($otherCluster in 0..($bestResult.k - 1)) {
        if ($otherCluster -eq $clusterId) { continue }
        $sim = Get-CosineSimilarity -A $documents[$i].vector -B $bestResult.run.centroids[$otherCluster]
        if ($sim -gt $bestOtherSimilarity) { $bestOtherSimilarity = $sim }
    }
    $margin = $ownSimilarity - $bestOtherSimilarity
    $confidence = if ($margin -ge 0.11) { 'high' } elseif ($margin -ge 0.04) { 'medium' } else { 'low' }

    $assignments.Add([pscustomobject]@{
        startup_id = $documents[$i].row.startup_id
        startup_name = $documents[$i].row.startup_name
        current_macro_theme = $documents[$i].row.macro_theme
        current_emergent_theme = $documents[$i].row.emergent_theme
        semantic_beta_theme = $themeName
        semantic_cluster_id = ('cluster_{0}' -f ($clusterId + 1))
        semantic_beta_score = [math]::Round($ownSimilarity * 100, 1)
        semantic_beta_margin = [math]::Round($margin * 100, 1)
        semantic_beta_confidence = $confidence
        gridx_match = Get-GridxMatch -Theme $themeName
        antom_match = Get-AntomMatch -Theme $themeName
        matched_signals = ((Get-TopTokens -Texts @($documents[$i].text) -Limit 6) -join '; ')
        source_url = $documents[$i].row.source_url
        source_type = $documents[$i].row.source_type
        review_status = $documents[$i].row.review_status
        evidence_excerpt = $documents[$i].row.evidence_excerpt
        startup_summary_v1 = $documents[$i].row.startup_summary_v1
    })
}

$themeSummaries = foreach ($themeName in ($assignments.semantic_beta_theme | Select-Object -Unique | Sort-Object)) {
    $members = @($assignments | Where-Object { $_.semantic_beta_theme -eq $themeName })
    $masterMembers = @($confirmedInclude | Where-Object { $_.startup_id -in $members.startup_id })
    $texts = @($members | ForEach-Object { @($_.startup_summary_v1, $_.evidence_excerpt) -join ' ' })
    $topTokens = Get-TopTokens -Texts $texts -Limit 8
    $majorCurrentMacro = Get-Dominant -Rows $masterMembers -Property 'macro_theme'
    $representatives = @($members | Sort-Object -Property @{ Expression = 'semantic_beta_score'; Descending = $true }, @{ Expression = 'startup_name'; Descending = $false } | Select-Object -First 4 -ExpandProperty startup_name) -join '; '
    $lowConfidenceCount = @($members | Where-Object { $_.semantic_beta_confidence -eq 'low' }).Count
    $confidenceShare = [math]::Round(((($members.Count - $lowConfidenceCount) / [double][math]::Max(1, $members.Count)) * 100), 1)
    $clusterQualityScore = [math]::Round((($confidenceShare * 0.7) + ([math]::Min(30, $members.Count * 1.5))), 1)
    $qualityLabel = if ($confidenceShare -ge 82) { 'strong' } elseif ($confidenceShare -ge 65) { 'promising' } else { 'noisy' }
    [pscustomobject]@{
        semantic_beta_theme = $themeName
        startup_count = $members.Count
        representative_startups = $representatives
        top_tokens = ($topTokens -join '; ')
        theme_description = Get-ThemeDescription -Theme $themeName
        majority_current_macro_theme = $majorCurrentMacro
        gridx_match = Get-GridxMatch -Theme $themeName
        antom_match = Get-AntomMatch -Theme $themeName
        low_confidence_count = $lowConfidenceCount
        cluster_quality_score = $clusterQualityScore
        confidence_share = $confidenceShare
        ambiguous_share = [math]::Round((($lowConfidenceCount / [double][math]::Max(1, $members.Count)) * 100), 1)
        cluster_quality_label = $qualityLabel
    }
}

$assignments | Sort-Object -Property semantic_beta_theme, startup_name | Export-Csv -LiteralPath $OutputAssignmentsPath -NoTypeInformation -Encoding UTF8
$themeSummaries | Sort-Object -Property @{ Expression = 'startup_count'; Descending = $true }, @{ Expression = 'semantic_beta_theme'; Descending = $false } | Export-Csv -LiteralPath $OutputThemesPath -NoTypeInformation -Encoding UTF8

$reportLines = @()
$reportLines += '# Semantic Taxonomy Beta'
$reportLines += ''
$reportLines += 'Generated at: ' + (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
$reportLines += ''
$reportLines += '## Scope'
$reportLines += ''
$reportLines += '- Universe used: include + confirmed only'
$reportLines += ('- Startups clustered: {0}' -f $assignments.Count)
$reportLines += ('- Candidate cluster counts tested: {0}' -f (($candidateResults | ForEach-Object { $_.k }) -join ', '))
$reportLines += ('- Selected cluster count: {0}' -f $bestResult.k)
$reportLines += ('- Best cluster quality score: {0}' -f $bestResult.quality.score)
$reportLines += ''
$reportLines += '## Method'
$reportLines += ''
$reportLines += '- Pure text clustering over audited startup text fields'
$reportLines += '- Vocabulary built from TF-IDF over include + confirmed startups'
$reportLines += '- Candidate cluster counts evaluated in a short range to avoid category explosion'
$reportLines += '- Themes named after clustering using dominant macro-context and top semantic tokens'
$reportLines += ''
$reportLines += '## Candidate K Scores'
$reportLines += ''
foreach ($candidate in ($candidateResults | Sort-Object k)) {
    $reportLines += ('- k={0}: score={1}, avg_margin={2}, avg_within={3}, small_clusters={4}' -f $candidate.k, $candidate.quality.score, $candidate.quality.avg_margin, $candidate.quality.avg_within, $candidate.quality.small_clusters)
}
$reportLines += ''
$reportLines += '## Theme Snapshot'
$reportLines += ''
foreach ($theme in ($themeSummaries | Sort-Object -Property @{ Expression = 'startup_count'; Descending = $true }, @{ Expression = 'semantic_beta_theme'; Descending = $false })) {
    $reportLines += ('### {0} ({1})' -f $theme.semantic_beta_theme, $theme.startup_count)
    $reportLines += ''
    $reportLines += ('- Description: {0}' -f $theme.theme_description)
    $reportLines += ('- Top tokens: {0}' -f $theme.top_tokens)
    $reportLines += ('- Representative startups: {0}' -f $theme.representative_startups)
    $reportLines += ('- Majority current macro theme: {0}' -f $theme.majority_current_macro_theme)
    $reportLines += ('- Match GRIDX: {0}' -f $theme.gridx_match)
    $reportLines += ('- Lens Antom: {0}' -f $theme.antom_match)
    $reportLines += ('- Low confidence assignments: {0}' -f $theme.low_confidence_count)
    $reportLines += ('- Cluster quality: {0} ({1}/100)' -f $theme.cluster_quality_label, $theme.cluster_quality_score)
    $reportLines += ''
}
$reportLines += '## Notes'
$reportLines += ''
$reportLines += '- This version no longer assigns startups to hand-built semantic families before clustering.'
$reportLines += '- Purity now comes from clustering first and naming later.'
$reportLines += '- Next step should be to improve visual geometry so inter-cluster distances also reflect these proximities.'

Set-Content -LiteralPath $OutputReportPath -Value ($reportLines -join [Environment]::NewLine) -Encoding UTF8

Write-Output "Semantic taxonomy beta built:"
Write-Output "  Assignments: $OutputAssignmentsPath"
Write-Output "  Themes: $OutputThemesPath"
Write-Output "  Report: $OutputReportPath"
