-- Migration 006: tech_codes y industry_codes (T3)
-- Razón: el clustering semántico (T3) produce un cluster_id dominante por embedding,
-- pero queremos también dos ejes cross-cutting: qué tecnologías usa cada startup
-- y sobre qué industria opera. Se persisten como JSON arrays para permitir queries
-- con json_each() en SQLite.
--
-- Los valores vienen de src/vocabularies.py extrayendo desde technical_stack/
-- technology_tags (tech) e industry_destination/domain_tags (industry).

ALTER TABLE startup_extended ADD COLUMN tech_codes TEXT;
ALTER TABLE startup_extended ADD COLUMN industry_codes TEXT;

-- Tabla de vocabularios cacheada para joins eficientes desde Datasette / queries
CREATE TABLE IF NOT EXISTS vocab_technologies (
    code            TEXT PRIMARY KEY,
    canonical_label TEXT NOT NULL,
    aliases         TEXT,
    grp             TEXT
);

CREATE TABLE IF NOT EXISTS vocab_industries (
    code            TEXT PRIMARY KEY,
    canonical_label TEXT NOT NULL,
    aliases         TEXT,
    grp             TEXT
);
