-- Migration 007: BIO Theme taxonomy (primary + secondary + universe flag)
-- Replaces macro_theme with a richer, semantically grounded classification.
-- macro_theme is preserved for backward compatibility during transition.

ALTER TABLE startup_extended ADD COLUMN bio_theme_primary    TEXT    DEFAULT NULL;
ALTER TABLE startup_extended ADD COLUMN bio_theme_secondary  TEXT    DEFAULT NULL;
ALTER TABLE startup_extended ADD COLUMN is_bio_universe      INTEGER DEFAULT NULL;  -- 1=true bio, 0=eco-adjacent
ALTER TABLE startup_extended ADD COLUMN bio_theme_confidence REAL    DEFAULT NULL;  -- cosine-style score 0-1
