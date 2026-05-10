param(
    [string]$NodesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\full_gephi_graph\nodes_full.csv",
    [string]$SupplementalEntitiesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\integrated\integrated_entities.csv",
    [string]$SeedAssignmentsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_taxonomy_assignments_v0.csv",
    [string]$ManualOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\manual_startup_taxonomy_overrides.csv",
    [string]$CountryOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\manual_startup_country_overrides.csv",
    [string]$AliasOverridesPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\staging\manual_alias_overrides.csv",
    [string]$OutputCsvPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\startup_taxonomy_assignments_v1.csv",
    [string]$OutputSummaryPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\taxonomy_v1_summary.csv",
    [string]$OutputJsPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\pilot\startup-taxonomy-data.js",
    [string]$ClearDropPath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\thesis_exclusion_clear_drop.csv",
    [string]$ReviewQueuePath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\thesis_exclusion_review_queue.csv",
    [string]$OutputScopePath = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\startup_scope_decisions.csv"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Normalize-Text {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return '' }
    $normalized = $Text.Trim().ToLowerInvariant()
    $normalized = $normalized.Replace([char]0x00B7, ' ')
    $normalized = [regex]::Replace($normalized, '[^a-z0-9]+', ' ')
    return $normalized.Trim()
}

function Normalize-Key {
    param([string]$Text)
    return ((Normalize-Text -Text $Text) -replace '\s+', '')
}

$script:MojibakeMarkers = @([char]0x00C3, [char]0x00C2, [char]0x00E2)

function Get-MojibakeScore {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return 0 }
    $score = 0
    foreach ($marker in $script:MojibakeMarkers) {
        $score += @($Text.ToCharArray() | Where-Object { $_ -eq $marker }).Count
    }
    return $score
}

function Repair-Mojibake {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return '' }

    $value = $Text
    $encodings = @(
        [System.Text.Encoding]::GetEncoding('ISO-8859-1'),
        [System.Text.Encoding]::GetEncoding(1252)
    )

    for ($i = 0; $i -lt 2; $i++) {
        $currentScore = Get-MojibakeScore $value
        if ($currentScore -eq 0) { break }

        foreach ($encoding in $encodings) {
            try {
                $candidate = [System.Text.Encoding]::UTF8.GetString($encoding.GetBytes($value))
                if ((Get-MojibakeScore $candidate) -lt $currentScore) {
                    $value = $candidate
                    break
                }
            } catch {}
        }
    }

    return $value
}

function Clean-Text {
    param([object]$Value)
    if ($null -eq $Value) { return '' }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return '' }
    return (Repair-Mojibake $text).Trim()
}

function Normalize-Text {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return '' }
    $normalized = Clean-Text $Text
    $normalized = $normalized.ToLowerInvariant()
    $normalized = $normalized.Replace([char]0x00B7, ' ')
    $normalized = [regex]::Replace($normalized, '[^a-z0-9]+', ' ')
    return $normalized.Trim()
}

function Get-Field {
    param(
        [object]$Row,
        [string]$Name
    )

    $property = $Row.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }

    return $property.Value
}

function Get-StartupLookupKeys {
    param(
        [string]$StartupId,
        [string]$StartupName
    )

    return @(
        (Normalize-Key -Text $StartupId),
        (Normalize-Key -Text $StartupName)
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique
}

function Resolve-CanonicalStartupName {
    param(
        [string]$StartupName,
        [hashtable]$AliasMap
    )

    $lookupKey = Normalize-Key -Text $StartupName
    if (-not [string]::IsNullOrWhiteSpace($lookupKey) -and $AliasMap.ContainsKey($lookupKey)) {
        return [string]$AliasMap[$lookupKey]
    }

    return [string]$StartupName
}

function Get-NodeCompletenessScore {
    param([object]$Node)

    $score = 0
    foreach ($field in @('d2', 'd4', 'd5')) {
        if (-not [string]::IsNullOrWhiteSpace([string](Get-Field -Row $Node -Name $field))) {
            $score += 1
        }
    }

    return $score
}

function New-Template {
    param(
        [string]$EmergentTheme,
        [string]$MarketLabel,
        [string]$TransitionFunction,
        [string]$TechnicalStack,
        [string]$OutputClass,
        [string]$Feedstock,
        [string]$IndustryDestination,
        [string]$MarketInterface
    )

    return [ordered]@{
        emergent_theme = $EmergentTheme
        market_label = $MarketLabel
        transition_function = $TransitionFunction
        technical_stack = $TechnicalStack
        output_class = $OutputClass
        feedstock = $Feedstock
        industry_destination = $IndustryDestination
        market_interface = $MarketInterface
    }
}

function Copy-Template {
    param([hashtable]$Template)
    $copy = [ordered]@{}
    foreach ($key in $Template.Keys) {
        $copy[$key] = $Template[$key]
    }
    return $copy
}

function Build-Assignment {
    param(
        [object]$Node,
        [hashtable]$Template,
        [string]$Method,
        [string]$TaxonomySource,
        [double]$Confidence,
        [string]$EvidenceSource,
        [string]$Notes
    )

    $assignment = Copy-Template -Template $Template
    $assignment['startup_id'] = Clean-Text $Node.id
    $assignment['startup_name'] = Clean-Text $Node.label
    $assignment['maturity_path'] = 'pending current evidence'
    $assignment['evidence_source'] = $EvidenceSource
    $assignment['confidence'] = [Math]::Round($Confidence, 2)
    $assignment['taxonomy_source'] = $TaxonomySource
    $assignment['assignment_method'] = $Method
    $assignment['structured_sector'] = Clean-Text $Node.d4
    $assignment['structured_country'] = Clean-Text $Node.d2
    $assignment['trl_current'] = ''
    $assignment['trl_current_confidence'] = ''
    $assignment['trl_current_status'] = 'pending_research'
    $assignment['trl_current_source_url'] = ''
    $assignment['trl_current_last_checked'] = ''
    $assignment['valuation_tier'] = [string]$Node.d5
    $assignment['notes'] = $Notes
    return [PSCustomObject]$assignment
}

function Get-MacroTheme {
    param([string]$EmergentTheme)
    switch ($EmergentTheme) {
        'continuous programmable biomanufacturing' { return 'biomanufacturing and bioindustrial platforms' }
        'industrial biotech and molecular tools' { return 'biomanufacturing and bioindustrial platforms' }
        'fermented functional ingredients' { return 'food biotech and novel ingredients' }
        'food transition ingredients and proteins' { return 'food biotech and novel ingredients' }
        'natural food preservation systems' { return 'food biotech and novel ingredients' }
        'microalgae functional ingredients' { return 'food biotech and novel ingredients' }
        'extremophile microbial ag inputs' { return 'ag biologicals and crop resilience' }
        'genome-enabled crop resilience' { return 'ag biologicals and crop resilience' }
        'data-driven pollination systems' { return 'ag biologicals and crop resilience' }
        'ag biologicals and animal resilience' { return 'ag biologicals and crop resilience' }
        'ag biologicals and crop resilience' { return 'ag biologicals and crop resilience' }
        'precision agriculture intelligence' { return 'precision agriculture and resource intelligence' }
        'ag-input market infrastructure' { return 'precision agriculture and resource intelligence' }
        'water intelligence for resilient agriculture' { return 'precision agriculture and resource intelligence' }
        'climate and resource intelligence platforms' { return 'climate, energy and resource systems' }
        'traceability and tokenized resource infrastructure' { return 'climate, energy and resource systems' }
        'critical materials and resource systems' { return 'climate, energy and resource systems' }
        'circular material systems' { return 'climate, energy and resource systems' }
        'resource recovery and bioremediation systems' { return 'climate, energy and resource systems' }
        'regenerative agroforestry and carbon systems' { return 'climate, energy and resource systems' }
        'nature restoration and carbon systems' { return 'climate, energy and resource systems' }
        'biobased chemistry and materials' { return 'biobased chemistry and advanced materials' }
        'computational biology and life-science software' { return 'computational biology and scientific software' }
        'health diagnostics and medtech' { return 'diagnostics and medtech' }
        'therapeutic and regenerative biology' { return 'therapeutics and regenerative medicine' }
        'frontier hardware and space systems' { return 'frontier hardware and infrastructure systems' }
        'semiconductor efficiency systems' { return 'frontier hardware and infrastructure systems' }
        'advanced semiconductor materials' { return 'frontier hardware and infrastructure systems' }
        'nuclear industrial engineering' { return 'frontier hardware and infrastructure systems' }
        'digital coordination and market infrastructure' { return 'peripheral or non-core digital ventures' }
        'frontier applied science ventures' { return 'peripheral or underclassified ventures' }
        default { return 'peripheral or underclassified ventures' }
    }
}

function Get-ThesisFit {
    param([string]$MacroTheme)
    switch ($MacroTheme) {
        'peripheral or non-core digital ventures' { return 'peripheral' }
        'peripheral or underclassified ventures' { return 'under_review' }
        default { return 'core' }
    }
}

function Matches-Any {
    param([string]$Text, [string[]]$Patterns)
    foreach ($pattern in $Patterns) {
        if ($Text -match $pattern) { return $true }
    }
    return $false
}

$templates = @{
    'continuous programmable biomanufacturing' = (New-Template 'continuous programmable biomanufacturing' 'biomanufacturing infrastructure' 'decentralized and digitized bioproduction' 'continuous bioprocessing; bioengineering; bio ai' 'manufacturing platform' 'cell culture media and biological production workflows' 'biologics and cell therapies' 'platform / infrastructure provider')
    'data-driven pollination systems' = (New-Template 'data-driven pollination systems' 'agriculture biotech' 'extractive-to-more-efficient agriculture' 'bee biology; plant science; data analytics' 'ag productivity service' 'pollination workflows and biodiversity data' 'fruit and specialty crop agriculture' 'services plus proprietary technology')
    'extremophile microbial ag inputs' = (New-Template 'extremophile microbial ag inputs' 'ag biologicals; regenerative agriculture' 'degraded-soils-to-productive-soils' 'extremophile microbiology; microbial inoculants' 'ag input' 'extremophile bacteria and soil biology' 'seeds and row crops' 'pipeline and input supplier')
    'water intelligence for resilient agriculture' = (New-Template 'water intelligence for resilient agriculture' 'climate ag platform' 'water-stress-to-efficient-irrigation' 'data platform; agronomy; climate measurement' 'measurement and optimization platform' 'irrigation and farm management data' 'agriculture and watershed management' 'B2B platform')
    'fermented functional ingredients' = (New-Template 'fermented functional ingredients' 'food ingredients; bioindustry' 'synthetic-to-biobased-functional-ingredients' 'fermentation; fungal or microbial engineering' 'functional ingredient' 'sugars and fermentation substrates' 'food, beverage and consumer ingredients' 'ingredient supplier')
    'genome-enabled crop resilience' = (New-Template 'genome-enabled crop resilience' 'ag biotech; crop traits' 'chemical-intensive-to-resilient-crop-systems' 'gene editing; crop trait development; plant science' 'crop trait technology' 'seeds and crop genetics' 'agriculture' 'licensing / trait platform')
    'food transition ingredients and proteins' = (New-Template 'food transition ingredients and proteins' 'foodtech ingredients; alternative proteins' 'animal-and-conventional-to-biobased-food-systems' 'protein formulation; ingredient processing; fermentation' 'food ingredient' 'plant proteins, cell systems or fermentation substrates' 'food and beverage' 'ingredient supplier')
    'biobased chemistry and materials' = (New-Template 'biobased chemistry and materials' 'green chemistry; biomaterials; bioindustry' 'petrochemical-to-biobased-industrial-chemistry' 'biobased solvents; materials science; formulation' 'green chemistry solution' 'bio-sourced compounds and industrial side streams' 'chemicals, materials, cosmetics and ag' 'ingredient and industrial solution supplier')
    'industrial biotech and molecular tools' = (New-Template 'industrial biotech and molecular tools' 'industrial biotech and biological tools' 'synthetic-and-fragmented-production-to-bioenabled-production' 'enzymes; molecular biology; microbial platforms' 'industrial biotech platform' 'molecular systems, enzymes and engineered biology' 'industrial biotech and research markets' 'platform / input supplier')
    'precision agriculture intelligence' = (New-Template 'precision agriculture intelligence' 'precision agriculture software' 'input-intensive-to-precision-application' 'data platforms; agronomic intelligence; computer vision' 'measurement and decision platform' 'field imagery, sensors and farm data' 'agriculture' 'B2B platform')
    'health diagnostics and medtech' = (New-Template 'health diagnostics and medtech' 'health diagnostics and medtech' 'reactive-to-precision-healthcare' 'diagnostics; medtech; imaging; sensing' 'diagnostic or medical device' 'clinical data, samples and sensing systems' 'healthcare providers and labs' 'product and clinical solution provider')
    'therapeutic and regenerative biology' = (New-Template 'therapeutic and regenerative biology' 'therapeutic biotech and regenerative medicine' 'conventional-care-to-biology-enabled-therapies' 'cell engineering; regenerative biology; therapeutic platforms' 'therapeutic platform' 'cells, tissues and biological payloads' 'biotech and healthcare' 'therapeutic platform')
    'computational biology and life-science software' = (New-Template 'computational biology and life-science software' 'computational biology and life-science software' 'slow-fragmented-r-and-d-to-data-driven-biology' 'ai; bioinformatics; omics; scientific software' 'discovery and decision software' 'biological data and scientific workflows' 'biotech, pharma and research labs' 'B2B software platform')
    'climate and resource intelligence platforms' = (New-Template 'climate and resource intelligence platforms' 'climate and resource intelligence' 'resource-waste-and-fragmentation-to-optimized-resilience' 'monitoring; optimization; infrastructure software' 'optimization platform' 'energy, water, climate and logistics data' 'energy, water, carbon and infrastructure systems' 'B2B platform')
    'digital coordination and market infrastructure' = (New-Template 'digital coordination and market infrastructure' 'software and market infrastructure' 'manual-and-fragmented-operations-to-digital-coordination' 'workflow automation; fintech; commerce; enterprise software' 'software platform' 'transaction, workflow and enterprise data' 'cross-sector enterprise markets' 'B2B or marketplace platform')
    'frontier hardware and space systems' = (New-Template 'frontier hardware and space systems' 'frontier hardware and space systems' 'constrained-legacy-infrastructure-to-frontier-hardware-systems' 'hardware; robotics; aerospace; sensing' 'hardware platform' 'advanced hardware and operational data' 'aerospace, infrastructure and industrial markets' 'hardware and systems company')
    'frontier applied science ventures' = (New-Template 'frontier applied science ventures' 'frontier applied science' 'experimental-science-to-commercial-application' 'mixed frontier science stack' 'applied science platform' 'multiple scientific inputs' 'multiple end markets' 'venture platform')
}

$nodesRaw = Import-Csv -LiteralPath $NodesPath | Where-Object { $_.d1 -eq 'Startup' -or $_.d1 -eq 'Startup4' }
$supplementalEntityRows = if (Test-Path -LiteralPath $SupplementalEntitiesPath) { Import-Csv -LiteralPath $SupplementalEntitiesPath } else { @() }
$seedRows = Import-Csv -LiteralPath $SeedAssignmentsPath
$manualOverrideRows = if (Test-Path -LiteralPath $ManualOverridesPath) { Import-Csv -LiteralPath $ManualOverridesPath } else { @() }
$countryOverrideRows = if (Test-Path -LiteralPath $CountryOverridesPath) { Import-Csv -LiteralPath $CountryOverridesPath } else { @() }
$aliasOverrideRows = if (Test-Path -LiteralPath $AliasOverridesPath) { Import-Csv -LiteralPath $AliasOverridesPath } else { @() }
$clearDropRows = if (Test-Path -LiteralPath $ClearDropPath) { Import-Csv -LiteralPath $ClearDropPath } else { @() }
$reviewQueueRows = if (Test-Path -LiteralPath $ReviewQueuePath) { Import-Csv -LiteralPath $ReviewQueuePath } else { @() }

$startupAliasMap = @{}
foreach ($row in $aliasOverrideRows) {
    $canonicalName = [string](Get-Field -Row $row -Name 'canonical_name')
    $aliasName = [string](Get-Field -Row $row -Name 'alias_name')
    if ([string]::IsNullOrWhiteSpace($canonicalName) -or [string]::IsNullOrWhiteSpace($aliasName)) {
        continue
    }

    $aliasKey = Normalize-Key -Text $aliasName
    if (-not [string]::IsNullOrWhiteSpace($aliasKey)) {
        $startupAliasMap[$aliasKey] = $canonicalName
    }
}

$manualOverridesByKey = @{}
foreach ($row in $manualOverrideRows) {
    $keys = Get-StartupLookupKeys -StartupId ([string]$row.startup_id) -StartupName ([string]$row.startup_name)
    foreach ($key in $keys) {
        $manualOverridesByKey[$key] = $row
    }
}

$nodeExistingKeys = @{}
foreach ($row in $nodesRaw) {
    $keys = Get-StartupLookupKeys -StartupId ([string]$row.id) -StartupName ([string]$row.label)
    foreach ($key in $keys) {
        $nodeExistingKeys[$key] = $true
    }
}

$supplementalNodesRaw = foreach ($row in $supplementalEntityRows) {
    if ([string](Get-Field -Row $row -Name 'integrated_type') -ne 'startup') {
        continue
    }

    $entityId = [string](Get-Field -Row $row -Name 'entity_id')
    $canonicalName = [string](Get-Field -Row $row -Name 'canonical_name')
    $keys = Get-StartupLookupKeys -StartupId $entityId -StartupName $canonicalName

    $hasManualCoverage = $false
    foreach ($key in $keys) {
        if ($manualOverridesByKey.ContainsKey($key)) {
            $hasManualCoverage = $true
            break
        }
    }
    if (-not $hasManualCoverage) {
        continue
    }

    $alreadyPresent = $false
    foreach ($key in $keys) {
        if ($nodeExistingKeys.ContainsKey($key)) {
            $alreadyPresent = $true
            break
        }
    }
    if ($alreadyPresent) {
        continue
    }

    [PSCustomObject]@{
        id = $entityId
        label = $canonicalName
        store_id = ''
        x = ''
        y = ''
        z = ''
        size_gephi = '1'
        r = ''
        g = ''
        b = ''
        alpha = ''
        degree = '0'
        indegree = '0'
        outdegree = '0'
        d1 = 'Startup'
        d2 = ''
        d3 = ''
        d4 = ''
        d5 = ''
        d6 = ''
        d7 = ''
        d8 = ''
        d10 = ''
        d11 = ''
        pageranks = '0'
    }
}

$manualOnlyNodesRaw = foreach ($row in $manualOverrideRows) {
    $startupId = [string](Get-Field -Row $row -Name 'startup_id')
    $startupName = [string](Get-Field -Row $row -Name 'startup_name')
    $keys = Get-StartupLookupKeys -StartupId $startupId -StartupName $startupName

    $alreadyPresent = $false
    foreach ($key in $keys) {
        if ($nodeExistingKeys.ContainsKey($key)) {
            $alreadyPresent = $true
            break
        }
    }
    if ($alreadyPresent) {
        continue
    }

    foreach ($key in $keys) {
        $nodeExistingKeys[$key] = $true
    }

    [PSCustomObject]@{
        id = $startupId
        label = $startupName
        store_id = ''
        x = ''
        y = ''
        z = ''
        size_gephi = '1'
        r = ''
        g = ''
        b = ''
        alpha = ''
        degree = '0'
        indegree = '0'
        outdegree = '0'
        d1 = 'Startup'
        d2 = ''
        d3 = ''
        d4 = ''
        d5 = ''
        d6 = ''
        d7 = ''
        d8 = ''
        d10 = ''
        d11 = ''
        pageranks = '0'
    }
}

$nodes = @(
    @($nodesRaw + $supplementalNodesRaw + $manualOnlyNodesRaw) |
        ForEach-Object {
            $resolvedCanonicalName = Resolve-CanonicalStartupName -StartupName ([string]$_.label) -AliasMap $startupAliasMap
            $canonicalKey = Normalize-Key -Text $resolvedCanonicalName
            [PSCustomObject]@{
                node = $_
                canonical_name = $resolvedCanonicalName
                canonical_key = $canonicalKey
                label_exact_match = [int]((Normalize-Key -Text ([string]$_.label)) -eq $canonicalKey)
                id_exact_match = [int]((Normalize-Key -Text ([string]$_.id)) -eq $canonicalKey)
                completeness = Get-NodeCompletenessScore -Node $_
            }
        } |
        Group-Object canonical_key |
        ForEach-Object {
            $preferred = $_.Group |
                Sort-Object `
                    @{ Expression = { $_.label_exact_match }; Descending = $true }, `
                    @{ Expression = { $_.id_exact_match }; Descending = $true }, `
                    @{ Expression = { $_.completeness }; Descending = $true }, `
                    @{ Expression = { ([string]$_.node.label).Length }; Descending = $true } |
                Select-Object -First 1

            $nodeCopy = [ordered]@{}
            foreach ($property in $preferred.node.PSObject.Properties) {
                $nodeCopy[$property.Name] = $property.Value
            }
            $nodeCopy['label'] = $preferred.canonical_name
            $nodeCopy['alias_collapsed_count'] = $_.Count
            [PSCustomObject]$nodeCopy
        }
)

$seedByKey = @{}
foreach ($row in $seedRows) {
    $keys = Get-StartupLookupKeys -StartupId ([string]$row.startup_id) -StartupName ([string]$row.startup_name)
    foreach ($key in $keys) {
        $seedByKey[$key] = $row
    }
}

$countryOverridesByKey = @{}
foreach ($row in $countryOverrideRows) {
    $keys = Get-StartupLookupKeys -StartupId ([string]$row.startup_id) -StartupName ([string]$row.startup_name)
    foreach ($key in $keys) {
        $countryOverridesByKey[$key] = $row
    }
}

$clearDropByKey = @{}
foreach ($row in $clearDropRows) {
    $keys = Get-StartupLookupKeys -StartupId '' -StartupName ([string]$row.startup_name)
    foreach ($key in $keys) {
        $clearDropByKey[$key] = $row
    }
}

$reviewQueueByKey = @{}
foreach ($row in $reviewQueueRows) {
    $keys = Get-StartupLookupKeys -StartupId '' -StartupName ([string]$row.startup_name)
    foreach ($key in $keys) {
        $reviewQueueByKey[$key] = $row
    }
}

$specificKeywordRules = @(
    @{ patterns = @('stamm'); template = 'continuous programmable biomanufacturing'; confidence = 0.84; notes = 'Specific carry-over from seed assignment' },
    @{ patterns = @('beeflow'); template = 'data-driven pollination systems'; confidence = 0.80; notes = 'Specific carry-over from seed assignment' },
    @{ patterns = @('punabio', 'puna bio'); template = 'extremophile microbial ag inputs'; confidence = 0.90; notes = 'Specific carry-over from seed assignment' },
    @{ patterns = @('kilimo'); template = 'water intelligence for resilient agriculture'; confidence = 0.70; notes = 'Specific carry-over from seed assignment' },
    @{ patterns = @('michroma'); template = 'fermented functional ingredients'; confidence = 0.90; notes = 'Specific carry-over from seed assignment' },
    @{ patterns = @('bioheuris'); template = 'genome-enabled crop resilience'; confidence = 0.88; notes = 'Specific carry-over from seed assignment' },
    @{ patterns = @('deepagro'); template = 'precision agriculture intelligence'; confidence = 0.74; notes = 'Specific carry-over from seed assignment' },
    @{ patterns = @('tomorrow foods', 'tomorrow_foods', 'tomorrow'); template = 'food transition ingredients and proteins'; confidence = 0.83; notes = 'Specific carry-over from seed assignment' },
    @{ patterns = @('bioeutectics'); template = 'biobased chemistry and materials'; confidence = 0.90; notes = 'Specific carry-over from seed assignment' }
)

$seedThemeOverrides = @{
    'fermented functional color ingredients' = 'fermented functional ingredients'
    'plant protein systems for food transition' = 'food transition ingredients and proteins'
    'biobased solvent systems' = 'biobased chemistry and materials'
    'precision agro-intelligence' = 'precision agriculture intelligence'
    'genome-enabled weed management' = 'genome-enabled crop resilience'
}

$assignments = foreach ($node in $nodes) {
    $nodeId = [string]$node.id
    $nodeLabel = [string]$node.label
    $sector = [string]$node.d4
    $normalizedId = Normalize-Key -Text $nodeId
    $normalizedLabel = Normalize-Key -Text $nodeLabel
    $searchText = Normalize-Text -Text ($nodeId + ' ' + $nodeLabel + ' ' + $sector)

    $seed = $null
    if ($seedByKey.ContainsKey($normalizedId)) {
        $seed = $seedByKey[$normalizedId]
    } elseif ($seedByKey.ContainsKey($normalizedLabel)) {
        $seed = $seedByKey[$normalizedLabel]
    }

    if ($null -ne $seed) {
        $seedTheme = [string]$seed.emergent_theme
        if ($seedThemeOverrides.ContainsKey($seedTheme)) {
            $seedTheme = $seedThemeOverrides[$seedTheme]
        }
        $seedTemplate = if ($templates.ContainsKey($seedTheme)) { $templates[$seedTheme] } else { $null }
        [PSCustomObject]@{
            startup_id = $nodeId
            startup_name = $nodeLabel
            emergent_theme = $seedTheme
            market_label = if ($seedTemplate) { [string]$seedTemplate.market_label } else { [string]$seed.market_label }
            transition_function = if ($seedTemplate) { [string]$seedTemplate.transition_function } else { [string]$seed.transition_function }
            technical_stack = if ($seedTemplate) { [string]$seedTemplate.technical_stack } else { [string]$seed.technical_stack }
            output_class = if ($seedTemplate) { [string]$seedTemplate.output_class } else { [string]$seed.output_class }
            feedstock = if ($seedTemplate) { [string]$seedTemplate.feedstock } else { [string]$seed.feedstock }
            industry_destination = if ($seedTemplate) { [string]$seedTemplate.industry_destination } else { [string]$seed.industry_destination }
            market_interface = if ($seedTemplate) { [string]$seedTemplate.market_interface } else { [string]$seed.market_interface }
            maturity_path = if ([string]::IsNullOrWhiteSpace([string]$seed.maturity_path)) { 'pending current evidence' } else { [string]$seed.maturity_path }
            evidence_source = [string]$seed.evidence_source
            confidence = [double]$seed.confidence
            taxonomy_source = 'taxonomy_v0_seed'
            assignment_method = 'manual_seed'
            structured_sector = $sector
            structured_country = [string]$node.d2
            trl_current = ''
            trl_current_confidence = ''
            trl_current_status = 'pending_research'
            trl_current_source_url = ''
            trl_current_last_checked = ''
            valuation_tier = [string]$node.d5
            notes = [string]$seed.notes
        }
        continue
    }

    $manualOverride = $null
    if ($manualOverridesByKey.ContainsKey($normalizedId)) {
        $manualOverride = $manualOverridesByKey[$normalizedId]
    } elseif ($manualOverridesByKey.ContainsKey($normalizedLabel)) {
        $manualOverride = $manualOverridesByKey[$normalizedLabel]
    }

    if ($null -ne $manualOverride) {
        [PSCustomObject]@{
            startup_id = $nodeId
            startup_name = $nodeLabel
            emergent_theme = [string]$manualOverride.emergent_theme
            market_label = [string]$manualOverride.market_label
            transition_function = [string]$manualOverride.transition_function
            technical_stack = [string]$manualOverride.technical_stack
            output_class = [string]$manualOverride.output_class
            feedstock = [string]$manualOverride.feedstock
            industry_destination = [string]$manualOverride.industry_destination
            market_interface = [string]$manualOverride.market_interface
            maturity_path = 'pending current evidence'
            evidence_source = [string]$manualOverride.evidence_source
            confidence = [double]$manualOverride.confidence
            taxonomy_source = 'manual_override'
            assignment_method = 'manual_override'
            structured_sector = $sector
            structured_country = [string]$node.d2
            trl_current = ''
            trl_current_confidence = ''
            trl_current_status = 'pending_research'
            trl_current_source_url = ''
            trl_current_last_checked = ''
            valuation_tier = [string]$node.d5
            notes = [string]$manualOverride.notes
        }
        continue
    }

    $specificRule = $specificKeywordRules | Where-Object { Matches-Any -Text $searchText -Patterns $_.patterns } | Select-Object -First 1
    if ($specificRule) {
        Build-Assignment -Node $node -Template $templates[$specificRule.template] -Method 'keyword_override' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence ([double]$specificRule.confidence) -EvidenceSource 'name_keyword_plus_graph_sector' -Notes ([string]$specificRule.notes)
        continue
    }

    if (Matches-Any -Text $searchText -Patterns @('space','satell','aero','skyloom','quantum south','aerialoop','novo space','innova space','lia aeospace','outpost')) {
        Build-Assignment -Node $node -Template $templates['frontier hardware and space systems'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.71 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Aerospace, satellite or hardware signals'
        continue
    }
    if (Matches-Any -Text $searchText -Patterns @('water','irrig','kilimo')) {
        Build-Assignment -Node $node -Template $templates['water intelligence for resilient agriculture'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.70 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Water and irrigation signals'
        continue
    }
    if (Matches-Any -Text $searchText -Patterns @('pollin','bee','beeflow')) {
        Build-Assignment -Node $node -Template $templates['data-driven pollination systems'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.76 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Pollination and bee biology signals'
        continue
    }
    if (Matches-Any -Text $searchText -Patterns @('onco','thera','organ','ocular','regen')) {
        Build-Assignment -Node $node -Template $templates['therapeutic and regenerative biology'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.72 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Therapeutic or regenerative signals'
        continue
    }
    if (Matches-Any -Text $searchText -Patterns @('med','health','diagn','nano','gisens','avatar','viewmind','microgenesis','qumir')) {
        Build-Assignment -Node $node -Template $templates['health diagnostics and medtech'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.70 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Medtech or diagnostics signals'
        continue
    }
    if (Matches-Any -Text $searchText -Patterns @('rna','omics','bioinformat','apasomics','bitgenia','multiplai','microscopia','bioseek','caspr')) {
        Build-Assignment -Node $node -Template $templates['computational biology and life-science software'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.69 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Scientific software or omics signals'
        continue
    }
    if (Matches-Any -Text $searchText -Patterns @('food','protein','dairy','cell farm','cellva','heartbest','updairy','fungi','michroma','done properly','tomorrow','dprotein','ergo foods','feedvax')) {
        Build-Assignment -Node $node -Template $templates['food transition ingredients and proteins'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.74 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Food systems or ingredient signals'
        continue
    }
    if (Matches-Any -Text $searchText -Patterns @('solv','chem','material','plaster','plast','notfossil','arqlite','biometallum','cyanomin','bioblends','bioplaster','nanoprox','bioeutectics','huiro','keclon')) {
        Build-Assignment -Node $node -Template $templates['biobased chemistry and materials'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.73 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Chemistry, materials or industrial replacement signals'
        continue
    }
    if ((Matches-Any -Text $searchText -Patterns @('enzyme','enzy','glyco','micro','cell','bio','molecular','phage','pepton','limay','mycorium','nunatak','apexzymes','single strand')) -and $sector -ne 'Digital Economy') {
        Build-Assignment -Node $node -Template $templates['industrial biotech and molecular tools'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.68 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Biological tools, enzymes or molecular platform signals'
        continue
    }
    if (Matches-Any -Text $searchText -Patterns @('agro','agri','crop','seed','farm','soil','weed','silo','zoomagri','auravant','wiagro','agrotoken','calice','beam croptech','laurus')) {
        if (Matches-Any -Text $searchText -Patterns @('gene','trait','seed','calice','bioheuris','beam croptech')) {
            Build-Assignment -Node $node -Template $templates['genome-enabled crop resilience'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.72 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Crop genetics and trait signals'
        } else {
            Build-Assignment -Node $node -Template $templates['precision agriculture intelligence'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.68 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Precision agriculture or farm workflow signals'
        }
        continue
    }
    if (Matches-Any -Text $searchText -Patterns @('energy','grid','carbon','climate','splight','gigablue','branch energy','solfium','circular','conciencia','clover','endless')) {
        Build-Assignment -Node $node -Template $templates['climate and resource intelligence platforms'] -Method 'keyword_rule' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.67 -EvidenceSource 'name_keyword_plus_graph_sector' -Notes 'Climate, energy or infrastructure optimization signals'
        continue
    }

    switch ($sector) {
        'AgriÂ·FoodÂ·Land Use' {
            if (Matches-Any -Text $searchText -Patterns @('food','protein','dairy','cell','fung','ingredient','tomorrow','heartbest','updairy')) {
                Build-Assignment -Node $node -Template $templates['food transition ingredients and proteins'] -Method 'sector_plus_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.67 -EvidenceSource 'graph_sector_plus_name_signal' -Notes 'Agri-food cluster leaning toward food transition'
            } elseif (Matches-Any -Text $searchText -Patterns @('seed','crop','trait','gene','weed')) {
                Build-Assignment -Node $node -Template $templates['genome-enabled crop resilience'] -Method 'sector_plus_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.67 -EvidenceSource 'graph_sector_plus_name_signal' -Notes 'Agri-food cluster leaning toward crop genetics'
            } elseif (Matches-Any -Text $searchText -Patterns @('soil','micro','bio','input','puna','nat4bio','ergo','geoprot')) {
                Build-Assignment -Node $node -Template $templates['extremophile microbial ag inputs'] -Method 'sector_plus_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.66 -EvidenceSource 'graph_sector_plus_name_signal' -Notes 'Agri-food cluster leaning toward biological inputs'
            } else {
                Build-Assignment -Node $node -Template $templates['precision agriculture intelligence'] -Method 'sector_default' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.58 -EvidenceSource 'graph_sector_default' -Notes 'Agri-food-land-use default bucket'
            }
            continue
        }
        'Human Health' {
            if (Matches-Any -Text $searchText -Patterns @('onco','thera','organ','ocular','regen','cell')) {
                Build-Assignment -Node $node -Template $templates['therapeutic and regenerative biology'] -Method 'sector_plus_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.69 -EvidenceSource 'graph_sector_plus_name_signal' -Notes 'Human health cluster leaning toward therapeutics'
            } else {
                Build-Assignment -Node $node -Template $templates['health diagnostics and medtech'] -Method 'sector_default' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.61 -EvidenceSource 'graph_sector_default' -Notes 'Human health default bucket'
            }
            continue
        }
        'BioÂ·Industry' {
            if (Matches-Any -Text $searchText -Patterns @('energy','grid','water','splight','gigablue','branch')) {
                Build-Assignment -Node $node -Template $templates['climate and resource intelligence platforms'] -Method 'sector_plus_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.66 -EvidenceSource 'graph_sector_plus_name_signal' -Notes 'Bio-industry cluster leaning toward climate/resource systems'
            } elseif (Matches-Any -Text $searchText -Patterns @('kilimo')) {
                Build-Assignment -Node $node -Template $templates['water intelligence for resilient agriculture'] -Method 'sector_plus_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.70 -EvidenceSource 'graph_sector_plus_name_signal' -Notes 'Bio-industry cluster with water intelligence signal'
            } else {
                Build-Assignment -Node $node -Template $templates['industrial biotech and molecular tools'] -Method 'sector_default' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.60 -EvidenceSource 'graph_sector_default' -Notes 'Bio-industry default bucket'
            }
            continue
        }
        'DeepÂ·Biotech' {
            if (Matches-Any -Text $searchText -Patterns @('michroma','ferment','color','ingredient','properly')) {
                Build-Assignment -Node $node -Template $templates['fermented functional ingredients'] -Method 'sector_plus_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.76 -EvidenceSource 'graph_sector_plus_name_signal' -Notes 'Deep biotech cluster with fermentation or ingredient signals'
            } else {
                Build-Assignment -Node $node -Template $templates['industrial biotech and molecular tools'] -Method 'sector_default' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.63 -EvidenceSource 'graph_sector_default' -Notes 'Deep biotech default bucket'
            }
            continue
        }
        'Digital Economy' {
            if (Matches-Any -Text $searchText -Patterns @('bio','omics','rna','cell','nano','micro','glyco','med','pharma','life')) {
                Build-Assignment -Node $node -Template $templates['computational biology and life-science software'] -Method 'sector_plus_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.60 -EvidenceSource 'graph_sector_plus_name_signal' -Notes 'Digital economy cluster with scientific or biotech signals'
            } elseif (Matches-Any -Text $searchText -Patterns @('agro','agri','crop','farm','silo','water')) {
                Build-Assignment -Node $node -Template $templates['precision agriculture intelligence'] -Method 'sector_plus_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.59 -EvidenceSource 'graph_sector_plus_name_signal' -Notes 'Digital economy cluster with agriculture workflow signals'
            } elseif (Matches-Any -Text $searchText -Patterns @('energy','grid','carbon','climate','resource','log','cargo')) {
                Build-Assignment -Node $node -Template $templates['climate and resource intelligence platforms'] -Method 'sector_plus_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.58 -EvidenceSource 'graph_sector_plus_name_signal' -Notes 'Digital economy cluster with climate or resource signals'
            } else {
                Build-Assignment -Node $node -Template $templates['digital coordination and market infrastructure'] -Method 'sector_default' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.49 -EvidenceSource 'graph_sector_default' -Notes 'Digital economy default bucket'
            }
            continue
        }
        default {
            if (Matches-Any -Text $searchText -Patterns @('bio','micro','cell','nano','gene','omics','rna','enzyme','fung','phage')) {
                Build-Assignment -Node $node -Template $templates['industrial biotech and molecular tools'] -Method 'unclassified_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.58 -EvidenceSource 'name_keyword_only' -Notes 'Unclassified node with biotech signals'
            } elseif (Matches-Any -Text $searchText -Patterns @('agro','crop','seed','soil','farm','pollin','bee')) {
                Build-Assignment -Node $node -Template $templates['precision agriculture intelligence'] -Method 'unclassified_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.56 -EvidenceSource 'name_keyword_only' -Notes 'Unclassified node with agriculture signals'
            } elseif (Matches-Any -Text $searchText -Patterns @('food','protein','dairy')) {
                Build-Assignment -Node $node -Template $templates['food transition ingredients and proteins'] -Method 'unclassified_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.56 -EvidenceSource 'name_keyword_only' -Notes 'Unclassified node with food transition signals'
            } elseif (Matches-Any -Text $searchText -Patterns @('space','satell','aero','hardware')) {
                Build-Assignment -Node $node -Template $templates['frontier hardware and space systems'] -Method 'unclassified_keyword' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.60 -EvidenceSource 'name_keyword_only' -Notes 'Unclassified node with hardware or space signals'
            } else {
                Build-Assignment -Node $node -Template $templates['frontier applied science ventures'] -Method 'fallback_default' -TaxonomySource 'taxonomy_v1_heuristic' -Confidence 0.41 -EvidenceSource 'fallback_default' -Notes 'Low-confidence fallback for currently underdescribed startup'
            }
            continue
        }
    }
}

$assignments = @($assignments) | ForEach-Object {
    $lookupKeys = Get-StartupLookupKeys -StartupId ([string]$_.startup_id) -StartupName ([string]$_.startup_name)
    $manualOverrideForAssignment = $null
    foreach ($key in $lookupKeys) {
        if ($manualOverridesByKey.ContainsKey($key)) {
            $manualOverrideForAssignment = $manualOverridesByKey[$key]
            break
        }
    }
    $macroTheme = Get-MacroTheme -EmergentTheme ([string]$_.emergent_theme)
    $currentMacroTheme = [string](Get-Field -Row $_ -Name 'macro_theme')
    $currentAssignmentMethod = [string](Get-Field -Row $_ -Name 'assignment_method')
    if ($currentAssignmentMethod -eq 'manual_override' -and -not [string]::IsNullOrWhiteSpace($currentMacroTheme)) {
        $macroTheme = $currentMacroTheme
    }
    if ($null -ne $manualOverrideForAssignment) {
        $overrideMacroTheme = [string](Get-Field -Row $manualOverrideForAssignment -Name 'macro_theme')
        if (-not [string]::IsNullOrWhiteSpace($overrideMacroTheme)) {
            $macroTheme = $overrideMacroTheme
        }
    }
    $countryOverrideForAssignment = $null
    foreach ($key in $lookupKeys) {
        if ($countryOverridesByKey.ContainsKey($key)) {
            $countryOverrideForAssignment = $countryOverridesByKey[$key]
            break
        }
    }
    $clearDrop = $null
    foreach ($key in $lookupKeys) {
        if ($clearDropByKey.ContainsKey($key)) {
            $clearDrop = $clearDropByKey[$key]
            break
        }
    }
    $reviewRow = $null
    foreach ($key in $lookupKeys) {
        if ($reviewQueueByKey.ContainsKey($key)) {
            $reviewRow = $reviewQueueByKey[$key]
            break
        }
    }
    $scopeDecision = 'include'
    $scopeReason = 'core_biobased_or_biocentric_scope'
    $scopeSource = 'taxonomy_macro_theme'
    if ($null -ne $manualOverrideForAssignment) {
        $overrideScopeDecision = [string](Get-Field -Row $manualOverrideForAssignment -Name 'scope_decision')
        $overrideScopeReason = [string](Get-Field -Row $manualOverrideForAssignment -Name 'scope_reason')
        $overrideScopeSource = [string](Get-Field -Row $manualOverrideForAssignment -Name 'scope_source')
        if (-not [string]::IsNullOrWhiteSpace($overrideScopeDecision)) {
            $scopeDecision = $overrideScopeDecision
            $scopeReason = $overrideScopeReason
            $scopeSource = $overrideScopeSource
        }
    } elseif ($null -ne $clearDrop) {
        $scopeDecision = 'exclude'
        $scopeReason = [string]$clearDrop.reason
        $scopeSource = 'thesis_exclusion_clear_drop'
    } elseif ($null -ne $reviewRow) {
        $scopeDecision = 'review'
        $scopeReason = [string]$reviewRow.reason
        $scopeSource = 'thesis_exclusion_review_queue'
    } elseif ($macroTheme -eq 'peripheral or non-core digital ventures') {
        $scopeDecision = 'exclude'
        $scopeReason = 'full_digital_no_materiality_signal'
        $scopeSource = 'taxonomy_macro_theme'
    } elseif ($macroTheme -eq 'peripheral or underclassified ventures') {
        $scopeDecision = 'review'
        $scopeReason = 'underclassified_no_clear_bio_materiality_signal'
        $scopeSource = 'taxonomy_macro_theme'
    }
    $_ | Add-Member -NotePropertyName 'macro_theme' -NotePropertyValue $macroTheme -Force
    $_ | Add-Member -NotePropertyName 'thesis_fit' -NotePropertyValue (Get-ThesisFit -MacroTheme $macroTheme) -Force
    $_ | Add-Member -NotePropertyName 'scope_decision' -NotePropertyValue $scopeDecision -Force
    $_ | Add-Member -NotePropertyName 'scope_reason' -NotePropertyValue $scopeReason -Force
    $_ | Add-Member -NotePropertyName 'scope_source' -NotePropertyValue $scopeSource -Force
    if ($null -ne $countryOverrideForAssignment) {
        $overrideCountry = [string](Get-Field -Row $countryOverrideForAssignment -Name 'structured_country')
        if (-not [string]::IsNullOrWhiteSpace($overrideCountry)) {
            $_ | Add-Member -NotePropertyName 'structured_country' -NotePropertyValue $overrideCountry -Force
        }
    }
    $_
} | Sort-Object startup_name
$assignments | Export-Csv -LiteralPath $OutputCsvPath -NoTypeInformation -Encoding UTF8
$assignments |
    Select-Object startup_id, startup_name, macro_theme, emergent_theme, thesis_fit, scope_decision, scope_reason, scope_source, structured_sector, confidence |
    Export-Csv -LiteralPath $OutputScopePath -NoTypeInformation -Encoding UTF8

$summaryRows = @()
$summaryRows += [PSCustomObject]@{ metric = 'startup_total'; value = @($assignments).Count }
$summaryRows += [PSCustomObject]@{ metric = 'seed_assignments'; value = @($assignments | Where-Object { $_.taxonomy_source -eq 'taxonomy_v0_seed' }).Count }
$summaryRows += [PSCustomObject]@{ metric = 'heuristic_assignments'; value = @($assignments | Where-Object { $_.taxonomy_source -eq 'taxonomy_v1_heuristic' }).Count }
$summaryRows += [PSCustomObject]@{ metric = 'confidence_high_ge_0_75'; value = @($assignments | Where-Object { [double]$_.confidence -ge 0.75 }).Count }
$summaryRows += [PSCustomObject]@{ metric = 'confidence_mid_0_55_to_0_74'; value = @($assignments | Where-Object { [double]$_.confidence -ge 0.55 -and [double]$_.confidence -lt 0.75 }).Count }
$summaryRows += [PSCustomObject]@{ metric = 'confidence_low_lt_0_55'; value = @($assignments | Where-Object { [double]$_.confidence -lt 0.55 }).Count }
$summaryRows += [PSCustomObject]@{ metric = 'scope::include'; value = @($assignments | Where-Object { $_.scope_decision -eq 'include' }).Count }
$summaryRows += [PSCustomObject]@{ metric = 'scope::review'; value = @($assignments | Where-Object { $_.scope_decision -eq 'review' }).Count }
$summaryRows += [PSCustomObject]@{ metric = 'scope::exclude'; value = @($assignments | Where-Object { $_.scope_decision -eq 'exclude' }).Count }
foreach ($group in ($assignments | Group-Object emergent_theme | Sort-Object Count -Descending)) {
    $summaryRows += [PSCustomObject]@{ metric = "theme::$($group.Name)"; value = $group.Count }
}
foreach ($group in ($assignments | Group-Object macro_theme | Sort-Object Count -Descending)) {
    $summaryRows += [PSCustomObject]@{ metric = "macro_theme::$($group.Name)"; value = $group.Count }
}
$summaryRows | Export-Csv -LiteralPath $OutputSummaryPath -NoTypeInformation -Encoding UTF8

$assignmentsById = [ordered]@{}
foreach ($assignment in $assignments) {
    $assignmentsById[[string]$assignment.startup_id] = [ordered]@{
        emergent_theme = [string]$assignment.emergent_theme
        market_label = [string]$assignment.market_label
        transition_function = [string]$assignment.transition_function
        technical_stack = [string]$assignment.technical_stack
        output_class = [string]$assignment.output_class
        feedstock = [string]$assignment.feedstock
        industry_destination = [string]$assignment.industry_destination
        market_interface = [string]$assignment.market_interface
        maturity_path = [string]$assignment.maturity_path
        evidence_source = [string]$assignment.evidence_source
        confidence = [double]$assignment.confidence
        taxonomy_source = [string]$assignment.taxonomy_source
        assignment_method = [string]$assignment.assignment_method
        macro_theme = [string]$assignment.macro_theme
        thesis_fit = [string]$assignment.thesis_fit
        scope_decision = [string]$assignment.scope_decision
        scope_reason = [string]$assignment.scope_reason
        scope_source = [string]$assignment.scope_source
        structured_sector = [string]$assignment.structured_sector
        structured_country = [string]$assignment.structured_country
        trl_current = [string]$assignment.trl_current
        trl_current_confidence = [string]$assignment.trl_current_confidence
        trl_current_status = [string]$assignment.trl_current_status
        trl_current_source_url = [string]$assignment.trl_current_source_url
        trl_current_last_checked = [string]$assignment.trl_current_last_checked
        valuation_tier = [string]$assignment.valuation_tier
        notes = [string]$assignment.notes
    }
}

$payload = [PSCustomObject]@{
    summary = [PSCustomObject]@{
        generated_at = (Get-Date).ToString('s')
        startup_total = @($assignments).Count
        seed_assignments = @($assignments | Where-Object { $_.taxonomy_source -eq 'taxonomy_v0_seed' }).Count
        heuristic_assignments = @($assignments | Where-Object { $_.taxonomy_source -eq 'taxonomy_v1_heuristic' }).Count
        confidence_high = @($assignments | Where-Object { [double]$_.confidence -ge 0.75 }).Count
        confidence_mid = @($assignments | Where-Object { [double]$_.confidence -ge 0.55 -and [double]$_.confidence -lt 0.75 }).Count
        confidence_low = @($assignments | Where-Object { [double]$_.confidence -lt 0.55 }).Count
        theme_count = @($assignments | Group-Object emergent_theme).Count
        macro_theme_count = @($assignments | Group-Object macro_theme).Count
        scope_include = @($assignments | Where-Object { $_.scope_decision -eq 'include' }).Count
        scope_review = @($assignments | Where-Object { $_.scope_decision -eq 'review' }).Count
        scope_exclude = @($assignments | Where-Object { $_.scope_decision -eq 'exclude' }).Count
    }
    theme_counts = @(
        $assignments | Group-Object emergent_theme | Sort-Object Count -Descending | ForEach-Object {
            [PSCustomObject]@{ theme = $_.Name; count = $_.Count }
        }
    )
    macro_theme_counts = @(
        $assignments | Group-Object macro_theme | Sort-Object Count -Descending | ForEach-Object {
            [PSCustomObject]@{ theme = $_.Name; count = $_.Count }
        }
    )
    assignmentsById = $assignmentsById
}

$js = "window.STARTUP_TAXONOMY_DATA = " + ($payload | ConvertTo-Json -Depth 8) + ";"
Set-Content -LiteralPath $OutputJsPath -Value $js -Encoding UTF8

Write-Output "Startup taxonomy layer built:"
Write-Output "  CSV: $OutputCsvPath"
Write-Output "  Summary: $OutputSummaryPath"
Write-Output "  JS: $OutputJsPath"

