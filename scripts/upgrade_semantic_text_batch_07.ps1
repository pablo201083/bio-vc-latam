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
        id='invitrall'; name='Invitrall'; macro='therapeutics and regenerative medicine'; theme='in vitro human organ models and drug testing'
        one='In-vitro human organ models for efficacy and toxicity testing.'
        summary='Invitrall is a biotechnology company developing in-vitro human organ models to evaluate compound efficacy and toxicity with higher biological relevance than conventional preclinical assays. Its core is organ-model and organoid-like testing infrastructure for drug discovery, toxicology and translational medicine. It is not a food ingredient or biofactory case; it should cluster with regenerative medicine, human organ models, drug testing and therapeutic R&D infrastructure.'
        problem='Drug discovery and toxicology testing often rely on models that poorly predict human organ-level biological response.'
        approach='In-vitro human organ models for biologically relevant efficacy and toxicity evaluation.'
        market='in-vitro human organ models for drug testing'
        stack='in-vitro organ models; human tissue models; toxicology; efficacy testing; drug discovery; translational medicine'
        transition='low-predictive-preclinical-testing-to-human-relevant-organ-models'
        output='human organ-model testing platform'
        destination='drug discovery, toxicology, pharma R&D and regenerative medicine'
        materiality='high'; note='Include as therapeutic R&D / organ-model infrastructure, not food biotech.'
        url='https://www.gridexponential.com/portfolio'; source='official_portfolio_profile'
        evidence='GRIDX portfolio says Invitrall develops in-vitro human organ models for evaluating efficacy and toxicity.'
        confidence='0.82'
    },
    @{
        id='dharma_bioscience'; name='Dharma BioScience'; macro='therapeutics and regenerative medicine'; theme='non-invasive tissue regeneration'
        one='Non-invasive regenerative-medicine platform for tissue repair.'
        summary='Dharma BioScience is a regenerative-medicine startup focused on non-invasive tissue regeneration. The public SF500 evidence is concise, but the semantic anchor is clear: tissue repair, regenerative biology and therapeutic intervention rather than diagnostics, food or agricultural biology. It belongs inside BIO VC LATAM as a therapeutics and regenerative-medicine company, with evidence depth marked as portfolio-level.'
        problem='Tissue damage and degenerative conditions need less invasive regenerative therapies.'
        approach='Regenerative-medicine platform for non-invasive tissue repair and biological restoration.'
        market='non-invasive tissue regeneration'
        stack='regenerative medicine; tissue regeneration; tissue repair; therapeutic biology; non-invasive treatment'
        transition='invasive-tissue-treatment-to-non-invasive-regenerative-repair'
        output='regenerative medicine therapeutic platform'
        destination='tissue repair, regenerative medicine and therapeutic R&D'
        materiality='high'; note='Include as regenerative medicine; source remains concise portfolio evidence.'
        url='https://sf500.com.ar/'; source='official_portfolio_profile'
        evidence='SF500 portfolio describes non-invasive tissue regeneration.'
        confidence='0.72'
    },
    @{
        id='lemu'; name='Lemu'; macro='climate, energy and resource systems'; theme='biodiversity MRV and nature intelligence'
        one='Nature intelligence and biodiversity MRV platform.'
        summary='Lemu is a Chilean nature-intelligence startup building Atlas, a biodiversity and nature-MRV platform that measures and manages nature-related impact using ecological indicators, satellite imagery, AI and the Lemu Nge biodiversity satellite. It is not agri-market software; it should cluster with nature restoration, biodiversity measurement, planetary monitoring and ecological intelligence infrastructure.'
        problem='Companies and land managers lack reliable biodiversity and nature-impact measurement for planetary-boundary stewardship.'
        approach='Ecological science, satellite imagery, AI and biodiversity satellite data for nature intelligence and MRV.'
        market='biodiversity MRV and nature intelligence'
        stack='biodiversity MRV; satellite imagery; ecological indicators; AI; nature intelligence; planetary monitoring'
        transition='opaque-nature-impact-to-measurable-biodiversity-MRV'
        output='nature-intelligence MRV platform'
        destination='biodiversity, conservation, land stewardship and nature-positive finance'
        materiality='high'; note='Include as planetary-boundary nature intelligence.'
        url='https://www.le.mu/'; source='official_website'
        evidence='Official site describes Atlas as nature intelligence combining ecological science, multi-modal sources and AI, powered by Lemu Nge, a biodiversity-focused satellite.'
        confidence='0.90'
    },
    @{
        id='waterplan'; name='Waterplan'; macro='climate, energy and resource systems'; theme='water risk and stewardship intelligence'
        one='AI-native water-risk and stewardship platform.'
        summary='Waterplan is an Argentina/US water-risk and stewardship platform helping water-dependent companies measure, report and respond to site-level water risks using AI and local environmental data. It is not agri-market infrastructure; it should cluster with planetary-boundary water stewardship, climate adaptation and resource-risk intelligence for industrial and watershed systems.'
        problem='Water-dependent companies face site-level water risk, scarcity and reporting obligations without enough local intelligence.'
        approach='AI-native water-risk analytics, local environmental data and stewardship workflows for operational response.'
        market='water-risk and stewardship intelligence'
        stack='water risk; AI analytics; local environmental data; water stewardship; climate adaptation; resource intelligence'
        transition='reactive-water-management-to-AI-native-water-stewardship'
        output='water-risk intelligence platform'
        destination='water-dependent industries, watersheds and climate-risk management'
        materiality='high'; note='Include as planetary-boundary water stewardship infrastructure.'
        url='https://www.waterplan.com/'; source='official_website'
        evidence='Official website describes Waterplan as the AI-native platform for water-dependent industries to manage risk, optimize operations and drive sustainable growth.'
        confidence='0.90'
    },
    @{
        id='arqlite'; name='Arqlite'; macro='climate, energy and resource systems'; theme='circular construction materials from plastic waste'
        one='Circular materials company converting hard-to-recycle plastic into construction aggregates.'
        summary='Arqlite is a circular-materials company converting hard-to-recycle plastics into low-carbon lightweight aggregates and other materials for construction and manufacturing. It is not biomanufacturing or molecular biotech; it belongs inside the broader BIO VC LATAM perimeter as planetary-boundary circular materials infrastructure that reduces plastic waste and substitutes virgin construction inputs.'
        problem='Hard-to-recycle plastics leak into waste streams while construction materials depend on high-impact virgin aggregates.'
        approach='Waste-plastic transformation into recycled lightweight aggregates and low-carbon construction materials.'
        market='circular construction materials from plastic waste'
        stack='plastic waste; recycled aggregates; circular materials; low-carbon construction; manufacturing materials'
        transition='hard-to-recycle-plastic-waste-to-low-carbon-construction-materials'
        output='recycled aggregate and circular material'
        destination='construction, manufacturing and circular materials'
        materiality='medium-high'; note='Include as circular materials and resource recovery, not biotech.'
        url='https://curbwaste.com/company-profiles-network/arqlite'; source='secondary_public_profile'
        evidence='Public company profiles describe technology that converts hard-to-recycle plastics into low-carbon materials and recycled aggregates for construction and manufacturing.'
        confidence='0.76'
    },
    @{
        id='ruuts'; name='Ruuts'; macro='climate, energy and resource systems'; theme='regenerative agriculture incentives and ecological outcomes'
        one='Regenerative agriculture incentives and ecological outcome measurement.'
        summary='Ruuts is a regenerative-agriculture platform creating market incentives tied to measurable ecological outcomes such as soil carbon, biodiversity, water-cycle restoration and productive transition for rural producers. It is not food ingredients; it should cluster with nature restoration, carbon intelligence, regenerative land management and ecological outcome measurement.'
        problem='Regenerative land transition lacks trusted incentives and measurable ecological outcomes for producers and markets.'
        approach='Regenerative land-management programs, ecological outcome measurement and market incentives for producers.'
        market='regenerative agriculture incentives and ecological outcome measurement'
        stack='regenerative agriculture; soil carbon; biodiversity; water cycle; ecological outcomes; producer incentives'
        transition='extractive-land-management-to-measured-regenerative-agriculture'
        output='regenerative agriculture outcome platform'
        destination='rural producers, land restoration, carbon and biodiversity markets'
        materiality='high'; note='Include as biocentric land restoration and planetary-boundary infrastructure.'
        url='https://ruuts.la/'; source='official_website'
        evidence='Ruuts official site describes regenerative land management that captures carbon, restores biodiversity and creates sustainable value for agricultural land.'
        confidence='0.86'
    },
    @{
        id='splight'; name='Splight'; macro='climate, energy and resource systems'; theme='AI grid optimization and renewable integration'
        one='AI for grid optimization and renewable energy integration.'
        summary='Splight is a climate-tech company using AI to optimize electric grids, renewable-energy forecasting, DERMS, congestion management and grid resilience. It is outside narrow bio-based technology, but fits the planetary-boundary perimeter as clean-energy infrastructure. It should cluster with climate and resource intelligence, not agri intelligence or traceable markets.'
        problem='Electric grids struggle to integrate variable renewable energy while managing congestion, forecasting and resilience.'
        approach='AI models for renewable forecasting, distributed-energy management, congestion reduction and grid optimization.'
        market='AI grid optimization and renewable integration'
        stack='AI grid optimization; renewable energy forecasting; DERMS; grid congestion; energy resilience'
        transition='constrained-electric-grids-to-AI-optimized-renewable-integration'
        output='grid intelligence platform'
        destination='renewable energy, electric grids and climate infrastructure'
        materiality='medium-high'; note='Include as planetary-boundary energy transition infrastructure, not bio-based.'
        url='https://content.splight-ai.com/blog/ai-powered-grids-the-future-of-efficient-renewable-energy'; source='official_website'
        evidence='Splight materials describe AI for renewable energy forecasting, DERMS, grid congestion reduction and resilience enhancement.'
        confidence='0.82'
    },
    @{
        id='agrolend'; name='Agrolend'; macro='precision agriculture and resource intelligence'; theme='agricultural credit and risk intelligence'
        one='Agricultural credit, receivables and risk-monitoring platform.'
        summary='Agrolend is a Brazilian agfintech focused on agricultural credit, receivables trading, data-driven risk analysis and monitoring for producers, investors and agribusiness. It is not nature restoration; it belongs only as a thesis-border case because it finances biological production systems. It should cluster with agri-finance, producer infrastructure and agricultural risk intelligence.'
        problem='Agricultural producers face inefficient credit access and investors need better agricultural-risk monitoring.'
        approach='Digital agricultural credit, data-driven risk analysis, monitoring and receivables trading infrastructure.'
        market='agricultural credit and risk intelligence'
        stack='agricultural credit; ag receivables; risk monitoring; producer finance; digital agfintech'
        transition='fragmented-rural-credit-to-data-driven-agricultural-finance'
        output='agricultural finance platform'
        destination='farmers, agribusiness credit, investors and rural finance'
        materiality='medium'; note='Include as border ag-finance infrastructure coupled to biological production systems.'
        url='https://spventures.com.br/portfolio/agrolend/'; source='official_portfolio_profile'
        evidence='SP Ventures says Agrolend reinvents agricultural credit through connections and data, integrating analysis, risk monitoring and digital trading of agricultural receivables.'
        confidence='0.78'
    },
    @{
        id='omica'; name='Omica'; macro='diagnostics and medtech'; theme='digital biobank and multiomics infrastructure'
        one='Digital biobank for underrepresented patient populations.'
        summary='Omica is a digital biobank focused on underrepresented patient populations, integrating longitudinal clinical data, multiomics, imaging and biospecimen access. Its role is clinical data infrastructure for precision medicine, biomarker research and therapeutic development. It is not animal protein, agtech or food systems; it should cluster with clinical diagnostics, multiomics, biobank infrastructure and precision-health research.'
        problem='Precision medicine datasets underrepresent many patient populations and lack integrated clinical, omics and biospecimen access.'
        approach='Digital biobank integrating longitudinal clinical data, multiomics, imaging and sample access.'
        market='digital biobank and multiomics infrastructure'
        stack='digital biobank; multiomics; clinical data; biospecimens; imaging; precision medicine'
        transition='underrepresented-clinical-data-to-integrated-multiomics-biobank'
        output='clinical data and biobank platform'
        destination='precision medicine, diagnostics, pharma R&D and biomarker discovery'
        materiality='high'; note='Include as clinical diagnostics / multiomics infrastructure.'
        url='https://www.omica.bio/'; source='official_website'
        evidence='Official website describes a digital biobank with longitudinal clinical data, integrated multiomics and flexible access to data and samples.'
        confidence='0.86'
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
        scope_source='semantic_text_batch_07_2026_05_08'; evidence_source=$item.source
        notes=$item.note; confidence=$item.confidence
    }
}

$profiles | Export-Csv -LiteralPath $profilePath -NoTypeInformation -Encoding UTF8
$taxonomies | Export-Csv -LiteralPath $taxonomyPath -NoTypeInformation -Encoding UTF8

Write-Output 'Semantic text batch 07 applied.'
Write-Output ("Updated {0} high-risk semantic profiles." -f $batch.Count)
