# Estructura de Inversión — BIO VC LATAM

_Generado 2026-07-02 con `python pipeline.py capital-structure`. Cuenta EMPRESAS por stage (no dólares: solo 10% de aristas tiene monto). El stage es el más avanzado entre las aristas reales con round_stage._

## Pirámide de stages (global)

- **Pre-seed / Accelerator**: 61 ████████████
- **Seed**: 164 ████████████████████████████████
- **Series A**: 42 ████████
- **Growth (B–D)**: 17 ███
- **Exit / IPO**: 5 █

## Pirámide por tema — ¿base sin cúspide?

| Tema | Pre-seed | Seed | Ser.A | Growth | Exit | Sin capital | A→Growth |
|------|---------|------|-------|--------|------|-------------|----------|
| Diagnostics & Devices | 12 | 35 | 12 | 4 | 0 | 59 | 0.34 |
| Therapeutics | 12 | 33 | 6 | 1 | 0 | 33 | 0.16 |
| Bioinputs & Crop Resilience | 8 | 23 | 3 | 4 | 2 | 45 | 0.29 |
| Food Systems & Alt Proteins | 10 | 20 | 4 | 0 | 1 | 54 | 0.17 |
| Biomaterials & Green Chemistry | 12 | 16 | 5 | 1 | 0 | 24 | 0.21 |
| Nature & Ecosystem Tech | 0 | 16 | 5 | 3 | 1 | 10 | 0.56 |
| Precision Agriculture | 0 | 14 | 6 | 2 | 1 | 39 | 0.64 |
| Biomanufacturing & Platform Technologies | 7 | 7 | 1 | 2 | 0 | 20 | 0.21 |

## Dependencia de capital extranjero por tema

| Tema | Aristas | Extranjeras | % extranjero |
|------|---------|-------------|--------------|
| Precision Agriculture | 75 | 28 | 37% |
| Nature & Ecosystem Tech | 83 | 23 | 27% |
| Bioinputs & Crop Resilience | 152 | 34 | 22% |
| Biomaterials & Green Chemistry | 82 | 16 | 19% |
| Biomanufacturing & Platform Technologies | 54 | 10 | 18% |
| Food Systems & Alt Proteins | 95 | 15 | 15% |
| Diagnostics & Devices | 168 | 22 | 13% |
| Therapeutics | 132 | 10 | 7% |

## Concentración de capital por tema (HHI)

> ⚠️ **Sesgo de recolección:** GridX aparece dominante en casi todos los temas porque su portfolio se barrió exhaustivamente (ver Frente A / `coverage`). La concentración real es menor; leer junto al mapa de cobertura, no como verdad de mercado.

| Tema | HHI | # inversores | Inversor dominante | Share |
|------|-----|--------------|--------------------|-------|
| Biomaterials & Green Chemistry | 0.187 | 26 | GridX | 40% |
| Biomanufacturing & Platform Technologies | 0.179 | 21 | GridX | 38% |
| Therapeutics | 0.133 | 29 | GridX | 31% |
| Food Systems & Alt Proteins | 0.104 | 35 | GridX | 28% |
| Diagnostics & Devices | 0.098 | 45 | GridX | 25% |
| Precision Agriculture | 0.092 | 26 | the_yield_lab_latam | 20% |
| Nature & Ecosystem Tech | 0.07 | 30 | Antom | 14% |
| Bioinputs & Crop Resilience | 0.059 | 53 | GridX | 17% |

## Sindicación (co-inversión)

254 pares de fondos co-invierten en ≥2 startups. Más sindicados:

- **GridX**: co-invierte con 42 fondos distintos
- **the_yield_lab_latam**: co-invierte con 33 fondos distintos
- **SOSV_IndieBio**: co-invierte con 32 fondos distintos
- **AIR Capital**: co-invierte con 29 fondos distintos
- **sp_ventures**: co-invierte con 22 fondos distintos
- **DraperCygnus**: co-invierte con 18 fondos distintos
- **SF500**: co-invierte con 16 fondos distintos
- **glocal**: co-invierte con 14 fondos distintos
- **kamay_ventures**: co-invierte con 14 fondos distintos
- **DragonesVP**: co-invierte con 13 fondos distintos
- **inventure**: co-invierte con 13 fondos distintos
- **corteva_catalyst**: co-invierte con 12 fondos distintos

Top pares:

- AIR Capital + GridX: 35 startups en común
- AIR Capital + DraperCygnus: 33 startups en común
- GridX + SOSV_IndieBio: 29 startups en común
- AIR Capital + SOSV_IndieBio: 20 startups en común
- Antom + glocal: 20 startups en común
- DragonesVP + DraperCygnus: 20 startups en común
- GridX + The Ganesha Lab: 15 startups en común
- AIR Capital + DragonesVP: 12 startups en común

## Capital no documentado

218 startups include sin ninguna arista de capital. Por tema:

- **Diagnostics & Devices**: 50/122 (41%)
- **Food Systems & Alt Proteins**: 39/89 (43%)
- **Bioinputs & Crop Resilience**: 35/85 (41%)
- **Therapeutics**: 28/85 (32%)
- **Precision Agriculture**: 26/62 (41%)
- **Biomaterials & Green Chemistry**: 18/58 (31%)
- **Biomanufacturing & Platform Technologies**: 16/37 (43%)
- **Nature & Ecosystem Tech**: 6/35 (17%)
