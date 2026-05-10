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
        id='radbio'; name='Radbio'; macro='therapeutics and regenerative medicine'; theme='biologic therapeutics for fibrosis and cancer'
        one='TGF-beta biologic therapeutics for fibrosis and cancer.'
        summary='Radbio is a biotechnology company developing biologic therapeutics that target TGF-beta biology for fibrosis, complex chronic disease and cancer indications. Its official evidence centers on a novel biomolecule and therapeutic platform rather than diagnostics, agriculture or materials. It belongs inside BIO VC LATAM as a core biologic-drug-development company working on frontier biomedicine.'
        problem='Fibrosis, cancer and complex chronic diseases need new targeted biological mechanisms beyond conventional small-molecule treatment.'
        approach='Biologic drug development focused on TGF-beta pathway modulation and novel biomolecule design.'
        market='TGF-beta biologic therapeutics'
        stack='biologic therapeutics; TGF-beta modulation; biomolecule development; fibrosis; oncology'
        transition='limited-fibrosis-and-cancer-treatment-to-targeted-biologic-therapeutics'
        output='biologic therapeutic candidate'
        destination='fibrosis, oncology and complex chronic disease therapeutics'
        materiality='high'; note='Include as therapeutic biotechnology.'
        url='https://radbiopharm.com/'; source='official_website'
        evidence='Official site describes a biotech company developing a novel biomolecule targeting TGF-beta for fibrosis and cancer indications.'
        confidence='0.88'
    },
    @{
        id='galtec'; name='Galtec Life'; macro='therapeutics and regenerative medicine'; theme='galectin immunotherapy platforms'
        one='Galectin-modulating immunotherapies for cancer and inflammatory disease.'
        summary='Galtec Life is an Argentine biotech developing immunotherapies based on galectin modulation for cancer, autoimmune diseases and chronic inflammatory conditions. The semantic anchor is therapeutic immunology: the company designs biological interventions that act on galectin-mediated immune and inflammatory pathways. It belongs inside BIO VC LATAM as a therapeutic biotech platform, not ag intelligence or generic life-science services.'
        problem='Cancer, autoimmune and chronic inflammatory diseases require better immune-modulating therapeutic mechanisms.'
        approach='Galectin modulation and immunotherapy development for oncology, autoimmunity and inflammation.'
        market='galectin-based immunotherapy platform'
        stack='galectin biology; immunotherapy; oncology; autoimmune disease; inflammatory disease; therapeutic biotech'
        transition='broad-inflammatory-disease-management-to-targeted-galectin-immunotherapy'
        output='galectin-modulating therapeutic platform'
        destination='oncology, autoimmune and inflammatory disease therapeutics'
        materiality='high'; note='Include as core therapeutic biotechnology.'
        url='https://galtec.ar/en/home/'; source='official_website'
        evidence='Official site describes immunotherapies based on galectin modulation for cancer, autoimmune diseases and chronic inflammatory conditions.'
        confidence='0.88'
    },
    @{
        id='nunatak_biotech'; name='Nunatak Biotech'; macro='ag biologicals and crop resilience'; theme='plant microbiome and soil restoration'
        one='Plant-microbiome platform for soil restoration and crop resilience.'
        summary='Nunatak Biotech designs plant-microorganism associations to restore soils and improve crop performance in adverse environments. Its official evidence points to plant-microbiome symbiosis, soil regeneration and biological crop resilience, making it a core ag-biologicals company. It belongs inside BIO VC LATAM as microbial / plant-microbiome infrastructure for regenerative agriculture.'
        problem='Degraded soils and adverse growing conditions reduce crop performance and agricultural resilience.'
        approach='Design of plant-microorganism associations and microbiome-based crop resilience systems.'
        market='plant-microbiome soil restoration technology'
        stack='plant microbiome; microbial symbiosis; soil restoration; crop resilience; regenerative agriculture'
        transition='degraded-soils-and-stressed-crops-to-microbiome-enabled-regeneration'
        output='plant-microbiome bioinput platform'
        destination='crop production, soil restoration and regenerative agriculture'
        materiality='high'; note='Include as core ag biologicals / soil regeneration technology.'
        url='https://www.nunatakbio.com/'; source='official_website'
        evidence='Official site describes plant-microbiome symbiosis design to restore soils and improve plant performance under adverse conditions.'
        confidence='0.88'
    },
    @{
        id='delee'; name='Delee'; macro='diagnostics and medtech'; theme='liquid biopsy and precision oncology diagnostics'
        one='Automated circulating tumor cell liquid-biopsy platform.'
        summary='Delee is a Mexican oncology diagnostics company developing CytoCatch, an automated platform for isolating and analyzing circulating tumor cells from blood. The technology is designed for reliable CTC capture, reproducibility and high recovery across cancer cell lines. It belongs inside BIO VC LATAM as precision-oncology liquid biopsy infrastructure for early detection, treatment monitoring and clinical decision support.'
        problem='Oncology needs non-invasive, reproducible ways to detect and monitor cancer biology from blood samples.'
        approach='Automated circulating tumor cell isolation, capture and blood-sample analysis.'
        market='circulating tumor cell liquid biopsy diagnostics'
        stack='liquid biopsy; circulating tumor cells; automated isolation; oncology diagnostics; blood analysis'
        transition='invasive-or-late-cancer-monitoring-to-automated-liquid-biopsy-diagnostics'
        output='CTC liquid-biopsy diagnostic platform'
        destination='oncology diagnostics and precision medicine'
        materiality='high'; note='Include as clinical diagnostics / precision oncology.'
        url='https://www.delee.co/'; source='official_website'
        evidence='Official site describes CytoCatch as a fully automated platform for isolating and analyzing circulating tumor cells with high recovery and reproducibility from blood samples.'
        confidence='0.90'
    },
    @{
        id='inner_cosmos'; name='Inner Cosmos'; macro='therapeutics and regenerative medicine'; theme='neurotherapeutic medical devices'
        one='Embedded brain-computer-interface therapy for depression.'
        summary='Inner Cosmos is a neurotechnology company developing a minimally invasive embedded brain-computer-interface therapy for treatment-resistant depression. Its Digital Pill is designed to read and stimulate brain networks, with public FDA early-feasibility milestones. It belongs inside BIO VC LATAM as neurotherapeutic medtech: a device-based biological intervention on neural circuits, not generic AI or wellness software.'
        problem='Treatment-resistant depression needs scalable therapeutic options beyond medication and conventional neuromodulation.'
        approach='Embedded BCI device that reads and stimulates brain networks for depression therapy.'
        market='brain-computer-interface therapy for depression'
        stack='brain-computer interface; neurostimulation; embedded device; depression therapy; neural circuits'
        transition='treatment-resistant-depression-to-embedded-neurotherapeutic-intervention'
        output='neurotherapeutic medical device'
        destination='mental health, neurology and neurotechnology'
        materiality='high'; note='Include as neurotherapeutic medtech; keep LATAM linkage under watch if needed.'
        url='https://innercosmos.ai/'; source='official_website'
        evidence='Official site describes the Digital Pill as an embedded BCI designed to treat depression and notes FDA-approved early feasibility study milestones.'
        confidence='0.84'
    },
    @{
        id='multiplai_health'; name='MultiplAI Health'; macro='diagnostics and medtech'; theme='transcriptomic screening and precision diagnostics'
        one='RNA sequencing and AI screening for cardiovascular disease.'
        summary='MultiplAI Health is an Argentina/UK preventive-medicine biotech using whole-blood RNA sequencing and AI to screen cardiovascular and other complex diseases remotely. Its platform combines blood-based transcriptomics, machine learning and scalable preventive-care workflows for earlier risk detection. It belongs inside BIO VC LATAM as genomic diagnostics and precision-health infrastructure, not therapeutics.'
        problem='Cardiovascular and complex diseases are often detected after risk has progressed and become costly to manage.'
        approach='Whole-blood RNA sequencing, transcriptomic biomarkers and AI models for remote disease screening.'
        market='AI transcriptomic screening for cardiovascular disease'
        stack='RNA sequencing; transcriptomics; machine learning; blood-based screening; cardiovascular diagnostics'
        transition='late-disease-detection-to-scalable-transcriptomic-prevention'
        output='blood-based transcriptomic diagnostic platform'
        destination='preventive medicine, cardiovascular screening and precision diagnostics'
        materiality='high'; note='Include as genomic diagnostics / precision health.'
        url='https://www.multiplaihealth.com/'; source='official_website'
        evidence='Official site describes whole-blood RNA sequencing plus AI screening for cardiovascular and other complex diseases.'
        confidence='0.90'
    },
    @{
        id='pill_ar'; name='Pill.AR'; macro='diagnostics and medtech'; theme='personalized medicine manufacturing'
        one='3D-printed personalized medicines platform.'
        summary='Pill.AR is an Argentine pharmaceutical-technology company developing 3D printing and software infrastructure for personalized medicines. Its system connects doctors, pharmacies and health centers so pharmacies can produce patient-specific oral formulations with dose customization, multi-drug integration and traceability. It belongs inside BIO VC LATAM as personalized-medicine manufacturing infrastructure and health-system technology.'
        problem='Standard oral medicines are often poorly personalized across dose, combination and patient-specific treatment needs.'
        approach='3D pharmaceutical printing, prescription software and pharmacy manufacturing workflows for personalized formulations.'
        market='3D-printed personalized medicine manufacturing'
        stack='3D printing; personalized medicine; pharmaceutical formulation; dose customization; pharmacy workflow software'
        transition='standardized-pill-manufacturing-to-personalized-pharmaceutical-production'
        output='personalized medicine manufacturing platform'
        destination='pharmacies, health centers and personalized therapeutics'
        materiality='medium-high'; note='Include as pharmaceutical manufacturing / medtech infrastructure.'
        url='https://pill.ar/'; source='official_website'
        evidence='Official website describes personalized medication production through 3D printing, connecting doctors, pharmacies and health centers, with multiple active ingredients in one capsule and precise dosing.'
        confidence='0.86'
    },
    @{
        id='qumir_nano'; name='Qumir Nano'; macro='ag biologicals and crop resilience'; theme='bio-nano agricultural inputs'
        one='Microbial-metabolite nanodelivery platform for crop inputs.'
        summary='Qumir Nano is an Argentine bio-nanotechnology startup developing agricultural bio-nano inputs through precision nanodelivery of microbial metabolites. Its official site describes a cell-free technology that integrates bioactive microbial metabolites into nanostructured delivery systems for crop protection, plant health, nutrition, resilience and lower chemical-input reliance. It belongs inside BIO VC LATAM as ag biologicals / bio-nanoinputs, not human nanomedicine or food ingredients.'
        problem='Crop protection and nutrition often depend on chemical inputs with inefficient delivery and environmental burden.'
        approach='Microbial-metabolite bioactives integrated into nanostructured delivery systems for crops.'
        market='bio-nano agricultural input platform'
        stack='microbial metabolites; nanodelivery; bio-nanoinputs; crop protection; plant resilience'
        transition='chemical-intensive-crop-inputs-to-microbial-metabolite-nanodelivery'
        output='bio-nano agricultural input'
        destination='crop protection, plant health and regenerative agriculture'
        materiality='high'; note='Include as ag biologicals and nanodelivery for crop resilience.'
        url='https://www.qumirnano.com/'; source='official_website'
        evidence='Official site describes bio-nanosolutions for agriculture, microbial-metabolite nanodelivery, crop protection, plant resilience and field trials in Argentina, Brazil and Paraguay.'
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
        scope_source='semantic_text_batch_04_2026_05_08'; evidence_source=$item.source
        notes=$item.note; confidence=$item.confidence
    }
}

$profiles | Export-Csv -LiteralPath $profilePath -NoTypeInformation -Encoding UTF8
$taxonomies | Export-Csv -LiteralPath $taxonomyPath -NoTypeInformation -Encoding UTF8

Write-Output 'Semantic text batch 04 applied.'
Write-Output ("Updated {0} high-risk semantic profiles." -f $batch.Count)
