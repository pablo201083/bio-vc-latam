"""Summaries batch 1 — 38 startups de alto riesgo. Inline Sonnet, 2026-06-25."""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "staging" / "entity_enrichments.csv"
src = "swarm_inline_sonnet_v1"
date = "2026-06-25"

# (entity_id, summary_en, confidence)
summaries = [
  ("forma-foods-mx", 0.85,
   "Forma Foods is a Tec de Monterrey spinout producing cultivated meat by growing animal muscle cells in bioreactors, eliminating livestock slaughter. The company targets Mexico's mass-market protein consumers with cost-competitive lab-grown beef and chicken, leveraging academic infrastructure and proximity to one of Latin America's largest food manufacturing ecosystems. Forma Foods represents Mexico's entry into the global cultivated protein race alongside major players in Brazil and Chile."),

  ("swebol-biotech-bo", 0.80,
   "Swebol Biotech is a joint spinout from Bolivia's UMSA and Sweden's Lund University developing agricultural bioinputs for Andean smallholder farming systems. The company applies microbial fermentation to produce nitrogen-fixing and phosphate-solubilizing bacterial consortia adapted to Bolivia's high-altitude soils, reducing chemical fertilizer dependency in quinoa, potato, and grain production. The Swedish-Bolivian collaboration bridges cutting-edge microbiology with deep local agronomic expertise."),

  ("silicochem-ec", 0.88,
   "SilicoChem is a UTPL university spinout engineering Saccharomyces cerevisiae strains to biosynthesize omega-3 fatty acids (EPA and DHA) through precision fermentation, bypassing fishmeal and fish oil supply chains. The Ecuadorian startup targets the aquaculture feed and human nutraceuticals markets with a land-based, scalable omega-3 source that reduces pressure on marine fisheries. SilicoChem's synthetic biology platform positions Ecuador as a precision fermentation hub for marine-analog bioactives."),

  ("koji-co", 0.88,
   "Koji is a Colombian precision fermentation company using Aspergillus oryzae (koji mold) to transform agricultural byproducts—sugarcane bagasse, coffee pulp, and corn stover—into functional biostimulants and protein-rich ingredients. The platform combines traditional koji fermentation with bioprocess data science to optimize yields and active compound profiles, producing certified bioinputs for Colombian growers and nutritional ingredients for the regional food industry. Koji closes the loop on Latin America's massive agricultural waste streams through biological upcycling."),

  ("viobact-cl", 0.88,
   "VioBact is a Universidad Católica del Norte spinout engineering marine probiotic consortia delivered via live rotifers to salmon and sea bass larvae in Chilean hatcheries. The platform colonizes larval fish guts with beneficial microorganisms that crowd out pathogens, improving survival rates and reducing antibiotic use from the first days of life. As Chile faces rising regulatory pressure on aquaculture antibiotic use, VioBact's biological approach addresses the industry's most critical early-stage mortality challenge."),

  ("bioram-mx", 0.90,
   "Bioram converts brewery waste from Heineken Mexico's operations into certified agricultural biostimulants through solid-state fermentation. The circular platform extracts spent yeast biomass, hop residues, and grain solubles to produce liquid and granular bioinputs that enhance soil microbiome activity and crop nutrient uptake in avocado, corn, and tomato systems. As a validated Heineken supply chain partner, Bioram demonstrates that industrial symbiosis can make Mexico's food sector both circular and biologically regenerative."),

  ("global-nano-additives-mx", 0.78,
   "Global Nano Additives is a Tec de Monterrey spinout engineering bio-derived nanoparticle lubricant additives from plant-based and biodegradable feedstocks to replace petroleum-based industrial lubricants. The company's nanotechnology platform synthesizes particles that reduce friction and extend equipment lifespan in automotive and manufacturing machinery, offering biodegradable performance alternatives with lower ecotoxicity. The startup positions Mexico at the frontier of green industrial chemistry where nanotechnology meets sustainable materials."),

  ("Bee Technology", 0.85,
   "Bee Technology develops FoodGuard, a biological food sanitizer derived from antimicrobial peptides found in bee defensins and royal jelly. The Chilean startup uses bioprospecting and peptide engineering to produce food-safe antimicrobial formulations that extend fresh fruit and vegetable shelf life without synthetic preservatives. FoodGuard targets Chile's fresh produce export sector, where extending post-harvest shelf life directly translates to higher margins and reduced waste across global supply chains."),

  ("mycoseaweed-cl", 0.85,
   "MycoSeaweed bioconverts Chilean macroalgae into high-protein functional ingredients using engineered fungal microbial consortia. The fermentation platform transforms seaweed biomass—harvested from Chile's 4,300 km coastline—into mycoprotein-rich powders with superior amino acid profiles and umami flavor compounds for alternative protein food applications. MycoSeaweed creates a circular value chain from underutilized marine biomass to premium functional ingredients, combining Chile's seaweed abundance with cutting-edge fungal fermentation."),

  ("lilliput-technologies-cr", 0.90,
   "Lilliput Technologies develops Lillishield, a biodegradable biopolymer crop coating applied as a sprayable solution that protects coffee seedlings from heat stress and water loss without interrupting photosynthesis. The Costa Rican startup's material forms a breathable film on leaf and stem surfaces that reduces transpiration-driven wilting during climate extremes, helping smallholder coffee farmers maintain yields through increasingly frequent heat waves without irrigation infrastructure. Founded in 2024 from Deep Science Ventures, Lillishield offers a low-cost scalable climate adaptation tool for tropical smallholders."),

  ("lilliput-technologies-ltd-cr", 0.90,
   "Lilliput Technologies develops Lillishield, a biodegradable biopolymer crop coating applied as a sprayable solution that protects coffee and other crops from heat stress and water loss without interrupting photosynthesis. The Costa Rican startup's material forms a breathable film on plant surfaces that reduces transpiration during climate extremes, helping smallholder farmers adapt to heat waves without expensive irrigation infrastructure. Lillishield provides a low-cost, scalable biological climate adaptation solution for tropical agriculture."),

  ("biofactory-br", 0.88,
   "BioFactory operates the world's largest Aedes aegypti mosquito biorefinery in Curitiba, Brazil, producing Wolbachia-infected and sterile mosquitoes for biological dengue and Zika vector control. The company's high-throughput mosquito production platform floods urban neighborhoods with non-pathogenic mosquitoes that outcompete wild disease-transmitting populations, reducing arbovirus transmission without chemical insecticides. In a continent where dengue kills tens of thousands annually and resistance to insecticides grows, BioFactory's biological control scales a proven epidemiological intervention."),

  ("infood-protein-cl", 0.90,
   "Infood Protein produces insect-derived protein flour, lipids, and organic fertilizer by bioconverting organic waste through black soldier fly (Hermetia illucens) larvae at industrial scale. The Chilean circular protein platform transforms food industry and agricultural residues into high-quality aquaculture and animal feed ingredients, offering a sustainable fishmeal replacement for Chile's salmon farming sector. Infood's insect bioconversion system closes the nutrient loop between waste streams and high-value feed markets with a fraction of conventional protein's land and water footprint."),

  ("tissue-nova-mx", 0.85,
   "Tissue Nova engineers 3D organoid and bioprinted tissue models from human and animal primary cells to replace animal testing in pharmaceutical toxicology and drug assessment. The Tec de Monterrey spinout develops organ-on-chip constructs and tissue arrays that replicate liver, skin, and intestinal microenvironments, enabling pharmaceutical and cosmetics clients to run OECD-compliant animal-free safety screening at a fraction of in vivo costs. Tissue Nova positions Mexico as a hub for next-generation preclinical testing infrastructure serving global pharma R&D."),

  ("pewman-innovation-cl", 0.88,
   "Pewman Innovation develops CRIOPROTECT, a bacterial biostimulant derived from Pseudomonas pewmanensis isolated from Patagonian environments that colonizes crop surfaces and inhibits ice crystal formation, protecting wine grapes, berries, and stone fruits from late frost events. The Chilean startup targets an economically devastating problem—late frosts that can destroy 50-80% of seasonal harvests overnight—with a biological spray applied days before frost risk windows. CRIOPROTECT offers growers a sustainable frost protection alternative to carbon-emitting smudge pots and energy-intensive wind machines."),

  ("grupo-bios-co", 0.72,
   "Grupo Bios is a Colombian biotechnology company producing biological inputs and fermentation-derived products for agricultural and industrial markets. Recognized as one of Colombia's leading deeptech biotech ventures, the company develops microbial consortia, enzyme formulations, and bio-based compounds at commercial scale, demonstrating that Latin American biotech can build profitable product-driven businesses anchored in regional biodiversity. Grupo Bios serves domestic agri-food clients while building export capacity to neighboring Andean markets."),

  ("recombine-biotech-br", 0.88,
   "Recombine Biotech is a Federal University of Viçosa spinout producing recombinant biopesticides and bioactive proteins through precision fermentation for Brazil's agriculture sector. Founded in 2019, the company engineers Bacillus-based microbial expression systems to produce Bt proteins, chitinases, and RNAi-based bioactives that control lepidopteran pests in soybean, corn, and sugarcane without synthetic chemistry. Recombine Biotech translates academic excellence from one of Brazil's premier agricultural universities into commercially scalable biological crop protection solutions."),

  ("bioprocess-automation-brasil-br", 0.82,
   "BioProcess Automation Brasil develops hardware and software platforms for real-time monitoring and automated control of industrial fermentation, supported by CNPq public research grants. The company produces bioreactor instrumentation including dissolved oxygen sensors, pH controllers, and SCADA-integrated data acquisition systems that improve batch consistency and yield predictability for pharmaceutical, food, and agricultural biotech manufacturers. As Brazilian biomanufacturing scales to meet domestic and export demand, BioProcess Automation provides the digital infrastructure backbone enabling reliable fermentation at commercial scale."),

  ("biolinker-br", 0.88,
   "Biolinker develops a cell-free protein synthesis platform that produces recombinant proteins in vitro without living host organisms, enabling rapid prototyping of antibodies, diagnostic antigens, and industrial enzymes. The Brazilian startup's cell-free transcription-translation system combines custom-formulated cell extracts with proprietary energy regeneration chemistry to accelerate protein production timelines from weeks to hours for pharmaceutical and biodiagnostics clients. Biolinker's platform removes the bottleneck of cell line development and fermentation scale-up that delays recombinant protein supply chains across Latin America."),

  ("biolife-innovations-bo", 0.85,
   "BioLife Innovations develops two complementary biotechnology products for Bolivia's agricultural and water sectors: BioBoost, a bacterial biofertilizer that improves nitrogen fixation and phosphate availability in quinoa and potato crops, and BioDetox, a biological water remediation system using enzyme-producing microorganisms to treat heavy metal contamination from artisanal mining operations. The Bolivian startup launched in 2018 addresses overlapping challenges of food security and environmental degradation in one of South America's most biodiverse and mining-intensive countries."),

  ("agrigenetic-ecuador-ec", 0.80,
   "Agrigenetic Ecuador applies reproductive biotechnology and genomic selection to improve cattle and poultry genetics for Ecuador's livestock sector. The company provides AI-based artificial insemination services using elite bull semen with quantified genetic merit scores, combined with molecular testing for disease resistance and production traits in tropical cattle breeds. By importing and distributing elite genetics adapted to equatorial conditions, Agrigenetic Ecuador improves herd productivity and disease resilience across Ecuador's coastal lowland and Andean dairy farming regions."),

  ("magenta-biolabs-cr", 0.80,
   "Magenta Biolabs is an IndieBio-accelerated Costa Rican biotech startup developing valuable biomolecules for the biotechnology industry using natural plant and microbial substrates. The company applies extraction and fermentation-based bioprocessing to isolate and produce specialty compounds—including pigments, enzymes, and bioactive secondary metabolites—sourced from Costa Rica's exceptional biodiversity. Magenta Biolabs positions Central America's megadiverse ecosystems as feedstock for high-value biotech inputs serving pharmaceutical, cosmetic, and food ingredient markets."),

  ("scintia-mx", 0.75,
   "Scintia is a Mexican biotech education and innovation platform democratizing access to laboratory science tools, curriculum, and co-working laboratory infrastructure for students, researchers, and early-stage biotech entrepreneurs. Founded in 2017, the company provides affordable molecular biology kits and online biotechnology training programs that build the human capital pipeline needed for Mexico's emerging biotech ecosystem. By lowering barriers to hands-on biological experimentation, Scintia accelerates the formation of the next generation of synthetic biology and biomanufacturing founders in Latin America."),

  ("ayni-desert-interaction-cl", 0.88,
   "Ayni Desert Interaction bioprospects extremophile microorganisms from the Atacama Desert—Earth's driest non-polar environment—to develop agricultural bioinputs with exceptional tolerance to drought, heat, and salinity stress. The Chilean startup's microbial formulations improve nutrient uptake and water-use efficiency in crops grown under arid conditions, targeting Chile's Norte Grande irrigation agriculture as well as analogous dryland farming systems in Peru, Bolivia, and global markets facing desertification. Ayni converts extreme biodiversity into a competitive advantage for climate-resilient agriculture."),

  ("nalca-biotech-cl", 0.90,
   "Nalca Biotech engineers modular continuous fermentation systems that reduce the capital intensity and operational complexity of scaling precision fermentation from lab to commercial production. The Chilean startup's bioreactor platform enables food companies and ingredient producers to manufacture fermentation-derived proteins, bioactives, and flavors at mid-scale without the multi-million dollar CAPEX of traditional batch fermentation facilities, democratizing access to industrial-scale bioprocessing across Latin America's emerging precision fermentation sector."),

  ("codebreaker-bioscience-cl", 0.88,
   "Codebreaker Bioscience develops Micro-ID, a soil and plant microbiome intelligence platform that translates metagenomic sequencing data into prescriptive bioinput recommendations for farmers and agronomists. The Chilean startup combines 16S rRNA amplicon sequencing with machine learning models trained on Latin American soil microbiome datasets to identify microbial community health indicators and recommend targeted biological amendments that optimize crop yields and soil biological function without guesswork."),

  ("cropguard-cl", 0.82,
   "CropGuard develops biological crop protection solutions for Chilean specialty agriculture, combining entomopathogenic fungi, predatory arthropods, and botanical bioactives into integrated pest management programs tailored to fruit, wine, and vegetable production systems. The company provides growers with biologically certified alternatives to synthetic pesticides that preserve beneficial insect populations, maintain organic certification eligibility, and comply with the tightening maximum residue limits applied by the EU and US to Chilean agricultural exports."),

  ("aquabyte-cl", 0.92,
   "Aquabyte deploys underwater computer vision systems and AI in salmon net pens, capturing over 1.3 million images daily per installation to monitor individual fish biomass, sea lice infestation levels, behavioral welfare indicators, and feeding appetite in real time. The platform's eight years of accumulated aquaculture training data enable precise biomass estimation, lice forecasting, and automated treatment triggers that reduce chemical sea lice treatments and improve feed conversion ratios across Chile's salmon farming operations. Aquabyte gives salmon producers the data infrastructure to optimize efficiency and comply with rising Norwegian-origin animal welfare standards."),

  ("ascribe-bio-br", 0.90,
   "Ascribe Bio produces Phytalix, a natural biofungicide from a proprietary Trichoderma strain that controls Sclerotinia and Fusarium soil-borne pathogens in soybean, sugarcane, and vegetable crops. The Brazilian startup raised a $12M Series A co-led by Acre Venture Partners and operates a fully domestic biological input supply chain, offering growers residue-free disease management that improves compliance with EU maximum residue limits increasingly restricting Brazilian agricultural commodities. Phytalix delivers commercial-scale biological efficacy verified in multi-season field trials across Brazil's major crop-producing states."),

  ("fieldfactors-mx", 0.78,
   "FieldFactors develops smart water management systems integrating precision irrigation, rainwater harvesting, and agricultural water recycling for commercial farming and urban agriculture in Mexico's water-stressed regions. The company's sensor-driven platforms continuously monitor soil moisture profiles and crop evapotranspiration demands, enabling automated irrigation scheduling that reduces water consumption by 30-50% compared to conventional flood irrigation in the Bajío and Northern Mexico's arid agricultural zones."),

  ("tierra-de-monte-mx", 0.85,
   "Tierra de Monte develops microbial consortia and biostimulant formulations for soil restoration and microbiome rehabilitation in degraded Mexican agricultural land. The Querétaro-based startup—founded in 2015 and VC-backed—inoculates depleted soils with native nitrogen-fixing bacteria, mycorrhizal fungi, and phosphate-solubilizing microbes to rebuild biological fertility without synthetic inputs, targeting avocado, berry, and corn growers pursuing organic certification or recovering soils degraded by decades of chemical agriculture."),

  ("plantverd-mx", 0.85,
   "PlantVerd applies biotechnology to large-scale ecosystem restoration, using native plant endophyte microbiomes and soil inoculants to accelerate reforestation and degraded land recovery across Mexico. Village Capital ranked PlantVerd #2 in its cohort for combining biological restoration science with carbon credit generation, enabling land managers to monetize verified biodiversity and carbon sequestration alongside productive land use. The company translates ecological restoration science into a financially viable model that aligns economic incentives with ecosystem regeneration."),

  ("ecocycle-biotech-ec", 0.85,
   "Ecocycle Biotech develops agricultural bioinputs from native Ecuadorian microorganisms specifically adapted to the country's diverse microclimates—from coastal lowlands to 3,000m Andean highlands. The startup isolates, characterizes, and formulates bacterial and fungal strains with proven performance under Ecuador-specific soil pH, temperature, and humidity conditions, producing liquid biofertilizers and biopesticides that outperform imported generic products for cacao, banana, and flower growers who together represent Ecuador's largest agricultural export sectors."),

  ("seedtech-cl", 0.82,
   "SeedTech develops precision seed coating and treatment technologies that encapsulate beneficial microorganisms, plant growth regulators, and bioprotective agents directly onto seed surfaces using polymer matrix delivery systems. The Chilean startup's controlled-release coatings ensure that biological agents remain viable and are released during germination, improving seedling establishment, root colonization by inoculant bacteria, and early-stage disease resistance without requiring separate soil applications. SeedTech targets Chile's certified seed production sector serving domestic and export cereal and vegetable markets."),

  ("green-xpo-lab-cr", 0.82,
   "Green Xpo Lab develops a remote sensing intelligence platform combining satellite multispectral imagery, drone surveys, and AI-powered computer vision for crop health monitoring, deforestation detection, and biodiversity assessment across Central America. The Costa Rican startup converts hyperspectral and RGB data into prescriptive field maps showing vegetation stress indices, pest pressure zones, and land-use change alerts, enabling farmers, conservation organizations, and government environmental agencies to make evidence-based land management decisions at landscape scale."),

  ("biorefinery-tech-brazil-br", 0.85,
   "Biorefinery Tech Brazil converts agroindustrial waste streams—sugarcane bagasse, corn stover, and citrus pulp—into platform chemicals including succinic acid, lactic acid, and bioethanol through enzymatic hydrolysis and microbial fermentation, supported by BNDES development financing. The company operates pilot biorefinery infrastructure enabling Brazil to capture higher-value bio-based chemicals from agricultural residues currently burned or landfilled by the country's massive agro-processing sector. Biorefinery Tech Brazil positions the world's largest sugarcane producer at the frontier of second-generation biorefinery technology."),

  ("agro-logica-co", 0.78,
   "Agro-Logica provides agricultural biotechnology services and biological crop optimization programs to Colombian smallholder and commercial growers. The company combines soil biology diagnostics, targeted bioinput formulation, and integrated agronomic advisory to design biological farming systems that reduce synthetic input costs, improve soil health metrics, and increase farm profitability in coffee, cacao, and tropical fruit production across Colombia's diverse agricultural regions. Agro-Logica bridges the gap between biological agriculture science and farmer-facing implementation at field scale."),

  ("quipu-cr", 0.80,
   "Quipu is a Costa Rican digital agriculture platform that won the 2021 IICA Hackathon for its mobile tool delivering agronomic recommendations, real-time market pricing, and climate-smart planting advice to smallholder farmers via WhatsApp-compatible interfaces accessible without smartphones or stable connectivity. The startup bridges the agricultural digital divide in rural Central America by translating complex agronomic decision support into simple conversational interfaces that reach farmers in indigenous and remote communities excluded from conventional precision agriculture platforms."),

  ("healthpoint-bo", 0.70,
   "HealthPoint is a Bolivian digital health company providing telemedicine, electronic health records, and remote patient monitoring services to underserved urban and rural communities through mobile platforms. Founded in 2018, the company connects patients with certified physicians via video consultation, enabling access to specialist care in regions where healthcare infrastructure is limited or absent. HealthPoint's digital health stack supports chronic disease management, prescription services, and preventive health programs across Bolivia's fragmented healthcare system."),

  ("bioproducts-co", 0.68,
   "BioProducts (Colombia) provides contract biomanufacturing and fermentation-based bioprocessing services to pharmaceutical, agricultural, and food industry clients requiring scale-up of biological active ingredients. The company offers CDMO-style capabilities for Colombian and regional biotech ventures lacking production infrastructure, enabling laboratory-stage biologics to advance toward commercial scale with validated GMP-compatible processes. BioProducts serves as an enabling platform that reduces the capital barrier for Colombian biotech startups commercializing fermentation-derived compounds."),
]

with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for eid, conf, summary in summaries:
        w.writerow([eid, "startup_extended", "startup_summary_en",
                    summary, src, conf, f"swarm_inline_summary {date}"])

total = sum(1 for _ in open(out, encoding="utf-8")) - 1
print(f"Summaries batch 1: {len(summaries)} filas escritas. Total entity_enrichments: {total}")
