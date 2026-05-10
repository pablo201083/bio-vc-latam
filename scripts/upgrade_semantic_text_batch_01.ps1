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
        id='um_grau_e_meio'; name='Um Grau e Meio'; macro='climate, energy and resource systems'; theme='planetary monitoring and resilience systems'
        one='AI wildfire detection and forest-monitoring platform.'
        summary='Brazilian B Corp deploying AI, high-resolution cameras and rapid-alert workflows to detect wildfire spots in seconds across forests, native vegetation, the Amazon and Pantanal. It belongs inside BIO VC LATAM as planetary-boundary and biocentric infrastructure: not biotech, but direct protection of living ecosystems, carbon stocks, biodiversity and land resilience.'
        problem='Slow wildfire detection and weak rapid-response infrastructure in forests and native areas.'
        approach='High-resolution cameras, AI fire-spot detection, monitoring infrastructure and alert workflows.'
        market='AI wildfire detection and forest-monitoring platform'
        stack='AI vision; high-resolution cameras; wildfire detection; forest monitoring; alert workflows; conservation monitoring'
        transition='slow-wildfire-response-to-real-time-forest-fire-detection-and-ecosystem-protection'
        output='ecosystem risk-monitoring and fire-detection infrastructure'
        destination='forest conservation, wildfire prevention and climate resilience'
        materiality='high'
        note='Include as planetary-boundary stewardship infrastructure protecting forests, biodiversity and carbon-rich ecosystems.'
        url='https://theyieldlablatam.com/companies/um-grau-e-meio/'; source='official_portfolio_profile'
        evidence='The Yield Lab profile describes high-resolution camera monitoring that automatically identifies fire spots in seconds and has monitored millions of hectares in forests, native areas, Amazon and Pantanal.'
        confidence='0.86'
    },
    @{
        id='outpost'; name='Outpost'; macro='computational biology and scientific software'; theme='computational biology and life-science software'
        one='Closed-loop microbiome predictive-biology platform.'
        summary='Outpost is a TechBio company making human microbiology computable by pairing wet-lab microbiology with machine learning and foundation-model style predictive systems. Its closed-loop engine is aimed at microbiome R&D, predictive medicine and biotech or consumer-health product development. It belongs inside BIO VC LATAM as computational biology infrastructure for living microbial ecosystems.'
        problem='Microbiome R&D is slow, empirical and difficult to predict across complex microbial ecosystems.'
        approach='Closed-loop wet-lab microbiology, machine learning and predictive microbial-ecosystem models.'
        market='microbiome foundation models and predictive biology'
        stack='wet-lab microbiology; machine learning; foundation models; microbiome modeling; predictive biology'
        transition='trial-and-error-microbiome-r-and-d-to-predictive-biology'
        output='microbiome predictive-biology platform'
        destination='biotech, pharma and consumer-health R&D'
        materiality='high'
        note='Include as computational biology for microbial ecosystems, not generic software.'
        url='https://www.outpost.bio/'; source='official_website'
        evidence='Official site describes a closed-loop engine pairing wet-lab biology with machine learning to make microbial ecosystems computable and enable predictive medicine.'
        confidence='0.88'
    },
    @{
        id='future_biome'; name='Future Biome'; macro='food biotech and novel ingredients'; theme='food biofactories and functional ingredients'
        one='Fungi-based precision prebiotics for microbiome function.'
        summary='Future Biome develops fungi-based precision prebiotics designed to optimize microbiome function. The available GRIDX evidence is concise, but the semantic core is clear: functional ingredients, fungal biology and microbiome modulation for food, gut-health and wellness applications. It belongs inside BIO VC LATAM as a food-biotech and microbiome ingredient company rather than animal-protein or generic fermentation infrastructure.'
        problem='Generic gut-health products lack targeted microbiome-function mechanisms.'
        approach='Fungi-based precision prebiotic development for microbiome modulation.'
        market='fungi-based precision prebiotics'
        stack='fungi; microbiome optimization; precision prebiotics; functional ingredients'
        transition='generic-gut-health-products-to-precision-microbiome-function'
        output='fungi-derived precision prebiotic ingredient'
        destination='food, gut health and wellness'
        materiality='high'
        note='Include as food biotech and microbiome ingredient technology.'
        url='https://www.gridexponential.com/portfolio'; source='official_portfolio_profile'
        evidence='GRIDX portfolio describes optimizing microbiome function with fungi-based precision prebiotics.'
        confidence='0.78'
    },
    @{
        id='beeflow'; name='Beeflow'; macro='ag biologicals and crop resilience'; theme='data-driven pollination systems'
        one='Pollination science and bee-biotechnology company for agriculture.'
        summary='Beeflow combines crop science, bee biology, data analytics and proprietary bee-nutrition technologies to provide professional pollination services that improve fruit yield and quality. It belongs inside BIO VC LATAM as a biocentric ag-biologicals company: the product is not software alone, but managed biological pollination performance in specialty-crop production.'
        problem='Pollination is inconsistent, climate-sensitive and often treated as an unmanaged input in fruit production.'
        approach='Crop data, bee biology and proprietary nutritional technologies applied through professional pollination services.'
        market='bee-based pollination science for specialty crops'
        stack='bee biology; plant science; crop data; proprietary bee nutrition; pollination services'
        transition='unmanaged-pollination-to-biological-pollination-performance'
        output='managed biological pollination service'
        destination='fruit and specialty crop agriculture'
        materiality='high'
        note='Include as direct intervention on living pollination systems and crop resilience.'
        url='https://www.beeflow.com/about-us'; source='official_website'
        evidence='Official site describes a biotechnology company providing professional pollination services using crop data and proprietary bee nutritional technologies.'
        confidence='0.90'
    },
    @{
        id='nanoprox'; name='NanoproX'; macro='diagnostics and medtech'; theme='nanomedicine and oncology devices'
        one='Bismuth-sulfide nanoparticle radiosensitizer for oncology.'
        summary='NanoproX develops bismuth-sulfide nanoparticles that act as radiosensitizers to increase radiotherapy effectiveness and reduce adverse effects, especially for hard-to-access tumors. It belongs inside BIO VC LATAM as oncology nanomedicine and medical technology: a physical nanoparticle intervention coupled to cancer treatment, not an agricultural or generic materials case.'
        problem='Radiotherapy can have limited efficacy and significant adverse effects in difficult tumors.'
        approach='Bismuth-sulfide nanoparticles for targeted radiosensitization during cancer radiotherapy.'
        market='nanotech-enhanced radiotherapy platform'
        stack='bismuth sulfide nanoparticles; targeted radiosensitization; oncology nanomedicine; radiotherapy'
        transition='low-efficacy-radiotherapy-to-more-precise-cancer-treatment'
        output='oncology nanoparticle radiosensitizer'
        destination='oncology and radiotherapy providers'
        materiality='high'
        note='Include as therapeutic medtech/nanomedicine for cancer treatment.'
        url='https://www.nanoprox.com/'; source='official_website'
        evidence='Official site describes bismuth sulfide nanoparticles that increase radiotherapy effectiveness and reduce adverse effects, especially in hard-to-access tumors.'
        confidence='0.88'
    },
    @{
        id='nanotica'; name='Nanotica'; macro='precision agriculture and resource intelligence'; theme='ag-input delivery and nanoencapsulation'
        one='In-field nanoencapsulation system for agricultural inputs.'
        summary='Nanotica develops in-field nanoencapsulation systems for crop inputs. Its nanotizer machine and empty capsules let farmers encapsulate agrochemicals at the moment of application, aiming to lower doses, reduce pollution, improve delivery into plant tissues and improve farm economics. It belongs inside BIO VC LATAM as precision input-delivery infrastructure, not as biological-input manufacturing.'
        problem='Conventional agrochemical application often requires high doses and causes inefficient delivery or pollution.'
        approach='Nanotizer equipment and capsules for in-situ nanoencapsulation of crop-protection inputs.'
        market='ag-input nanoencapsulation technology'
        stack='nanotechnology; nanoencapsulation; agrochemical delivery; crop protection; farm equipment'
        transition='high-dose-agrochemical-application-to-lower-dose-precision-delivery'
        output='in-field nanoencapsulation equipment and capsules'
        destination='agriculture and crop protection'
        materiality='medium-high'
        note='Include as precision agricultural input-delivery infrastructure; keep distinct from microbial bioinputs.'
        url='https://nanotica.com.ar/en/'; source='official_website'
        evidence='Official site says Nanotica developed nanoencapsulation technology to lower agrochemical doses, reduce pollution and improve food safety, using a nanotizer machine and empty capsules for in-situ pesticide nanoencapsulation.'
        confidence='0.90'
    },
    @{
        id='puna_bio'; name='Puna Bio'; macro='ag biologicals and crop resilience'; theme='extremophile microbial ag inputs'
        one='Extremophile microbial seed treatments for crop resilience.'
        summary='Puna Bio develops microbial seed-treatment inoculants from extremophile microorganisms isolated from the Argentine Puna. Its R&D platform prospects extreme ecosystems, isolates and characterizes strains, maintains a culture collection and validates field performance to improve crop nutrition, stress tolerance, yield and soil regeneration. It is a core BIO VC LATAM ag-biologicals company.'
        problem='Crops need better resilience, nutrition and soil performance under stress.'
        approach='Extremophile microbiology, strain isolation, culture collections and field-validated microbial seed treatments.'
        market='extremophile microbial inoculants for row crops'
        stack='extremophile microbiology; microbial inoculants; seed treatment; field trials; soil regeneration'
        transition='chemical-or-stress-limited-crop-production-to-microbial-crop-resilience'
        output='microbial seed-treatment inoculant'
        destination='seeds, row crops and regenerative agriculture'
        materiality='high'
        note='Include as core microbial bioinput technology for crop resilience and soil regeneration.'
        url='https://www.puna.bio/en'; source='official_website'
        evidence='Official site describes extremophile bacteria from the Argentine Puna used to develop seed-treatment microbial inoculants that enhance crop performance and regenerate soils, with a culture collection and field trials.'
        confidence='0.94'
    },
    @{
        id='plamic'; name='Plamic'; macro='therapeutics and regenerative medicine'; theme='microfluidic nanomedicine manufacturing'
        one='Microfluidic lab-on-a-chip platform for nanomedicine manufacturing.'
        summary='PLAMIC develops microfluidic lab-on-a-chip systems to design, manufacture and characterize nanoscale drug-delivery formulations for health applications. Public sources frame its problem as low reproducibility, reagent waste and difficult scale-up in conventional nanomedicine manufacturing. It belongs inside BIO VC LATAM as biomedical process infrastructure for nanomedicine, not as crop or ag-input technology.'
        problem='Nanomedicine manufacturing suffers from low reproducibility, high reagent waste and scale-up difficulty.'
        approach='Microfluidic lab-on-a-chip systems for controlled nanomedicine design, production and characterization.'
        market='microfluidic nanomedicine manufacturing platform'
        stack='microfluidics; lab-on-a-chip; nanomedicine; drug delivery; formulation characterization'
        transition='batch-nanomedicine-production-to-controlled-microfluidic-manufacturing'
        output='microfluidic nanomedicine manufacturing platform'
        destination='health and pharmaceutical manufacturing'
        materiality='high'
        note='Include as biomedical process and drug-delivery manufacturing infrastructure.'
        url='https://www.argentina.gob.ar/ciencia/seppCTI/desarrollo-tecnologico-e-innovacion/diseno-fabricacion-y-caracterizacion-de-chips-o'; source='government_public_profile'
        evidence='Argentina.gob.ar describes PLAMIC as a microfluidic platform for designing, manufacturing and characterizing lab-on-a-chip systems for health applications and nanomedicine production.'
        confidence='0.86'
    },
    @{
        id='auravant'; name='Auravant'; macro='precision agriculture and resource intelligence'; theme='precision agriculture intelligence'
        one='Precision agriculture and agronomic decision platform.'
        summary='Auravant provides precision-agriculture software that combines agronomic models, satellite imagery, georeferenced layers, operational records and traceability workflows for crop production. It belongs inside BIO VC LATAM as an intelligence layer for biological production systems: software, but directly coupled to field decisions, sustainability, yield and traceable management of material agriculture.'
        problem='Farm decisions are fragmented across field data, imagery, records and operational workflows.'
        approach='Agronomic models, satellite imagery, georeferenced layers and traceability tools for crop operations.'
        market='precision agriculture and agronomic decision platform'
        stack='agronomic models; satellite imagery; georeferenced layers; operational traceability; crop analytics'
        transition='fragmented-field-data-to-traceable-precision-decisions'
        output='precision agriculture decision platform'
        destination='agriculture and agribusiness'
        materiality='medium-high'
        note='Include as digital infrastructure tightly coupled to crop production systems.'
        url='https://www.auravant.com/en/about-us/'; source='official_website'
        evidence='Official site describes precision agriculture, agronomic models, satellite imagery and traceability to make crop production more efficient, sustainable and economically viable.'
        confidence='0.88'
    },
    @{
        id='viewmind'; name='ViewMind'; macro='diagnostics and medtech'; theme='clinical diagnostics and medical devices'
        one='Ocular digital phenotyping for neurocognitive diagnostics.'
        summary='ViewMind develops neurocognitive diagnostics based on ocular digital phenotyping, measuring eye-movement responses to assess cognitive status and specific brain-health domains. Its technology supports diagnosis, monitoring and therapy-development workflows in neurology and pharma studies. It belongs inside BIO VC LATAM as non-invasive clinical diagnostics and medical-device infrastructure.'
        problem='Neurocognitive assessment is often late, subjective, invasive or hard to scale.'
        approach='Eye tracking, ocular digital phenotyping and statistical brain-health models.'
        market='ocular digital phenotyping for neurocognitive health'
        stack='eye tracking; ocular digital phenotyping; statistical brain-health models; neurodiagnostics'
        transition='late-invasive-cognitive-assessment-to-scalable-non-invasive-neurodiagnostics'
        output='neurocognitive diagnostic device/software platform'
        destination='brain health, neurology and pharma studies'
        materiality='high'
        note='Include as clinical diagnostics/medtech for brain health.'
        url='https://www.viewmind.com/about/'; source='official_website'
        evidence='Official site describes ocular digital phenotyping technology to assess cognitive status through eye movement responses and specific cognitive domains.'
        confidence='0.88'
    },
    @{
        id='wiagro'; name='Wiagro'; macro='precision agriculture and resource intelligence'; theme='post-harvest monitoring and traceability'
        one='Post-harvest grain monitoring and traceability platform.'
        summary='Wiagro monitors stored grain and silo bags using sensors, satellite connectivity, environmental data, predictive models and digital traceability. Its Smart Silobag system is designed to prevent post-harvest losses, improve proof of origin and give producers or grain operators real-time visibility. It belongs inside BIO VC LATAM as crop-supply-chain resilience infrastructure.'
        problem='Stored grain can suffer post-harvest losses, low visibility and weak proof of origin.'
        approach='Sensors, satellite connectivity, predictive models, traceability software and blockchain-enabled records.'
        market='post-harvest grain monitoring and traceability'
        stack='sensors; satellite connectivity; predictive models; traceability platform; blockchain; grain monitoring'
        transition='post-harvest-loss-and-low-visibility-to-real-time-grain-monitoring'
        output='post-harvest grain monitoring system'
        destination='agriculture and grain supply chains'
        materiality='medium-high'
        note='Include as monitoring and traceability infrastructure for biological crop supply chains.'
        url='https://www.wiagro.com/'; source='official_website'
        evidence='Official site says Smart Silobag combines sensor data, environmental information and predictive models to prevent post-harvest loss, improve traceability and provide proof of origin.'
        confidence='0.88'
    },
    @{
        id='solfium'; name='Solfium'; macro='climate, energy and resource systems'; theme='distributed clean-energy deployment'
        one='Solar, storage and e-mobility deployment platform for value-chain decarbonization.'
        summary='Solfium provides solar energy, storage and e-mobility solutions for homes, companies, industrial clients and corporate value chains, with an explicit model for decarbonization. It is not bio-based, but fits the broader planetary-boundary perimeter as clean-energy deployment infrastructure that can reduce emissions across material supply chains.'
        problem='Homes and companies face fragmented adoption of solar, storage and e-mobility solutions.'
        approach='Solar deployment, storage, e-mobility solutions and corporate value-chain decarbonization programs.'
        market='distributed solar, storage and e-mobility platform'
        stack='solar deployment; energy storage; e-mobility; value-chain decarbonization'
        transition='fossil-energy-dependence-to-distributed-clean-energy-adoption'
        output='distributed clean-energy deployment platform'
        destination='energy transition, solar, storage and e-mobility'
        materiality='medium'
        note='Include as planetary-boundary transition infrastructure, not as biotech.'
        url='https://solfium.com/en/'; source='official_website'
        evidence='Official site describes Solfium as a partner in solar energy, storage and e-mobility, including a corporate model to decarbonize value chains.'
        confidence='0.82'
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
        scope_source='semantic_text_batch_01_2026_05_08'; evidence_source=$item.source
        notes=$item.note; confidence=$item.confidence
    }
}

$profiles | Export-Csv -LiteralPath $profilePath -NoTypeInformation -Encoding UTF8
$taxonomies | Export-Csv -LiteralPath $taxonomyPath -NoTypeInformation -Encoding UTF8

Write-Output 'Semantic text batch 01 applied.'
Write-Output ("Updated {0} high-risk semantic profiles." -f $batch.Count)
