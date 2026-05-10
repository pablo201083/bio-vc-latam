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
        startup_id='argentag'
        startup_name='ArgenTAG'
        macro_theme='computational biology and scientific software'
        emergent_theme='computational biology and life-science software'
        market_label='single-cell long-read sequencing platform'
        technical_stack='single-cell genomics; long-read sequencing; sequencing workflow software and tools'
        transition_function='high-cost-single-cell-sequencing-to-scalable-long-read-access'
        output_class='research tools platform'
        feedstock='single-cell sequencing workflows'
        industry_destination='biopharma, biomedical research and life-science labs'
        market_interface='research tools company'
        scope_decision='include'
        scope_reason='official_portfolio_signal_bio_based_or_biocentric'
        scope_source='sosv_indiebio_portfolio_official'
        evidence_source='sosv_company_profile_2026'
        notes='SOSV company page describes a scalable single-cell solution for long-read sequencers that democratizes single-cell sequencing.'
        confidence='0.89'
    }
    [pscustomobject]@{
        startup_id='nat4bio'
        startup_name='Nat4Bio'
        macro_theme='food biotech and novel ingredients'
        emergent_theme='food transition ingredients and proteins'
        market_label='edible anti-spoilage coatings for fruit'
        technical_stack='microbial fermentation; bacteria and fungi-derived edible coatings; food preservation biotech'
        transition_function='chemical-fungicides-and-waxes-to-natural-zero-residue-food-protection'
        output_class='food protection ingredient platform'
        feedstock='microbial fermentation compounds'
        industry_destination='fresh produce and food supply chains'
        market_interface='ingredient and food protection company'
        scope_decision='include'
        scope_reason='official_portfolio_signal_bio_based_or_biocentric'
        scope_source='sosv_indiebio_portfolio_official'
        evidence_source='sosv_company_profile_2026'
        notes='SOSV company page describes naturally-sourced zero-residue coatings for fresh fruit produced through microbial fermentation.'
        confidence='0.91'
    }
    [pscustomobject]@{
        startup_id='microterra'
        startup_name='MicroTerra'
        macro_theme='food biotech and novel ingredients'
        emergent_theme='food transition ingredients and proteins'
        market_label='aquatic plant functional ingredients'
        technical_stack='lemna cultivation; aquafarm integration; plant-based ingredient processing'
        transition_function='polluting-aquaculture-to-water-cleaning-functional-ingredient-production'
        output_class='functional ingredient platform'
        feedstock='lemna grown in aquaculture systems'
        industry_destination='plant-based food and food ingredients'
        market_interface='ingredient company'
        scope_decision='include'
        scope_reason='official_portfolio_signal_bio_based_or_biocentric'
        scope_source='sosv_indiebio_portfolio_official'
        evidence_source='sosv_company_profile_2026'
        notes='SOSV company page describes lemna-based functional ingredients grown alongside aquafarms, reducing water footprint and cleaning water.'
        confidence='0.90'
    }
    [pscustomobject]@{
        startup_id='kresko_rnatech'
        startup_name='Kresko RNAtech'
        macro_theme='food biotech and novel ingredients'
        emergent_theme='food transition ingredients and proteins'
        market_label='fresh-food bioactive RNA ingredients'
        technical_stack='bioactive RNA isolation; food extracts; functional ingredient stabilization'
        transition_function='rapidly-lost-food-bioactives-to-stable-health-relevant-ingredients'
        output_class='functional ingredient platform'
        feedstock='fresh fruits, vegetables, herbs, roots and milk-derived bioactive RNA'
        industry_destination='food, nutrition and gut health'
        market_interface='ingredient company'
        scope_decision='include'
        scope_reason='official_portfolio_signal_bio_based_or_biocentric'
        scope_source='sosv_indiebio_portfolio_official'
        evidence_source='sosv_company_profile_2026'
        notes='SOSV company page describes isolating supernutrient bioactive RNAs from fresh foods and stabilizing them into extracts.'
        confidence='0.88'
    }
    [pscustomobject]@{
        startup_id='unibaio'
        startup_name='Unibaio'
        macro_theme='ag biologicals and crop resilience'
        emergent_theme='ag biologicals and crop resilience'
        market_label='natural microparticles for agro-input performance'
        technical_stack='natural polymers; microparticles; crop input delivery'
        transition_function='high-runoff-agrochemicals-to-more-efficient-biological-and-chemical-input-delivery'
        output_class='ag-input enabling platform'
        feedstock='agrochemical and biological crop protectant formulations'
        industry_destination='agriculture'
        market_interface='ag technology platform'
        scope_decision='include'
        scope_reason='official_portfolio_signal_bio_based_or_biocentric'
        scope_source='sosv_indiebio_portfolio_official'
        evidence_source='sosv_company_profile_2026'
        notes='SOSV company page describes natural microparticles that improve penetration of crop protectants and reduce agrochemical doses up to 80%.'
        confidence='0.90'
    }
)

$profileRows = @(
    [pscustomobject]@{
        startup_id='argentag'
        startup_name='ArgenTAG'
        startup_summary_v1='Startup de herramientas genómicas que desarrolla una solución escalable de single-cell sequencing para secuenciadores long-read. Entra en tesis por computational biology and scientific software.'
        business_one_liner='Scalable single-cell long-read sequencing platform.'
        problem_addressed='El single-cell sequencing sigue siendo caro y dependiente de secuenciadores de alto costo, limitando su adopción en laboratorios.'
        technical_approach='Solución para realizar single-cell sequencing sobre secuenciadores DNA long-read más accesibles.'
        industry_destination='Biopharma, biomedical research and life-science labs'
        materiality_signal='high'
        thesis_scope_note='Entra por plataforma clara de bioinformática e instrumental para investigación biomédica, no por software generalista.'
        source_url='https://sosv.com/company/argentag/'
        source_type='official_company_profile'
        source_date='2026-04-21'
        evidence_excerpt='SOSV states that ArgenTAG developed the first truly scalable single-cell solution for long-read sequencers and changed the economics of single-cell sequencing.'
        summary_confidence='high'
        review_status='reviewed'
    }
    [pscustomobject]@{
        startup_id='nat4bio'
        startup_name='Nat4Bio'
        startup_summary_v1='Startup food biotech que desarrolla recubrimientos comestibles, naturales y sin residuos para proteger frutas del deterioro. Entra en tesis por food biotech and novel ingredients.'
        business_one_liner='Natural zero-residue edible coatings for fresh fruit.'
        problem_addressed='Dependencia de ceras y fungicidas químicos para extender la vida útil de frutas frescas.'
        technical_approach='Fermentación microbiana de bacterias y hongos para producir compuestos aplicados como recubrimientos comestibles.'
        industry_destination='Fresh produce and food supply chains'
        materiality_signal='high'
        thesis_scope_note='Entra por biotecnología alimentaria, preservación natural y reducción de desperdicio en cadenas materiales de alimentos.'
        source_url='https://sosv.com/company/nat4bio/'
        source_type='official_company_profile'
        source_date='2026-04-21'
        evidence_excerpt='SOSV describes naturally-sourced and zero-residue coatings that protect fruit from spoilage, produced through microbial fermentation of bacteria and fungi.'
        summary_confidence='high'
        review_status='reviewed'
    }
    [pscustomobject]@{
        startup_id='microterra'
        startup_name='MicroTerra'
        startup_summary_v1='Startup de ingredientes funcionales plant-based que cultiva lemna en acuifarms para producir ingredientes alimentarios mientras limpia agua y reduce huella hídrica. Entra en tesis por food biotech and novel ingredients.'
        business_one_liner='Water-cleaning plant-based functional ingredients from lemna.'
        problem_addressed='Necesidad de ingredientes plant-based más sustentables y sistemas alimentarios con menor uso y contaminación de agua.'
        technical_approach='Cultivo de lemna junto a granjas acuícolas para transformar nutrientes residuales en ingredientes funcionales.'
        industry_destination='Plant-based food and food ingredients'
        materiality_signal='high'
        thesis_scope_note='Entra por ingrediente biobasado con fuerte vínculo a circularidad hídrica, alimentos y límites planetarios.'
        source_url='https://sosv.com/company/microterra/'
        source_type='official_company_profile'
        source_date='2026-04-21'
        evidence_excerpt='SOSV says microTERRA grows lemna with aquafarms to create plant-based ingredients, cleaner aquafarm water and a reduced water footprint.'
        summary_confidence='high'
        review_status='reviewed'
    }
    [pscustomobject]@{
        startup_id='kresko_rnatech'
        startup_name='Kresko RNAtech'
        startup_summary_v1='Startup food biotech que aísla RNAs bioactivos de alimentos frescos y los estabiliza en extractos funcionales. Entra en tesis por food biotech and novel ingredients.'
        business_one_liner='Bioactive RNA extracts from fresh food.'
        problem_addressed='Los compuestos bioactivos de alimentos frescos se degradan rápidamente y se pierden antes de ser aprovechados.'
        technical_approach='Aislamiento, descubrimiento funcional y estabilización de RNAs bioactivos presentes en frutas, verduras, hierbas, raíces y leche.'
        industry_destination='Food, nutrition and gut health'
        materiality_signal='high'
        thesis_scope_note='Entra por ingrediente funcional claramente biobasado y por su interfaz con nutrición, salud y alimentos.'
        source_url='https://sosv.com/company/kresko-rnatech/'
        source_type='official_company_profile'
        source_date='2026-04-21'
        evidence_excerpt='SOSV says Kresko isolates supernutrient bioactive RNAs from fresh foods and stabilizes them into extracts with health-relevant effects.'
        summary_confidence='high'
        review_status='reviewed'
    }
    [pscustomobject]@{
        startup_id='unibaio'
        startup_name='Unibaio'
        startup_summary_v1='Startup agtech que desarrolla micropartículas naturales para mejorar el desempeño de agroinsumos y reducir dosis de químicos hasta en 80%. Entra en tesis por ag biologicals and crop resilience.'
        business_one_liner='Natural microparticles that make agrochemicals and biologicals more efficient.'
        problem_addressed='Gran parte de los herbicidas, pesticidas y fertilizantes se pierden en el ambiente en lugar de ser absorbidos por los cultivos.'
        technical_approach='Micropartículas basadas en polímeros naturales que mejoran penetración y eficacia de crop protectants biológicos y sintéticos.'
        industry_destination='Agriculture'
        materiality_signal='high'
        thesis_scope_note='Entra por mejora material directa de sistemas agrícolas y por transición hacia insumos más eficientes y compatibles con salud ambiental.'
        source_url='https://sosv.com/company/unibaio/'
        source_type='official_company_profile'
        source_date='2026-04-21'
        evidence_excerpt='SOSV says Unibaio uses natural microparticles to enhance crop protectants and reduce chemical application doses by up to 80%.'
        summary_confidence='high'
        review_status='reviewed'
    }
)

Upsert-CsvById -Path (Join-Path $Root 'quality\manual_startup_taxonomy_overrides.csv') -Rows $taxonomyRows
Upsert-CsvById -Path (Join-Path $Root 'quality\manual_startup_profile_overrides.csv') -Rows $profileRows

Write-Output "SOSV / IndieBio portfolio sweep applied."
