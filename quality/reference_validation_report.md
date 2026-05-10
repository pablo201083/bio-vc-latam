# Reference Validation Report

Generated at: 2026-05-09 14:21:58

Errors: 0
Warnings: 0

## Checks

- include_source_url [error/pass]: Include rows must have an auditable source_url. (0)
- duplicate_startup_names [error/pass]: Startup names should not duplicate after normalization. (0)
- duplicate_investor_names [error/pass]: Investor names should not duplicate after normalization. (0)
- canonical_edge_investor_resolution [error/pass]: Canonical investment edges must point to canonical investor ids. (0)
- canonical_edge_startup_resolution [warning/pass]: Canonical investment edges must resolve to master startups, aliases, or tracked external canonical startup nodes. (0)
- canonical_edge_external_startups [info/warn]: Canonical investment edges pointing to startup nodes outside the master dataset; review as expansion candidates or keep as capital-network context. (47)
- include_country_coverage [warning/pass]: Include rows should have structured_country for regional coverage analysis. (0)
- include_fragile_or_stub [warning/pass]: Include rows should be moved from fragile/taxonomy_stub to source-backed seeded or reviewed. (0)
- source_registry_tier1 [info/pass]: Source registry should contain tier 1 official sources. (255)
