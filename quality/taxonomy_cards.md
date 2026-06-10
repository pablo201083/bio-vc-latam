# Fichas de Taxonomía — Universo BIO VC LATAM

_Generado 2026-06-10 desde `src/reclassify.py` (THEMES) + la DB. Regenerar con `python pipeline.py taxonomy-cards`._

La taxonomía operativa es **single-level**: un tema primario por startup. Estas 8 fichas son la referencia legible para terceros y el estándar contra el que se valida cada clasificación. El principio de desambiguación es **el destino del output**, no el mecanismo biológico.

**496 startups `include`** distribuidas en 8 temas.

| Tema | n | Cross-cutting |
|------|---|---------------|
| Diagnostics & Health Access | 111 | — |
| Therapeutics | 78 | — |
| Farm Intelligence | 67 | — |
| Bioinputs & Crop Resilience | 66 | — |
| Food Systems & Alt Proteins | 64 | — |
| Biomaterials & Circular Economy | 54 | — |
| Nature & Ecosystem Tech | 35 | — |
| Biomanufacturing & Platform Technologies | 21 | transversal |


---

## Diagnostics & Health Access  ·  111 startups

**Definición.** Companies applying biology to detect, monitor, or measure human disease. Includes molecular diagnostics, point-of-care testing, biosensors, medical devices with biological components, fertility diagnostics, spectral/imaging diagnostics, and digital health platforms where a biological assay is the core component.

**Fronteras (cómo se decide en casos límite).**

- vs **Therapeutics**: Diagnostics *detecta/mide/monitorea* enfermedad; Therapeutics *interviene para tratar*. Un test molecular → Diagnostics; una terapia celular → Therapeutics.
- vs **Biomanufacturing**: si el core es un ensayo biológico de detección → Diagnostics; si es producir el biológico → Biomanufacturing.

**Startups arquetípicas** (mayor confianza, con fuente externa):

- **Caspr Biotech** (CL) — Develops rapid molecular diagnostic tests using proprietary Cas proteins discovered in extremophiles — novel CRISPR nucleases beyond Cas9/Cas12 — enabling point-of-care diagnostics from extremophile-derived biology.
- **Embryoxite** (AR) — Non-invasive IVF diagnostic.
- **MZP** (AR) — Advanced coagulation diagnostics for critical care.
- **Bleps Vision** (CL) — Dispositivo portatil de salud visual para diagnostico corneal.
- **Limay Biosciences** (AR) — Portable molecular diagnostics company.

**Queda explícitamente afuera.**

- Telemedicina/EHR sin ensayo biológico como core.
- Wearables de consumo sin valor diagnóstico clínico.


---

## Therapeutics  ·  78 startups

**Definición.** Companies developing treatments that intervene in human or animal biology to cure, manage, or prevent disease: drug discovery, biologics, monoclonal antibodies, biosimilars, cell/gene therapy, mRNA therapeutics, oncology, rare diseases, regenerative medicine, nanomedicine, veterinary therapeutics, and drug delivery systems.

**Fronteras (cómo se decide en casos límite).**

- vs **Diagnostics & Health Access**: el output es un tratamiento (droga, biológico, terapia celular/génica), no una medición.
- vs **Biomanufacturing**: descubrir/desarrollar la terapia → Therapeutics; producir el biológico a escala como plataforma → Biomanufacturing.

**Startups arquetípicas** (mayor confianza, con fuente externa):

- **Autem Medical** (BR) — Non-invasive electromagnetic oncology treatment platform.
- **HeXemBio** (US) — Hematopoietic stem-cell rejuvenation therapy platform.
- **Ayuvant** (NL) — Biotech terapeutica basada en RNA nanoparticle immunotherapy.
- **Exomas** (AR) — Terapias neuroregenerativas basadas en exosomas.
- **Mesenchyal-T** (AR) — AI-powered mesenchymal stem-cell therapy for bone regeneration.

**Queda explícitamente afuera.**

- Wellness/suplementos sin desarrollo terapéutico.
- Software de salud sin intervención biológica.


---

## Farm Intelligence  ·  67 startups

**Definición.** Digital intelligence for agriculture: precision farming platforms, agronomic decision tools, satellite/drone monitoring, IoT crop sensors, agrifintech, and farm management software.

**Fronteras (cómo se decide en casos límite).**

- vs **Bioinputs & Crop Resilience**: Farm Intelligence es *software/datos* (sensores, satélite, agrofintech); Bioinputs es un *producto biológico* aplicado al cultivo.
- vs **Nature & Ecosystem Tech**: si el objeto es el rendimiento del productor → Farm Intelligence; si el objeto es el ecosistema/carbono/biodiversidad → Nature.

**Startups arquetípicas** (mayor confianza, con fuente externa):

- **Aegro** (BR) — Farm operations and financial management platform.
- **Agrosmart** (BR) — Climate-smart agronomic and irrigation intelligence platform.
- **BemAgro** (BR) — AI and drone-imagery SaaS for high-resolution crop intelligence.
- **Precision Ag** (BR) — Agricultural drone spraying and crop-monitoring services.
- **Seedz** (BR) — Agribusiness loyalty, marketplace and producer-intelligence platform.

**Queda explícitamente afuera.**

- Fintech agrícola sin acople biológico ni de recursos (crédito puro, marketplace).
- Logística/trading de commodities como software horizontal.


---

## Bioinputs & Crop Resilience  ·  66 startups

**Definición.** Biological inputs for agriculture and biological interventions in crop/plant systems: biofertilizers, biostimulants, biopesticides, biocontrol agents, CRISPR/gene-edited crop varieties, precision breeding, seed treatments, plant tissue culture, entomopathogenic solutions.

**Fronteras (cómo se decide en casos límite).**

- vs **Farm Intelligence**: el output es un insumo biológico (biofertilizante, biocontrol, semilla editada), no una plataforma digital.
- vs **Food Systems**: si la biología termina en el cultivo/suelo → Bioinputs; si el output se ingiere → Food Systems.

**Startups arquetípicas** (mayor confianza, con fuente externa):

- **Bsafe Biotech** (BR) — Brazilian agricultural biocontrol company developing biological pest-control solutions with a novel mode of action designed to be safe by design, targeting crop protection for South American farmers from São Paulo.
- **Solubio Tecnologias Agricolas** (BR) — On-farm biological input production system.
- **BUG Agentes Biologicos** (BR) — Macrobial biological control company.
- **Decoy** (BR) — Innovative biological pesticides for livestock and agriculture.
- **MicroIN** (AR) — Microencapsulation for bioinputs.

**Queda explícitamente afuera.**

- Agroquímicos sintéticos convencionales sin componente biológico.


---

## Food Systems & Alt Proteins  ·  64 startups

**Definición.** Companies whose OUTPUT goes into human or animal food/nutrition: precision fermentation for food proteins/dairy/fats, novel food ingredients, functional foods, nutraceuticals, prebiotics/probiotics (food context), plant-based food products, cultivated/cell-based meat, insect protein, aquaculture biotech, and food biopreservation.
Key distinction from Biomaterials: the END PRODUCT is ingested (food, supplement, ingredient) — not a material, packaging, or industrial chemical.

**Fronteras (cómo se decide en casos límite).**

- vs **Biomaterials**: misma biología (fermentación), distinto destino — si el producto final se **ingiere** (alimento, ingrediente, suplemento) → Food; si es material/químico/energía → Biomaterials.
- vs **Bioinputs**: el output es comida/nutrición humana o animal, no un insumo de campo.

**Startups arquetípicas** (mayor confianza, con fuente externa):

- **Algalife** (AR) — Develops a technology platform for optimizing industrial microalgae cultivation and production processes, targeting productivity and efficiency improvements in biobased manufacturing.
- **BioBlends** (AR) — Food preservation biotech for clean-label shelf-life extension.
- **Cellva** (BR) — Microencapsulated functional ingredients for food and beverage.
- **Future Cow** (BR) — Produces animal-free casein and whey dairy proteins via precision fermentation by inserting cow protein genes into microorganisms, delivering dried powder ingredients for ice cream, cheese, and dairy applications. São Paulo, Brazil.
- **Innovai** (CL) — Seafood shelf-life bioactive coating platform.

**Queda explícitamente afuera.**

- Marcas de alimentos sin tecnología bio/proceso novedoso.
- Delivery/retail de comida.


---

## Biomaterials & Circular Economy  ·  54 startups

**Definición.** Companies using biological processes to produce materials, chemicals, or energy carriers replacing petrochemical equivalents. The OUTPUT is a material, industrial chemical, or energy product — not food.
Covers bioplastics, biopolymers, mycelium materials, biobased packaging, industrial enzymes (non-food), green chemistry, e-fuels, biogas for energy.

**Fronteras (cómo se decide en casos límite).**

- vs **Food Systems**: el output es un **material, químico industrial o vector energético** (bioplástico, enzima industrial, e-fuel), no alimento.
- vs **Biomanufacturing**: Biomaterials nombra el *producto* (material/circular); Biomanufacturing nombra la *plataforma/capacidad* de producción transversal.

**Startups arquetípicas** (mayor confianza, con fuente externa):

- **Calfix** (AR) — Biotech concrete crack repair platform.
- **CyanoMin** (AR) — Biological desalination and mineral recovery from hypersaline brines.
- **INMET** (AR) — Compostable PHB biopolymer from agro-industrial waste.
- **POLYMERA** (UY) — Bio-based biodegradable superabsorbent polymers.
- **Bioplastix** (AR) — Engineers E. coli and Halomonas bacteria to intracellularly produce PLA and PHB bioplastics from agro-industrial waste sugars using AI-guided precision fermentation. Scaling from UNAM labs in Cuernavaca, Mexico with Argentina operations.

**Queda explícitamente afuera.**

- Reciclaje mecánico o gestión de residuos sin transformación biológica.
- Energía renovable sin componente bio/material (paneles, software de red puro).


---

## Nature & Ecosystem Tech  ·  35 startups

**Definición.** Companies applying technology to protect, restore, or monitor natural ecosystems: carbon removal/sequestration, reforestation tech, biodiversity monitoring, ocean/aquatic ecosystem health, bioremediation, water quality, satellite forest monitoring, and ecosystem service markets.

**Fronteras (cómo se decide en casos límite).**

- vs **Farm Intelligence**: el objeto es el ecosistema natural (carbono, biodiversidad, agua, bosque, océano), no la productividad agrícola.
- vs **Bioinputs**: la biorremediación y el monitoreo ambiental van acá; la intervención sobre el cultivo va a Bioinputs.

**Startups arquetípicas** (mayor confianza, con fuente externa):

- **Waterplan** (AR) — AI-native water-risk and stewardship platform.
- **Carbonext** (BR) — Nature-based carbon and forest conservation platform.
- **Moss** (BR) — Carbon credit and nature-finance infrastructure.
- **Nideport** (AR) — Nature restoration and carbon-credit platform.
- **Mombak** (BR) — Large-scale native biodiverse reforestation platform.

**Queda explícitamente afuera.**

- Mercados de carbono puramente financieros sin base natural/tecnológica.
- ESG/reporting como software horizontal.


---

## Biomanufacturing & Platform Technologies  ·  21 startups

**Definición.** Plataformas y capacidades de producción biológica que sirven a múltiples verticales: fermentación de precisión, biología sintética/cell-free, enzimas, escalado de bioprocesos, biofoundries y digital twins de bioproceso. El valor es la capacidad de *producir* lo biológico, no un producto final de consumo.

> ⚠️ Este tema existe en la DB pero **no** en el clasificador `src/reclassify.py`. Correr `reclassify-themes` reasignaría estas startups a uno de los otros 7. Unificar antes de un rebuild de temas.

**Fronteras (cómo se decide en casos límite).**

- Tema **transversal**: plataformas de producción biológica (fermentación de precisión, biología sintética, enzimas, escalado de bioprocesos) que sirven a varios verticales.
- Regla: si la empresa *vende la capacidad/plataforma* → Biomanufacturing; si vende el *producto final* (alimento, material, terapia) → el tema de ese producto.

**Startups arquetípicas** (mayor confianza, con fuente externa):

- **HARMONY** (BR) — Precision fermentation platform producing human milk oligosaccharides (HMOs) and bioactive proteins for infant nutrition. Technology is biomanufacturing; market is food/nutrition. Bridges both themes.
- **SpecLab** (BR) — AI spectral analytics and laboratory digitization platform.
- **Biolinker Synthetic Biology** (BR) — Cell-free protein expression and synthetic-biology platform.
- **Mavios** (AR) — AI-based digital twin for bioprocess scale-up.
- **APEXzymes** (BR) — Industrial enzyme company using circular feedstocks.

**Queda explícitamente afuera.**

- Manufactura industrial sin base biológica.
- Automatización genérica de laboratorio sin foco bio.
