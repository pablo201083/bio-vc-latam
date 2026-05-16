-- Migration 009: funding stage fields en startup_extended
-- Fuente inicial: GRIDX Excel (buckets en $M), luego Pitchbook (montos exactos)
-- Campos en $USD millones; NULL = no data

ALTER TABLE startup_extended ADD COLUMN funding_bucket_usd   INTEGER;  -- bucket GRIDX: 0/<1, 1, 5, 10, 15, 25, 100, 500, 1000
ALTER TABLE startup_extended ADD COLUMN valuation_bucket_usd INTEGER;  -- bucket GRIDX: <1, 1, 5, 10, 15, 25, 50, 100, 500, 1000
ALTER TABLE startup_extended ADD COLUMN funding_stage        TEXT;     -- pre-seed | seed | series-a | series-b | series-c+ | growth
ALTER TABLE startup_extended ADD COLUMN funding_source       TEXT;     -- 'gridx' | 'pitchbook' | 'manual'
ALTER TABLE startup_extended ADD COLUMN last_funding_at      TEXT;     -- ISO date de la ronda más reciente (cuando se conoce)
