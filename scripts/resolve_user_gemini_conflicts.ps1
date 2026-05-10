param(
    [string]$Root = "C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Upsert-CsvById {
    param(
        [string]$Path,
        [object[]]$Rows
    )

    $existing = if (Test-Path -LiteralPath $Path) { Import-Csv -LiteralPath $Path } else { @() }
    $map = @{}
    foreach ($row in $existing) {
        $map[[string]$row.startup_id] = $row
    }
    foreach ($row in $Rows) {
        $map[[string]$row.startup_id] = $row
    }
    $map.Values | Sort-Object startup_name | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
}

$taxonomyRows = @(
    [pscustomobject]@{
        startup_id='webee'
        startup_name='Webee'
        macro_theme='peripheral or non-core digital ventures'
        emergent_theme='digital coordination and market infrastructure'
        market_label='industrial IoT and AI for manufacturing'
        technical_stack='industrial IoT; computer vision; predictive maintenance; industrial AI'
        transition_function='manual-industrial-operations-to-data-driven-manufacturing-optimization'
        output_class='industrial software platform'
        feedstock='industrial operations data'
        industry_destination='manufacturing'
        market_interface='B2B platform'
        scope_decision='exclude'
        scope_reason='official_site_signal_non_thesis_industrial_software'
        scope_source='webee_official_site'
        evidence_source='webee_official_site_2026'
        notes='Official site describes AI and IIoT optimization for smart factories, manufacturing, assets, energy and water, but not a bio-based, biocentric or nature-restoration company.'
        confidence='0.90'
    }
    [pscustomobject]@{
        startup_id='circular'
        startup_name='Circular'
        macro_theme='peripheral or non-core digital ventures'
        emergent_theme='digital coordination and market infrastructure'
        market_label='professional network and recruiting platform'
        technical_stack='professional network; recruiting marketplace'
        transition_function='legacy-recruiting-to-digital-network-platform'
        output_class='software platform'
        feedstock='professional network data'
        industry_destination='recruiting and talent'
        market_interface='platform'
        scope_decision='exclude'
        scope_reason='official_site_signal_full_digital_no_materiality'
        scope_source='circular_official_site'
        evidence_source='user_gemini_candidate_2026'
        notes='User-provided candidate and official site indicate a professional network and technical recruiting platform, without material or biocentric thesis fit.'
        confidence='0.92'
    }
    [pscustomobject]@{
        startup_id='clover'
        startup_name='Clover'
        macro_theme='peripheral or non-core digital ventures'
        emergent_theme='digital coordination and market infrastructure'
        market_label='IT infrastructure and enterprise solutions'
        technical_stack='IT infrastructure; networking; VoIP; security systems'
        transition_function='legacy-enterprise-it-to-managed-tech-services'
        output_class='enterprise software and services'
        feedstock='enterprise IT operations'
        industry_destination='enterprise IT'
        market_interface='services company'
        scope_decision='exclude'
        scope_reason='official_site_signal_full_digital_no_materiality'
        scope_source='clover_official_site'
        evidence_source='clover_official_site_2026'
        notes='Official site describes IT infrastructure, networking, security systems and enterprise technology services, not a thesis-core material or biocentric company.'
        confidence='0.94'
    }
    [pscustomobject]@{
        startup_id='conciencia'
        startup_name='Conciencia'
        macro_theme='peripheral or non-core digital ventures'
        emergent_theme='digital coordination and market infrastructure'
        market_label='education platform'
        technical_stack='edtech; soft skills development'
        transition_function='traditional-learning-to-digital-skills-platform'
        output_class='software platform'
        feedstock='education workflows'
        industry_destination='education'
        market_interface='platform'
        scope_decision='exclude'
        scope_reason='candidate_signal_edtech_non_thesis'
        scope_source='user_gemini_candidate_csv'
        evidence_source='user_gemini_candidate_2026'
        notes='User-provided candidate describes an edtech focused on soft skills and social awareness, not a thesis-core material or biocentric company.'
        confidence='0.83'
    }
    [pscustomobject]@{
        startup_id='crinsurance'
        startup_name='CRInsurance'
        macro_theme='peripheral or non-core digital ventures'
        emergent_theme='digital coordination and market infrastructure'
        market_label='credit insurance insurtech'
        technical_stack='insurance software; credit guarantees'
        transition_function='legacy-insurance-to-digital-credit-insurance'
        output_class='fintech / insurtech platform'
        feedstock='insurance and credit workflows'
        industry_destination='insurance'
        market_interface='platform'
        scope_decision='exclude'
        scope_reason='candidate_signal_insurtech_non_thesis'
        scope_source='user_gemini_candidate_csv'
        evidence_source='user_gemini_candidate_2026'
        notes='User-provided candidate describes an insurtech for credit insurance and guarantees, without thesis-core material or biocentric fit.'
        confidence='0.86'
    }
    [pscustomobject]@{
        startup_id='endless'
        startup_name='Endless'
        macro_theme='peripheral or non-core digital ventures'
        emergent_theme='digital coordination and market infrastructure'
        market_label='low-connectivity computing platform'
        technical_stack='operating system; connectivity software'
        transition_function='limited-connectivity-computing-to-accessible-software'
        output_class='software platform'
        feedstock='computing workflows'
        industry_destination='computing and education access'
        market_interface='platform'
        scope_decision='exclude'
        scope_reason='candidate_signal_non_thesis_software'
        scope_source='user_gemini_candidate_csv'
        evidence_source='user_gemini_candidate_2026'
        notes='User-provided candidate describes technology for accessible computing in low-connectivity areas, but not a thesis-core biobased, biocentric or planetary-systems company.'
        confidence='0.83'
    }
    [pscustomobject]@{
        startup_id='mavios'
        startup_name='Mavios'
        macro_theme='peripheral or non-core digital ventures'
        emergent_theme='digital coordination and market infrastructure'
        market_label='asset and inventory management platform'
        technical_stack='asset management software; inventory software'
        transition_function='manual-asset-management-to-digital-inventory-platform'
        output_class='software platform'
        feedstock='inventory and asset data'
        industry_destination='enterprise operations'
        market_interface='platform'
        scope_decision='exclude'
        scope_reason='candidate_signal_non_thesis_software'
        scope_source='user_gemini_candidate_csv'
        evidence_source='user_gemini_candidate_2026'
        notes='User-provided candidate describes technology for asset and inventory management, not a thesis-core biobased, biocentric or planetary-systems company.'
        confidence='0.84'
    }
    [pscustomobject]@{
        startup_id='splight'
        startup_name='Splight'
        macro_theme='climate, energy and resource systems'
        emergent_theme='climate and resource intelligence platforms'
        market_label='AI for renewable grid optimization'
        technical_stack='AI; DERMS; renewable energy forecasting; grid optimization'
        transition_function='congested-fossil-dependent-grids-to-better-renewable-integration'
        output_class='climate intelligence platform'
        feedstock='grid and renewable energy data'
        industry_destination='electricity grids and renewable energy'
        market_interface='B2B platform'
        scope_decision='include'
        scope_reason='official_site_signal_planetary_systems_energy_transition'
        scope_source='splight_official_site'
        evidence_source='splight_official_site_2026'
        notes='Splight materials describe AI and DERMS for renewable integration, grid resilience and reduced curtailment; this is a valid planetary-systems / energy-transition case, not biomanufacturing.'
        confidence='0.89'
    }
)

$profileRows = @(
    [pscustomobject]@{
        startup_id='webee'
        startup_name='Webee'
        startup_summary_v1='Plataforma de IIoT e IA para manufactura, mantenimiento predictivo y optimizacion operativa en smart factories. Queda afuera por no ser una startup biobasada, biocentrica ni de restauracion de sistemas planetarios.'
        business_one_liner='Industrial IoT and AI platform for manufacturing operations.'
        problem_addressed='Ineficiencias operativas, downtime y costos en manufactura industrial.'
        technical_approach='IIoT, vision computacional, mantenimiento predictivo e inteligencia operacional.'
        industry_destination='Manufacturing'
        materiality_signal='low'
        thesis_scope_note='Queda afuera por software industrial generalista, aunque tenga modulos de energia y agua.'
        source_url='https://www.webee.io/'
        source_type='official_website'
        source_date='2026-04-21'
        evidence_excerpt='Official site describes AI and IIoT optimization for smart factories, monitoring assets, production, energy and water.'
        summary_confidence='high'
        review_status='reviewed'
    }
    [pscustomobject]@{
        startup_id='circular'
        startup_name='Circular'
        startup_summary_v1='Red profesional y plataforma de recruiting tecnico. Queda afuera por no tener acople material, biobasado o biocentrico.'
        business_one_liner='Professional network and recruiting platform.'
        problem_addressed='Fricciones en reclutamiento y networking profesional.'
        technical_approach='Plataforma digital de red profesional y talento.'
        industry_destination='Recruiting and talent'
        materiality_signal='low'
        thesis_scope_note='Queda afuera por full digital sin relacion con materialidad o limites planetarios.'
        source_url='https://circular.com'
        source_type='official_website'
        source_date='2026-04-21'
        evidence_excerpt='Candidate and official positioning indicate a professional network and technical recruiting platform.'
        summary_confidence='high'
        review_status='reviewed'
    }
    [pscustomobject]@{
        startup_id='clover'
        startup_name='Clover'
        startup_summary_v1='Empresa de infraestructura IT, networking, seguridad y telefonia IP para organizaciones. Queda afuera por no ser thesis-core.'
        business_one_liner='Enterprise IT infrastructure and technology services.'
        problem_addressed='Necesidades de infraestructura y soporte IT empresarial.'
        technical_approach='Infraestructura IT, redes, seguridad y servicios tecnologicos.'
        industry_destination='Enterprise IT'
        materiality_signal='low'
        thesis_scope_note='Queda afuera por ser servicios IT / enterprise tech sin acople material relevante para la tesis.'
        source_url='https://www.clover.com.ar/'
        source_type='official_website'
        source_date='2026-04-21'
        evidence_excerpt='Official site describes IT infrastructure, networking, hardware consulting, VoIP, security systems and servers.'
        summary_confidence='high'
        review_status='reviewed'
    }
    [pscustomobject]@{
        startup_id='conciencia'
        startup_name='Conciencia'
        startup_summary_v1='Edtech orientada a habilidades blandas y conciencia social. Queda afuera por no tener thesis fit material, biobasado ni biocentrico.'
        business_one_liner='Edtech for soft skills and social awareness.'
        problem_addressed='Necesidad de formacion en habilidades blandas.'
        technical_approach='Plataforma educativa digital.'
        industry_destination='Education'
        materiality_signal='low'
        thesis_scope_note='Queda afuera por edtech sin acople a sistemas materiales o vivos.'
        source_url='https://conciencia.education'
        source_type='candidate_website_from_user_csv'
        source_date='2026-04-21'
        evidence_excerpt='User-provided candidate describes an edtech focused on soft skills and social awareness.'
        summary_confidence='medium'
        review_status='seeded'
    }
    [pscustomobject]@{
        startup_id='crinsurance'
        startup_name='CRInsurance'
        startup_summary_v1='Insurtech especializada en seguros de credito y garantias. Queda afuera por no tener thesis fit material, biobasado ni biocentrico.'
        business_one_liner='Insurtech for credit insurance and guarantees.'
        problem_addressed='Gestion de seguros de credito y garantias.'
        technical_approach='Plataforma insurtech.'
        industry_destination='Insurance'
        materiality_signal='low'
        thesis_scope_note='Queda afuera por fintech/insurtech sin relacion con sistemas materiales o vivos.'
        source_url='https://crinsurance.com.br'
        source_type='candidate_website_from_user_csv'
        source_date='2026-04-21'
        evidence_excerpt='User-provided candidate describes CRInsurance as an insurtech for credit insurance and guarantees.'
        summary_confidence='medium'
        review_status='seeded'
    }
    [pscustomobject]@{
        startup_id='endless'
        startup_name='Endless'
        startup_summary_v1='Tecnologia para hacer la computacion mas accesible en areas con baja conectividad. Queda afuera por no ser thesis-core.'
        business_one_liner='Accessible computing for low-connectivity areas.'
        problem_addressed='Limitaciones de acceso a computacion en contextos de baja conectividad.'
        technical_approach='Software y sistemas de computacion accesible.'
        industry_destination='Computing and education access'
        materiality_signal='low'
        thesis_scope_note='Queda afuera por software / access tech sin acople material o biocentrico suficiente.'
        source_url='https://endlessos.org'
        source_type='candidate_website_from_user_csv'
        source_date='2026-04-21'
        evidence_excerpt='User-provided candidate describes Endless as technology for accessible computing in low-connectivity areas.'
        summary_confidence='medium'
        review_status='seeded'
    }
    [pscustomobject]@{
        startup_id='mavios'
        startup_name='Mavios'
        startup_summary_v1='Tecnologia para gestion de activos e inventarios. Queda afuera por no tener thesis fit material, biobasado ni biocentrico.'
        business_one_liner='Asset and inventory management platform.'
        problem_addressed='Gestion ineficiente de activos e inventarios.'
        technical_approach='Software de gestion de activos e inventarios.'
        industry_destination='Enterprise operations'
        materiality_signal='low'
        thesis_scope_note='Queda afuera por software horizontal sin relacion suficiente con la tesis.'
        source_url='https://mavios.com'
        source_type='candidate_website_from_user_csv'
        source_date='2026-04-21'
        evidence_excerpt='User-provided candidate describes Mavios as technology for asset and inventory management.'
        summary_confidence='medium'
        review_status='seeded'
    }
    [pscustomobject]@{
        startup_id='splight'
        startup_name='Splight'
        startup_summary_v1='Startup climate-tech que usa IA para optimizar redes electricas e integracion de energias renovables. Entra en tesis por climate, energy and resource systems.'
        business_one_liner='AI for grid optimization and renewable energy integration.'
        problem_addressed='Congestion, curtailment y menor resiliencia en redes con alta penetracion renovable.'
        technical_approach='AI, forecasting y DERMS para mejorar operacion de redes y recursos energéticos distribuidos.'
        industry_destination='Electricity grids and renewable energy'
        materiality_signal='high'
        thesis_scope_note='Entra como caso de transicion energetica y limites planetarios; no es bio, pero si thesis-relevant.'
        source_url='https://content.splight-ai.com/blog/ai-powered-grids-the-future-of-efficient-renewable-energy'
        source_type='official_website'
        source_date='2026-04-21'
        evidence_excerpt='Splight materials describe AI for renewable energy forecasting, DERMS, grid congestion reduction and resilience enhancement.'
        summary_confidence='high'
        review_status='reviewed'
    }
)

Upsert-CsvById -Path (Join-Path $Root 'quality\manual_startup_taxonomy_overrides.csv') -Rows $taxonomyRows
Upsert-CsvById -Path (Join-Path $Root 'quality\manual_startup_profile_overrides.csv') -Rows $profileRows

Write-Output "User Gemini conflicts resolved."
