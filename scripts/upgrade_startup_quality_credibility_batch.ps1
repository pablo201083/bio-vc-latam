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
            $row.$column = if ($Values.ContainsKey($column)) { $Values[$column] } else { '' }
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
$countryPath = Join-Path $Root 'quality\manual_startup_country_overrides.csv'

$profiles = @(Import-Csv -LiteralPath $profilePath)
$taxonomies = @(Import-Csv -LiteralPath $taxonomyPath)
$countries = @(Import-Csv -LiteralPath $countryPath)

$profileColumns = @('startup_id','startup_name','startup_summary_v1','business_one_liner','problem_addressed','technical_approach','industry_destination','materiality_signal','thesis_scope_note','source_url','source_type','source_date','evidence_excerpt','summary_confidence','review_status')
$taxonomyColumns = @('startup_id','startup_name','macro_theme','emergent_theme','market_label','technical_stack','transition_function','output_class','feedstock','industry_destination','market_interface','scope_decision','scope_reason','scope_source','evidence_source','notes','confidence')
$countryColumns = @('startup_id','startup_name','structured_country','country_basis','source_url','source_date','notes')

$batch = @(
    @{
        startup_id='123seguro'; startup_name='123Seguro'; country='AR'; country_basis='official_website_latam_insurance_marketplace'
        scope_decision='exclude'; scope_reason='insurance_marketplace_no_material_bio_or_planetary_boundary_signal'; confidence='0.88'
        macro_theme='peripheral or non-core digital ventures'; emergent_theme='digital coordination and market infrastructure'; market_label='online insurance marketplace'
        technical_stack='insurance comparison; online quote flow; digital brokerage'; transition_function='offline-insurance-shopping-to-digital-marketplace'
        output_class='insurance marketplace'; industry_destination='consumer and SME insurance'; market_interface='B2C/B2B marketplace'
        summary='Argentine/LatAm online insurance marketplace focused on comparing and buying insurance products such as car, home, personal accident and related coverage. It is a credible venture-backed digital business, but current public evidence shows insurance distribution and brokerage rather than biology, biobased materials, biocentric production systems or planetary-boundary stewardship. It should remain outside BIO VC LATAM as a non-material fintech/insurtech adjacent to the broader VC ecosystem.'
        one_liner='Online insurance comparison and brokerage marketplace.'
        problem='Fragmented insurance discovery, quoting and purchasing.'
        approach='Digital marketplace and quote flow for insurance products.'
        destination='Insurance and financial services.'
        materiality='low'
        note='Exclude: relevant to LATAM VC, but no material BIO, biological-system or planetary-boundary role in public evidence.'
        source_url='https://www.123seguro.com/'; source_type='official_website'
        evidence='Official website presents 123Seguro as an online insurance marketplace for comparing and buying insurance products.'
    },
    @{
        startup_id='amaro'; startup_name='Amaro'; country='BR'; country_basis='official_website_brazil_fashion_retail'
        scope_decision='exclude'; scope_reason='fashion_ecommerce_no_material_bio_or_regenerative_signal'; confidence='0.90'
        macro_theme='peripheral or non-core digital ventures'; emergent_theme='digital commerce and consumer platforms'; market_label='fashion e-commerce'
        technical_stack='e-commerce; digital retail; logistics; consumer brand'; transition_function='offline-fashion-retail-to-digital-commerce'
        output_class='fashion retail platform'; industry_destination='consumer fashion retail'; market_interface='B2C commerce'
        summary='Brazilian fashion and lifestyle e-commerce brand selling apparel, basics, swimwear, jeans, accessories and related consumer products through a digital retail experience. It belongs in a broad LATAM VC landscape, but not in the BIO VC LATAM thesis: public evidence points to consumer fashion retail rather than biobased materials, circular textile innovation, biological manufacturing or planetary-boundary stewardship. It should stay excluded unless future evidence shows a specific biomaterials or regenerative textile line.'
        one_liner='Brazilian fashion and lifestyle e-commerce brand.'
        problem='Digital access and merchandising for consumer fashion.'
        approach='Online storefront, product catalog, logistics and consumer-brand operations.'
        destination='Fashion retail.'
        materiality='low'
        note='Exclude: fashion commerce, not biomaterials or regenerative textile technology in current evidence.'
        source_url='https://amaro.com/'; source_type='official_website'
        evidence='Official site shows AMARO as a fashion retail store with categories such as clothing, jeans, swimwear, basics and collections.'
    },
    @{
        startup_id='barte'; startup_name='Barte'; country='BR'; country_basis='official_website_sao_paulo_address'
        scope_decision='exclude'; scope_reason='payments_and_corporate_banking_no_material_bio_signal'; confidence='0.92'
        macro_theme='peripheral or non-core digital ventures'; emergent_theme='digital finance and payments infrastructure'; market_label='B2B payment infrastructure'
        technical_stack='payments orchestration; acquiring-as-a-service; corporate banking; fraud controls; APIs'; transition_function='manual-payment-operations-to-digital-financial-infrastructure'
        output_class='payments and banking infrastructure'; industry_destination='fintech and enterprise finance'; market_interface='B2B SaaS/API'
        summary='Brazilian B2B payments infrastructure company offering omnichannel payments, custom checkout, receivables management, acquiring-as-a-service, corporate banking, fraud controls, reconciliation and financial dashboards for large companies and fintechs. It is well sourced and relevant to LATAM fintech, but current evidence shows horizontal financial infrastructure rather than BIO VC LATAM materiality. It remains excluded because it does not operate on biological systems, biobased products or planetary-boundary stewardship.'
        one_liner='B2B payments, acquiring and corporate banking infrastructure.'
        problem='Complex payment acceptance, reconciliation, fraud and treasury workflows.'
        approach='Modular payments, acquiring-as-a-service and banking APIs/platform tools.'
        destination='Fintech and enterprise finance.'
        materiality='low'
        note='Exclude: strong fintech company, but no BIO/material/planetary-boundary thesis fit.'
        source_url='https://www.barte.com/'; source_type='official_website'
        evidence='Official site describes Barte as payment infrastructure for large companies and fintechs, including omnichannel payments, acquiring-as-a-service and corporate banking.'
    },
    @{
        startup_id='cobli'; startup_name='Cobli'; country='BR'; country_basis='official_website_brazil_fleet_platform'
        scope_decision='exclude'; scope_reason='fleet_telemetry_efficiency_but_no_bio_or_planetary_thesis_core'; confidence='0.84'
        macro_theme='peripheral or non-core digital ventures'; emergent_theme='mobility and logistics efficiency software'; market_label='fleet management and telematics'
        technical_stack='vehicle tracking; video telemetry; CAN telemetry; mobile apps; AI driver-risk detection'; transition_function='manual-fleet-management-to-data-driven-logistics-efficiency'
        output_class='fleet telematics platform'; industry_destination='logistics and fleet operations'; market_interface='B2B SaaS/hardware'
        summary='Brazilian fleet-management and telematics platform that helps companies track vehicles, monitor driver behavior, reduce fuel and maintenance costs, improve safety and manage fleet operations through video telemetry, CAN telemetry, mobile apps and analytics. It may support operational efficiency and lower emissions indirectly, but it is not specifically biobased, biocentric or a planetary-boundary stewardship company. It should stay excluded from BIO VC LATAM while remaining a useful example of adjacent climate-efficiency software.'
        one_liner='Fleet tracking, video telemetry and logistics-efficiency platform.'
        problem='Low visibility, safety risk and operational inefficiency in vehicle fleets.'
        approach='Vehicle tracking, video telemetry, telemetry data and mobile workflows.'
        destination='Logistics and fleet operations.'
        materiality='low-medium'
        note='Exclude: indirect efficiency signal is not enough for BIO thesis without biological/material/planetary-boundary specificity.'
        source_url='https://www.cobli.co/'; source_type='official_website'
        evidence='Official site describes Cobli as a fleet platform with video telemetry, telemetry and mobile apps to reduce costs and improve productivity and safety.'
    },
    @{
        startup_id='tissue_dynamics'; startup_name='Tissue Dynamics'; country='IL'; country_basis='official_website_locations'
        scope_decision='exclude'; scope_reason='non_latam_biotech_company_despite_strong_bio_relevance'; confidence='0.94'
        macro_theme='therapeutics and regenerative medicine'; emergent_theme='organ models and drug discovery platforms'; market_label='human organoid drug-discovery platform'
        technical_stack='human organoids; AI; robotic automation; metabolic sensors; drug discovery'; transition_function='animal-and-static-assays-to-human-organoid-drug-discovery'
        output_class='drug discovery and toxicology platform'; industry_destination='pharma and biotech R&D'; market_interface='B2B platform/services'
        summary='Tissue Dynamics is a therapeutics and drug-discovery company using AI, human organoids, robotic automation and real-time sensor platforms to generate human-relevant safety, efficacy and patient-response data. It is clearly biotech and would fit a global bio map, but it should remain outside BIO VC LATAM because the company publicly lists locations in France and Israel, not a LATAM base or founding signal in our current evidence. This is a high-quality exclude, not a weak digital stub.'
        one_liner='Human organoid and AI platform for drug discovery and toxicology.'
        problem='Poor translation from traditional preclinical models to human drug response.'
        approach='Human organoids, robotics, sensors and AI software for drug discovery and toxicology.'
        destination='Pharma and biotech R&D.'
        materiality='high'
        note='Exclude only on geography, not on bio relevance: strong biotech but no LATAM base in current evidence.'
        source_url='https://www.tissuedynamics.com/'; source_type='official_website'
        evidence='Official site describes real-time organ physiology, AI platforms, human organoids, robotic automation and lists locations in France and Israel.'
    },
    @{
        startup_id='hybridon'; startup_name='Hybridon'; country='AR'; country_basis='public_biotech_profile_argentina'
        scope_decision='include'; scope_reason='bioactive_materials_and_antimicrobial_nanotechnology_signal'; confidence='0.80'
        macro_theme='biobased chemistry and advanced materials'; emergent_theme='bioactive materials and surface technologies'; market_label='antimicrobial nanomaterials'
        technical_stack='nanotechnology; antimicrobial materials; bioactive coatings; materials science'; transition_function='passive-surfaces-to-bioactive-antimicrobial-materials'
        output_class='bioactive material technology'; industry_destination='health, textiles and surface materials'; market_interface='B2B materials technology'
        summary='Argentine materials-science startup developing antimicrobial nanotechnology and bioactive surface/material applications. The current evidence is not yet as deep as a full company technical profile, but it is materially closer to the BIO VC LATAM thesis than to generic software: its value proposition is a physical antimicrobial technology for health, textiles or surface-material use cases. It should move from provisional exclude to include-under-review as a bioactive materials and advanced-materials case, with follow-up needed to confirm product maturity and exact biological mechanism.'
        one_liner='Antimicrobial nanotechnology for bioactive materials and surfaces.'
        problem='Microbial contamination and infection risk in surfaces, textiles and health-adjacent materials.'
        approach='Nanotechnology-enabled antimicrobial material or coating applications.'
        destination='Health, textiles and surface materials.'
        materiality='medium-high'
        note='Promote from stub exclude to include-under-review because public signal is material and bioactive rather than generic digital.'
        source_url='https://hybridon.com.ar/'; source_type='official_website_or_public_profile'
        evidence='Public web evidence describes Hybridon as an Argentine antimicrobial nanotechnology/materials startup; needs deeper technical source follow-up.'
    }
)

foreach ($item in $batch) {
    $profiles = Upsert-Row -Rows $profiles -KeyColumn 'startup_id' -KeyValue $item.startup_id -Columns $profileColumns -Values @{
        startup_id=$item.startup_id; startup_name=$item.startup_name; startup_summary_v1=$item.summary; business_one_liner=$item.one_liner
        problem_addressed=$item.problem; technical_approach=$item.approach; industry_destination=$item.destination; materiality_signal=$item.materiality
        thesis_scope_note=$item.note; source_url=$item.source_url; source_type=$item.source_type; source_date='2026-05-08'
        evidence_excerpt=$item.evidence; summary_confidence='high'; review_status='reviewed'
    }
    $taxonomies = Upsert-Row -Rows $taxonomies -KeyColumn 'startup_id' -KeyValue $item.startup_id -Columns $taxonomyColumns -Values @{
        startup_id=$item.startup_id; startup_name=$item.startup_name; macro_theme=$item.macro_theme; emergent_theme=$item.emergent_theme; market_label=$item.market_label
        technical_stack=$item.technical_stack; transition_function=$item.transition_function; output_class=$item.output_class; feedstock=''
        industry_destination=$item.destination; market_interface=$item.market_interface; scope_decision=$item.scope_decision; scope_reason=$item.scope_reason
        scope_source='manual_credibility_cleanup_2026_05_08'; evidence_source=$item.source_type; notes=$item.note; confidence=$item.confidence
    }
    $countries = Upsert-Row -Rows $countries -KeyColumn 'startup_id' -KeyValue $item.startup_id -Columns $countryColumns -Values @{
        startup_id=$item.startup_id; startup_name=$item.startup_name; structured_country=$item.country; country_basis=$item.country_basis
        source_url=$item.source_url; source_date='2026-05-08'; notes=$item.note
    }
}

$profiles | Export-Csv -LiteralPath $profilePath -NoTypeInformation -Encoding UTF8
$taxonomies | Export-Csv -LiteralPath $taxonomyPath -NoTypeInformation -Encoding UTF8
$countries | Export-Csv -LiteralPath $countryPath -NoTypeInformation -Encoding UTF8

Write-Output 'Startup credibility cleanup batch applied.'
Write-Output 'Updated 4 weak excludes, 1 high-quality non-LATAM bio exclude, and 1 include-under-review promotion.'
