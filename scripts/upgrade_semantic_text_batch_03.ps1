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
        id='biosynaptica'; name='BioSynaptica'; macro='therapeutics and regenerative medicine'; theme='neurotherapeutics and biopharmaceutical platforms'
        one='Biopharmaceutical platform for neurodegenerative diseases.'
        summary='BioSynaptica is an Argentine biotechnology company developing innovative biopharmaceuticals for neurodegenerative diseases, with public evidence centered on a neuropharmaceutical based on human erythropoietin derivatives. The company belongs inside BIO VC LATAM as a therapeutic biotech case: its core is drug development for brain and nervous-system disease, not ag intelligence or generic life-science services.'
        problem='Neurodegenerative diseases lack effective disease-modifying therapies and need new biopharmaceutical mechanisms.'
        approach='Human erythropoietin derivative research and biopharmaceutical development for neuroprotection.'
        market='neurodegenerative disease biopharmaceuticals'
        stack='biopharmaceuticals; erythropoietin derivatives; neuropharmaceuticals; neurodegenerative disease therapeutics'
        transition='symptomatic-neurodegenerative-care-to-novel-biopharmaceutical-neurotherapeutics'
        output='neurotherapeutic biopharmaceutical candidate'
        destination='neurology, CNS therapeutics and pharmaceutical R&D'
        materiality='high'; note='Include as core therapeutic biotechnology.'
        url='https://biosynaptica.com/'; source='official_website'
        evidence='Official site says BioSynaptica develops innovative biopharmaceuticals for neurodegenerative diseases and focuses on a neuropharmaceutical based on human erythropoietin derivatives.'
        confidence='0.86'
    },
    @{
        id='epiliquid'; name='Epiliquid'; macro='diagnostics and medtech'; theme='liquid biopsy and molecular diagnostics'
        one='Liquid-biopsy biomarker platform for early cancer detection.'
        summary='Epiliquid is an Argentine diagnostics startup developing an accessible liquid-biopsy platform for early cancer detection using blood-based biomarkers. Its public company profile positions the company around non-invasive biomarker detection, which makes it a clinical molecular-diagnostics case rather than general biotech. It belongs inside BIO VC LATAM as cancer screening and liquid-biopsy infrastructure.'
        problem='Cancer is often detected late, while invasive diagnostic procedures can be costly, slow or difficult to scale.'
        approach='Blood-based liquid biopsy, biomarker detection and non-invasive molecular screening workflows.'
        market='liquid biopsy for early cancer detection'
        stack='liquid biopsy; blood biomarkers; molecular diagnostics; early cancer detection; non-invasive screening'
        transition='late-invasive-cancer-diagnosis-to-accessible-liquid-biopsy-screening'
        output='liquid-biopsy diagnostic platform'
        destination='oncology diagnostics, screening and clinical laboratories'
        materiality='high'; note='Include as clinical diagnostics / molecular medtech.'
        url='https://ar.linkedin.com/company/epiliquid'; source='public_company_profile'
        evidence='Company profile describes an accessible liquid biopsy biomarker detection platform for early cancer detection.'
        confidence='0.78'
    },
    @{
        id='satellites_on_fire'; name='Satellites on Fire'; macro='climate, energy and resource systems'; theme='wildfire detection and ecosystem resilience'
        one='Real-time wildfire detection using satellites, cameras and AI.'
        summary='Satellites on Fire develops early wildfire detection and smart monitoring systems that combine satellites, cameras, proprietary AI models and alert workflows. It is not bio-based, but it is directly biocentric: the product protects forests, land, biodiversity, carbon stocks and human settlements by detecting fires before public satellite systems can respond. It belongs inside BIO VC LATAM as planetary-boundary and ecosystem-resilience infrastructure.'
        problem='Wildfires can spread before conventional public satellite monitoring or manual reporting detects them.'
        approach='Satellite data, cameras, proprietary AI models and alert workflows for early fire detection.'
        market='AI wildfire detection and ecosystem monitoring'
        stack='satellite monitoring; cameras; AI fire detection; early alerts; forest-risk monitoring'
        transition='late-wildfire-detection-to-real-time-ecosystem-protection'
        output='wildfire detection and monitoring platform'
        destination='forests, land management, conservation and climate-risk response'
        materiality='high'; note='Include as biocentric planetary-boundary infrastructure.'
        url='https://www.satellitesonfire.com/en'; source='official_website'
        evidence='Official site describes early fire detection, smart monitoring and alerts using satellites, cameras and proprietary AI, helping detect fires before public satellite systems.'
        confidence='0.88'
    },
    @{
        id='gameet'; name='Gameet'; macro='diagnostics and medtech'; theme='reproductive biotech and assisted reproduction devices'
        one='3D-printed microdevice platform for assisted reproduction.'
        summary='Gameet is an Argentine reproductive-biotech startup developing 3D-printed microdevices to optimize the production of healthy human embryos in assisted-reproduction workflows. Its technology sits at the intersection of medtech, embryology and reproductive biology: a physical microdevice designed to improve biological outcomes in fertility treatment. It belongs inside BIO VC LATAM as reproductive medtech and bioinstrumentation.'
        problem='Assisted reproduction can suffer from inconsistent embryo-production conditions and limited biological optimization.'
        approach='3D-printed microdevices and controlled assisted-reproduction workflows for embryo development.'
        market='assisted reproduction microdevices'
        stack='3D printing; microdevices; reproductive biology; embryology; assisted reproduction'
        transition='manual-assisted-reproduction-workflows-to-biologically-optimized-microdevices'
        output='reproductive medtech microdevice'
        destination='fertility clinics and assisted reproduction laboratories'
        materiality='high'; note='Include as reproductive medtech / bioinstrumentation.'
        url='https://www.gameet.life/'; source='official_website'
        evidence='Official site describes Gameet as a biotechnology startup optimizing healthy human embryo production through 3D-printed microdevices for assisted reproduction.'
        confidence='0.86'
    },
    @{
        id='lipock'; name='Lipock'; macro='therapeutics and regenerative medicine'; theme='drug delivery and bioactive formulation platforms'
        one='Lipid nanocapsule platform for volatile and hydrophobic actives.'
        summary='Lipock develops lipid nanocapsules that improve the efficacy of volatile and hydrophobic active compounds. The core semantic signal is drug delivery and bioactive formulation: nanoscale lipid encapsulation used to stabilize, deliver or improve actives that are otherwise difficult to formulate. It belongs inside BIO VC LATAM as nanomedicine / formulation infrastructure for therapeutics, cosmetics or bioactive health products.'
        problem='Volatile and hydrophobic active compounds can be difficult to stabilize, formulate and deliver effectively.'
        approach='Lipid nanocapsule formulation for encapsulation, stabilization and controlled delivery of active compounds.'
        market='lipid nanocapsule drug-delivery and formulation platform'
        stack='lipid nanocapsules; encapsulation; drug delivery; hydrophobic actives; formulation technology'
        transition='hard-to-formulate-actives-to-lipid-nanocapsule-delivery'
        output='lipid nanocapsule formulation platform'
        destination='therapeutics, cosmetics and bioactive health-product formulation'
        materiality='high'; note='Include as biomedical formulation and drug-delivery technology.'
        url='https://www.gridexponential.com/portfolio'; source='official_portfolio_profile'
        evidence='GRIDX portfolio says Lipock develops lipid nanocapsules that improve the efficacy of volatile and hydrophobic actives.'
        confidence='0.82'
    },
    @{
        id='future_cow'; name='Future Cow'; macro='food biotech and novel ingredients'; theme='precision-fermented dairy proteins'
        one='Precision-fermented animal-free dairy protein.'
        summary='Future Cow is a Brazilian food-biotech company producing animal-free dairy proteins through precision fermentation. Its platform uses DNA coding in microbial hosts to produce milk proteins without cows, enabling dairy ingredients with lower animal dependence and potential emissions benefits. It belongs inside BIO VC LATAM as a core food-biotech and alternative-protein company, specifically precision-fermented dairy biofactories.'
        problem='Conventional dairy protein depends on cattle, land, feed and methane-intensive animal production.'
        approach='DNA coding and microbial precision fermentation to produce milk proteins without animals.'
        market='precision-fermented animal-free dairy protein'
        stack='precision fermentation; microbial hosts; milk proteins; DNA coding; alternative dairy'
        transition='animal-dairy-protein-to-microbial-precision-fermented-dairy'
        output='animal-free dairy protein ingredient'
        destination='food ingredients, dairy alternatives and alternative proteins'
        materiality='high'; note='Include as core food biotech and precision-fermentation biofactory.'
        url='https://www.futurecow.com.br/'; source='official_website'
        evidence='Official site says Future Cow uses precision fermentation and DNA coding in microbial hosts to produce animal-free milk protein for dairy products.'
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
        scope_source='semantic_text_batch_03_2026_05_08'; evidence_source=$item.source
        notes=$item.note; confidence=$item.confidence
    }
}

$profiles | Export-Csv -LiteralPath $profilePath -NoTypeInformation -Encoding UTF8
$taxonomies | Export-Csv -LiteralPath $taxonomyPath -NoTypeInformation -Encoding UTF8

Write-Output 'Semantic text batch 03 applied.'
Write-Output ("Updated {0} high-risk semantic profiles." -f $batch.Count)
