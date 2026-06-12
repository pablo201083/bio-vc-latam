# Fichas de Taxonomía — Universo BIO VC LATAM

_Generado 2026-06-10 desde `src/reclassify.py` (THEMES) + la DB. Regenerar con `python pipeline.py taxonomy-cards`._

La taxonomía operativa es **single-level**: un tema primario por startup. Estas fichas son la referencia legible para terceros y el estándar contra el que se valida cada clasificación. El principio de desambiguación es **el destino del output**, no el mecanismo biológico.

**496 startups `include`** distribuidas en 9 temas (8 bio-core/coupled + 1 eco-adjacent).

| Tema | n | bio=0 | Intensidad |
|------|---|-------|------------|
| Diagnostics & Devices | 110 | 2 | bio-core |
| Therapeutics | 81 | 0 | bio-core |
| Food Systems & Alt Proteins | 74 | 0 | bio-core |
| Bioinputs & Crop Resilience | 64 | 0 | bio-core |
| Biomaterials & Green Chemistry | 54 | 3 | bio-core |
| Precision Agriculture *(rearmado)* | 39 | **0** | bio-coupled (B1/B2) |
| **Digital AgTech & Agrifintech** *(nuevo)* | 24 | 24 | **eco-adjacent · is_bio=0** |
| Nature & Ecosystem Tech | 34 | 2 | bio-core |
| Biomanufacturing & Platform Technologies | 27 | 1 | transversal |

> ✅ **Re-audit del flag `is_bio_universe` (P1, 2026-06-12).** El rearme reveló que el flag estaba
> mal puesto de forma sistémica. 17 empresas bio-core estaban marcadas bio=0 (genómica, diagnóstico
> molecular, biomoléculas, fagos, indicadores biológicos) → corregidas a 1
> (`scripts/oneoff/reaudit_is_bio_universe.py`). Universo `is_bio=0`: 56 → 32. Resultado: **todos los
> temas bio quedan ≤6% bio=0** y *Digital AgTech & Agrifintech* es la única capa eco-adjacent. Con el
> flag limpio, Biomaterials (3) y Diagnostics (2) **no necesitan partirse** — sus colas eran ruido,
> no clusters. Los 8 eco-adjacent dispersos (Nexxto, Pixed, CIRCCLO, MUTA, nChemi, Ecotrace, ucrop.it,
> Pharmalens) quedan in-theme con flag (decisión "híbrido").

> ✅ **Rearme ejecutado (2026-06-12).** El viejo Precision Agriculture catch-all (66, 47% bio=0) se
> partió bajo el **gate de acople B1**: 39 quedan (acople a cultivo/hato; **0% bio=0**, homogéneo),
> 24 salen a *Digital AgTech & Agrifintech* (eco-adjacent, is_bio=0), 3 (vertical farming) van a
> Food Systems por destino del output. Reasignación en DB vía `diff_and_log_update`
> (`scripts/oneoff/rearm_farm_intelligence.py`). Todos los temas bio quedan ≤11% bio=0.
>
> ⚠️ El clasificador `src/reclassify.py` todavía tiene un solo "Precision Agriculture" con
> `is_bio_default: False` y keywords de agrifintech — **debe partirse o un `reclassify-themes`
> revierte el rearme.** Mismo estado pendiente que Biomanufacturing.


---

## Diagnostics & Devices  ·  110 startups

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

## Therapeutics  ·  82 startups

**Definición.** Companies developing treatments that intervene in human or animal biology to cure, manage, or prevent disease: drug discovery, biologics, monoclonal antibodies, biosimilars, cell/gene therapy, mRNA therapeutics, oncology, rare diseases, regenerative medicine, nanomedicine, veterinary therapeutics, and drug delivery systems.

**Fronteras (cómo se decide en casos límite).**

- vs **Diagnostics & Devices**: el output es un tratamiento (droga, biológico, terapia celular/génica), no una medición.
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

## Food Systems & Alt Proteins  ·  65 startups

**Definición.** Companies whose OUTPUT goes into human or animal food/nutrition: precision fermentation for food proteins/dairy/fats, novel food ingredients, functional foods, nutraceuticals, prebiotics/probiotics (food context), plant-based food products, cultivated/cell-based meat, insect protein, aquaculture biotech, and food biopreservation.
Key distinction from Biomaterials: the END PRODUCT is ingested (food, supplement, ingredient) — not a material, packaging, or industrial chemical.

**Fronteras (cómo se decide en casos límite).**

- vs **Biomaterials**: misma biología (fermentación), distinto destino — si el producto final se **ingiere** (alimento, ingrediente, suplemento) → Food; si es material/químico/energía → Biomaterials.
- vs **Bioinputs**: el output es comida/nutrición humana o animal, no un insumo de campo.

**Startups arquetípicas** (mayor confianza, con fuente externa):

- **BioBlends** (AR) — Food preservation biotech for clean-label shelf-life extension.
- **Cellva** (BR) — Microencapsulated functional ingredients for food and beverage.
- **Future Cow** (BR) — Produces animal-free casein and whey dairy proteins via precision fermentation by inserting cow protein genes into microorganisms, delivering dried powder ingredients for ice cream, cheese, and dairy applications. São Paulo, Brazil.
- **Innovai** (CL) — Seafood shelf-life bioactive coating platform.
- **Food4You** (AR) — Bacteria-enabled plant-based food enhancement.

**Queda explícitamente afuera.**

- Marcas de alimentos sin tecnología bio/proceso novedoso.
- Delivery/retail de comida.


---

## Precision Agriculture  ·  ~35 startups *(angostado 2026-06-12)*

**Definición.** Inteligencia digital **bio-coupled / TechBio** para agricultura: software, sensores o IA cuyo objeto es un sistema vivo específico — este cultivo, este patógeno, este hato. Cubre agronomía de precisión, fenotipado, genómica/microbioma aplicada, modelos de resistencia a enfermedad, sanidad de hato y riego de precisión atado a la biología del cultivo.

**Gate de admisión (3 condiciones, todas obligatorias)** — `bio_definition_operativa.md` §4:
1. **Foco bio específico** — un organismo/sistema vivo concreto, no "el agro" en general.
2. **Entendimiento bio clave** — incorpora conocimiento biológico real (genómica, fisiología, microbioma, patología, fenotipo).
3. **Soporte tech = representación de la biología** (clase Isomorphic/AlphaFold) — modela/predice/representa el estado biológico. Sensar o rociar un campo, o mover datos, **no** alcanza sin modelo biológico detrás.

Si no cumple las tres → **Digital AgTech & Agrifintech** (eco-adjacent). Un puro sistema de telemetría IoT o data-infrastructure sin modelo biológico es plomería, no TechBio.

> ⚠️ Tema **angostado**. Antes incluía toda la capa digital del agro (agrifintech, marketplaces, ERP). Esa cola eco-adjacent se movió a **Digital AgTech & Agrifintech** (`is_bio_universe=0`). Ver split en `bio_definition_operativa.md`.

**Fronteras (cómo se decide en casos límite).**

- vs **Digital AgTech & Agrifintech**: si el software lee/modula un sistema vivo específico (agronomía de precisión, sanidad de hato) → Precision Agriculture (bio-coupled); si es financiero/marketplace/logístico/ERP sin lectura biológica → Digital AgTech (eco-adjacent). El dominio `agri-food` **no** basta para acople.
- vs **Bioinputs & Crop Resilience**: Precision Agriculture es *software/datos* acoplados al cultivo; Bioinputs es un *producto biológico* aplicado al cultivo.
- vs **Nature & Ecosystem Tech**: si el objeto es el rendimiento del productor → Precision Agriculture; si el objeto es el ecosistema/carbono/biodiversidad → Nature.

**Startups arquetípicas** (bio-coupled, con fuente externa):

- **Agrosmart** (BR) — Climate-smart agronomic and irrigation intelligence platform (acople al cultivo).
- **DeepAgro** (AR) — Computer vision para spraying selectivo sobre maleza/cultivo específico.
- **BemAgro** (BR) — AI and drone-imagery SaaS for high-resolution crop intelligence.
- **Rumina** (BR) — Inteligencia de sanidad y producción de hato lechero.
- **Inspectral** (BR) — Multispectral/hyperspectral imagery para leer estado fisiológico del cultivo.

**Queda explícitamente afuera** (→ Digital AgTech & Agrifintech).

- Agrifintech: crédito/seguro rural, trade-finance, bancos digitales (Agrolend, Agricapital, TerraMagna).
- Marketplaces, tokenización, trazabilidad/logística, ERP de gestión sin lectura biológica.


---

## Digital AgTech & Agrifintech  ·  ~31 startups *(nuevo 2026-06-12 · eco-adjacent · is_bio_universe=0)*

**Definición.** Capa **digital y financiera** que habilita al agro sin acople biológico directo: agrifintech (crédito, seguro, trade-finance), marketplaces y plataformas B2B de insumos/granos, tokenización de commodities, trazabilidad/logística, ERP y farm-management de gestión. Pertenece a la tesis amplia BIO LATAM por el vínculo con la transición del sistema agroalimentario, pero **la biología no es el motor** — es `eco-adjacent` (`scope_decision=include`, `is_bio_universe=0`). No se esconde ni se fuerza a un tema bio.

**Fronteras (cómo se decide en casos límite).**

- vs **Precision Agriculture**: falla el **test de acople** — el software no lee ni modula un sistema vivo específico; sirve a cualquier transacción/gestión agrícola.
- **Crédito/seguro puro sin tesis material** → candidato a `review`/`exclude` (falla *pertenencia*, no solo intensidad). Distinguir del agrifintech que financia la transición agroecológica.

**Startups arquetípicas** (eco-adjacent, con fuente externa):

- **Agrolend** (BR) — Agricultural credit / agfintech (banco digital agro).
- **Agrotoken** (AR) — Tokenización de granos como colateral.
- **Agrofy** (AR) — Marketplace y ecosistema digital de agronegocios.
- **TerraMagna** (BR) — Crédito, receivables e infraestructura de fondos agro.
- **goFlux** (BR) — Freight SaaS B2B para logística agrícola.

**Queda explícitamente afuera.**

- Cualquier empresa con acople biológico directo → Precision Agriculture o Bioinputs.
- Fintech horizontal sin vertical agro → fuera de la tesis (`exclude`).


---

## Bioinputs & Crop Resilience  ·  61 startups

**Definición.** Biological inputs for agriculture and biological interventions in crop/plant systems: biofertilizers, biostimulants, biopesticides, biocontrol agents, CRISPR/gene-edited crop varieties, precision breeding, seed treatments, plant tissue culture, entomopathogenic solutions.

**Fronteras (cómo se decide en casos límite).**

- vs **Precision Agriculture**: el output es un insumo biológico (biofertilizante, biocontrol, semilla editada), no una plataforma digital.
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

## Biomaterials & Green Chemistry  ·  54 startups

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

## Nature & Ecosystem Tech  ·  34 startups

**Definición.** Companies applying technology to protect, restore, or monitor natural ecosystems: carbon removal/sequestration, reforestation tech, biodiversity monitoring, ocean/aquatic ecosystem health, bioremediation, water quality, satellite forest monitoring, and ecosystem service markets.

**Fronteras (cómo se decide en casos límite).**

- vs **Precision Agriculture**: el objeto es el ecosistema natural (carbono, biodiversidad, agua, bosque, océano), no la productividad agrícola.
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

## Biomanufacturing & Platform Technologies  ·  26 startups

**Definición.** Plataformas y capacidades de producción biológica que sirven a múltiples verticales: fermentación de precisión, biología sintética/cell-free, enzimas, escalado de bioprocesos, biofoundries y digital twins de bioproceso. El valor es la capacidad de *producir* lo biológico, no un producto final de consumo.

> ⚠️ Este tema existe en la DB pero **no** en el clasificador `src/reclassify.py`. Correr `reclassify-themes` reasignaría estas startups a uno de los otros 7. Unificar antes de un rebuild de temas.

**Fronteras (cómo se decide en casos límite).**

- Tema **transversal**: plataformas de producción biológica (fermentación de precisión, biología sintética, enzimas, escalado de bioprocesos) que sirven a varios verticales.
- Regla: si la empresa *vende la capacidad/plataforma* → Biomanufacturing; si vende el *producto final* (alimento, material, terapia) → el tema de ese producto.

**Startups arquetípicas** (mayor confianza, con fuente externa):

- **Algalife** (AR) — Develops a technology platform for optimizing industrial microalgae cultivation and production processes, targeting productivity and efficiency improvements in biobased manufacturing.
- **HARMONY** (BR) — Precision fermentation platform producing human milk oligosaccharides (HMOs) and bioactive proteins for infant nutrition. Technology is biomanufacturing; market is food/nutrition. Bridges both themes.
- **SpecLab** (BR) — AI spectral analytics and laboratory digitization platform.
- **Biolinker Synthetic Biology** (BR) — Cell-free protein expression and synthetic-biology platform.
- **Mavios** (AR) — AI-based digital twin for bioprocess scale-up.

**Queda explícitamente afuera.**

- Manufactura industrial sin base biológica.
- Automatización genérica de laboratorio sin foco bio.
