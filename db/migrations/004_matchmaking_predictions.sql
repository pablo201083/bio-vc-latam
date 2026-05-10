-- Migration 004: matchmaking_predictions (T5)
-- Razón: el matchmaker actual recomienda pero no aprende. Esta tabla persiste cada
-- predicción del top-N para poder cruzarla con outcomes y medir precision por
-- bucket de score. Habilita calibración del matchmaker a lo largo del tiempo.

CREATE TABLE IF NOT EXISTS matchmaking_predictions (
    prediction_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_date         TEXT NOT NULL,      -- cuándo se generó la predicción
    startup_id              TEXT NOT NULL,
    investor_id             TEXT NOT NULL,
    score                   REAL NOT NULL,
    score_components_json   TEXT,               -- JSON con los componentes: theme_fit, country_adj, tag_overlap, portfolio_depth, evidence, role_strength, stage_fit
    reasons                 TEXT,               -- texto humano-legible: "comparte 3 etiquetas BIO/tech..."

    -- Materialization tracking (se llena cuando llega un outcome que matchea)
    materialized            INTEGER DEFAULT NULL,   -- NULL=desconocido, 1=funded, 0=descartado (>180 días sin materializar)
    materialized_at         TEXT,
    outcome_id              INTEGER,

    FOREIGN KEY (startup_id) REFERENCES entities(entity_id),
    FOREIGN KEY (investor_id) REFERENCES entities(entity_id),
    FOREIGN KEY (outcome_id) REFERENCES outcomes(outcome_id)
);

CREATE INDEX IF NOT EXISTS idx_pred_pair ON matchmaking_predictions(startup_id, investor_id);
CREATE INDEX IF NOT EXISTS idx_pred_date ON matchmaking_predictions(prediction_date);
CREATE INDEX IF NOT EXISTS idx_pred_materialized ON matchmaking_predictions(materialized);
CREATE INDEX IF NOT EXISTS idx_pred_score ON matchmaking_predictions(score);
