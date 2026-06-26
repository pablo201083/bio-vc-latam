# Estructura de Inversión — BIO VC LATAM

_Generado 2026-06-25 con `python pipeline.py capital-structure`. Cuenta EMPRESAS por stage (no dólares: solo 10% de aristas tiene monto). El stage es el más avanzado entre las aristas reales con round_stage._

## Pirámide de stages (global)

- **Pre-seed / Accelerator**: 61 ████████████
- **Seed**: 164 ████████████████████████████████
- **Series A**: 42 ████████
- **Growth (B–D)**: 17 ███
- **Exit / IPO**: 5 █

## Pirámide por tema — ¿base sin cúspide?

| Tema | Pre-seed | Seed | Ser.A | Growth | Exit | Sin capital | A→Growth |
|------|---------|------|-------|--------|------|-------------|----------|
| Diagnostics & Devices | 12 | 35 | 12 | 4 | 0 | 58 | 0.34 |
| Therapeutics | 12 | 33 | 6 | 1 | 0 | 45 | 0.16 |
| Food Systems & Alt Proteins | 11 | 21 | 4 | 0 | 1 | 58 | 0.16 |
| Bioinputs & Crop Resilience | 8 | 21 | 3 | 3 | 2 | 39 | 0.28 |
| Biomaterials & Green Chemistry | 11 | 16 | 5 | 2 | 0 | 24 | 0.26 |
| Nature & Ecosystem Tech | 0 | 17 | 5 | 3 | 1 | 8 | 0.53 |
| Precision Agriculture | 0 | 14 | 6 | 2 | 1 | 39 | 0.64 |
| Biomanufacturing & Platform Technologies | 7 | 7 | 1 | 2 | 0 | 13 | 0.21 |

## Dependencia de capital extranjero por tema

| Tema | Aristas | Extranjeras | % extranjero |
|------|---------|-------------|--------------|
| Precision Agriculture | 91 | 37 | 40% |
| Nature & Ecosystem Tech | 117 | 29 | 24% |
| Biomanufacturing & Platform Technologies | 80 | 13 | 16% |
| Biomaterials & Green Chemistry | 135 | 21 | 15% |
| Food Systems & Alt Proteins | 161 | 25 | 15% |
| Bioinputs & Crop Resilience | 216 | 33 | 15% |
| Diagnostics & Devices | 247 | 24 | 9% |
| Therapeutics | 205 | 11 | 5% |

## Concentración de capital por tema (HHI)

> ⚠️ **Sesgo de recolección:** GridX aparece dominante en casi todos los temas porque su portfolio se barrió exhaustivamente (ver Frente A / `coverage`). La concentración real es menor; leer junto al mapa de cobertura, no como verdad de mercado.

| Tema | HHI | # inversores | Inversor dominante | Share |
|------|-----|--------------|--------------------|-------|
| Biomanufacturing & Platform Technologies | 0.259 | 20 | GridX | 48% |
| Biomaterials & Green Chemistry | 0.25 | 31 | GridX | 48% |
| Therapeutics | 0.182 | 29 | GridX | 38% |
| Food Systems & Alt Proteins | 0.169 | 37 | GridX | 38% |
| Diagnostics & Devices | 0.128 | 45 | GridX | 30% |
| Precision Agriculture | 0.096 | 25 | the_yield_lab_latam | 19% |
| Bioinputs & Crop Resilience | 0.095 | 48 | GridX | 25% |
| Nature & Ecosystem Tech | 0.087 | 30 | Antom | 20% |

## Sindicación (co-inversión)

322 pares de fondos co-invierten en ≥2 startups. Más sindicados:

- **GridX**: co-invierte con 44 fondos distintos
- **AIR Capital**: co-invierte con 38 fondos distintos
- **the_yield_lab_latam**: co-invierte con 34 fondos distintos
- **SOSV_IndieBio**: co-invierte con 32 fondos distintos
- **sp_ventures**: co-invierte con 31 fondos distintos
- **SF500**: co-invierte con 21 fondos distintos
- **DraperCygnus**: co-invierte con 19 fondos distintos
- **DragonesVP**: co-invierte con 17 fondos distintos
- **sosv**: co-invierte con 17 fondos distintos
- **kamay_ventures**: co-invierte con 15 fondos distintos
- **glocal**: co-invierte con 14 fondos distintos
- **inventure**: co-invierte con 14 fondos distintos

Top pares:

- AIR Capital + GridX: 104 startups en común
- GridX + SOSV_IndieBio: 73 startups en común
- AIR Capital + DraperCygnus: 69 startups en común
- Antom + glocal: 57 startups en común
- DragonesVP + DraperCygnus: 35 startups en común
- AIR Capital + SOSV_IndieBio: 33 startups en común
- GridX + zentynel: 28 startups en común
- GridX + The Ganesha Lab: 27 startups en común

## Capital no documentado

218 startups include sin ninguna arista de capital. Por tema:

- **Diagnostics & Devices**: 48/121 (39%)
- **Food Systems & Alt Proteins**: 42/95 (44%)
- **Therapeutics**: 39/97 (40%)
- **Precision Agriculture**: 28/62 (45%)
- **Bioinputs & Crop Resilience**: 28/76 (36%)
- **Biomaterials & Green Chemistry**: 18/58 (31%)
- **Biomanufacturing & Platform Technologies**: 11/30 (36%)
- **Nature & Ecosystem Tech**: 4/34 (11%)
