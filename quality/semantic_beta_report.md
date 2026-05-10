# Semantic Taxonomy Beta

Generated at: 2026-04-24 11:56:38

## Scope

- Universe used: include + confirmed only
- Startups clustered: 234
- Candidate cluster counts tested: 7, 8, 9, 10
- Selected cluster count: 10
- Best cluster quality score: 0.3246

## Method

- Pure text clustering over audited startup text fields
- Vocabulary built from TF-IDF over include + confirmed startups
- Candidate cluster counts evaluated in a short range to avoid category explosion
- Themes named after clustering using dominant macro-context and top semantic tokens

## Candidate K Scores

- k=7: score=0.2852, avg_margin=0.1793, avg_within=0.3025, small_clusters=0
- k=8: score=0.3189, avg_margin=0.2043, avg_within=0.3274, small_clusters=0
- k=9: score=0.322, avg_margin=0.2132, avg_within=0.3363, small_clusters=1
- k=10: score=0.3246, avg_margin=0.2118, avg_within=0.3451, small_clusters=1

## Theme Snapshot

### ag biologicals and crop resilience (56)

- Description: Startups que intervienen directamente sobre cultivos, bioinsumos, microbiomas, polinizacion o resiliencia agropecuaria con biologia aplicada.
- Top tokens: crop; resilience; biologicals; precision; resource; climate; monitoring; monitoreo
- Representative startups: Gênica; Branch Energy; Arakion; Neocrop Technologies
- Majority current macro theme: ag biologicals and crop resilience
- Match GRIDX: Agri-food-land use
- Lens Antom: despliegue / intervencion
- Low confidence assignments: 11
- Cluster quality: promising (86.3/100)

### food ingredients and biofactories (43)

- Description: Startups que usan biologia, fermentacion o microorganismos para producir ingredientes, proteinas o mejoras funcionales en sistemas alimentarios.
- Top tokens: ingredients; precision; produce; novel; animal; fermentation; sustainable; proteinas
- Representative startups: APEXzymes; Enzyva; BreakPET; Keclon
- Majority current macro theme: food biotech and novel ingredients
- Match GRIDX: Agri-food-land use / Bio-industry
- Lens Antom: despliegue material
- Low confidence assignments: 3
- Cluster quality: strong (95.1/100)

### resource recovery and remediation (43)

- Description: Startups que recuperan materiales, cierran ciclos o remedian residuos, emisiones y flujos criticos del sistema productivo.
- Top tokens: acople; infraestructura; cadenas; yield; latam; digital; productores; says
- Representative startups: CerradoX; Incluirtec; Radial; Agricapital
- Majority current macro theme: climate, energy and resource systems
- Match GRIDX: Bio-industry / Climate systems
- Lens Antom: restauracion / despliegue material
- Low confidence assignments: 2
- Cluster quality: strong (96.7/100)

### therapeutics and regenerative bio (32)

- Description: Startups que construyen terapias, delivery biologico o medicina regenerativa sobre mecanismos moleculares, celulares o inmunologicos.
- Top tokens: therapeutics; diagnostics; diseases; regenerative; enfermedades; medicine; cancer; terapias
- Representative startups: Libera; Scitherm Therapeutics; Circa Therapeutics; Galtec Life
- Majority current macro theme: therapeutics and regenerative medicine
- Match GRIDX: Human health
- Lens Antom: biocentrico
- Low confidence assignments: 0
- Cluster quality: strong (100/100)

### agri intelligence and traceable markets (28)

- Description: Startups que organizan decision agronomica, trazabilidad, comercializacion o infraestructura transaccional acoplada a cadenas agroalimentarias materiales.
- Top tokens: agtech; animal; precision; intelligence; says; resource; data; claramente
- Representative startups: @Tech; JetBov; TBIT; Sylvarum
- Majority current macro theme: precision agriculture and resource intelligence
- Match GRIDX: Agri-food-land use
- Lens Antom: conexion / despliegue
- Low confidence assignments: 2
- Cluster quality: strong (95/100)

### clinical diagnostics and medical devices (16)

- Description: Startups que diagnostican, detectan o actuan clinicamente sobre sistemas vivos mediante dispositivos, pruebas o plataformas medicas concretas.
- Top tokens: medtech; diagnostics; diagnostico; dispositivos; devices; treatment; tratamiento; ganesha
- Representative startups: AVaTAR MedTech; HIAMET; ViewMind; MZP
- Majority current macro theme: diagnostics and medtech
- Match GRIDX: Human health
- Lens Antom: intervencion clinica sobre sistemas vivos
- Low confidence assignments: 0
- Cluster quality: strong (94/100)

### biobased chemistry and circular materials (13)

- Description: Startups que reemplazan rutas fosiles o contaminantes por quimica verde, biomateriales o circularidad material.
- Top tokens: discovery; drug; diagnostics; descubrimiento; cancer; molecular; medtech; diagnostico
- Representative startups: Aplife Biotech; Ubique Bio; Qnity; Fungi Life
- Majority current macro theme: biobased chemistry and advanced materials
- Match GRIDX: Bio-industry
- Lens Antom: despliegue material / limites planetarios
- Low confidence assignments: 0
- Cluster quality: strong (90/100)

### biomanufacturing and molecular platforms (3)

- Description: Startups que habilitan produccion biologica, herramientas moleculares o manufactura biotecnologica escalable.
- Top tokens: cell; single; biomanufacturing; therapies; stamm; sequencing; related; read
- Representative startups: ArgenTAG; Stämm; Ergo Foods
- Majority current macro theme: biomanufacturing and bioindustrial platforms
- Match GRIDX: Deep-biotech / Bio-industry
- Lens Antom: despliegue material
- Low confidence assignments: 0
- Cluster quality: strong (74/100)

## Notes

- This version no longer assigns startups to hand-built semantic families before clustering.
- Purity now comes from clustering first and naming later.
- Next step should be to improve visual geometry so inter-cluster distances also reflect these proximities.
