param(
    [string]$MasterPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_master_dataset.csv",
    [string]$OutputSummaryCsvPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_single_level_candidates.csv",
    [string]$OutputClustersCsvPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_single_level_clusters.csv",
    [string]$OutputAssignmentsCsvPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_single_level_assignments.csv",
    [string]$OutputReportPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\semantic_single_level_report.md",
    [string]$OutputDataJsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\semantic-single-level-data.js",
    [string]$ManualSemanticOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\manual_semantic_theme_overrides.csv"
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

function Get-FieldValue {
    param(
        [object]$Object,
        [string]$Name
    )
    if ($null -eq $Object) { return '' }
    if ($Object.PSObject.Properties.Name -contains $Name) {
        return $Object.$Name
    }
    return ''
}

function Load-ManualSemanticOverrides {
    param([string]$Path)
    $map = @{}
    if (-not (Test-Path -LiteralPath $Path)) { return $map }
    foreach ($row in (Import-Csv -LiteralPath $Path)) {
        $id = Clean-Text (Get-FieldValue -Object $row -Name 'startup_id')
        $theme = Clean-Text (Get-FieldValue -Object $row -Name 'semantic_single_theme')
        if (-not $id -or -not $theme) { continue }
        $map[$id] = [pscustomobject]@{
            startup_id = $id
            semantic_single_theme = $theme
            override_reason = Clean-Text (Get-FieldValue -Object $row -Name 'override_reason')
            source_url = Clean-Text (Get-FieldValue -Object $row -Name 'source_url')
            review_status = Clean-Text (Get-FieldValue -Object $row -Name 'review_status')
        }
    }
    return $map
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
    $value = (-join $chars)
    $replacements = [ordered]@{
        'single cell' = 'singlecell'
        'long read' = 'longread'
        'precision fermentation' = 'precisionfermentation'
        'digital twin' = 'digitaltwin'
        'drug delivery' = 'drugdelivery'
        'medical devices' = 'medicaldevices'
        'clinical devices' = 'clinicaldevices'
        'dispositivos medicos' = 'medicaldevices'
        'dispositivos clinicos' = 'clinicaldevices'
        'medicina regenerativa' = 'regenerativemedicine'
        'medical' = 'medical'
        'medico' = 'medical'
        'medica' = 'medical'
        'clinical' = 'clinical'
        'clinico' = 'clinical'
        'clinica' = 'clinical'
        'diagnostics' = 'diagnostics'
        'diagnostic' = 'diagnostics'
        'diagnostico' = 'diagnostics'
        'deteccion' = 'detection'
        'therapeutics' = 'therapeutics'
        'therapeutic' = 'therapeutics'
        'terapia' = 'therapeutics'
        'terapias' = 'therapeutics'
        'terapeutica' = 'therapeutics'
        'regenerative' = 'regenerative'
        'regenerativa' = 'regenerative'
        'regenerativo' = 'regenerative'
        'ingredients' = 'ingredients'
        'ingredient' = 'ingredients'
        'ingredientes' = 'ingredients'
        'ingrediente' = 'ingredients'
        'proteins' = 'proteins'
        'protein' = 'proteins'
        'proteinas' = 'proteins'
        'proteina' = 'proteins'
        'fermentation' = 'fermentation'
        'fermentacion' = 'fermentation'
        'enzyme' = 'enzymes'
        'enzymes' = 'enzymes'
        'enzima' = 'enzymes'
        'enzimas' = 'enzymes'
        'genomics' = 'genomics'
        'genomic' = 'genomics'
        'genomica' = 'genomics'
        'sequencing' = 'sequencing'
        'sequence' = 'sequencing'
        'secuenciacion' = 'sequencing'
        'satellites' = 'satellite'
        'satellite' = 'satellite'
        'satelites' = 'satellite'
        'satelite' = 'satellite'
        'monitoring' = 'monitoring'
        'monitor' = 'monitoring'
        'monitoreo' = 'monitoring'
        'wildfire' = 'wildfire'
        'wildfires' = 'wildfire'
        'incendios' = 'wildfire'
        'carbon removal' = 'carbonremoval'
        'remocion carbono' = 'carbonremoval'
        'carbon' = 'carbon'
        'carbono' = 'carbon'
        'waste' = 'waste'
        'residuos' = 'waste'
        'residuo' = 'waste'
        'recycling' = 'recycling'
        'recycle' = 'recycling'
        'reciclaje' = 'recycling'
        'circular' = 'circular'
        'platform' = 'platform'
        'platforms' = 'platform'
        'plataforma' = 'platform'
        'plataformas' = 'platform'
        'software' = 'software'
        'traceability' = 'traceability'
        'trazabilidad' = 'traceability'
        'marketplace' = 'marketplace'
        'markets' = 'markets'
        'market' = 'market'
        'mercado' = 'market'
        'mercados' = 'markets'
        'agriculture' = 'agriculture'
        'agricultura' = 'agriculture'
        'agricultural' = 'agricultural'
        'agricola' = 'agricultural'
        'crop' = 'crop'
        'crops' = 'crop'
        'cultivo' = 'crop'
        'cultivos' = 'crop'
        'soil' = 'soil'
        'suelo' = 'soil'
        'pollination' = 'pollination'
        'polinizacion' = 'pollination'
        'pollinator' = 'pollinators'
        'polinizadores' = 'pollinators'
        'biomaterials' = 'biomaterials'
        'biomateriales' = 'biomaterials'
        'biomaterial' = 'biomaterials'
        'materials' = 'materials'
        'materiales' = 'materials'
        'material' = 'materials'
        'cells' = 'cells'
        'cell' = 'cells'
        'celulas' = 'cells'
        'celula' = 'cells'
        'tissue' = 'tissue'
        'tissues' = 'tissue'
        'tejido' = 'tissue'
        'tejidos' = 'tissue'
        'productores' = 'growers'
        'granos' = 'grains'
        'semillas' = 'seeds'
        'quimica' = 'chemistry'
        'quimicos' = 'chemicals'
        'acuicultura' = 'aquaculture'
        'reemplazar' = 'replace'
        'huella' = 'footprint'
        'remediacion' = 'remediation'
        'litio' = 'lithium'
        'tierras' = 'land'
        'oceano' = 'ocean'
        'energia' = 'energy'
        'bateria' = 'battery'
        'emisiones' = 'emissions'
        'riego' = 'irrigation'
        'plastico' = 'plastic'
        'polimero' = 'polymer'
        'recuperacion' = 'recovery'
        'restaurar' = 'restoration'
        'ambiental' = 'environmental'
        'datos' = 'data'
        'productos' = 'products'
        'producto' = 'products'
        'infraestructura' = 'infrastructure'
        'agricolas' = 'agricultural'
        'agricolo' = 'agricultural'
        'nanotecnologia' = 'nanotechnology'
        'nanomedicina' = 'nanomedicine'
        'compuestos' = 'compounds'
        'compuesto' = 'compounds'
        'vegetales' = 'plant'
        'vegetal' = 'plant'
        'pequenos' = 'small'
        'pequeno' = 'small'
        'gestion' = 'management'
        'mantiene' = 'maintains'
        'recursos' = 'resources'
        'recurso' = 'resources'
        'usando' = 'using'
        'origen' = 'origin'
        'microorganismos' = 'microorganisms'
        'microorganismo' = 'microorganisms'
        'tisular' = 'tissue'
        'llevar' = 'delivery'
        'campo' = 'field'
        'antibioticos' = 'antibiotics'
        'resiliencia' = 'resilience'
        'biologicos' = 'biologicals'
        'biologico' = 'biologicals'
        'rendimiento' = 'yield'
        'producers' = 'growers'
        'bioinsumos' = 'bioinputs'
        'planetario' = 'planetary'
        'planetarios' = 'planetary'
        'toxicos' = 'toxic'
        'toxico' = 'toxic'
        'sustitucion' = 'substitution'
        'raras' = 'rare'
        'rara' = 'rare'
        'virales' = 'viral'
        'viral' = 'viral'
        'vectores' = 'vectors'
        'vector' = 'vectors'
        'activos' = 'active'
        'activo' = 'active'
        'transforma' = 'transforms'
        'transformar' = 'transform'
        'tratamiento' = 'treatment'
        'tratamientos' = 'treatment'
        'seguimiento' = 'monitoring'
        'manufactura' = 'manufacturing'
        'optimizar' = 'optimization'
        'enfermedades' = 'disease'
        'cosmetica' = 'cosmetics'
    }
    foreach ($key in $replacements.Keys) {
        $pattern = '\b' + [regex]::Escape($key) + '\b'
        $value = [regex]::Replace($value, $pattern, [string]$replacements[$key])
    }
    return $value
}

function Strip-EditorialText {
    param([string]$Text)
    $value = Clean-Text $Text
    if (-not $value) { return '' }
    $patterns = @(
        '(?i)\s+entra en tesis.*$',
        '(?i)\s+belongs inside.*$',
        '(?i)\s+belongs in.*$',
        '(?i)\s+queda fuera.*$',
        '(?i)\s+sale de tesis.*$',
        '(?i)^official site describes\s+',
        '(?i)^official site presents\s+',
        '(?i)^official site states\s+',
        '(?i)^linkedin company profile states that\s+',
        '(?i)^linkedin company profile describes\s+',
        '(?i)^f6s profile describes\s+',
        '(?i)^gridx describes\s+',
        '(?i)^argentina\.gob\.ar describes\s+',
        '(?i)^the yield lab latam portfolio describes\s+'
    )
    foreach ($pattern in $patterns) {
        $value = [regex]::Replace($value, $pattern, '')
    }
    $value = [regex]::Replace($value, '(?i)\bstrip\s*editorialtext\b', '')
    $value = [regex]::Replace($value, '(?i)\beditorialtext\b', '')
    $value = [regex]::Replace($value, '(?i)\bstrip\b', '')
    return $value.Trim()
}

function Get-DocumentText {
    param($Row)
    return @(
        Strip-EditorialText $Row.startup_summary_v1,
        Strip-EditorialText $Row.business_one_liner
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
        'and','the','del','las','los','una','uno','ser','estar','como','mas','its','our','your','into',
        'industry','industrial','market','markets','mercado','mercados','production','produccion','products','product',
        'health','salud','food','alimentos','agriculture','agricultura','agricultural','biotech','bio','life','scientific','software',
        'research','clinical','clinico','clinica','biology','biologia','medical','medico','medica','materials','materiales',
        'official','site','describes','entra','tesis','source','sources','based','sourcebacked','reviewed','seeded',
        'portfolio','website','gridx','develops','developing','user','users',
        'latam','latin','america','american','regional','region','inside','belongs','core','confirmed','include',
        'brazil','brasil','brazilian','brasilena','brasileno','argentina','argentine','mexico','mexican',
        'chile','chilean','chilena','chileno','colombia','colombian','uruguay','uruguayan','peru','peruvian',
        'strip','editorialtext','mediante','partir','combina','foco','menor','alto','bajo','using','used',
        'produce','producir','produces','natural','naturales','funcionales','modular','sustentables','sustainable',
        'throughput','applied','aplica','aplicada','aplicado',
        'adentro','dejamos','caso','borde','claramente','directo','directa','enfocada','enfocado',
        'startup','compania','company','empresa','solucion','soluciones','plataforma','plataformas',
        'desarrolla','desarrollan','desarrollado','desarrollo','desarrollar','permite','permiten',
        'mejorar','mejora','reduce','reducir','hace','hacer','sistema','sistemas','basada','basado',
        'aplicada','aplicado','aplicables','directamente','fuerte','acople','material','materiales',
        'cadena','cadenas','real','reales','core','thesis','founded','about','team',
        'infrastructure','management','maintains','using','origin','small','field','resources','resource',
        'productos','producto','infraestructura','nanotecnologia','compuestos','vegetales','pequenos','gestion',
        'mantiene','recursos','usando','origen','campo','leading','delivery','high','low','menos','active','transforms','transform',
        'clean','text','trata','transporte','transferencia','volver','vida','util','care','free','label'
    )
}

function Get-WeightedTokenBag {
    param(
        [string]$Text,
        [string[]]$Stopwords,
        [double]$Weight = 1.0,
        [string]$Prefix = ''
    )
    $items = New-Object System.Collections.Generic.List[object]
    foreach ($token in (Get-Tokens -Text $Text -Stopwords $Stopwords)) {
        $key = if ($Prefix) { "${Prefix}:${token}" } else { $token }
        $items.Add([pscustomobject]@{
            token = $key
            display_token = $token
            weight = $Weight
        }) | Out-Null
    }
    return @($items.ToArray())
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
        if ($candidateIndex -ge 0) { $seeds.Add($candidateIndex) } else { break }
    }

    return @($seeds.ToArray())
}

function Run-KMeansLike {
    param(
        [object[]]$Documents,
        [int]$K,
        [int]$MaxIterations = 8
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
            $newCentroids += ,(Get-Centroid -Documents $Documents -Indices @($clusters[$c].ToArray()))
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
        [string[]]$TopTokens,
        [string[]]$RepresentativeNames = @()
    )
    $tokenSet = @{}
    foreach ($token in $TopTokens) { $tokenSet[$token] = $true }
    $repText = ($RepresentativeNames -join ' ').ToLowerInvariant()

    switch ($DominantMacro) {
        'food biotech and novel ingredients' {
            if ($repText -match 'apexzymes|keclon|enzyva|breakpet') { return 'industrial enzymes and bioprocess platforms' }
            return 'food ingredients and biofactories'
        }
        'diagnostics and medtech' { return 'clinical diagnostics and medical devices' }
        'therapeutics and regenerative medicine' {
            if ($tokenSet.ContainsKey('agtech') -or $tokenSet.ContainsKey('crop') -or $tokenSet.ContainsKey('products') -or $tokenSet.ContainsKey('cosmetics') -or $tokenSet.ContainsKey('ingredients')) {
                return 'bioactive products and regenerative edge cases'
            }
            return 'therapeutics and regenerative bio'
        }
        'biomanufacturing and bioindustrial platforms' { return 'biomanufacturing and molecular platforms' }
        'computational biology and scientific software' { return 'computational biology and genomic intelligence' }
        'ag biologicals and crop resilience' {
            if ($tokenSet.ContainsKey('cells') -and ($tokenSet.ContainsKey('therapeutics') -or $tokenSet.ContainsKey('regenerative'))) {
                return 'cell-based regenerative and crop bio platforms'
            }
            if ($tokenSet.ContainsKey('traceability') -or $tokenSet.ContainsKey('marketplace') -or $tokenSet.ContainsKey('agronomic') -or $tokenSet.ContainsKey('precision') -or $tokenSet.ContainsKey('growers') -or $tokenSet.ContainsKey('grains')) {
                return 'agri intelligence and traceable markets'
            }
            return 'ag biologicals and crop resilience'
        }
        'precision agriculture and resource intelligence' { return 'agri intelligence and traceable markets' }
        'biobased chemistry and advanced materials' {
            if ($tokenSet.ContainsKey('biomaterials') -or $tokenSet.ContainsKey('biobased') -or $tokenSet.ContainsKey('chemistry') -or $tokenSet.ContainsKey('aquaculture') -or $tokenSet.ContainsKey('replace')) {
                return 'biobased chemistry and circular materials'
            }
            if ($tokenSet.ContainsKey('waste') -or $tokenSet.ContainsKey('carbon') -or $tokenSet.ContainsKey('footprint') -or $tokenSet.ContainsKey('remediation') -or $tokenSet.ContainsKey('lithium')) {
                return 'resource recovery and remediation'
            }
            return 'biobased chemistry and circular materials'
        }
        'climate, energy and resource systems' {
            if ($tokenSet.ContainsKey('traceability') -or $tokenSet.ContainsKey('growers') -or $tokenSet.ContainsKey('grains') -or $tokenSet.ContainsKey('agricultural') -or $tokenSet.ContainsKey('precision')) {
                return 'agri intelligence and traceable markets'
            }
            if ($tokenSet.ContainsKey('waste') -or $tokenSet.ContainsKey('carbon') -or $tokenSet.ContainsKey('footprint') -or $tokenSet.ContainsKey('remediation') -or $tokenSet.ContainsKey('land')) {
                return 'resource recovery and remediation'
            }
            if ($tokenSet.ContainsKey('satellite') -or $tokenSet.ContainsKey('wildfire') -or $tokenSet.ContainsKey('monitoring') -or $tokenSet.ContainsKey('ocean')) {
                return 'planetary monitoring and resilience systems'
            }
            return 'climate and resource intelligence platforms'
        }
        'frontier hardware and infrastructure systems' { return 'planetary monitoring and resilience systems' }
        default {
            if ($repText -match 'apexzymes|keclon|enzyva|breakpet') { return 'industrial enzymes and bioprocess platforms' }
            if ($tokenSet.ContainsKey('genomics') -or $tokenSet.ContainsKey('sequencing') -or $tokenSet.ContainsKey('bioinformatics')) { return 'computational biology and genomic intelligence' }
            if ($tokenSet.ContainsKey('ingredient') -or $tokenSet.ContainsKey('proteins') -or $tokenSet.ContainsKey('food')) { return 'food ingredients and biofactories' }
            if ($tokenSet.ContainsKey('therapeutics') -or $tokenSet.ContainsKey('cancer') -or $tokenSet.ContainsKey('regenerative')) {
                if ($tokenSet.ContainsKey('agtech') -or $tokenSet.ContainsKey('crop') -or $tokenSet.ContainsKey('products') -or $tokenSet.ContainsKey('cosmetics') -or $tokenSet.ContainsKey('ingredients')) {
                    return 'bioactive products and regenerative edge cases'
                }
                return 'therapeutics and regenerative bio'
            }
            if ($tokenSet.ContainsKey('diagnostics') -or $tokenSet.ContainsKey('device') -or $tokenSet.ContainsKey('biopsy')) { return 'clinical diagnostics and medical devices' }
            if ($tokenSet.ContainsKey('crop') -or $tokenSet.ContainsKey('soil') -or $tokenSet.ContainsKey('microbial')) { return 'ag biologicals and crop resilience' }
            if ($tokenSet.ContainsKey('traceability') -or $tokenSet.ContainsKey('agronomic') -or $tokenSet.ContainsKey('irrigation') -or $tokenSet.ContainsKey('growers') -or $tokenSet.ContainsKey('grains')) { return 'agri intelligence and traceable markets' }
            if ($tokenSet.ContainsKey('plastic') -or $tokenSet.ContainsKey('polymer') -or $tokenSet.ContainsKey('biomaterials')) { return 'biobased chemistry and circular materials' }
            if ($tokenSet.ContainsKey('energy') -or $tokenSet.ContainsKey('battery') -or $tokenSet.ContainsKey('emissions')) { return 'climate and resource intelligence platforms' }
            if ($tokenSet.ContainsKey('satellite') -or $tokenSet.ContainsKey('ocean') -or $tokenSet.ContainsKey('wildfire') -or $tokenSet.ContainsKey('monitoring')) { return 'planetary monitoring and resilience systems' }
            if ($tokenSet.ContainsKey('recovery') -or $tokenSet.ContainsKey('waste') -or $tokenSet.ContainsKey('remediation') -or $tokenSet.ContainsKey('footprint') -or $tokenSet.ContainsKey('carbon')) { return 'resource recovery and remediation' }
            return 'semantic edge cases'
        }
    }
}

function Ensure-UniqueLabel {
    param(
        [string]$BaseLabel,
        [hashtable]$UsedLabels,
        [string[]]$TopTokens,
        [string]$DominantMacro
    )
    $label = Clean-Text $BaseLabel
    if (-not $label) { $label = 'semantic edge cases' }
    if (-not $UsedLabels.ContainsKey($label)) {
        $UsedLabels[$label] = 1
        return $label
    }

    $tokenText = ($TopTokens -join ' ')
    $curated = ''
    if ($DominantMacro -eq 'ag biologicals and crop resilience' -and $tokenText -match 'crop|agricultural|control|agrobiotech|resilience') {
        $curated = 'crop biologicals and grower resilience'
    } elseif ($tokenText -match 'traceability|seeds|grains|growers') {
        $curated = 'grain traceability and producer infrastructure'
    } elseif ($tokenText -match 'diagnostics|molecular|genomics|detection') {
        $curated = 'molecular diagnostics and genomics'
    } elseif ($tokenText -match 'therapeutics|disease|drug|discovery|cancer') {
        $curated = 'drug discovery and disease therapeutics'
    } elseif ($tokenText -match 'animal|dairy') {
        $curated = 'animal protein and fermentation systems'
    } elseif ($tokenText -match 'cells|proteins|fermentation|enzymes|biotechnology') {
        $curated = 'cell protein and biofactory platforms'
    } elseif ($tokenText -match 'biomaterials|waste|biobased|chemicals') {
        $curated = 'biobased materials and waste valorization'
    } elseif ($tokenText -match 'carbon|native|nature|monitoring|scale') {
        $curated = 'nature restoration and carbon intelligence'
    } elseif ($tokenText -match 'medtech|devices|treatment|monitoring') {
        $curated = 'clinical devices and patient monitoring'
    } elseif ($tokenText -match 'monitoring|data|environmental|satellite|restoration') {
        $curated = 'environmental monitoring and restoration intelligence'
    } elseif ($tokenText -match 'regenerative|ingredients|products') {
        $curated = 'regenerative bioactive ingredients'
    } elseif ($tokenText -match 'therapeutics|optimization|restoration|manufacturing') {
        $curated = 'therapeutic bioprocess and regenerative platforms'
    } elseif ($tokenText -match 'data|agribusiness|management') {
        $curated = 'agribusiness data and management platforms'
    } elseif ($tokenText -match 'biomaterials|traceability|waste') {
        $curated = 'circular biomaterials and traceable waste streams'
    } elseif ($tokenText -match 'diagnostics|cells') {
        $curated = 'cellular diagnostics and analysis platforms'
    }
    if ($curated) {
        $curatedCandidate = $curated
        $curatedCounter = 2
        while ($UsedLabels.ContainsKey($curatedCandidate)) {
            $curatedCandidate = "$curated variant $curatedCounter"
            $curatedCounter++
        }
        $UsedLabels[$curatedCandidate] = 1
        return $curatedCandidate
    }

    $qualifiers = @(
        $TopTokens |
            Where-Object {
                $_ -and
                $_ -notmatch '^(agtech|precision|intelligence|infrastructure|biological|direct|focused)$'
            } |
            Select-Object -First 3
    )
    $suffix = if ($qualifiers.Count) { ($qualifiers -join ' and ') } elseif ($DominantMacro) { $DominantMacro } else { 'semantic variant' }
    $candidate = "$suffix systems"
    $counter = 2
    while ($UsedLabels.ContainsKey($candidate)) {
        $candidate = "$label - $suffix $counter"
        $counter++
    }
    $UsedLabels[$candidate] = 1
    return $candidate
}

function Get-ThemeDescription {
    param([string]$Theme)
    if ($Theme -match '^clinical diagnostics and bioinstrumentation') { return 'Diagnostics, detection, bioinstrumentation and clinical devices for health or biological analysis.' }
    if ($Theme -match '^regenerative bio and bioactive platforms') { return 'Regenerative biology, tissue engineering and bioactive products across health, food, cosmetics or biomaterials.' }
    if ($Theme -match '^agri intelligence and crop systems') { return 'Agronomic intelligence, crop decisioning, biological application and data systems for agriculture.' }
    if ($Theme -match '^traceable agri-food and circular supply chains') { return 'Traceability, producer infrastructure and circular supply-chain coordination for agri-food and material flows.' }
    if ($Theme -match '^bio-process and resource optimization') { return 'Optimization platforms for bioprocesses, pollination, energy, cold chains, logistics or resource-intensive operating systems.' }
    if ($Theme -match '^biobased chemistry and molecular materials') { return 'Biobased chemistry, biomaterials, molecular manufacturing and circular material substitution.' }
    if ($Theme -match '^food ingredients and fermentation platforms') { return 'Food ingredients, fermentation, proteins, functional formulations and biofactory-enabled food systems.' }
    if ($Theme -match '^crop biologicals and grower resilience') { return 'Biological inputs, biocontrol and crop-resilience technologies applied directly to growers and agricultural systems.' }
    if ($Theme -match '^grain traceability and producer infrastructure') { return 'Digital infrastructure for traceability, seeds, grains, growers and commercial coordination across agri-food chains.' }
    if ($Theme -match '^molecular diagnostics and genomics') { return 'Molecular diagnostics, genomics, detection and analytical platforms based on biological data.' }
    if ($Theme -match '^drug discovery and disease therapeutics') { return 'Therapeutic discovery, complex-disease platforms, cancer biology and biological delivery.' }
    if ($Theme -match '^animal protein and fermentation systems') { return 'Animal protein, fermentation, alternative dairy and bioprocesses connected to food or animal health.' }
    if ($Theme -match '^cell protein and biofactory platforms') { return 'Cell, protein, enzyme and biofactory platforms that support biological production across food, therapeutics or industrial biotech.' }
    if ($Theme -match '^biobased materials and waste valorization') { return 'Biomaterials, biobased chemistry and waste valorization into circular materials or inputs.' }
    if ($Theme -match '^nature restoration and carbon intelligence') { return 'Ecosystem restoration, carbon intelligence, nature monitoring and planetary resilience systems.' }
    if ($Theme -match '^clinical devices and patient monitoring') { return 'Medical devices, clinical monitoring and technologies for patient tracking or support.' }
    if ($Theme -match '^environmental monitoring and restoration intelligence') { return 'Environmental monitoring, satellite or sensor data, and tools for restoration or ecosystem resilience.' }
    if ($Theme -match '^regenerative bioactive ingredients') { return 'Bioactive ingredients and regenerative applications connecting food, health, cosmetics or biomaterials.' }
    if ($Theme -match '^cell-based regenerative and crop bio platforms') { return 'Cell-based, plant-linked and regenerative biology platforms that mix therapeutics, bioactive products or crop-facing biology.' }
    if ($Theme -match '^therapeutic bioprocess and regenerative platforms') { return 'Therapeutic platforms, biological manufacturing and regenerative technologies close to health or tissue repair.' }
    if ($Theme -match '^agribusiness data and management platforms') { return 'Data, management and decision platforms for agribusiness, growers and agri-food chains.' }
    if ($Theme -match '^circular biomaterials and traceable waste streams') { return 'Biomaterials, traceable waste and circular flows connecting materials, food or natural resources.' }
    if ($Theme -match '^cellular diagnostics and analysis platforms') { return 'Cellular diagnostics, biological analysis and platforms for detecting or characterizing health processes.' }
    switch ($Theme) {
        'food ingredients and biofactories' { return 'Food ingredients, fermentation and biofactory systems.' }
        'ag biologicals and crop resilience' { return 'Biological inputs and productive resilience for agricultural systems.' }
        'agri intelligence and traceable markets' { return 'Agronomic decisioning, traceability and material coordination of agri-food chains.' }
        'clinical diagnostics and medical devices' { return 'Diagnostics, detection and clinical devices.' }
        'therapeutics and regenerative bio' { return 'Therapeutics, biological delivery and regenerative medicine.' }
        'bioactive products and regenerative edge cases' { return 'Bioactive or regenerative cases mixing health, cosmetics, food or agriculture that are not pure therapeutics.' }
        'industrial enzymes and bioprocess platforms' { return 'Enzymes, bioindustrial tools and process platforms for biological manufacturing.' }
        'biomanufacturing and molecular platforms' { return 'Biological production and enabling molecular tools.' }
        'biobased chemistry and circular materials' { return 'Biomaterials and circular chemistry based on biological inputs.' }
        'computational biology and genomic intelligence' { return 'Scientific software coupled to life sciences, genomics and biological discovery.' }
        'climate and resource intelligence platforms' { return 'Software coupled to physical systems for energy, resources and decarbonization.' }
        'planetary monitoring and resilience systems' { return 'Monitoring, observation and resilience of planetary systems.' }
        'resource recovery and remediation' { return 'Material recovery, loop closure and remediation.' }
        default { return 'Single-level semantic cluster over include + confirmed startups.' }
    }
}

function Get-ClusterNamingPolicy {
    param(
        [string]$ProfileId,
        [int]$K,
        [int]$ClusterNumber,
        [string]$FallbackLabel
    )
    if ($ProfileId -eq 'technology_heavy' -and $K -eq 7) {
        switch ($ClusterNumber) {
            1 { return [pscustomobject]@{ label = 'clinical diagnostics and bioinstrumentation'; status = 'curated'; anchor_regex = 'diagnostics|medtech|medicaldevices|clinicaldevices|biopsy|detection|imaging|corneal|respiratory|tumor|coagulation|genomics|molecular|cancer' } }
            2 { return [pscustomobject]@{ label = 'regenerative bio and bioactive platforms'; status = 'curated'; anchor_regex = 'regenerative|tissue|cells|bioactive|stem|wound|biomaterials|scaffolds|culture|healthspan|ingredients|cosmetics|microencapsulation' } }
            3 { return [pscustomobject]@{ label = 'agri intelligence and crop systems'; status = 'curated'; anchor_regex = 'agtech|agronomic|crop|growers|farm|field|geospatial|drone|irrigation|seeds|plant|biologicals|pollination|livestock|soil' } }
            4 { return [pscustomobject]@{ label = 'traceable agri-food and circular supply chains'; status = 'curated'; anchor_regex = 'traceability|marketplace|supply|chain|producer|growers|grains|tokenization|recycling|logistics|passport|verification|sustainability|vertical|farming' } }
            5 { return [pscustomobject]@{ label = 'bio-process and resource optimization'; status = 'curated'; anchor_regex = 'optimization|bioprocess|microalgae|pollination|microbiome|energy|forecasting|cold|refrigeration|logistics|freight|yield|grid|plant|fungi|glycobiology' } }
            6 { return [pscustomobject]@{ label = 'biobased chemistry and molecular materials'; status = 'curated'; anchor_regex = 'chemistry|biomaterials|biosynthesis|molecule|microbiology|biomineralization|pigments|textile|biopolymer|proteins|insects|formulations|polymer' } }
            7 { return [pscustomobject]@{ label = 'food ingredients and fermentation platforms'; status = 'curated'; anchor_regex = 'ingredients|proteins|fermentation|precisionfermentation|enzymes|plant|dairy|bacteria|yeast|foodtech|formulation|nutraceutical|encapsulation|biopolymer|compostable' } }
        }
    }
    return [pscustomobject]@{ label = $FallbackLabel; status = 'auto'; anchor_regex = '' }
}

function Get-ClusterFit {
    param(
        [object]$Document,
        [string[]]$TopTokens,
        [double]$Margin,
        [string]$AnchorRegex
    )
    $docTokenSet = @{}
    foreach ($token in $Document.tokens) {
        if ($token) { $docTokenSet[$token] = $true }
    }
    $overlapTokens = @(
        $TopTokens |
            Where-Object { $_ -and $docTokenSet.ContainsKey($_) } |
            Select-Object -Unique
    )
    $searchText = @(
        $Document.text,
        $Document.technology_features,
        $Document.industry_features,
        (Clean-Text (Get-FieldValue -Object $Document.row -Name 'market_label')),
        (Clean-Text (Get-FieldValue -Object $Document.row -Name 'technical_stack')),
        (Clean-Text (Get-FieldValue -Object $Document.row -Name 'transition_function')),
        (Clean-Text (Get-FieldValue -Object $Document.row -Name 'notes'))
    ) -join ' '
    $anchorMatch = $true
    if ($AnchorRegex) {
        $anchorMatch = (Normalize-Text $searchText) -match $AnchorRegex
    }
    $flags = New-Object System.Collections.Generic.List[string]
    if ($Margin -lt 0.04) { $flags.Add('low_margin') | Out-Null }
    if ($overlapTokens.Count -lt 1) { $flags.Add('weak_token_overlap') | Out-Null }
    if (-not $anchorMatch) { $flags.Add('weak_policy_fit') | Out-Null }
    $fit = if ($flags.Count -eq 0) { 'good' } elseif ($Margin -ge 0.04 -and $anchorMatch) { 'watch' } else { 'review' }
    return [pscustomobject]@{
        fit = $fit
        flags = @($flags.ToArray())
        overlap_count = $overlapTokens.Count
        overlap_tokens = ($overlapTokens -join '; ')
        policy_fit = $anchorMatch
    }
}

function Get-CanonicalThemeForMacro {
    param([string]$MacroTheme)
    switch (Clean-Text $MacroTheme) {
        'ag biologicals and crop resilience' { return 'ag biologicals and crop resilience' }
        'food biotech and novel ingredients' { return 'food ingredients and biofactories' }
        'precision agriculture and resource intelligence' { return 'agri intelligence and traceable markets' }
        'diagnostics and medtech' { return 'clinical diagnostics and medical devices' }
        'therapeutics and regenerative medicine' { return 'therapeutics and regenerative bio' }
        'biomanufacturing and bioindustrial platforms' { return 'industrial enzymes and bioprocess platforms' }
        'climate, energy and resource systems' { return 'climate and resource intelligence platforms' }
        'frontier hardware and infrastructure systems' { return 'climate and resource intelligence platforms' }
        'biobased chemistry and advanced materials' { return 'climate and resource intelligence platforms' }
        'computational biology and scientific software' { return 'clinical diagnostics and medical devices' }
        default { return 'climate and resource intelligence platforms' }
    }
}

function Run-SeededSemanticClusters {
    param(
        [object[]]$Documents,
        [string[]]$Themes,
        [int]$MaxIterations = 12
    )
    $centroids = @{}
    foreach ($theme in $Themes) {
        $themeDocs = @($Documents | Where-Object { (Get-CanonicalThemeForMacro $_.row.macro_theme) -eq $theme })
        if ($themeDocs.Count -eq 0) {
            $themeDocs = @($Documents | Sort-Object -Property token_count -Descending | Select-Object -First 3)
        }
        $indices = @()
        for ($i = 0; $i -lt $Documents.Count; $i++) {
            if ($themeDocs -contains $Documents[$i]) { $indices += $i }
        }
        $centroids[$theme] = Get-Centroid -Documents $Documents -Indices $indices
    }

    $assignments = @{}
    for ($iteration = 0; $iteration -lt $MaxIterations; $iteration++) {
        $changed = $false
        $themeMembers = @{}
        foreach ($theme in $Themes) {
            $themeMembers[$theme] = New-Object System.Collections.Generic.List[int]
        }

        for ($i = 0; $i -lt $Documents.Count; $i++) {
            $bestTheme = $Themes[0]
            $bestSimilarity = -1.0
            foreach ($theme in $Themes) {
                $similarity = Get-CosineSimilarity -A $Documents[$i].vector -B $centroids[$theme]
                if ($similarity -gt $bestSimilarity) {
                    $bestSimilarity = $similarity
                    $bestTheme = $theme
                }
            }
            if (-not $assignments.ContainsKey($i) -or $assignments[$i] -ne $bestTheme) {
                $assignments[$i] = $bestTheme
                $changed = $true
            }
            $themeMembers[$bestTheme].Add($i)
        }

        foreach ($theme in $Themes) {
            $indices = @($themeMembers[$theme].ToArray())
            if ($indices.Count -eq 0) { continue }
            $centroids[$theme] = Get-Centroid -Documents $Documents -Indices $indices
        }
        if (-not $changed -and $iteration -gt 0) { break }
    }

    return [pscustomobject]@{
        themes = $Themes
        assignments = $assignments
        centroids = $centroids
    }
}

function Get-SizeCv {
    param([int[]]$Counts)
    if ($Counts.Count -eq 0) { return 0.0 }
    $mean = ($Counts | Measure-Object -Average).Average
    if ($mean -le 0) { return 0.0 }
    $variance = (($Counts | ForEach-Object { [math]::Pow($_ - $mean, 2) } | Measure-Object -Sum).Sum) / $Counts.Count
    return [math]::Sqrt($variance) / $mean
}

function To-JsonSafe {
    param([object]$Value)
    return ($Value | ConvertTo-Json -Depth 8)
}

if (-not (Test-Path -LiteralPath $MasterPath)) {
    throw "Missing master dataset: $MasterPath"
}

$manualSemanticOverrides = Load-ManualSemanticOverrides -Path $ManualSemanticOverridesPath
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
    $textTokens = @(Get-Tokens -Text $text -Stopwords $stopwords)
    $technologyText = @(
        Clean-Text $row.technical_stack,
        Clean-Text $row.market_label,
        Clean-Text $row.transition_function
    ) -join ' '
    $industryText = @(
        Clean-Text $row.industry_destination,
        Clean-Text $row.structured_sector,
        Clean-Text $row.macro_theme,
        Clean-Text $row.emergent_theme
    ) -join ' '
    $technologyTokens = @(Get-Tokens -Text $technologyText -Stopwords $stopwords)
    $industryTokens = @(Get-Tokens -Text $industryText -Stopwords $stopwords)
    [pscustomobject]@{
        row = $row
        text = $text
        text_tokens = $textTokens
        technology_tokens = $technologyTokens
        industry_tokens = $industryTokens
        tokens = @($textTokens + $technologyTokens + $industryTokens)
        token_count = @($textTokens + $technologyTokens + $industryTokens).Count
        technology_features = (($technologyTokens | Select-Object -Unique | Select-Object -First 6) -join '; ')
        industry_features = (($industryTokens | Select-Object -Unique | Select-Object -First 6) -join '; ')
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
$maxDf = [math]::Max($minDf + 1, [math]::Ceiling($docCount * 0.45))
$vocabulary = @(
    $docFrequency.GetEnumerator() |
    Where-Object { $_.Value -ge $minDf -and $_.Value -le $maxDf } |
    Sort-Object Name |
    ForEach-Object { $_.Name }
)

function Build-WeightedDocuments {
    param(
        [object[]]$RawDocs,
        [string[]]$Vocabulary,
        [hashtable]$DocFrequency,
        [int]$DocCount,
        [double]$TextWeight,
        [double]$TechnologyWeight,
        [double]$IndustryWeight
    )
    $vocabularyLookup = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($item in $Vocabulary) { [void]$vocabularyLookup.Add([string]$item) }
    $built = New-Object System.Collections.Generic.List[object]
    foreach ($doc in $RawDocs) {
    $termCounts = @{}
        $bags = @()
        foreach ($token in $doc.text_tokens) { $bags += [pscustomobject]@{ token = $token; weight = $TextWeight } }
        foreach ($token in $doc.technology_tokens) { $bags += [pscustomobject]@{ token = "tech:$token"; base_token = $token; weight = $TechnologyWeight } }
        foreach ($token in $doc.industry_tokens) { $bags += [pscustomobject]@{ token = "industry:$token"; base_token = $token; weight = $IndustryWeight } }

        foreach ($item in $bags) {
            $token = [string]$item.token
            $baseToken = if ($item.PSObject.Properties.Name -contains 'base_token') { [string]$item.base_token } else { $token }
            if (-not $vocabularyLookup.Contains($baseToken)) { continue }
            if (-not $termCounts.ContainsKey($token)) { $termCounts[$token] = 0.0 }
            $termCounts[$token] = [double]$termCounts[$token] + [double]$item.weight
        }
        $vector = @{}
        $totalTerms = [double][math]::Max(1, ($termCounts.Values | Measure-Object -Sum).Sum)
        foreach ($token in $termCounts.Keys) {
            $baseToken = ($token -replace '^(tech|industry):', '')
            $tf = [double]$termCounts[$token] / $totalTerms
            $idf = [math]::Log((1.0 + $DocCount) / (1.0 + [double]$DocFrequency[$baseToken])) + 1.0
            $vector[$token] = $tf * $idf
        }
        $built.Add([pscustomobject]@{
            row = $doc.row
            text = $doc.text
            tokens = $doc.tokens
            token_count = $doc.token_count
            technology_features = $doc.technology_features
            industry_features = $doc.industry_features
            vector = $vector
        })
    }
    return $built
}

$weightProfiles = @(
    [pscustomobject]@{ id = 'balanced'; label = 'Balanced'; text_weight = 1.0; technology_weight = 0.65; industry_weight = 0.45; description = 'Audited text first, with technology and industry as auxiliary dimensions.' },
    [pscustomobject]@{ id = 'technology_heavy'; label = 'Technology-heavy'; text_weight = 0.85; technology_weight = 1.15; industry_weight = 0.35; description = 'Increases the weight of technical_stack, market_label and transition_function.' },
    [pscustomobject]@{ id = 'industry_heavy'; label = 'Industry-heavy'; text_weight = 0.85; technology_weight = 0.4; industry_weight = 1.1; description = 'Increases the weight of industry destination, structured sector and editorial taxonomy.' }
)

$documents = Build-WeightedDocuments -RawDocs @($rawDocs) -Vocabulary $vocabulary -DocFrequency $docFrequency -DocCount $docCount -TextWeight 1.0 -TechnologyWeight 0.65 -IndustryWeight 0.45

$candidateSummaries = New-Object System.Collections.Generic.List[object]
$clusterRows = New-Object System.Collections.Generic.List[object]
$dashboardCandidates = New-Object System.Collections.Generic.List[object]
$recommendedAssignments = New-Object System.Collections.Generic.List[object]

foreach ($profile in $weightProfiles) {
    $documents = Build-WeightedDocuments -RawDocs @($rawDocs) -Vocabulary $vocabulary -DocFrequency $docFrequency -DocCount $docCount -TextWeight $profile.text_weight -TechnologyWeight $profile.technology_weight -IndustryWeight $profile.industry_weight
    foreach ($k in 5..12) {
    if ($k -ge $documents.Count) { continue }
    $run = Run-KMeansLike -Documents @($documents) -K $k
    $quality = Get-ClusterQuality -Documents @($documents) -Assignments $run.assignments -Centroids $run.centroids

    $clusterLabels = @{}
    $usedLabels = @{}
    $clusterPayload = New-Object System.Collections.Generic.List[object]
    $clusterSizes = New-Object System.Collections.Generic.List[int]
    $lowConfidenceTotal = 0

    foreach ($clusterId in 0..($k - 1)) {
        $memberIndices = @($quality.clusters[$clusterId].ToArray())
        if ($memberIndices.Count -eq 0) { continue }
        $clusterSizes.Add($memberIndices.Count)
        $memberRows = @($memberIndices | ForEach-Object { $documents[$_].row })
        $memberTexts = @($memberIndices | ForEach-Object { $documents[$_].text })
        $topTokens = @(Get-TopTokens -Texts $memberTexts -Limit 8)
        $dominantMacro = Get-Dominant -Rows $memberRows -Property 'macro_theme'
        $representatives = @(
            $memberIndices |
            Sort-Object -Property @{ Expression = { Get-CosineSimilarity -A $documents[$_].vector -B $run.centroids[$clusterId] }; Descending = $true } |
            Select-Object -First 4 |
            ForEach-Object { $documents[$_].row.startup_name }
        )
        $baseLabel = Get-ThemeLabel -DominantMacro $dominantMacro -TopTokens $topTokens -RepresentativeNames $representatives
        $label = Ensure-UniqueLabel -BaseLabel $baseLabel -UsedLabels $usedLabels -TopTokens $topTokens -DominantMacro $dominantMacro
        $namingPolicy = Get-ClusterNamingPolicy -ProfileId $profile.id -K $k -ClusterNumber ($clusterId + 1) -FallbackLabel $label
        $label = Clean-Text $namingPolicy.label
        if (-not $label) { $label = 'semantic edge cases' }
        if ($namingPolicy.status -eq 'curated' -and -not $usedLabels.ContainsKey($label)) {
            $usedLabels[$label] = 1
        }
        $clusterLabels[$clusterId] = $label

        $margins = @()
        foreach ($index in $memberIndices) {
            $ownSim = Get-CosineSimilarity -A $documents[$index].vector -B $run.centroids[$clusterId]
            $bestOther = 0.0
            foreach ($otherCluster in 0..($k - 1)) {
                if ($otherCluster -eq $clusterId) { continue }
                $sim = Get-CosineSimilarity -A $documents[$index].vector -B $run.centroids[$otherCluster]
                if ($sim -gt $bestOther) { $bestOther = $sim }
            }
            $margin = $ownSim - $bestOther
            $margins += $margin
        }
        $avgMargin = if ($margins.Count) { ($margins | Measure-Object -Average).Average } else { 0.0 }
        $lowConfidence = @($margins | Where-Object { $_ -lt 0.04 }).Count
        $lowConfidenceTotal += $lowConfidence
        $clusterMembers = @(
            $memberIndices |
                ForEach-Object {
                    $index = [int]$_
                    $ownSim = Get-CosineSimilarity -A $documents[$index].vector -B $run.centroids[$clusterId]
                    $bestOther = 0.0
                    foreach ($otherCluster in 0..($k - 1)) {
                        if ($otherCluster -eq $clusterId) { continue }
                        $sim = Get-CosineSimilarity -A $documents[$index].vector -B $run.centroids[$otherCluster]
                        if ($sim -gt $bestOther) { $bestOther = $sim }
                    }
                    $margin = $ownSim - $bestOther
                    $confidence = if ($margin -ge 0.11) { 'high' } elseif ($margin -ge 0.04) { 'medium' } else { 'low' }
                    if ($namingPolicy.status -eq 'curated') {
                        $fit = Get-ClusterFit -Document $documents[$index] -TopTokens $topTokens -Margin $margin -AnchorRegex $namingPolicy.anchor_regex
                    } else {
                        $autoFlags = @()
                        if ($margin -lt 0.04) { $autoFlags += 'low_margin' }
                        $fit = [pscustomobject]@{
                            fit = if ($autoFlags.Count) { 'review' } else { 'good' }
                            flags = $autoFlags
                            overlap_count = ''
                            overlap_tokens = ''
                            policy_fit = $true
                        }
                    }
                    [pscustomobject]@{
                        startup_id = $documents[$index].row.startup_id
                        startup_name = $documents[$index].row.startup_name
                        score = [math]::Round($ownSim * 100, 1)
                        margin = [math]::Round($margin * 100, 1)
                        confidence = $confidence
                        cluster_fit = $fit.fit
                        fit_flags = ($fit.flags -join '; ')
                        policy_fit = $fit.policy_fit
                        token_overlap_count = $fit.overlap_count
                        token_overlap = $fit.overlap_tokens
                        source_url = $documents[$index].row.source_url
                        review_status = $documents[$index].row.review_status
                        technology_features = $documents[$index].technology_features
                        industry_features = $documents[$index].industry_features
                    }
                } |
                Sort-Object -Property @{ Expression = 'score'; Descending = $true }, startup_name
        )
        $reviewFitCount = @($clusterMembers | Where-Object { $_.cluster_fit -eq 'review' }).Count
        $watchFitCount = @($clusterMembers | Where-Object { $_.cluster_fit -eq 'watch' }).Count
        $credibilityScore = [math]::Round([math]::Max(0, 100 - (($reviewFitCount * 7.0 + $watchFitCount * 2.5 + $lowConfidence * 3.0) / [math]::Max(1, $memberIndices.Count) * 10.0)), 1)

        $clusterPayload.Add([pscustomobject]@{
            cluster_id = "k${k}_cluster_$($clusterId + 1)"
            label = $label
            description = Get-ThemeDescription -Theme $label
            naming_status = $namingPolicy.status
            size = $memberIndices.Count
            dominant_macro = $dominantMacro
            top_tokens = ($topTokens -join '; ')
            representatives = ($representatives -join '; ')
            avg_margin = [math]::Round($avgMargin * 100, 1)
            low_confidence_count = $lowConfidence
            review_fit_count = $reviewFitCount
            watch_fit_count = $watchFitCount
            credibility_score = $credibilityScore
            members = $clusterMembers
        })

        $clusterRows.Add([pscustomobject]@{
            feature_profile = $profile.id
            k = $k
            cluster_id = "cluster_$($clusterId + 1)"
            cluster_label = $label
            description = Get-ThemeDescription -Theme $label
            naming_status = $namingPolicy.status
            startup_count = $memberIndices.Count
            dominant_macro = $dominantMacro
            top_tokens = ($topTokens -join '; ')
            representatives = ($representatives -join '; ')
            avg_margin = [math]::Round($avgMargin * 100, 1)
            low_confidence_count = $lowConfidence
            review_fit_count = $reviewFitCount
            watch_fit_count = $watchFitCount
            credibility_score = $credibilityScore
        })
    }

    $uniqueLabels = @($clusterLabels.Values | Select-Object -Unique)
    $labelCompression = if ($uniqueLabels.Count) { [math]::Round($k / [double]$uniqueLabels.Count, 2) } else { 1.0 }
    $sizeCounts = @($clusterSizes.ToArray())
    $largestShare = if ($sizeCounts.Count) { ($sizeCounts | Measure-Object -Maximum).Maximum / [double]$docCount } else { 0.0 }
    $sizeCv = Get-SizeCv -Counts $sizeCounts
    $lowConfidenceShare = $lowConfidenceTotal / [double][math]::Max(1, $docCount)
    $labelUniqueness = $uniqueLabels.Count / [double][math]::Max(1, $k)
    $balanceScore = [math]::Max(0.0, 1.0 - $sizeCv)
    $explainability = ($quality.avg_margin * 0.32) + ($quality.avg_within * 0.22) + ($labelUniqueness * 0.20) + ($balanceScore * 0.16) + ((1.0 - $lowConfidenceShare) * 0.10)
    $explainabilityScore = [math]::Round($explainability * 100, 1)

    $candidate = [pscustomobject]@{
        feature_profile = $profile.id
        feature_profile_label = $profile.label
        text_weight = $profile.text_weight
        technology_weight = $profile.technology_weight
        industry_weight = $profile.industry_weight
        k = $k
        startups = $docCount
        avg_margin = [math]::Round($quality.avg_margin * 100, 1)
        avg_within = [math]::Round($quality.avg_within * 100, 1)
        low_confidence_share = [math]::Round($lowConfidenceShare * 100, 1)
        small_clusters = $quality.small_clusters
        unique_labels = $uniqueLabels.Count
        label_compression = $labelCompression
        size_cv = [math]::Round($sizeCv, 2)
        largest_cluster_share = [math]::Round($largestShare * 100, 1)
        explainability_score = $explainabilityScore
    }
    $candidateSummaries.Add($candidate)
    $dashboardCandidates.Add([pscustomobject]@{
        feature_profile = $profile.id
        feature_profile_label = $profile.label
        feature_profile_description = $profile.description
        weights = [pscustomobject]@{
            text = $profile.text_weight
            technology = $profile.technology_weight
            industry = $profile.industry_weight
        }
        k = $k
        metrics = $candidate
        clusters = @($clusterPayload.ToArray())
    })

    if ($profile.id -eq 'balanced' -and $k -eq ($candidateSummaries | Where-Object { $_.feature_profile -eq 'balanced' } | Sort-Object -Property @{ Expression = 'explainability_score'; Descending = $true }, @{ Expression = 'k'; Descending = $false } | Select-Object -First 1).k) {
        $recommendedAssignments.Clear()
        for ($i = 0; $i -lt $documents.Count; $i++) {
            $clusterId = $run.assignments[$i]
            $themeLabel = $clusterLabels[$clusterId]
            $ownSim = Get-CosineSimilarity -A $documents[$i].vector -B $run.centroids[$clusterId]
            $bestOther = 0.0
            foreach ($otherCluster in 0..($k - 1)) {
                if ($otherCluster -eq $clusterId) { continue }
                $sim = Get-CosineSimilarity -A $documents[$i].vector -B $run.centroids[$otherCluster]
                if ($sim -gt $bestOther) { $bestOther = $sim }
            }
            $margin = $ownSim - $bestOther
            $confidence = if ($margin -ge 0.11) { 'high' } elseif ($margin -ge 0.04) { 'medium' } else { 'low' }
            $recommendedAssignments.Add([pscustomobject]@{
                startup_id = $documents[$i].row.startup_id
                startup_name = $documents[$i].row.startup_name
                semantic_single_theme = $themeLabel
                semantic_single_cluster_id = "cluster_$($clusterId + 1)"
                semantic_single_score = [math]::Round($ownSim * 100, 1)
                semantic_single_margin = [math]::Round($margin * 100, 1)
                semantic_single_confidence = $confidence
                source_url = $documents[$i].row.source_url
                review_status = $documents[$i].row.review_status
                technology_features = $documents[$i].technology_features
                industry_features = $documents[$i].industry_features
            })
        }
    }
}
}

$recommended = $candidateSummaries |
    Where-Object { $_.feature_profile -eq 'balanced' } |
    Sort-Object -Property @{ Expression = 'explainability_score'; Descending = $true }, @{ Expression = 'k'; Descending = $false } |
    Select-Object -First 1

$recommendedCandidate = $dashboardCandidates |
    Where-Object { $_.feature_profile -eq $recommended.feature_profile -and [int]$_.k -eq [int]$recommended.k } |
    Select-Object -First 1

if (-not $recommendedCandidate) {
    throw "Unable to find recommended candidate payload for profile=$($recommended.feature_profile), k=$($recommended.k)."
}

$recommendedClusters = New-Object System.Collections.Generic.List[object]
$recommendedAssignments = New-Object System.Collections.Generic.List[object]
foreach ($cluster in $recommendedCandidate.clusters) {
    $recommendedClusters.Add([pscustomobject]@{
        cluster_id = $cluster.cluster_id
        label = $cluster.label
        cluster_label = $cluster.label
        description = $cluster.description
        naming_status = $cluster.naming_status
        size = $cluster.size
        startup_count = $cluster.size
        dominant_macro = $cluster.dominant_macro
        top_tokens = $cluster.top_tokens
        representatives = $cluster.representatives
        avg_margin = $cluster.avg_margin
        low_confidence_count = $cluster.low_confidence_count
        review_fit_count = $cluster.review_fit_count
        watch_fit_count = $cluster.watch_fit_count
        credibility_score = $cluster.credibility_score
        members = $cluster.members
    })
    foreach ($member in $cluster.members) {
        $recommendedAssignments.Add([pscustomobject]@{
            startup_id = $member.startup_id
            startup_name = $member.startup_name
            semantic_single_theme = $cluster.label
            semantic_single_cluster_id = $cluster.cluster_id
            semantic_single_score = $member.score
            semantic_single_margin = $member.margin
            semantic_single_confidence = $member.confidence
            semantic_single_override = 'no'
            semantic_single_override_reason = ''
            source_url = $member.source_url
            review_status = $member.review_status
            technology_features = $member.technology_features
            industry_features = $member.industry_features
        })
    }
}

$manualOverrideCount = 0
foreach ($item in $recommendedAssignments) {
    if (-not $manualSemanticOverrides.ContainsKey([string]$item.startup_id)) { continue }
    $override = $manualSemanticOverrides[[string]$item.startup_id]
    $item.semantic_single_theme = $override.semantic_single_theme
    $item.semantic_single_confidence = 'curated'
    $item.semantic_single_override = 'yes'
    $item.semantic_single_override_reason = $override.override_reason
    $matchingCluster = $recommendedClusters |
        Where-Object { (Clean-Text $_.cluster_label) -eq $override.semantic_single_theme } |
        Select-Object -First 1
    if ($matchingCluster) {
        $item.semantic_single_cluster_id = $matchingCluster.cluster_id
    }
    $manualOverrideCount++
}

foreach ($cluster in $recommendedClusters) {
    $clusterMembers = @(
        $recommendedAssignments |
            Where-Object { (Clean-Text $_.semantic_single_theme) -eq (Clean-Text $cluster.cluster_label) } |
            Sort-Object startup_name
    )
    $cluster.members = $clusterMembers
    $cluster.startup_count = $clusterMembers.Count
    $cluster.size = $clusterMembers.Count
}

$assignmentsById = @{}
foreach ($item in $recommendedAssignments) {
    $assignmentsById[$item.startup_id] = $item
}

$candidateSummaries | Sort-Object -Property k | Export-Csv -LiteralPath $OutputSummaryCsvPath -NoTypeInformation -Encoding UTF8
$clusterRows | Sort-Object -Property k, @{ Expression = 'startup_count'; Descending = $true }, cluster_label | Export-Csv -LiteralPath $OutputClustersCsvPath -NoTypeInformation -Encoding UTF8
$recommendedAssignments | Sort-Object -Property semantic_single_theme, startup_name | Export-Csv -LiteralPath $OutputAssignmentsCsvPath -NoTypeInformation -Encoding UTF8

$reportLines = @()
$reportLines += '# Semantic Single-Level Sweep'
$reportLines += ''
$reportLines += ('- Universe: include + confirmed only')
$reportLines += ('- Startups clustered: {0}' -f $docCount)
$reportLines += ('- Candidate k values tested: 5, 6, 7, 8, 9, 10, 11, 12')
$reportLines += ('- Recommended single-level k: {0}' -f $recommended.k)
$reportLines += ('- Recommended explainability score: {0}' -f $recommended.explainability_score)
$reportLines += ('- Source-backed manual semantic overrides applied to operational assignments: {0}' -f $manualOverrideCount)
$reportLines += ''
$reportLines += '## Candidate comparison'
$reportLines += ''
foreach ($candidate in ($candidateSummaries | Sort-Object -Property feature_profile, k)) {
    $reportLines += ('- profile={0}, k={1}: explainability={2}, avg_margin={3}, avg_within={4}, low_conf_share={5}%, unique_labels={6}, label_compression={7}, size_cv={8}, largest_cluster_share={9}%' -f
        $candidate.feature_profile, $candidate.k, $candidate.explainability_score, $candidate.avg_margin, $candidate.avg_within, $candidate.low_confidence_share, $candidate.unique_labels, $candidate.label_compression, $candidate.size_cv, $candidate.largest_cluster_share)
}
$reportLines += ''
$reportLines += ('## Adopted k={0} taxonomy' -f $recommended.k)
$reportLines += ''
$reportLines += ('- Operational assignments use the recommended single-level semantic cut ({0}, k={1}), so the visible taxonomy stays source-backed, comparable across startups and free of macro/micro nesting.' -f $recommended.feature_profile, $recommended.k)
$reportLines += ''
foreach ($cluster in ($recommendedClusters | Sort-Object -Property @{ Expression = 'startup_count'; Descending = $true }, cluster_label)) {
    $reportLines += ('### {0} ({1})' -f $cluster.cluster_label, $cluster.startup_count)
    $reportLines += ('- Description: {0}' -f $cluster.description)
    $reportLines += ('- Dominant macro: {0}' -f $cluster.dominant_macro)
    $reportLines += ('- Top tokens: {0}' -f $cluster.top_tokens)
    $reportLines += ('- Representatives: {0}' -f $cluster.representatives)
    $reportLines += ('- Avg margin: {0}' -f $cluster.avg_margin)
    $reportLines += ('- Low confidence: {0}' -f $cluster.low_confidence_count)
    $reportLines += ('- Naming status: {0}' -f $cluster.naming_status)
    $reportLines += ('- Credibility score: {0}' -f $cluster.credibility_score)
    $reportLines += ('- Fit review/watch: {0}/{1}' -f $cluster.review_fit_count, $cluster.watch_fit_count)
    $reportLines += ''
}
[IO.File]::WriteAllLines($OutputReportPath, $reportLines)

$payload = [pscustomobject]@{
    summary = [pscustomobject]@{
        startups = $docCount
        recommended_k = $recommended.k
        recommended_profile = $recommended.feature_profile
        recommended_explainability_score = $recommended.explainability_score
    }
    weight_profiles = @($weightProfiles)
    candidates = @($dashboardCandidates.ToArray())
    recommended = [pscustomobject]@{
        k = $recommended.k
        clusters = $recommendedClusters
        assignments = @($recommendedAssignments.ToArray())
        assignmentsById = $assignmentsById
    }
}

$js = "window.SEMANTIC_SINGLE_LEVEL_DATA = " + (To-JsonSafe $payload) + ";"
[IO.File]::WriteAllText($OutputDataJsPath, $js, [Text.Encoding]::UTF8)

Write-Host ("Built semantic single-level sweep. Recommended k={0}" -f $recommended.k)
