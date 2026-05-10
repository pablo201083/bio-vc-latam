-- Migration 005: ecosystem graph outputs (T2)
-- Razón: el schema base tiene `derived_graph_metrics` para métricas por nodo (PageRank,
-- betweenness, etc.) — esas van a startup_extended. Pero el grafo también produce
-- 3 outputs derivados que no son por-nodo: bridges (edges entre comunidades),
-- bottlenecks (nodos críticos), y whitespace (oportunidades estratégicas).

CREATE TABLE IF NOT EXISTS ecosystem_bridges (
    bridge_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entity_id    TEXT NOT NULL,
    target_entity_id    TEXT NOT NULL,
    source_community    INTEGER,
    target_community    INTEGER,
    weight              REAL,
    computed_at         TEXT,

    FOREIGN KEY (source_entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (target_entity_id) REFERENCES entities(entity_id)
);
CREATE INDEX IF NOT EXISTS idx_bridges_source ON ecosystem_bridges(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_bridges_target ON ecosystem_bridges(target_entity_id);

CREATE TABLE IF NOT EXISTS ecosystem_bottlenecks (
    entity_id           TEXT PRIMARY KEY,
    betweenness         REAL,
    in_degree           INTEGER,
    out_degree          INTEGER,
    risk_if_removed     TEXT,                       -- 'critical' | 'high' | 'moderate'
    computed_at         TEXT,

    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE IF NOT EXISTS ecosystem_whitespace (
    whitespace_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    macro_theme         TEXT,
    country_code        TEXT,
    startup_count       INTEGER,
    investor_count      INTEGER,
    total_capital_usd   REAL,
    opportunity_score   REAL,                       -- startup_count / max(investor_count, 1)
    computed_at         TEXT
);
CREATE INDEX IF NOT EXISTS idx_whitespace_theme ON ecosystem_whitespace(macro_theme);
CREATE INDEX IF NOT EXISTS idx_whitespace_country ON ecosystem_whitespace(country_code);
CREATE INDEX IF NOT EXISTS idx_whitespace_score ON ecosystem_whitespace(opportunity_score);
