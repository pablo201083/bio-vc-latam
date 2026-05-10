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
    param(
        [object[]]$Rows,
        [string]$KeyColumn,
        [string]$KeyValue,
        [hashtable]$Values,
        [string[]]$Columns
    )
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
        id='nairotech'; name='Nairotech'; macro='biobased chemistry and advanced materials'; theme='functional advanced materials and biointerface surfaces'
        one='Antimicrobial polymer and nanotechnology materials platform.'
        summary='Nairotech is an Argentine materials company working with special polymers, composites and nanotechnology, including antimicrobial polyolefin pellets designed to reduce the persistence of viruses, bacteria and fungi on surfaces. The bio signal is not that the material is biobased; it is an advanced-material intervention at the biological interface, with applications in safer surfaces, packaging and industrial substitution. It belongs inside BIO VC LATAM as functional materials with antimicrobial and public-health relevance.'
        problem='Conventional polymers and surfaces can carry persistent microbial contamination and lack functional antimicrobial properties.'
        approach='Special polymers, composites and nanotechnology applied to antimicrobial polyolefin pellets and functional material formulations.'
        market='antimicrobial polymer and nanotechnology materials'
        stack='special polymers; composites; nanotechnology; antimicrobial polyolefins; functional materials'
        transition='passive-polymer-surfaces-to-antimicrobial-functional-materials'
        output='antimicrobial polymer material'
        destination='packaging, surfaces, public health and industrial materials'
        materiality='medium-high'; note='Include as advanced material with direct biointerface relevance, not as biotech or agtech.'
        url='https://www.argentina.gob.ar/noticias/disenan-plasticos-con-propiedades-antimicrobianas'; source='government_public_profile'
        evidence='Argentina Agencia I+D+i describes Nairotech as a company specialized in special polymers and selected for antimicrobial polyolefin pellets that reduce virus, bacteria and fungi persistence on surfaces.'
        confidence='0.84'
    },
    @{
        id='culttivo'; name='Culttivo'; macro='precision agriculture and resource intelligence'; theme='ag-finance, risk and producer intelligence'
        one='Climate-aware credit and risk platform for coffee producers.'
        summary='Culttivo is a Brazilian coffee-finance and risk-intelligence platform that uses satellite imagery, analytics and ESG or climate-risk signals to improve credit access for coffee producers. It is not a biotech company, but it is directly attached to a material biological production system: coffee farming. It belongs inside BIO VC LATAM as agri-finance infrastructure for resilient crop production, producer transition and climate-risk underwriting.'
        problem='Coffee producers face inefficient, opaque credit access and weak climate or ESG risk evaluation.'
        approach='Satellite imagery, analytics and producer-risk workflows for transparent agricultural credit.'
        market='coffee producer credit and climate-risk intelligence'
        stack='satellite imagery; advanced analytics; ESG risk; climate risk; agricultural credit workflows'
        transition='opaque-coffee-credit-to-climate-aware-producer-finance'
        output='agricultural credit and risk-intelligence platform'
        destination='coffee production and agricultural finance'
        materiality='medium-high'; note='Include as financial infrastructure tightly coupled to crop production and resilience.'
        url='https://theyieldlablatam.com/companies/culttivo/'; source='official_portfolio_profile'
        evidence='The Yield Lab Latam describes Culttivo as a digital platform delivering efficient and transparent credit to coffee producers using satellite imagery and advanced analytics.'
        confidence='0.84'
    },
    @{
        id='seedz'; name='Seedz'; macro='precision agriculture and resource intelligence'; theme='agri-market infrastructure and producer engagement'
        one='Agribusiness loyalty, marketplace and producer-intelligence platform.'
        summary='Seedz is a Brazilian agtech platform for agribusiness loyalty, producer engagement, commercial intelligence, rewards, payments and credit access. Its relevance is infrastructural rather than biological: it organizes the commercial layer around farms, input channels and producer relationships in agricultural value chains. It belongs inside BIO VC LATAM as agri-market and producer-engagement infrastructure directly attached to material biological production.'
        problem='Agribusiness channels have fragmented producer relationships, weak commercial intelligence and poor engagement infrastructure.'
        approach='Digital loyalty, rewards, payments, credit access and business-intelligence workflows for agribusiness networks.'
        market='agribusiness loyalty and producer-engagement infrastructure'
        stack='loyalty platform; producer engagement; payments; credit access; commercial intelligence; ag marketplace'
        transition='fragmented-ag-channels-to-data-driven-producer-engagement'
        output='agri-market infrastructure platform'
        destination='agribusiness channels, producers and agricultural input markets'
        materiality='medium'; note='Include as agriculture-market infrastructure, not as food biotech or animal protein.'
        url='https://www.seedz.ag/'; source='official_website'
        evidence='Official site describes technology for agribusiness, including producer rewards, commercial intelligence, incentives, payments and credit access.'
        confidence='0.82'
    },
    @{
        id='cytbac'; name='Cytbac'; macro='therapeutics and regenerative medicine'; theme='vaccine and immunotherapy platforms'
        one='Genetically engineered vaccine and immunotherapy platform.'
        summary='Cytbac is an Argentine biotechnology startup developing vaccines and immunotherapies for humans and animals using predictive genomics, AI/ML and genetically engineered insect-virus vectors. Public WISE evidence frames the platform as a way to deliver pathogen or tumor fragments and trigger stronger cellular immune responses. It belongs inside BIO VC LATAM as a core therapeutic biotech platform, not as ag intelligence or generic software.'
        problem='Many vaccine and immunotherapy approaches are slow to design and may not induce strong cellular immune responses.'
        approach='Predictive genomics, AI/ML and engineered insect-virus vectors for antigen delivery.'
        market='genetically engineered vaccine and immunotherapy platform'
        stack='predictive genomics; AI/ML; engineered insect-virus vectors; antigen delivery; cellular immunity'
        transition='conventional-vaccine-design-to-engineered-immunotherapy-platforms'
        output='vaccine and immunotherapy platform'
        destination='human and animal health'
        materiality='high'; note='Include as core therapeutic biotechnology.'
        url='https://wiselatinamerica.com/Proyecto_Detalle.aspx?proyecto_id=1064'; source='external_profile'
        evidence='WISE Latin America describes Cytbac as an Argentine biotech startup with a disruptive vaccine and therapy platform for humans and animals.'
        confidence='0.88'
    },
    @{
        id='notfossil'; name='NotFossil'; macro='climate, energy and resource systems'; theme='bioremediation and microbial resource recovery'
        one='Microbial biofilters for hydrocarbon degradation.'
        summary='NotFossil develops biofilters that use proprietary microorganisms to degrade hydrocarbons. The company is a clear biological remediation case: it applies microbial metabolism to reduce fossil contamination and recover environmental function. It belongs inside BIO VC LATAM as a bioremediation and planetary-boundary startup, not as ag intelligence or generic climate software.'
        problem='Hydrocarbon contamination persists in industrial and environmental contexts where conventional remediation is costly or incomplete.'
        approach='Biofilters and proprietary microbes selected or engineered for hydrocarbon degradation.'
        market='microbial hydrocarbon bioremediation'
        stack='biofilters; proprietary microbes; hydrocarbon degradation; environmental remediation'
        transition='persistent-fossil-contamination-to-microbial-bioremediation'
        output='microbial bioremediation system'
        destination='environmental remediation, oil and industrial contamination'
        materiality='high'; note='Include as direct microbial remediation of planetary-boundary pressure.'
        url='https://sf500.com.ar/'; source='official_portfolio_profile'
        evidence='SF500 portfolio describes biofilters development with proprietary microbes to degrade hydrocarbons.'
        confidence='0.86'
    },
    @{
        id='radial'; name='Radial'; macro='biobased chemistry and advanced materials'; theme='fungal biomaterials and residue valorization'
        one='Fungal biomaterials made from residues.'
        summary='Radial transforms organic residues into fungal materials for lower-impact material applications. The semantic anchor is simple and strong: fungal biology, waste valorization and biomaterial production. It belongs inside BIO VC LATAM as a biobased materials startup, not as circularity software or generic resource recovery.'
        problem='Material production depends on extractive feedstocks while organic residues remain underused.'
        approach='Fungal growth and residue transformation into usable biomaterial formats.'
        market='fungal biomaterials from residues'
        stack='fungal materials; mycelium; residue valorization; biomaterial production'
        transition='waste-and-extractive-materials-to-fungal-biomaterial-production'
        output='fungal biomaterial'
        destination='biomaterials, packaging, design and low-impact materials'
        materiality='high'; note='Include as core biobased material and residue valorization.'
        url='https://www.gridexponential.com/portfolio'; source='official_portfolio_profile'
        evidence='GRIDX portfolio says Radial transforms residues into fungal materials.'
        confidence='0.84'
    },
    @{
        id='biometallum'; name='BioMetallum'; macro='climate, energy and resource systems'; theme='biomining and critical minerals'
        one='Biomining and direct lithium extraction company.'
        summary='BioMetallum is an Argentine biomining company using microorganisms, synthetic biology and AI-driven exploration to extract lithium and other metals with lower water use, fewer chemicals and reduced environmental impact. It is a high-fit planetary and biobased-industrial case because it applies living systems to critical-mineral extraction for the energy transition. It belongs inside BIO VC LATAM as biomining and resource-recovery infrastructure.'
        problem='Critical-mineral extraction can be water-intensive, chemically intensive and environmentally damaging.'
        approach='Microorganisms, synthetic biology and AI-assisted exploration for biomining and lithium extraction.'
        market='biomining and lower-impact critical-mineral extraction'
        stack='microorganisms; synthetic biology; biomining; AI exploration; direct lithium extraction'
        transition='chemical-intensive-mining-to-biological-critical-mineral-recovery'
        output='biomining process platform'
        destination='lithium, critical minerals and energy-transition materials'
        materiality='high'; note='Include as industrial biotechnology for critical minerals and resource recovery.'
        url='https://bio-metallum.com/'; source='official_website'
        evidence='Official site describes BioMetallum as an Argentinian biomining startup using microorganisms, synthetic biology and AI-driven exploration for efficient lithium and metal extraction with lower water use and environmental impact.'
        confidence='0.90'
    },
    @{
        id='magnamed'; name='Magnamed'; macro='diagnostics and medtech'; theme='critical-care medical devices'
        one='Mechanical ventilation and respiratory critical-care devices.'
        summary='Magnamed is a Brazilian medtech company specialized in respiratory care, mechanical ventilation and critical-care devices for ICU, emergency and transport use. Its BIO VC LATAM fit is clinical infrastructure: hardware and medical-device manufacturing for human physiology and hospital care. It should cluster with clinical devices, not with materials or food.'
        problem='Hospitals and emergency systems need reliable respiratory-care and ventilation equipment across ICU, transport and acute-care settings.'
        approach='Design and manufacturing of mechanical ventilators and respiratory critical-care devices.'
        market='respiratory care and mechanical ventilation devices'
        stack='mechanical ventilation; respiratory care; ICU devices; emergency-care hardware; medical-device manufacturing'
        transition='limited-critical-care-respiratory-capacity-to-scalable-medical-device-infrastructure'
        output='respiratory medical device'
        destination='hospitals, ICU, emergency and transport care'
        materiality='high'; note='Include as clinical medical-device infrastructure.'
        url='https://www.inovacoesmagnamed.com.br/company'; source='official_website'
        evidence='Official company page says Magnamed specializes in respiratory care, develops mechanical ventilators, and is based in Sao Paulo/Cotia, Brazil.'
        confidence='0.86'
    },
    @{
        id='branch_energy'; name='Branch Energy'; macro='climate, energy and resource systems'; theme='distributed clean-energy infrastructure'
        one='On-site batteries and clean-energy management platform.'
        summary='Branch Energy deploys clean-energy and energy-management infrastructure, including on-site batteries and data analytics, to reduce customer energy costs, increase resilience and lower carbon emissions. It is not biotech, but it fits the broader planetary-boundary perimeter as emissions-reduction and resilience infrastructure for material systems. It should cluster with climate and resource intelligence rather than biofactories or medical devices.'
        problem='Energy users face high costs, grid fragility and carbon-intensive electricity consumption.'
        approach='On-site batteries, clean-energy infrastructure and analytics for cost, resilience and emissions reduction.'
        market='distributed clean-energy and battery resilience platform'
        stack='on-site batteries; clean-energy infrastructure; energy analytics; carbon reduction; resilience management'
        transition='carbon-intensive-grid-dependence-to-resilient-clean-energy-infrastructure'
        output='distributed energy-resilience platform'
        destination='commercial, industrial and energy-transition customers'
        materiality='medium'; note='Include as planetary-boundary transition infrastructure, not as bio-based technology.'
        url='https://www.linkedin.com/company/branch-energy'; source='official_public_profile'
        evidence='LinkedIn company profile states that Branch Energy helps customers reduce energy costs while increasing resilience by deploying on-site batteries and other energy infrastructure.'
        confidence='0.78'
    },
    @{
        id='satellogic'; name='Satellogic'; macro='climate, energy and resource systems'; theme='earth observation and planetary monitoring'
        one='Earth-observation satellites for environmental and climate monitoring.'
        summary='Satellogic operates an Earth-observation platform that provides high-frequency satellite imagery for environmental conservation, restoration, wildfire assessment, climate monitoring and natural-resource protection. It is outside narrow biotech, but inside the broader BIO VC LATAM perimeter as planetary-monitoring infrastructure: a tool for managing ecosystems, land use, climate risks and natural capital. It should cluster with climate and planetary intelligence.'
        problem='Environmental, climate and land-use decisions often lack frequent, affordable and scalable observation data.'
        approach='Satellite constellations, Earth-observation imagery and geospatial analytics for environmental monitoring.'
        market='earth observation for planetary and resource monitoring'
        stack='satellite imagery; Earth observation; geospatial analytics; wildfire assessment; climate monitoring'
        transition='sparse-environmental-data-to-high-frequency-planetary-monitoring'
        output='earth-observation data platform'
        destination='environmental conservation, climate monitoring and natural-resource management'
        materiality='medium-high'; note='Include as planetary-boundary monitoring infrastructure.'
        url='https://satellogic.com/earth-observation/environment-climate/'; source='official_website'
        evidence='Official site describes Earth Observation for environmental conservation, restoration, wildfire assessment, climate monitoring and natural resource protection.'
        confidence='0.84'
    },
    @{
        id='tbit'; name='TBIT'; macro='precision agriculture and resource intelligence'; theme='seed and grain quality intelligence'
        one='AI seed and grain analysis platform.'
        summary='TBIT is a Brazilian agtech replacing manual seed and grain analysis with digital image processing and AI. The technology supports objective quality evaluation for seed companies, grain handlers and agricultural supply chains. It belongs inside BIO VC LATAM as crop-input and grain-quality intelligence: software and vision models applied to biological agricultural materials.'
        problem='Manual seed and grain analysis is slow, subjective and difficult to standardize.'
        approach='Image processing and AI models for digital seed and grain quality analysis.'
        market='AI seed and grain quality analysis'
        stack='computer vision; image processing; AI quality analysis; seed analysis; grain analysis'
        transition='manual-seed-and-grain-analysis-to-digital-quality-intelligence'
        output='agricultural quality-analysis platform'
        destination='seeds, grains and agricultural supply chains'
        materiality='medium-high'; note='Include as precision agriculture intelligence applied directly to biological crop materials.'
        url='https://www.kptl.com.br/portfolio/tbit/'; source='official_portfolio_profile'
        evidence='KPTL describes TBIT as replacing manual seed and grain analysis with accurate digital analysis based on image processing and AI.'
        confidence='0.84'
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
        scope_source='semantic_text_batch_02_2026_05_08'; evidence_source=$item.source
        notes=$item.note; confidence=$item.confidence
    }
}

$profiles | Export-Csv -LiteralPath $profilePath -NoTypeInformation -Encoding UTF8
$taxonomies | Export-Csv -LiteralPath $taxonomyPath -NoTypeInformation -Encoding UTF8

Write-Output 'Semantic text batch 02 applied.'
Write-Output ("Updated {0} high-risk semantic profiles." -f $batch.Count)
