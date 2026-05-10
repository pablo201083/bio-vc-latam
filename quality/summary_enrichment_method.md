# Summary Enrichment Method

Goal: improve the semantic map by replacing thin, endogenous, or mixed-language summaries with richer source-backed English descriptions.

## Target Length

- Standard curated summary: 45-60 words.
- Fragile semantic case: 55-75 words.
- Avoid going beyond 80 words unless the startup spans multiple technologies or markets.

## Required Signals

Each summary should include, when available from auditable sources:

- Product or platform: what the startup sells or builds.
- Technology or mechanism: biology, chemistry, hardware, software, AI, fermentation, diagnostics, biomaterials, etc.
- Market or use case: agriculture, food, health, materials, water, restoration, industry, finance for material systems.
- BIO relevance: biobased, biocentric, living-system transition, or planetary-boundary management.
- Inclusion rationale: why it belongs inside BIO VC LATAM.

## Style

- Write in English for semantic consistency.
- Use concrete nouns and verbs; avoid generic filler such as "innovative", "solution", "platform" without context.
- Do not use internal-only phrases as evidence.
- Keep the evidence trail in `source_url`, `source_type`, and `evidence_excerpt`.

## Template

`[Startup] develops [product/technology] for [market/use case], using [mechanism or stack]. It belongs inside BIO VC LATAM as [bio/material/planetary role], because [source-backed inclusion rationale].`

## Good Example

`Brazilian ag biologicals platform enabling farmers to produce bioinputs on farm through integrated technology, equipment, quality control, training and technical assistance. It belongs inside BIO VC LATAM as a core biological-input and crop-resilience company.`

## Batch Workflow

1. Build `quality/semantic_curation_priority_current.csv`.
2. Run `scripts/build_summary_enrichment_batch.ps1`.
3. Curate the highest-priority summaries first.
4. Rebuild semantic assignments and compare low-confidence count, distinctive tokens, and visual outliers.
