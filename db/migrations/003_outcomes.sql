-- Migration 003: outcomes (T4 + T5)
-- Razón: para cerrar el loop del matchmaker (T5) y poder medir momentum sectorial (T4),
-- el sistema necesita registrar eventos reales del ecosistema: funding rounds, exits,
-- pilots, partnerships, fallas. Se ingieren manualmente vía staging/outcomes_incoming.csv
-- o vía Datasette write form. NO se ingieren por agentes IA (decisión del usuario).

CREATE TABLE IF NOT EXISTS outcomes (
    outcome_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id           TEXT NOT NULL,                  -- startup u otra entidad principal del outcome
    outcome_type        TEXT NOT NULL,                  -- 'funding_round' | 'exit' | 'pilot_signed' | 'partnership' | 'failure' | 'product_launch'
    outcome_date        TEXT NOT NULL,                  -- ISO date YYYY-MM-DD
    counterparty_id     TEXT,                           -- ej: investor_id para funding_round, corporate_id para pilot
    amount_usd          REAL,
    currency            TEXT,
    source_url          TEXT NOT NULL,                  -- evidencia pública obligatoria
    notes               TEXT,
    added_by            TEXT,                           -- curador que lo ingresó
    added_at            TEXT,                           -- timestamp de ingesta

    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE INDEX IF NOT EXISTS idx_outcomes_entity ON outcomes(entity_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_date ON outcomes(outcome_date);
CREATE INDEX IF NOT EXISTS idx_outcomes_type ON outcomes(outcome_type);
CREATE INDEX IF NOT EXISTS idx_outcomes_counterparty ON outcomes(counterparty_id);
