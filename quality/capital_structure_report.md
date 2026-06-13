# Estructura de Inversión — BIO VC LATAM

_Generado 2026-06-12 con `python pipeline.py capital-structure`. Cuenta EMPRESAS por stage (no dólares: solo 10% de aristas tiene monto). El stage es el más avanzado entre las aristas reales con round_stage._

## Pirámide de stages (global)

- **Pre-seed / Accelerator**: 64 ████████████
- **Seed**: 161 ████████████████████████████████
- **Series A**: 42 ████████
- **Growth (B–D)**: 19 ███
- **Exit / IPO**: 5 █

## Pirámide por tema — ¿base sin cúspide?

| Tema | Pre-seed | Seed | Ser.A | Growth | Exit | Sin capital | A→Growth |
|------|---------|------|-------|--------|------|-------------|----------|
| Diagnostics & Devices | 13 | 34 | 12 | 5 | 0 | 46 | 0.36 |
| Therapeutics | 13 | 30 | 6 | 1 | 0 | 31 | 0.16 |
| Bioinputs & Crop Resilience | 9 | 21 | 3 | 4 | 2 | 25 | 0.3 |
| Food Systems & Alt Proteins | 11 | 21 | 4 | 0 | 1 | 37 | 0.16 |
| Biomaterials & Green Chemistry | 11 | 16 | 5 | 2 | 0 | 20 | 0.26 |
| Nature & Ecosystem Tech | 0 | 17 | 5 | 3 | 1 | 8 | 0.53 |
| Precision Agriculture | 0 | 15 | 6 | 2 | 1 | 15 | 0.6 |
| Biomanufacturing & Platform Technologies | 7 | 7 | 1 | 2 | 0 | 10 | 0.21 |

## Dependencia de capital extranjero por tema

| Tema | Aristas | Extranjeras | % extranjero |
|------|---------|-------------|--------------|
| Precision Agriculture | 49 | 15 | 30% |
| Nature & Ecosystem Tech | 53 | 16 | 30% |
| Biomaterials & Green Chemistry | 53 | 16 | 30% |
| Bioinputs & Crop Resilience | 79 | 19 | 24% |
| Food Systems & Alt Proteins | 49 | 9 | 18% |
| Diagnostics & Devices | 103 | 16 | 15% |
| Biomanufacturing & Platform Technologies | 26 | 4 | 15% |
| Therapeutics | 75 | 6 | 8% |

## Concentración de capital por tema (HHI)

> ⚠️ **Sesgo de recolección:** GridX aparece dominante en casi todos los temas porque su portfolio se barrió exhaustivamente (ver Frente A / `coverage`). La concentración real es menor; leer junto al mapa de cobertura, no como verdad de mercado.

| Tema | HHI | # inversores | Inversor dominante | Share |
|------|-----|--------------|--------------------|-------|
| Biomanufacturing & Platform Technologies | 0.183 | 14 | GridX | 38% |
| Therapeutics | 0.126 | 24 | GridX | 28% |
| Biomaterials & Green Chemistry | 0.124 | 29 | GridX | 32% |
| Food Systems & Alt Proteins | 0.121 | 23 | GridX | 30% |
| Precision Agriculture | 0.096 | 20 | sp_ventures | 18% |
| Diagnostics & Devices | 0.07 | 44 | GridX | 20% |
| Nature & Ecosystem Tech | 0.063 | 28 | Antom | 13% |
| Bioinputs & Crop Resilience | 0.062 | 37 | GridX | 17% |

## Sindicación (co-inversión)

64 pares de fondos co-invierten en ≥2 startups. Más sindicados:

- **the_yield_lab_latam**: co-invierte con 11 fondos distintos
- **DraperCygnus**: co-invierte con 7 fondos distintos
- **GridX**: co-invierte con 7 fondos distintos
- **sp_ventures**: co-invierte con 7 fondos distintos
- **SOSV_IndieBio**: co-invierte con 6 fondos distintos
- **kaszek**: co-invierte con 5 fondos distintos
- **l_catterton**: co-invierte con 5 fondos distintos
- **AIR Capital**: co-invierte con 5 fondos distintos
- **zentynel**: co-invierte con 5 fondos distintos
- **inventure**: co-invierte con 5 fondos distintos
- **amazon_climate_pledge_fund**: co-invierte con 5 fondos distintos
- **glocal**: co-invierte con 4 fondos distintos

Top pares:

- kaszek + l_catterton: 9 startups en común
- AIR Capital + DraperCygnus: 8 startups en común
- AIR Capital + GridX: 8 startups en común
- GridX + SOSV_IndieBio: 8 startups en común
- Antom + glocal: 5 startups en común
- AIR Capital + SOSV_IndieBio: 4 startups en común
- GridX + The Ganesha Lab: 4 startups en común
- GridX + zentynel: 4 startups en común

## Capital no documentado

151 startups include sin ninguna arista de capital. Por tema:

- **Diagnostics & Devices**: 41/110 (37%)
- **Food Systems & Alt Proteins**: 30/74 (40%)
- **Therapeutics**: 27/81 (33%)
- **Bioinputs & Crop Resilience**: 19/64 (29%)
- **Biomaterials & Green Chemistry**: 15/54 (27%)
- **Biomanufacturing & Platform Technologies**: 9/27 (33%)
- **Precision Agriculture**: 6/39 (15%)
- **Nature & Ecosystem Tech**: 4/34 (11%)
