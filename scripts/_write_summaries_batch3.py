"""Summaries batch 3 — 24 restantes. Cierra el ciclo. Inline Sonnet, 2026-06-25."""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "staging" / "entity_enrichments.csv"
src = "swarm_inline_sonnet_v1"
date = "2026-06-25"

summaries = [
  ("caribbean-medtech-do", 0.72,
   "Caribbean MedTech provides medical device sales, marketing, and distribution services across the Dominican Republic and Caribbean region, connecting international medical device manufacturers with regional hospital systems, clinics, and distributors. The company offers regulatory clearance support, clinical training, and after-sales service for diagnostic imaging, surgical instruments, and patient monitoring equipment, filling a market access gap for global medtech firms entering Caribbean health systems where regulatory navigation and local relationships determine market penetration success."),

  ("medimarket-online-ve", 0.72,
   "Medimarket Online is a Venezuelan e-commerce platform for pharmaceutical and health product retail, connecting consumers with certified pharmacies and medical suppliers through a digital marketplace launched in 2021. The platform addresses Venezuela's severe fragmentation in pharmaceutical access by aggregating inventory availability across multiple suppliers, enabling price comparison, and providing home delivery of medications and health products in a context where pharmacy supply chains are chronically disrupted. Medimarket Online applies digital marketplace infrastructure to a critical health access problem in a constrained economy."),

  ("magic-green-cr", 0.70,
   "Magic Green is a Costa Rican agritech startup developing agricultural technology solutions for the country's growing precision agriculture sector. The company leverages Costa Rica's high agricultural technology adoption environment to develop and pilot digital tools supporting farm management, crop monitoring, and input optimization for smallholder and commercial producers. Magic Green operates within Costa Rica's internationally recognized sustainable agriculture ecosystem, building tech-enabled tools that support the country's agri-export certification and environmental compliance requirements."),

  ("biodiverso-insumos-br", 0.85,
   "BioDiverso Insumos produces agricultural biostimulants and crop inputs sourced from Brazil's exceptional biological diversity, isolating and characterizing microbial and botanical actives from native Brazilian ecosystems for commercial bioinput formulation. The company develops bacterial consortia, fungal inoculants, and plant extract concentrates derived from Atlantic Forest and Cerrado biodiversity hotspots, producing biostimulants that improve crop root development, stress tolerance, and nutrient assimilation validated in Brazilian tropical soil conditions for soybean, sugarcane, and vegetable growers."),

  ("lifepack-co", 0.88,
   "Lifepack produces biodegradable disposable tableware—plates, cups, and trays—from corn starch and pineapple waste using thermopressing and bioplastic injection molding. The Colombian startup's packaging decomposes within 180 days under home composting conditions and within 60 days in industrial composting facilities, offering food service businesses a compostable alternative to conventional single-use plastics. Lifepack addresses the Latin American food service sector's shift toward circular packaging compliance as municipal plastics regulations tighten across Colombia's major cities."),

  ("microlabs-mx", 0.85,
   "Microlabs is a Mexican R&D biotech company developing sustainable biopesticides and microbial agricultural inputs using endemic soil bacterial and fungal isolates screened for pesticidal and biostimulant activity. The company's discovery pipeline identifies novel strains with commercial potential from Mexico's diverse agricultural microbiomes, formulates them into stable liquid and granular bioinput products, and validates efficacy in field trials across corn, tomato, and avocado production systems. Microlabs builds Mexico's domestic biological input innovation capacity, reducing reliance on European and North American biopesticide multinationals."),

  ("agritech-bolivia-bo", 0.75,
   "AgriTech Bolivia develops agricultural technology solutions leveraging AI and IoT to address water shortages and productivity challenges facing Bolivian smallholder and commercial farmers. The company provides sensor-based irrigation management, satellite-assisted crop monitoring, and mobile farm advisory platforms adapted to Bolivia's diverse agroecological zones—from lowland tropics to Andean highlands—helping farmers optimize water use efficiency and input application in a country where both water scarcity and excess precipitation threaten agricultural productivity."),

  ("agrobit-bolivia-operations-bo", 0.75,
   "Agrobit's Bolivia operations deploy a blockchain-enabled smart farm platform for sustainable agriculture supply chain management in Bolivian quinoa and grain production, backed by the Italian parent company's global agtech platform. The system provides farm-level data collection, satellite crop monitoring, and blockchain-verified traceability from field to export, enabling Bolivian quinoa cooperatives to document sustainable production practices and access premium organic and fair-trade markets. Agrobit's Bolivia deployment demonstrates how global agtech platforms can be adapted to support smallholder commodity export chains in Andean agricultural systems."),

  ("krtl-biotech-bolivia-expansion-bo", 0.82,
   "KRTL Biotech is a biopharmaceutical company expanding into Bolivia through a partnership with the Centro de Investigaciones Químicas of UMSA, establishing local bioproduction and distribution capabilities for biological medicines and diagnostic biologics in the Bolivian market. The company's Bolivia expansion focuses on building in-country biological manufacturing capacity for vaccines, therapeutic proteins, and diagnostic antigens that are currently imported, reducing Bolivia's dependency on international pharmaceutical supply chains for critical biological health products."),

  ("energytop-via-proinpa-bo", 0.88,
   "Energytop, commercialized through Bolivia's PROINPA foundation, produces biofertilizer formulations containing four complementary microorganism species that capture atmospheric nitrogen and solubilize soil-bound phosphorus for quinoa, potato, and grain crops in Andean highland farming systems. The product replaces chemical nitrogen and phosphorus fertilizers with biological alternatives adapted to Bolivia's high-altitude soils and cool temperatures, reducing chemical input costs for smallholder farmers in one of Latin America's most agriculturally important Andean nations. Energytop demonstrates the PROINPA model of converting Bolivian agricultural research into commercially accessible bioinput products."),

  ("innovatech-bo", 0.75,
   "Innovatech Bolivia provides IFAD-backed digital agricultural solutions and fintech services for Bolivian smallholder farmers, combining mobile agronomic advisory platforms with microfinance access tools that improve farm productivity and financial inclusion simultaneously. The platform delivers climate-smart planting recommendations, market price information, and digital credit scoring based on farm production data, enabling smallholders to access formal financial services while improving agricultural decision-making in Bolivia's subsistence and smallholder farming communities."),

  ("biohack-uio-ec", 0.82,
   "BioHack UIO is Ecuador's first community biotechnology laboratory, founded in 2020 in Quito to democratize access to biological experimentation tools and synthetic biology education for students, researchers, and citizen scientists. The open lab provides affordable access to PCR machines, gel electrophoresis, microscopy, and biological safety cabinets alongside workshops in molecular biology and biodesign, building the grassroots biotechnology culture and human capital pipeline that Ecuador's emerging bioeconomy requires. BioHack UIO positions community biotech labs as an infrastructure layer for distributed biological innovation in Latin America."),

  ("biogenesis-bago-ec", 0.80,
   "Biogenesis Bagó Ecuador is the local operation of Biogenesis Bagó, a leading Latin American animal health and nutrition biotechnology company producing veterinary biologics—vaccines, diagnostics, and nutritional supplements—for Ecuador's cattle, poultry, and aquaculture sectors. The company provides bovine reproductive vaccines, mastitis diagnostics, and livestock nutritional biologics validated for Ecuadorian tropical production conditions, offering producers biologically-based animal health programs that improve herd productivity while reducing antibiotic dependency in food-producing animals."),

  ("minerba-ec", 0.70,
   "MinerBA develops data-driven industrial analytics platforms for Ecuador's southern industrial corridor, providing operational intelligence tools for mining, chemical, and agro-industrial operations that optimize process efficiency and resource consumption. The company's sensor integration and machine learning dashboards enable plant managers to identify production inefficiencies, predict equipment failures, and reduce energy and material waste in industrial processes. While primarily focused on industrial analytics, MinerBA's work in Ecuador's mining-adjacent agricultural processing sector intersects with environmental monitoring and resource efficiency objectives relevant to the bio-economy transition."),

  ("digital-twin-corporation-cr", 0.80,
   "Digital Twin Corporation develops IoT platforms using novel fruit-shaped digital twin sensor devices that embed seamlessly into agricultural environments, collecting microclimate data on temperature, humidity, and CO2 levels for crop monitoring and agricultural waste management optimization. The Costa Rican startup's biomorphic sensor design allows devices to be placed directly in crop canopies or waste processing facilities, providing more representative and physically proximate environmental measurements than conventional weather stations, with applications in post-harvest quality management and circular bioeconomy waste tracking."),

  ("geanext-cr", 0.72,
   "GeaNext is a Costa Rican agritech startup developing precision agriculture solutions to improve productivity and resource efficiency for the country's smallholder and commercial farmers. The company combines agronomic data analysis with digital farm management tools adapted to Costa Rica's diverse crop systems including coffee, pineapple, and banana, supporting growers in optimizing fertilizer application, pest management timing, and harvest scheduling. GeaNext operates within Costa Rica's internationally recognized sustainable agriculture sector targeting both domestic food security and export quality certification markets."),

  ("biotech-cr", 0.85,
   "BioTech Costa Rica develops sustainable biocontrol solutions as natural alternatives to chemical pesticides for the country's specialty agriculture sector. The company produces entomopathogenic and mycoparasitic biological control agents derived from Costa Rica's endemic microbial diversity, validated for pest and disease management in coffee, ornamental plants, and tropical fruit crops. Co-founders with deep entomology and plant pathology expertise position BioTech CR to supply biologically certified crop protection products to Costa Rica's organic certification and premium export market supply chains."),

  ("wseeds-co", 0.80,
   "WSeeds is a Colombian digital agriculture platform combining AI, satellite imagery, blockchain traceability, and WhatsApp-based conversational interfaces to provide smallholder farmers with agronomic recommendations, crop monitoring alerts, and supply chain documentation tools accessible through basic mobile phones. The platform democratizes precision agriculture intelligence by delivering actionable field insights through channels farmers already use, enabling rural Colombian producers to access crop insurance, certifications, and premium buyer markets through verifiable digital farm records."),

  ("agrocontrol-gt", 0.75,
   "Agrocontrol develops agricultural monitoring and control technology for Guatemalan commercial farming operations, providing IoT sensor networks and automated alert systems for irrigation management, microclimate monitoring, and crop health surveillance. The company's platforms integrate soil moisture sensors, weather stations, and pest pressure monitors with cloud-based farm management software, enabling growers in Guatemala's coffee, sugarcane, and vegetable sectors to automate precision input applications and receive early warnings for frost risk, drought stress, and disease outbreak conditions."),

  ("fermentlabs-co", 0.88,
   "FermentLabs Colombia develops a precision fermentation platform for sustainable leather tanning and textile dyeing, producing bio-based tanning agents and natural dyes through microbial fermentation as alternatives to the chromium and synthetic chemical processes that make conventional leather production one of the most polluting industries globally. The company's fermentation-derived compounds provide equivalent leather performance with dramatically reduced toxic effluent, positioning Colombia's substantial leather and textile manufacturing sector to meet global demand for bio-based, circular fashion supply chains."),

  ("biometrics-medellin-co", 0.90,
   "BioMetrics Medellín develops a point-of-care diagnostic platform for parasitic and tropical infectious diseases endemic to Colombia and Latin America, using lateral flow immunoassay and biosensor technologies validated for Chagas disease, leishmaniasis, malaria, and dengue detection in primary care and field settings. The Medellín-based startup's compact diagnostic devices deliver pathogen identification with laboratory-comparable sensitivity without requiring cold chain reagents or trained laboratory staff, enabling mass screening programs and outbreak response in the endemic zones where these diseases cause the greatest morbidity."),

  ("agroguia-ve", 0.78,
   "Agroguía is a Venezuelan precision agriculture startup providing GPS-based field mapping, tractor path optimization, and data-driven planting recommendations to smallholder farmers via a mobile application accessible on basic smartphones. The company maps field geometry and soil variability to generate zone-specific input recommendations for crop planting density, fertilization, and irrigation scheduling, improving land use efficiency and yield predictability for Venezuelan grain and vegetable producers operating under constrained access to agrochemical inputs and technical advisory services."),

  ("agricultic-do", 0.75,
   "Agricultic modernizes Dominican Republic agriculture through AI-powered commodity pricing tools, market intelligence platforms, and precision input advisory systems that connect smallholder and commercial farmers with real-time market data and decision support. The company applies machine learning to agricultural commodity price forecasting and crop input optimization, helping Dominican growers make evidence-based planting and selling decisions in volatile commodity markets. Agricultic targets cacao, coffee, and avocado producers whose export market access depends on timely market intelligence and certified quality production practices."),

  ("agro360-do", 0.78,
   "Agro360 develops AI-powered IoT platforms combining wireless soil sensors, weather stations, and satellite imagery to provide Dominican Republic farmers with automated precision agriculture management across diverse tropical crop systems. The company's cloud platform processes multi-source environmental data to trigger automated irrigation systems, generate pest risk alerts, and optimize fertilizer application timing, offering an exponential technology approach to Dominican agriculture productivity gaps that constrain the country's food security and agricultural export potential."),
]

with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for eid, conf, summary in summaries:
        w.writerow([eid, "startup_extended", "startup_summary_en",
                    summary, src, conf, f"swarm_inline_summary {date}"])

total = sum(1 for _ in open(out, encoding="utf-8")) - 1
print(f"Summaries batch 3 (final): {len(summaries)} filas. Total entity_enrichments: {total}")
