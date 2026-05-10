param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack"
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

function Upsert-Row {
    param([object[]]$Rows, [string]$KeyColumn, [string]$KeyValue, [hashtable]$Values, [string[]]$Columns)
    foreach ($row in $Rows) {
        if ((Clean-Text $row.$KeyColumn) -ne $KeyValue) { continue }
        foreach ($column in $Columns) {
            if ($Values.ContainsKey($column)) { $row.$column = $Values[$column] }
        }
        return $Rows
    }
    $object = [ordered]@{}
    foreach ($column in $Columns) {
        $object[$column] = if ($Values.ContainsKey($column)) { $Values[$column] } else { '' }
    }
    return @($Rows) + [pscustomobject]$object
}

$profilePath = Join-Path $Root 'quality\manual_startup_profile_overrides.csv'
$taxonomyPath = Join-Path $Root 'quality\manual_startup_taxonomy_overrides.csv'
$profiles = @(Import-Csv -LiteralPath $profilePath)
$taxonomies = @(Import-Csv -LiteralPath $taxonomyPath)

$profileColumns = @('startup_id','startup_name','startup_summary_v1','business_one_liner','problem_addressed','technical_approach','industry_destination','materiality_signal','thesis_scope_note','source_url','source_type','source_date','evidence_excerpt','summary_confidence','review_status')
$taxonomyColumns = @('startup_id','startup_name','macro_theme','emergent_theme','market_label','technical_stack','transition_function','output_class','feedstock','industry_destination','market_interface','scope_decision','scope_reason','scope_source','evidence_source','notes','confidence')

$batch = @(
    @{
        id='innova_space'; name='Innova Space'; macro='climate, energy and resource systems'; theme='satellite IoT and planetary monitoring'
        one='Satellite IoT for environmental, water and agriculture monitoring.'
        summary='Innova Space deploys picosatellites and satellite-IoT connectivity for remote monitoring applications, including environmental sensing, water-quality monitoring, agriculture, maritime activity and remote infrastructure. It is not biotech and not generic aerospace for this project: its BIO VC LATAM relevance is planetary-boundary infrastructure that makes distributed environmental and agricultural systems observable. It should cluster with planetary monitoring, climate resilience and resource intelligence.'
        problem='Remote environmental, water and agricultural systems often lack low-cost connectivity and real-time monitoring infrastructure.'
        approach='Picosatellite constellation, satellite IoT connectivity and remote sensing workflows for distributed monitoring.'
        market='satellite IoT for planetary and agricultural monitoring'
        stack='picosatellites; satellite IoT; environmental monitoring; water-quality monitoring; agriculture monitoring; remote sensing'
        transition='unobserved-remote-systems-to-satellite-enabled-planetary-monitoring'
        output='satellite IoT monitoring infrastructure'
        destination='environmental monitoring, agriculture, water quality and remote infrastructure'
        materiality='medium-high'; note='Include as planetary monitoring infrastructure, not as generic aerospace.'
        url='https://www.innova-space.com/en/'; source='official_website'
        evidence='Official site highlights environmental, farming, water-quality and maritime monitoring applications enabled by its satellite IoT platform.'
        confidence='0.84'
    },
    @{
        id='promip'; name='Promip'; macro='ag biologicals and crop resilience'; theme='biological pest control and crop protection'
        one='Biological pest-control products and integrated pest management.'
        summary='Promip is a Brazilian technology-based company producing biological products for integrated pest-management programs, including macrobiologicals and microbiologicals from its biofactory. The company is a core ag-biologicals case: its products are living or biologically derived crop-protection agents used to reduce chemical pest-control dependence. It should cluster with biological pest control, crop resilience and agricultural bioinputs, not climate monitoring.'
        problem='Chemical pest control can create resistance, residues and ecological pressure in agricultural production.'
        approach='Biofactory production of macrobiological and microbiological pest-control products for integrated pest management.'
        market='biological pest control and integrated pest management'
        stack='macrobiologicals; microbiologicals; biofactory; integrated pest management; crop protection; biological control'
        transition='chemical-pest-control-to-biological-integrated-pest-management'
        output='biological crop-protection product'
        destination='crop production, pest management and agricultural biologicals'
        materiality='high'; note='Include as core ag biologicals / biological crop protection.'
        url='https://promip.agr.br/institucional/'; source='official_website'
        evidence='Official institutional page describes Promip as a technology-based company with biological products for integrated pest management and a biofactory producing micro and macrobiological products.'
        confidence='0.90'
    },
    @{
        id='asclepii'; name='Asclepii'; macro='therapeutics and regenerative medicine'; theme='regenerative wound care and tissue repair'
        one='Regenerative wound-care matrix and nanosilver hydrogel platform.'
        summary='Asclepii is a regenerative-medicine company developing wound-care technologies between basic bandages and complex cell therapies. Its Artemis tissue-regeneration matrix and Poseidon nanosilver hydrogel wound dressing are clinical wound-healing products for tissue repair, infection control and modern wound management. It is not a food-ingredient or cosmetic case; it should cluster with regenerative medicine, wound care, tissue repair and clinical biomaterials.'
        problem='Chronic and complex wounds need scalable tissue-repair technologies beyond simple dressings and before expensive cell therapies.'
        approach='Tissue-regeneration matrices and nanosilver hydrogel wound dressings for clinical wound care.'
        market='regenerative wound-care and tissue-repair platform'
        stack='regenerative medicine; wound care; tissue repair; nanosilver hydrogel; clinical biomaterials; tissue-regeneration matrix'
        transition='passive-wound-dressings-to-regenerative-tissue-repair-products'
        output='regenerative wound-care medical product'
        destination='wound care, tissue repair, hospitals and clinical medicine'
        materiality='high'; note='Include as regenerative medicine / clinical biomaterials, not food or cosmetics.'
        url='https://asclepii.com/'; source='official_website'
        evidence='Official site describes Poseidon as an FDA-cleared nanosilver hydrogel wound dressing and positions Asclepii around regenerative medicine for modern wound care; legacy site describes Artemis as a scalable tissue-regeneration matrix.'
        confidence='0.90'
    },
    @{
        id='bybug'; name='ByBug'; macro='biomanufacturing and bioindustrial platforms'; theme='insect bioreactors for recombinant proteins'
        one='Engineered insect bioreactors for recombinant proteins and bioinputs.'
        summary='ByBug is a Chilean biotechnology company building an insect-based biomanufacturing platform using genetically modified black soldier fly larvae as living bioreactors. ByBug Synthetics transforms agro-food byproducts into recombinant proteins and bioinputs for pharmaceutical, veterinary, industrial-enzyme and agricultural markets. It is not grain traceability or producer infrastructure; it should cluster with biomanufacturing, recombinant proteins, engineered insects and circular biofactories.'
        problem='Recombinant proteins and bioinputs can be expensive to produce with conventional fermentation and cell-culture infrastructure.'
        approach='Genetically engineered black soldier fly larvae used as living bioreactors fed with agro-food byproducts.'
        market='insect bioreactor recombinant protein platform'
        stack='engineered insects; black soldier fly larvae; recombinant proteins; synthetic biology; bioinputs; circular biomanufacturing'
        transition='capital-intensive-protein-manufacturing-to-insect-bioreactor-biomanufacturing'
        output='insect bioreactor biomanufacturing platform'
        destination='pharmaceuticals, veterinary products, industrial enzymes and agricultural bioinputs'
        materiality='high'; note='Include as circular biomanufacturing, not agri-finance or traceability.'
        url='https://www.bybug.io/tecnologia/'; source='official_website'
        evidence='Official technology page says ByBug Synthetics uses black soldier fly larvae as bioreactors to transform organic waste into recombinant proteins and bioinputs through synthetic biology and genetic engineering.'
        confidence='0.92'
    },
    @{
        id='nat4bio'; name='Nat4Bio'; macro='food biotech and novel ingredients'; theme='edible coatings and post-harvest biopreservation'
        one='Natural zero-residue edible coatings for fresh fruit.'
        summary='Nat4Bio is an Argentine food-protection biotech developing nature-inspired, cell-free biological formulations and edible coatings that extend fresh-produce shelf life and reduce post-harvest waste. Its pipeline uses native microorganisms, microbial biopolymers, natural antimicrobials and food-grade excipients to protect citrus, avocados, apples, pears and other crops. It should cluster with food biotech, post-harvest preservation, edible coatings and food-loss reduction.'
        problem='Fresh fruit loses value and creates waste because conventional post-harvest protection leaves residues or fails to extend shelf life enough.'
        approach='Cell-free biological formulations, edible coatings, microbial biopolymers and natural antimicrobials for fresh produce.'
        market='edible coatings and post-harvest biopreservation'
        stack='edible coatings; microbial biopolymers; natural antimicrobials; food-grade excipients; post-harvest preservation; native microorganisms'
        transition='residue-heavy-post-harvest-treatment-to-natural-biological-food-preservation'
        output='zero-residue edible coating'
        destination='fresh produce, fruit exports, food preservation and food-waste reduction'
        materiality='high'; note='Include as food biotech / biological preservation, not generic food marketplace.'
        url='https://www.nat4bio.com/'; source='official_website'
        evidence='Nat4Bio says it develops nature-inspired, cell-free biological formulations and food-grade coatings based on microbial biopolymers, natural antimicrobials and native microorganisms to protect fresh produce and reduce waste.'
        confidence='0.92'
    },
    @{
        id='sylvarum'; name='Sylvarum'; macro='ag biologicals and crop resilience'; theme='non-thermal plasma seed treatment'
        one='Non-thermal plasma seed-performance platform.'
        summary='Sylvarum is an Argentine agtech using non-thermal plasma and plant electro-hacking to improve seed quality, germination, vigor, pathogen control and yield without genetic modification or chemical residue. The technology is a physical-biological seed treatment that stimulates natural plant potential and reduces pesticide dependence. It should cluster with crop resilience, seed treatment, plant physiology and agricultural biologicals, not with climate monitoring.'
        problem='Seed performance, pathogen pressure and crop vigor often require chemical treatment or produce inconsistent yields.'
        approach='Non-thermal plasma seed treatment and controlled electrical stimulation of plant biological potential.'
        market='non-thermal plasma seed treatment'
        stack='non-thermal plasma; seed treatment; plant electro-hacking; germination; pathogen control; crop resilience'
        transition='chemical-seed-treatment-to-residue-free-plasma-seed-performance'
        output='seed-performance treatment platform'
        destination='seeds, crop production and agricultural biologicals'
        materiality='high'; note='Include as biocentric seed-treatment and crop-resilience infrastructure.'
        url='https://www.sylvarum.co/'; source='official_website'
        evidence='Official site describes non-thermal plasma seed treatment, chemical-free dry processing, germination/vigor improvement, pathogen control and yield improvement.'
        confidence='0.90'
    },
    @{
        id='outpost'; name='Outpost'; macro='computational biology and scientific software'; theme='microbiome predictive biology and techbio'
        one='Closed-loop microbiome predictive-biology platform.'
        summary='Outpost is a TechBio company making human microbiology computable by pairing wet-lab microbiology with machine learning and foundation-model style predictive systems. Its closed-loop engine is aimed at microbiome R&D, predictive medicine and biotech or consumer-health product development. It is not a clinical medical device or diagnostics product; it should cluster with computational biology, microbiome modeling, predictive biology and life-science software.'
        problem='Microbiome R&D is slow, empirical and hard to predict across complex microbial ecosystems.'
        approach='Closed-loop wet-lab microbiology, machine learning and predictive models for microbial ecosystems.'
        market='microbiome predictive biology and techbio platform'
        stack='microbiome modeling; wet-lab microbiology; machine learning; foundation models; predictive biology; techbio'
        transition='empirical-microbiome-RD-to-computable-predictive-biology'
        output='microbiome predictive-biology platform'
        destination='biotech, pharma, consumer health and microbiome R&D'
        materiality='high'; note='Include as computational biology / microbiome techbio, not medical device.'
        url='https://www.outpost.bio/'; source='official_website'
        evidence='Official site describes a closed-loop engine pairing wet-lab biology with machine learning to make microbial ecosystems computable and enable predictive medicine.'
        confidence='0.90'
    }
)

foreach ($item in $batch) {
    $profiles = Upsert-Row -Rows $profiles -KeyColumn 'startup_id' -KeyValue $item.id -Columns $profileColumns -Values @{
        startup_id=$item.id; startup_name=$item.name; startup_summary_v1=$item.summary; business_one_liner=$item.one
        problem_addressed=$item.problem; technical_approach=$item.approach; industry_destination=$item.destination
        materiality_signal=$item.materiality; thesis_scope_note=$item.note; source_url=$item.url; source_type=$item.source
        source_date='2026-05-08'; evidence_excerpt=$item.evidence; summary_confidence='high'; review_status='reviewed'
    }
    $taxonomies = Upsert-Row -Rows $taxonomies -KeyColumn 'startup_id' -KeyValue $item.id -Columns $taxonomyColumns -Values @{
        startup_id=$item.id; startup_name=$item.name; macro_theme=$item.macro; emergent_theme=$item.theme
        market_label=$item.market; technical_stack=$item.stack; transition_function=$item.transition; output_class=$item.output
        feedstock=''; industry_destination=$item.destination; market_interface='B2B / platform'
        scope_decision='include'; scope_reason='source_backed_material_bio_or_planetary_signal'
        scope_source='semantic_text_batch_06_2026_05_08'; evidence_source=$item.source
        notes=$item.note; confidence=$item.confidence
    }
}

$profiles | Export-Csv -LiteralPath $profilePath -NoTypeInformation -Encoding UTF8
$taxonomies | Export-Csv -LiteralPath $taxonomyPath -NoTypeInformation -Encoding UTF8

Write-Output 'Semantic text batch 06 applied.'
Write-Output ("Updated {0} high-risk semantic profiles." -f $batch.Count)
