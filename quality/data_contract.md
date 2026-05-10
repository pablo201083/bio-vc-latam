# BIO VC LATAM Data Contract

This project has one reference unit: a LATAM startup evaluated for the BIO VC thesis.

## Startup Scope

- `scope_decision = include`: the startup belongs in the thesis universe.
- `scope_decision = exclude`: the startup is outside the thesis universe.
- `scope_status = confirmed`: the decision is backed by an external source or explicit editorial review.
- `scope_status = provisional`: the decision is still useful for queues, but not a final reference decision.

Every `include` row must have:

- `source_url`
- `startup_summary_v1`
- `business_one_liner`
- `macro_theme`
- `review_status`

Every production-ready `include` row should also have:

- `structured_country`
- `source_type`
- `evidence_excerpt`
- `data_quality_score_10`
- `quality_band`

## Strategic Tags

Strategic tags are non-exclusive labels. They do not replace `scope_decision`
or the operative semantic cluster.

- `bio_lens_tags`: why the startup matters for the BIO thesis.
- `domain_tags`: the destination system or market being transformed.
- `technology_tags`: the technical capabilities visible in the sourced profile.
- `scale_tags`: the intervention scale where the startup operates.

Rules:

- Tags are multi-label fields separated by `; `.
- Tags come from the controlled vocabulary in `quality/strategic_tag_dictionary.csv`.
- `scope_decision` remains the editorial in/out/review decision.
- `semantic_single_theme` or the adopted cluster remains the main visual category.
- Tags explain cross-cutting lenses such as biobased, biocentric,
  planetary-boundary, regenerative, circular, human-health-bio, and
  bio-enabled-industrial-transition.

## Source Trust

- `trust_tier = 1`: official company site, official fund portfolio, official public program profile.
- `trust_tier = 2`: structured public profiles such as LinkedIn, F6S, Crunchbase, CB Insights, or fund/company pages not fully official.
- `trust_tier = 3`: secondary public sources, public articles, manual research notes with a URL.
- `trust_tier = 4`: weak or legacy signal. This should not drive final inclusion by itself.

## Capital Network

The production fund view should privilege public, auditable relations.

- Use official portfolio pages and public company/fund profiles for fund analytics.
- Keep historical graph edges only when they help discovery or have enough density to be analytically useful.
- Exclude isolated private or inherited notes through `canonical/manual_investment_edge_exclusions.csv`.

## Validation Rules

The pipeline should warn or fail when:

- an `include` startup has no `source_url`
- startup names duplicate after normalization
- investor names duplicate after normalization
- canonical investment edges point to unknown investors
- too many include rows remain fragile, stubbed, or missing country/base

Generated validation lives in:

- `quality/reference_validation_report.csv`
- `quality/reference_validation_report.md`
