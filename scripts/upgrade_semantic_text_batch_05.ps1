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
        id='biotalife'; name='Biotalife'; macro='diagnostics and medtech'; theme='microbiome medical devices and womens health'
        one='Microbiome medical devices for vaginal health.'
        summary='Biotalife is a microbiome medtech company developing medical devices that naturally rebalance human microbiota, with an explicit focus on women''s health conditions such as vaginal thrush, bacterial vaginosis and dryness. The company belongs inside BIO VC LATAM as microbiome-linked clinical device infrastructure: a health product acting on human microbial ecosystems, not generic wellness or agtech.'
        problem='Vaginal microbiota imbalance contributes to recurring health conditions and often lacks gentle, microbiome-preserving treatment options.'
        approach='Medical devices designed to rebalance human microbiota naturally in women''s health applications.'
        market='microbiome medical devices for vaginal health'
        stack='human microbiome; medical devices; vaginal microbiota; women''s health; bacterial vaginosis; thrush'
        transition='symptom-focused-womens-health-products-to-microbiome-rebalancing-medical-devices'
        output='microbiome medical device'
        destination='women''s health, gynecology and microbiome care'
        materiality='high'; note='Include as microbiome medtech / human health device.'
        url='https://www.biotalife.com/'; source='official_website'
        evidence='Official site describes medical devices that naturally balance human microbiota, particularly for vaginal thrush, bacterial vaginosis and dryness.'
        confidence='0.86'
    },
    @{
        id='metabix-biotech'; name='metaBIX Biotech'; macro='diagnostics and medtech'; theme='environmental pathogen intelligence and biosecurity'
        one='Environmental sampling and AI bio-vigilance platform.'
        summary='metaBIX Biotech is a Uruguayan bio-vigilance company combining environmental sampling, biotechnology hardware and AI models to predict disease and microbiological contamination risks. Its platform analyzes environmental samples to generate early warnings for plants, animals, humans and food-production systems. It belongs inside BIO VC LATAM as pathogen intelligence, biosecurity and prevention infrastructure across living systems.'
        problem='Disease and contamination risks in plants, animals, humans and food systems are often detected too late.'
        approach='Environmental sample collection, biotechnology hardware and AI models for infection-pressure and contamination early warning.'
        market='environmental pathogen intelligence and bio-vigilance'
        stack='environmental sampling; biotechnology hardware; AI disease prediction; pathogen surveillance; biosecurity'
        transition='reactive-disease-response-to-environmental-pathogen-early-warning'
        output='bio-vigilance and pathogen-intelligence platform'
        destination='food production, animal health, plant health, human health and biosecurity'
        materiality='high'; note='Include as diagnostics / biosecurity infrastructure for living systems.'
        url='https://mtec-sc.org/life-sciences/metabix-biotech'; source='external_company_profile'
        evidence='MTEC describes metaBIX as using AI and biotechnology for disease prediction and early warning systems from environmental samples, with hardware, biotechnology and AI for infection-pressure assessment.'
        confidence='0.82'
    },
    @{
        id='new_organs_biotech'; name='New Organs Biotech'; macro='therapeutics and regenerative medicine'; theme='gene-edited regenerative medicine and organ replacement'
        one='Gene-edited regenerative medicine for organ shortage.'
        summary='New Organs Biotech is an Argentine regenerative-medicine startup combining gene editing and precision medicine to address chronic organ shortages and the limits of conventional transplantation. Public evidence is currently from GRIDX, but the biological mechanism is clear: engineered organ and regenerative-health solutions for transplant medicine. It belongs inside BIO VC LATAM as regenerative biology and therapeutic platform infrastructure.'
        problem='Organ shortage and transplant limitations create unmet needs in chronic and end-stage disease.'
        approach='Gene editing, precision medicine and regenerative biology for engineered organ or transplant-related solutions.'
        market='gene-edited regenerative medicine for organ replacement'
        stack='gene editing; precision medicine; regenerative medicine; organ shortage; transplant biology'
        transition='donor-organ-shortage-to-engineered-regenerative-organ-solutions'
        output='regenerative medicine therapeutic platform'
        destination='transplant medicine, regenerative health and organ replacement'
        materiality='high'; note='Include as regenerative medicine; evidence depth remains medium because public source is portfolio-level.'
        url='https://www.gridexponential.com/portfolio'; source='official_portfolio_profile'
        evidence='GRIDX portfolio describes New Organs Biotech as combining gene editing with precision medicine to solve organ shortage.'
        confidence='0.78'
    },
    @{
        id='inmet'; name='INMET'; macro='biobased chemistry and advanced materials'; theme='PHB biopolymers and compostable materials'
        one='Compostable PHB biopolymer from agro-industrial waste.'
        summary='INMET is an Argentine biomaterials company developing PHB biopolymer from agro-industrial byproducts through synthetic-biology strain optimization and a solvent-free downstream process. Its material is described as fully bio-based, compostable and biodegradable even in marine environments, with validated plastics applications. It belongs inside BIO VC LATAM as core biobased chemistry, circular biomaterials and fossil-plastic substitution infrastructure.'
        problem='Fossil plastics persist in the environment while agro-industrial residues remain underused as material feedstocks.'
        approach='Synthetic-biology strain optimization and solvent-free PHB biopolymer production from agro-industrial byproducts.'
        market='PHB biopolymer and compostable biomaterials'
        stack='PHB; biopolymer; synthetic biology; agro-industrial waste; solvent-free process; compostable plastics'
        transition='fossil-plastic-materials-to-compostable-biobased-PHB'
        output='compostable PHB biopolymer'
        destination='packaging, plastics, biomaterials and circular materials'
        materiality='high'; note='Include as core biobased chemistry / biomaterials.'
        url='https://inmet.com.ar/en/biomateriales/'; source='official_website'
        evidence='INMET says it transforms agro-industrial waste into a 100 percent bio-based and compostable biopolymer through a solvent-free process; SF500 describes PHB biopolymer made with synthetic biology strain optimization.'
        confidence='0.92'
    },
    @{
        id='siloreal'; name='SiloReal'; macro='precision agriculture and resource intelligence'; theme='agricultural asset verification and collateral infrastructure'
        one='Remote verification infrastructure for agricultural assets.'
        summary='SiloReal provides infrastructure to remotely verify, digitalize and value agricultural assets in the field so they can be insured, financed and transacted as real collateral. The company is not biotech, but it is directly attached to material biological production systems because it makes crop and inventory assets legible for finance, insurance and trade. It belongs inside BIO VC LATAM as agri-finance and traceability infrastructure.'
        problem='Agricultural inventory and field assets are hard to verify remotely, limiting insurance, financing and collateral use.'
        approach='Remote verification, digital asset records and valuation workflows for agricultural inventory and field assets.'
        market='agricultural asset verification and collateral infrastructure'
        stack='remote verification; agricultural assets; digital collateral; crop inventory; insurance; financing'
        transition='opaque-field-assets-to-verifiable-agricultural-collateral'
        output='agricultural asset verification platform'
        destination='agriculture, rural finance, insurance and commodity transactions'
        materiality='medium-high'; note='Include as market infrastructure coupled to material crop systems.'
        url='https://www.siloreal.com/en/'; source='official_website'
        evidence='Official site describes remote verification and digitalization of field assets so they can be insured, financed and transacted as collateral.'
        confidence='0.84'
    },
    @{
        id='trebe_biotech'; name='Trebe Biotech'; macro='food biotech and novel ingredients'; theme='complex protein production and biomanufacturing'
        one='Complex protein production platform.'
        summary='Trebe Biotech is a food-biotech / biomanufacturing startup focused on making complex proteins simpler and more affordable. Public evidence is currently concise through the SF500 portfolio, but the semantic signal is protein production and biological manufacturing rather than generic food software. It belongs inside BIO VC LATAM as a complex-protein platform linked to alternative ingredients and bioprocessing.'
        problem='Complex proteins can be expensive, difficult to produce and hard to scale for food, health or industrial applications.'
        approach='Biotechnology and biomanufacturing workflows for simpler and more affordable complex protein production.'
        market='complex protein production and biomanufacturing'
        stack='complex proteins; biomanufacturing; protein production; biotechnology; fermentation-adjacent platform'
        transition='expensive-complex-proteins-to-affordable-biomanufactured-proteins'
        output='complex protein production platform'
        destination='food biotech, ingredients and biological manufacturing'
        materiality='high'; note='Include as food biotech / protein biomanufacturing; evidence depth remains portfolio-level.'
        url='https://sf500.com.ar/'; source='official_portfolio_profile'
        evidence='SF500 portfolio describes complex proteins, simple and affordable.'
        confidence='0.72'
    },
    @{
        id='krilltech'; name='Krilltech'; macro='ag biologicals and crop resilience'; theme='nano-biofertilizers and plant physiology'
        one='Nano-biofertilizer and plant physiology platform.'
        summary='Krilltech is a Brazilian agtech developing sustainable crop-input technology based on organic nanostructures that act as fertilizer, biofortificant and nutrient carrier to improve plant performance. Its Arbolin Biogenesis product is described as organic, nano-structured, non-toxic and biocompatible. It belongs inside BIO VC LATAM as crop-resilience input technology, plant physiology and nano-biofertilizer infrastructure.'
        problem='Crops need more efficient nutrient delivery and performance enhancement with lower toxicity and environmental burden.'
        approach='Organic nanostructures used as fertilizer, biofortificant and nutrient carrier for plant physiology.'
        market='nano-biofertilizer and plant physiology platform'
        stack='organic nanostructures; biofertilizer; biofortification; nutrient carrier; plant physiology; crop input'
        transition='conventional-fertilization-to-nano-enabled-plant-performance'
        output='nano-biofertilizer crop input'
        destination='crop production, plant nutrition and agricultural biologicals'
        materiality='high'; note='Include as ag biologicals / crop input technology.'
        url='https://krilltech.com.br/'; source='official_website'
        evidence='Official website describes Arbolin Biogenesis as organic nano-structured, non-toxic and biocompatible, acting as fertilizer, biofortificant and nutrient carrier.'
        confidence='0.88'
    },
    @{
        id='nilus'; name='Nilus'; macro='climate, energy and resource systems'; theme='food rescue and circular food access'
        one='Food rescue and low-cost food access platform.'
        summary='Nilus is a Latin American food-rescue and food-access platform that connects surplus or inefficient food supply with low-cost distribution channels. It is not biotech, but it belongs in the broader BIO VC LATAM perimeter as food-system circularity infrastructure: it reduces food waste, improves affordability and acts on a material biological supply chain. It should cluster with resource recovery, food systems and circular logistics.'
        problem='Food waste and inefficient distribution increase emissions, cost and food insecurity across urban food systems.'
        approach='Food rescue, surplus coordination and low-cost distribution infrastructure for edible food supply.'
        market='food rescue and circular food-access platform'
        stack='food rescue; surplus food; circular logistics; food access; affordability; waste reduction'
        transition='food-waste-and-inefficient-distribution-to-circular-food-access'
        output='food-system circularity platform'
        destination='food access, food waste reduction and urban food systems'
        materiality='medium-high'; note='Include as planetary-boundary food-waste infrastructure, not biotech.'
        url='https://newtopia.vc/portfolio/'; source='official_portfolio_profile'
        evidence='Newtopia official portfolio lists Nilus among its companies; public profiles describe food rescue / affordable food access.'
        confidence='0.72'
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
        scope_source='semantic_text_batch_05_2026_05_08'; evidence_source=$item.source
        notes=$item.note; confidence=$item.confidence
    }
}

$profiles | Export-Csv -LiteralPath $profilePath -NoTypeInformation -Encoding UTF8
$taxonomies | Export-Csv -LiteralPath $taxonomyPath -NoTypeInformation -Encoding UTF8

Write-Output 'Semantic text batch 05 applied.'
Write-Output ("Updated {0} high-risk semantic profiles." -f $batch.Count)
