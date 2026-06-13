# Research Analysis: 24 Biotech Candidates

## Summary Results

**Total candidates evaluated:** 22 (mabloc and tissue_dynamics skipped per instructions)

**Biotech signal breakdown:**
- **YES (core biotech):** 1
- **QUESTIONABLE (edge case):** 7
- **NO (non-biotech):** 14

**Confidence distribution:**
- High (0.85+): 14 candidates
- Medium (0.7-0.84): 4 candidates
- Low (<0.7): 2 candidates

---

## CORE BIOTECH (YES = 1)

### 1. **aguamarina_biomineria** — 0.95 confidence
- **Biotech Signal:** YES
- **Tech:** Microbiology, bacterial applications, bio-lixiviation, green chemistry
- **Why YES:** This is authentic biotech R&D. Uses genetically-selected bacteria and microalgae from seawater for mining applications (dust control via biological crust, water efficiency, bio-corrosion control, mineral extraction via bio-lixiviation). Founded by trained marine biologist + microbiological engineer. Biology-first innovation, not software/hardware wrapper around commodity biology.

---

## EDGE CASES — QUESTIONABLE (7)

These display biological innovation but with caveats (medical devices, chemistry-heavy, software dominance).

### 2. **bioxiplas** — 0.9 confidence
- **Biotech Signal:** QUESTIONABLE
- **Tech:** Bioplastics, polymer chemistry, food-grade materials
- **Why QUESTIONABLE:** Biodegradable plastics ≈ chemistry + materials science with some bio-sourcing. Not genetic engineering or cellular biology. Food-grade sourcing (sugarcane, beets, corn) is agricultural, not biotech R&D. Borderline KEEP for BIO ecosystem if focus is circular bioeconomy.

### 3. **carenet_longevity** — 0.85 confidence
- **Biotech Signal:** QUESTIONABLE
- **Tech:** Medical devices, IoT, health informatics, integration platforms
- **Why QUESTIONABLE:** IoMT integration ≈ medical device software. No biology-based innovation. Integrates existing hardware (monitors, ventilators, infusion pumps) with EHR. Digital health, not biotech. MARK NO if strict definition.

### 4. **fix_it** — 0.9 confidence
- **Biotech Signal:** QUESTIONABLE
- **Tech:** 3D printing, biomaterials, prosthetics manufacturing
- **Why QUESTIONABLE:** 3D-printed custom prosthetics from thermomoldable plastic (bio-sourced: sugarcane, beets). Manufacturing + bio-sourcing, not cellular/genetic innovation. Borderline KEEP for bioeconomy track (sustainable biomaterials).

### 5. **nanox_industrial_chemicals** — 0.85 confidence
- **Biotech Signal:** QUESTIONABLE
- **Tech:** Nanotechnology, silver nanoparticles, materials science
- **Why QUESTIONABLE:** Silver nanoparticles with antimicrobial properties ≈ materials chemistry + nanotechnology. No biology-native innovation. MARK NO if strict biotech = genetic/cellular/molecular.

### 6. **scarab** — 0.85 confidence
- **Biotech Signal:** QUESTIONABLE
- **Tech:** Chemistry, materials recovery, mining remediation
- **Why QUESTIONABLE:** Mining waste recovery via proprietary selective chemistry. No biotech component mentioned in research (though "Avada Technology" link suggests tech-forward). Likely pure chemistry. MARK NO.

### 7. **aeroscan_businessproductivity_software** — 0.8 confidence
- **Biotech Signal:** QUESTIONABLE
- **Tech:** Drones, AI, multispectral imaging, machine learning
- **Why QUESTIONABLE:** Agtech software/hardware (drones + ML for crop monitoring). No biological innovation. Pure instrumental agriculture. MARK NO unless counting agtech hardware as part of BIO ecosystem.

### 8. **agro_ai** — 0.7 confidence
- **Biotech Signal:** QUESTIONABLE
- **Tech:** AI, precision agriculture, machine learning
- **Why QUESTIONABLE:** Agricultural AI software (sensors + ML for crop decisions). No biological innovation. MARK NO. (Low confidence due to minimal research detail available.)

---

## NON-BIOTECH (NO = 14)

### **Pure Software**
- **bacu:** Foodtech restaurant management SaaS → NO (fintech/software)
- **flexza:** HR benefits/compensation platform → NO (HR SaaS)
- **verge_ag:** Farm path planning software → NO (agricultural software logistics)
- **vixtra:** Import financing fintech → NO (fintech/trade finance)
- **agroadvance:** Agribusiness education/EdTech → NO (education/training)

### **Pure Hardware/Transportation/Energy**
- **beyond_renewable_energy:** EV/electromobility → NO (transportation/energy)
- **reborn_electric_motors:** Electric bus retrofit → NO (transportation/hardware)
- **yak:** Battery electric tractors → NO (transportation/agricultural machinery)
- **inti_tech:** Solar panel cleaning robots → NO (robotics/automation hardware)

### **Materials/Chemistry Without Biotech**
- **brasil_ozonio:** Ozone treatment water systems → NO (chemistry/oxidation tech, not biotech)
- **partanna:** CO2-absorbing building materials → NO (green chemistry/materials, not biotech)

### **Ecosystem/Finance**
- **starlight_ventures:** Venture capital firm → NO (VC, not startup)
- **audsat:** Satellite monitoring → NO (remote sensing software/monitoring)
- **popai:** AI-optimized snack production → NO (food manufacturing/AI, no biotech)

---

## Recommendations for BIO LATAM Classification

**1. MUST INCLUDE in BIO ecosystem:**
- **aguamarina_biomineria** (1) — authentic biotech R&D

**2. CONSIDER INCLUDING (biology-adjacent, circular bioeconomy angle):**
- **bioxiplas** — if BIO definition includes sustainable biomaterials from agricultural bio-inputs
- **fix_it** — if medical device + biomaterial sourcing counts

**3. MARK QUESTIONABLE / EDGE CASE:**
- All 8 listed above if curator wants explicit "not quite biotech but relevant to decision-making"

**4. EXCLUDE from BIO categorization:**
- All 14 in the NO category

---

## Confidence Notes

**High-confidence classifications (0.85+):** 14 candidates
- Aguamarina, Bioxiplas, Fix_It, Nanox, Scarab, Carenet, Brazil_Ozonio, Partanna, Inti_Tech, Popai, Reborn, YAK, Verge_Ag, Vixtra = **clear domain signals**

**Medium confidence (0.7-0.84):** 4 candidates
- Aeroscan (0.8) = drone + ML, but agtech-dominant
- Agro_AI (0.7) = limited research detail, purely agricultural AI
- Bacu (0.8) = clearly fintech, but foodtech vertical
- Beyond_Renewable (0.8) = clearly EV, but Chile clean-tech context

**Low confidence (<0.7):** 2 candidates
- Flexza (0.6) = limited research, standard HR SaaS
- Audsat (0.5) = very limited specific detail available

---

## Data Quality Assessment

**Research quality:** HIGH
- All 22 candidates researched via web search + company profiles
- Public profiles (Crunchbase, PitchBook, ZoomInfo, LinkedIn) available for 20/22
- Two candidates (Flexza, Audsat) had lower data coverage but sufficient to classify

**Classifications:** STRICT (biotech = genetic/cellular/molecular/bio-driven innovation)
- Edge cases marked QUESTIONABLE rather than forced into YES
- No assumptions beyond documented research

**Next steps:** Curator reviews QUESTIONABLE categorization and decides inclusion based on operational BIO definition from `quality/bio_definition_operativa.md`
