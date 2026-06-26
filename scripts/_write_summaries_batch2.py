"""Summaries batch 2 — 40 startups. Inline Sonnet, 2026-06-25."""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "staging" / "entity_enrichments.csv"
src = "swarm_inline_sonnet_v1"
date = "2026-06-25"

summaries = [
  ("fermentlab-br", 0.82,
   "FermentLab develops fermentation technology and bioprocess engineering solutions for industrial biology applications in Brazil. The company provides custom fermentation platform development, strain optimization, and scale-up services for food, pharmaceutical, and agricultural biotech clients seeking to accelerate from laboratory fermentation protocols to commercially viable production processes. FermentLab fills a critical gap in Brazil's biotech ecosystem by providing applied fermentation expertise that bridges academic research and commercial manufacturing."),

  ("innmetec-co", 0.90,
   "Innmetec develops digital surgical planning software and custom patient-specific bone implants using hydroxyapatite-polymer composite biomaterials that match the mechanical and biological properties of native bone. The Colombian medtech company combines 3D medical imaging, CAD design, and additive manufacturing to produce implants tailored to individual patients' anatomy, reducing surgical time and improving osseointegration outcomes in reconstructive orthopedic and maxillofacial procedures. Innmetec positions Colombia as a regional hub for biomaterial-based precision implant technology."),

  ("inkus-biotech-cl", 0.88,
   "Inkus Biotech applies advanced genomics and AI to accelerate the genetic improvement of aquatic species for pathogen resistance and climate adaptation in Chilean aquaculture. The company uses whole-genome sequencing, QTL mapping, and machine learning to identify genetic markers associated with disease resistance to SRS, IHN, and sea lice in salmon, enabling selective breeding programs that reduce antibiotic use and mortality in Chile's $5 billion salmon industry while building biological resilience to rising ocean temperatures."),

  ("protera-bio-cl", 0.92,
   "Protera Bio uses AI-designed proteins to replace synthetic food additives, improve product shelf life, and enhance nutritional profiles in packaged foods. The Chilean startup's proprietary algorithm generates novel protein sequences with specific functional properties—emulsification, preservation, texturization—that match or exceed synthetic additive performance while meeting clean-label consumer demands. Protera's computational protein design platform enables food manufacturers to reformulate products without sacrificing functionality, opening a large-scale substitution market across the global clean-label food industry."),

  ("eatcloud-co", 0.80,
   "EatCloud is a Colombian food waste redistribution platform that has redirected 42,000 tons of surplus food and generated 95 million meals by connecting food producers, retailers, and wholesalers with social organizations, food banks, and discounted consumer markets. The platform uses AI-driven matching algorithms to route near-expiry and cosmetically imperfect food that would otherwise be discarded through efficient logistics channels before quality deteriorates, reducing greenhouse gas emissions from food waste decomposition while addressing food insecurity across Colombia's urban centers."),

  ("xeptiva-therapeutics-uy", 0.90,
   "Xeptiva Therapeutics develops peptide-based vaccines targeting chronic inflammatory conditions in companion animals, beginning with canine osteoarthritis—a condition affecting 20% of dogs globally. The Uruguayan biotech uses antigenic peptide engineering to induce sustained immune modulation that reduces joint inflammation without chronic NSAID use, addressing a $4 billion veterinary therapeutics market underserved by existing treatments. Xeptiva's peptide vaccine platform is extensible to other immune-mediated conditions in pets and livestock, building a pipeline from a single biological mechanism."),

  ("ecombio-cl", 0.90,
   "Ecombio develops probiotic bacterial consortia that combat flavobacteriosis and reduce antibiotic use in fresh water salmon hatcheries in Chile and Norway. The company's probiotic formulations colonize juvenile salmon intestines and gill surfaces with competitive exclusion bacteria that displace Flavobacterium psychrophilum and Tenacibaculum maritimum—pathogens responsible for significant mortality in salmon larvae worldwide. Ecombio's biological disease management platform addresses the aquaculture antibiotic resistance crisis at the most vulnerable life stage with a validated, regulatory-compliant alternative."),

  ("agroscan-ec", 0.85,
   "Agroscan Ecuador develops drone-based multispectral imaging and AI-powered computer vision platforms for precision crop health monitoring in banana, cacao, and flower export production systems. The company's aerial survey service identifies early-stage nutrient deficiencies, fungal infections, and water stress from spectral signatures invisible to the naked eye, enabling farmers to apply targeted interventions days before symptoms become visible and economically significant. Agroscan turns Ecuador's agricultural monitoring challenge into a competitive intelligence advantage for export-grade crop certification."),

  ("dimitra-bolivia-operations-bo", 0.78,
   "Dimitra's Connected Farmer platform delivers AI-powered agronomic decision support, satellite-derived crop monitoring, and blockchain-verified supply chain traceability to quinoa and grain smallholder farmers in Bolivia through the PROINPA agricultural development program. The platform provides field officers and farmers with mobile access to planting calendars, weather-based advisories, market prices, and financial services, connecting remote Andean communities to digital agricultural infrastructure. Dimitra's Bolivia operations demonstrate how global agtech platforms can be deployed through local NGO-government partnerships to reach subsistence farming communities."),

  ("nanomedical-cr", 0.78,
   "Nanomedical develops disinfection and sterilization technology for medical applications in Costa Rica, leveraging nanotechnology-based antimicrobial agents that provide broad-spectrum pathogen elimination on medical surfaces and instruments. The company targets healthcare facility infection control markets with nano-enabled disinfectant formulations that maintain efficacy against drug-resistant hospital pathogens including MRSA and Klebsiella at lower concentrations than conventional chemical disinfectants, reducing toxic chemical burden on healthcare workers and patients."),

  ("nemacontrol-biologicos-br", 0.90,
   "NemaControl Biologicos produces nematode-based biocontrol solutions and Bacillus amyloliquefaciens bioprotectants developed in partnership with EMBRAPA, Brazil's federal agricultural research corporation. The company commercializes entomopathogenic nematode formulations that penetrate and kill soil-dwelling agricultural pests including white grubs, rootworms, and fungus gnats without soil chemical residues, serving Brazil's ornamental plant, vegetable, and turf management sectors. NemaControl's EMBRAPA partnership provides R&D credibility and access to decades of Brazilian agricultural entomology knowledge."),

  ("biomar-cr", 0.75,
   "BioMar Costa Rica is the local operation of BioMar Group, a global aquaculture feed manufacturer that produces nutritionally optimized fish and shrimp feeds for Costa Rica's tilapia, shrimp, and marine fish farming sectors. The company formulates species-specific diets incorporating marine ingredients, plant proteins, and micronutrient premixes that maximize feed conversion ratios and growth performance while reducing marine ingredient dependency through alternative protein inclusion. BioMar's Costa Rica presence supports the country's growing aquaculture sector with globally validated feed science adapted to tropical production conditions."),

  ("recirculab-cl", 0.85,
   "ReCircuLab develops circular bioeconomy solutions for Chilean aquaculture and marine biotechnology, using AI-driven waste characterization to identify high-value compounds in salmon processing byproducts and marine biomass residues. The company recovers collagen, omega-3 fatty acids, hydroxyapatite, and bioactive peptides from fish skin, bones, and viscera that are currently discarded or rendered into low-value meal, creating new revenue streams from waste while reducing the environmental impact of Chile's massive salmon processing industry."),

  ("bioplast-br", 0.85,
   "BioPlast develops bioplastics and biodegradable packaging materials from renewable plant-based feedstocks including sugarcane, corn starch, and cassava, targeting Brazil's food packaging and single-use plastics markets. The company produces PHA- and PLA-based films, trays, and coatings that biodegrade within 90-180 days under industrial composting conditions, offering food manufacturers a regulatory-compliant alternative to conventional plastics as Brazil's single-use plastics legislation tightens. BioPlast leverages Brazil's abundant biomass supply to build cost-competitive biopolymer production at domestic scale."),

  ("bontix-do", 0.80,
   "Bontix develops a smart agricultural ecosystem integrating IoT sensors, AI analytics, and cloud-based farm management for Dominican Republic smallholder and commercial farmers. The platform collects real-time field data on soil moisture, microclimate conditions, and crop growth parameters, delivering automated irrigation controls and agronomic alerts via mobile interfaces that help farmers optimize inputs and reduce crop losses in the Caribbean's increasingly erratic climate. Bontix applies precision agriculture technology to address productivity gaps in Dominican Republic's cacao, banana, and vegetable export sectors."),

  ("respiratorydx-co", 0.90,
   "RespiratoryDx develops non-invasive respiratory diagnostic devices that use acoustic biomarker analysis to detect tuberculosis and other respiratory infections without sputum samples or laboratory infrastructure. The Colombian startup's technology analyzes cough sound signatures and breathing patterns with AI classifiers trained on clinical datasets to identify pathogen-specific acoustic fingerprints, enabling community-level TB screening in resource-limited settings where laboratory access, trained technicians, and cold chain infrastructure are unavailable. RespiratoryDx addresses a critical TB detection gap in Latin America's highest-burden countries."),

  ("terrasos-br", 0.88,
   "Terrasos develops biodiversity credit instruments and habitat banking mechanisms that enable corporations to offset their land-use biodiversity impacts by financing verified habitat protection and restoration projects in Latin America. Supported by IDB Lab, the company has structured conservation finance transactions protecting over 6,950 hectares and mobilizing $7 million in private biodiversity investment, creating market infrastructure for nature-based solutions that complements carbon credit markets. Terrasos builds the financial plumbing that connects corporate biodiversity commitments with on-the-ground conservation outcomes."),

  ("decoy", 0.85,
   "Decoy develops innovative biological pesticides for Brazilian livestock and agriculture, distributing biological control agents that replace synthetic insecticides and acaricides for cattle tick, whitefly, and caterpillar management. The company's product portfolio includes entomopathogenic fungi formulations (Beauveria bassiana, Metarhizium anisopliae), predatory mites, and biopesticide blends validated in Brazilian field conditions, enabling livestock producers and crop farmers to reduce chemical residue loads while meeting growing export market demands for clean production certification."),

  ("biiosmart-co", 0.82,
   "BIIOSMART develops intelligent molecular therapeutics (IMT) combining targeted drug delivery systems with bioactive molecules to improve the precision and efficacy of pharmaceutical treatments for chronic conditions. The Colombian biotech integrates biopolymer nanocarriers with therapeutic payloads that release drugs in response to specific physiological triggers—pH, enzyme activity, temperature—improving drug bioavailability and reducing systemic side effects. BIIOSMART's platform positions Colombia at the intersection of nanomedicine and precision therapeutics for chronic disease management."),

  ("corpogen-co", 0.80,
   "CorpoGen is a Colombian non-profit research center founded in 1995 specializing in genomics, environmental microbiology, and molecular biology applied to agriculture, health, and conservation. The center develops molecular biology kits and diagnostic tools for pathogen detection, conducts microbiome research on Colombian soils and water systems, and provides contract genomics services to the agricultural and public health sectors. CorpoGen functions as a critical bridge between Colombian academic microbiology and applied biotechnology commercialization, incubating spinouts and transferring validated protocols to industry."),

  ("neocroptech-cl", 0.88,
   "NeoCropTech applies CRISPR gene editing and molecular marker-assisted breeding to develop drought-resistant wheat and climate-resilient cereal varieties for Chilean and Andean agriculture. Founded in 2020, the company introduces targeted mutations in water-use efficiency and heat tolerance genes identified through multi-year field trials, enabling varieties that maintain yields under the progressive desertification affecting Chile's Central Valley agricultural zones without introducing foreign DNA, complying with Chile's regulatory framework for gene-edited crops."),

  ("welii-ar", 0.82,
   "Welii develops an integrated health tracking application that aggregates biometric data from wearable devices—heart rate monitors, glucose sensors, and activity trackers—with a cloud-based hospital information management system for chronic disease monitoring and preventive health programs. The Argentine startup enables patients to share continuous physiological data with their clinical teams through structured health APIs, improving remote patient monitoring, medication adherence tracking, and early intervention for cardiovascular, metabolic, and respiratory conditions in outpatient care settings."),

  ("bioceres-ar", 0.95,
   "Bioceres is Argentina's leading agricultural biotechnology company and the developer of the world's first commercially approved genetically modified drought-tolerant wheat (HB4), engineered with a sunflower transcription factor gene that activates stress response pathways under water deficit. Listed on NASDAQ, Bioceres also produces biological seed treatments, crop nutrients, and inoculants that form an integrated biological input platform for Argentine, Brazilian, and global grain producers. The company's HB4 wheat represents a landmark achievement: the first GM crop with demonstrated yield stability under the drought conditions that will characterize climate-changed agriculture across the Southern Cone."),

  ("biofresh-br", 0.80,
   "BioFresh develops food biotechnology solutions for natural preservation of fresh and minimally processed foods, using probiotic bacterial cultures, bacteriocins, and protective fermentation to extend shelf life without synthetic preservatives. The Brazilian startup produces bioprotective cultures and natural antimicrobial formulations validated for fresh meat, dairy, and ready-to-eat vegetables, enabling food manufacturers to achieve clean-label preservation performance competitive with chemical alternatives while meeting growing consumer and regulatory demand for additive-free food products."),

  ("cellculture-br", 0.82,
   "CellCulture Brazil provides cell culture media, bioreactor systems, and bioprocess engineering services for pharmaceutical, veterinary vaccine, and cultivated meat applications. The company manufactures animal-component-free culture media formulations and single-use bioreactor consumables adapted to the specific requirements of mammalian cell lines, insect cells, and stem cells used in Brazilian biotech R&D and small-scale production. CellCulture's domestic supply of cell culture inputs reduces the importation dependency and customs delays that constrain Brazilian biotech laboratories and emerging biomanufacturers."),

  ("salmoss-biotech-cl", 0.85,
   "SALMOSS Biotech extracts and processes hydroxyapatite and collagen from salmon processing byproducts to produce bone and dental graft biomaterials for medical and veterinary orthopedic applications. Founded in 2022, the Chilean startup transforms what are currently discarded salmon bones and cartilage into purified, sterilized HAp scaffolds with mineral composition closely matching human bone, offering a cost-competitive alternative to bovine and synthetic bone graft materials for reconstructive surgery. SALMOSS creates circular value from Chile's massive salmon industry waste stream while addressing a domestic biomaterials import dependency."),

  ("aquabio-cl", 0.80,
   "AquaBio develops biotechnology solutions for disease detection and health management in Chilean aquaculture operations. The company provides diagnostic services, biological health products, and monitoring platforms for salmon and other farmed species, integrating molecular diagnostics with environmental microbiology assessments to give farm managers a comprehensive picture of pathogen pressure and biosecurity risk. AquaBio's integrated health intelligence approach supports the Chilean aquaculture sector's transition from reactive antibiotic use to proactive biological disease management."),

  ("fungicontrol-co", 0.85,
   "FungiControl develops biological fungicides and disease management solutions for Colombian agriculture using specially selected fungal strains and plant-derived antifungal compounds. The company produces mycoparasitic fungi formulations that colonize and destroy pathogenic fungus hyphae in soil and on crop surfaces, providing residue-free control of Botrytis, Phytophthora, and Fusarium infections in coffee, flowers, and vegetables. FungiControl's biological fungicide portfolio enables Colombian growers to meet export market residue requirements while preserving beneficial soil microbial communities."),

  ("biocell-mx", 0.85,
   "BioCell Mexico manufactures patented collagen-based bioingredients—including hydrolyzed collagen peptides, native collagen fibers, and collagen-elastin complexes—extracted from animal hides and bones using enzymatic and biological processing methods. The company's bioactive collagen products serve the functional food, nutraceuticals, cosmetics, and pharmaceutical industries with clinically validated raw materials that support joint health, skin elasticity, wound healing, and bone density. BioCell's bio-based collagen manufacturing positions Mexico as an exporter of high-value biological ingredients derived from the domestic livestock processing sector."),

  ("oncoprecision-ar", 0.90,
   "OncoPrecision develops patient-derived therapeutic antibodies targeting cancer treatment gaps identified through individual tumor genomic and proteomic profiling. The Argentine biotech uses patient biopsy data to identify tumor-specific surface antigens and neoepitopes, then engineers antibody candidates—including bispecifics and ADC payloads—tailored to each patient's cancer molecular signature. OncoPrecision's precision oncology approach addresses the fundamental limitation of standard-of-care chemotherapy: non-selectivity that damages healthy tissue while missing tumor subclones with acquired resistance mechanisms."),

  ("devalor-cl", 0.82,
   "DeValor develops aquaculture biotechnology solutions for Chilean salmon and mussel farming, focusing on disease diagnostics, nutritional supplements, and biological health products that improve survival rates and production efficiency. The company produces functional feed additives incorporating immunostimulants, prebiotics, and botanical extracts that strengthen fish immune competence, combined with rapid field diagnostic kits for early pathogen detection. DeValor's integrated approach to aquaculture health management reflects the sector's shift from reactive antibiotic treatment toward proactive biological disease prevention."),

  ("biowit-mx", 0.88,
   "BIOWIT develops point-of-care molecular diagnostic technologies that bring laboratory-level accuracy to rural Mexican clinics and underserved communities lacking access to centralized laboratory infrastructure. The company's biosensor and lateral flow assay platforms detect infectious disease pathogens, metabolic biomarkers, and food safety contaminants using minimally trained operators and minimal equipment, with results in under 30 minutes. BIOWIT's accessible diagnostics address Mexico's significant rural-urban health equity gap by enabling clinically actionable disease detection at the primary care level."),

  ("cellva-ingredients-br", 0.88,
   "Cellva Ingredients uses cellular agriculture to produce microencapsulated food ingredients—flavor compounds, vitamins, pigments, and bioactive lipids—through precision fermentation and cell culture processes that replace conventional plant or animal extraction. The Brazilian startup's microencapsulation platform enables the production of standardized, stable ingredient concentrates with superior bioavailability and shelf life for the functional food and nutraceuticals industries, reducing supply chain variability inherent in agricultural extraction of bioactive compounds."),

  ("consiste-br", 0.85,
   "Consiste develops biopreservatives and natural antimicrobial formulations for Brazil's food industry, producing protective bacterial cultures, bacteriocins, and plant extract concentrates that extend product shelf life without synthetic preservatives. The company's natural antimicrobial systems target Listeria, Salmonella, and spoilage fungi in processed meats, dairy, and ready-to-eat foods, enabling Brazilian food manufacturers to achieve clean-label formulation compliance while maintaining food safety standards required for export to the EU and US markets."),

  ("cepha-biotech-br", 0.90,
   "CEPHA Biotech develops low-cost portable molecular diagnostic systems using synthetic biology-based detection mechanisms that bring nucleic acid testing capabilities outside centralized laboratories. The Brazilian startup engineers cell-free biosensors and CRISPR-Cas detection systems integrated into compact field-deployable devices for pathogen identification in clinical, veterinary, and agricultural settings. CEPHA's democratized molecular diagnostics address the critical gap between laboratory-grade sensitivity and the point-of-care accessibility required in Brazil's vast interior regions and the global South's underserved healthcare systems."),

  ("hem-healthtech-co", 0.92,
   "Hem Healthtech develops paper-based point-of-care diagnostic platforms for blood analysis, spun out from Universidad de los Andes in Colombia. The startup's microfluidic paper analytical devices (µPADs) perform complete blood count, coagulation panels, and metabolic biomarker measurements from a single fingerstick blood drop, providing laboratory-grade results in minutes without refrigerated reagents or trained laboratory technicians. Hem's low-cost, equipment-free diagnostics are engineered specifically for primary care settings in Colombia and Latin America's resource-limited healthcare infrastructure."),

  ("labtronics-sas-co", 0.82,
   "Labtronics SAS develops and commercializes PCR molecular diagnostics and genetic testing platforms for clinical, veterinary, and food safety applications in Colombia. The company produces validated molecular diagnostic kits for infectious disease detection, pathogen genotyping, and genetic screening that meet ISO and INVIMA regulatory standards, serving public health laboratories, private clinics, and food quality control facilities. Labtronics builds Colombia's domestic molecular diagnostics manufacturing capacity, reducing dependency on imported kits for critical disease surveillance programs including tuberculosis, HIV, and tropical infectious diseases."),

  ("alecrim-biotech-br", 0.90,
   "Alecrim Biotech uses precision fermentation to produce plant-based protein ingredients from fungal and microbial biomass as alternatives to animal-derived proteins, backed by FAPESP research grants. The Brazilian startup engineers mycoprotein production through optimized solid-state and submerged fermentation processes using food-grade fungal strains, producing protein concentrates with complete amino acid profiles and functional texturizing properties for the plant-based meat and dairy alternative sectors. Alecrim converts Brazil's abundant agricultural feedstocks into high-value precision fermentation proteins for the global alternative protein transition."),

  ("nutrissis-biotech-br", 0.88,
   "Nutrissis Biotech produces biofortified proteins through metabolic engineering and strain optimization of microbial production hosts, supported by FAPESP and CNPq grants. The Brazilian startup develops fermentation strains that overproduce essential amino acids, vitamins, and bioactive peptides integrated directly into protein matrices, creating nutritionally superior protein ingredients for functional foods and clinical nutrition applications. Nutrissis's approach to protein biofortification through fermentation strain engineering represents an alternative to conventional vitamin fortification that adds nutrients post-production rather than biosynthesizing them."),

  ("cellmeat-brasil-br", 0.88,
   "Cellmeat Brasil develops cultivated meat bioreactor infrastructure and bioprocess engineering for large-scale animal cell cultivation, positioning Brazil to become a manufacturer and technology exporter for the global cultivated protein sector. The company focuses on the critical scaling challenge of cultivated meat: designing cost-effective bioreactors, scaffold systems, and culture media formulations that enable continuous cell expansion at commercially viable production costs. Brazil's combination of bioprocess engineering expertise, large domestic food market, and low-cost agricultural inputs makes Cellmeat's infrastructure play strategically significant for the cultivated protein industry's global scaling ambitions."),

  ("myvac-bioproducts-br", 0.85,
   "Myvac Bioproducts manufactures industrial enzymes and biological active compounds through fermentation-based bioprocessing for the food, feed, agricultural, and pharmaceutical industries in Brazil. The company produces protease, amylase, cellulase, and specialty enzyme formulations at industrial scale using domestically optimized microbial production strains, serving Brazilian agro-industrial clients requiring high-volume enzyme supply at competitive prices. Myvac reduces Brazil's industrial enzyme import dependency by building domestic manufacturing capacity for functional biologics that are currently dominated by European and North American producers."),

  ("microbiota-agricola-br", 0.90,
   "Microbiota Agricola develops agricultural bioinputs from Amazonian microbial biodiversity, isolating and formulating bacterial and fungal strains from Brazil's rainforest and Cerrado biomes with unique capacities for nitrogen fixation, phosphate solubilization, and plant hormone production. Operating from TecnoPARQ-UFV technology park, the company produces liquid and granular biofertilizer and biostimulant formulations validated in Brazilian tropical soils, offering growers biological alternatives to synthetic inputs rooted in the most biodiverse terrestrial ecosystem on Earth."),
]

with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for eid, conf, summary in summaries:
        w.writerow([eid, "startup_extended", "startup_summary_en",
                    summary, src, conf, f"swarm_inline_summary {date}"])

total = sum(1 for _ in open(out, encoding="utf-8")) - 1
print(f"Summaries batch 2: {len(summaries)} filas. Total entity_enrichments: {total}")
