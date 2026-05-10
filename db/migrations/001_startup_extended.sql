-- Migration 001: startup_extended
-- Razón: schema_observatorio_biotech_v2.sql está sellado, pero startup_master_dataset.csv
-- tiene ~25 campos editoriales sin lugar en el schema base. Esta tabla los aloja sin
-- modificar el contrato sellado. También aloja columnas que llenan T2 (grafo) y T3 (semántica).

CREATE TABLE IF NOT EXISTS startup_extended (
    startup_id              TEXT PRIMARY KEY,

    -- Editorial / calidad (de master_dataset)
    data_quality_score      REAL,
    quality_band            TEXT,
    review_status           TEXT,
    bio_lens_tags           TEXT,
    domain_tags             TEXT,
    technology_tags         TEXT,
    scale_tags              TEXT,
    business_one_liner      TEXT,
    assignment_method       TEXT,
    taxonomy_confidence     REAL,
    scope_decision          TEXT,
    scope_status            TEXT,
    scope_basis             TEXT,
    scope_reason            TEXT,
    macro_theme             TEXT,
    emergent_theme          TEXT,
    market_label            TEXT,
    transition_function     TEXT,
    technical_stack         TEXT,
    industry_destination    TEXT,
    thesis_fit              TEXT,
    materiality_signal      TEXT,
    thesis_scope_note       TEXT,
    research_priority       TEXT,
    missing_signals         TEXT,
    startup_summary_v1      TEXT,
    summary_confidence      TEXT,
    valuation_tier          TEXT,
    trl_current_status      TEXT,
    last_reviewed_at        TEXT,

    -- T3: semántica con embeddings (llenado por src/clustering.py)
    cluster_id              INTEGER DEFAULT -1,
    cluster_label           TEXT,
    cluster_confidence      REAL,
    umap_x                  REAL,
    umap_y                  REAL,
    is_outlier              INTEGER DEFAULT 0,

    -- T2: análisis de grafo (llenado por src/graph_analytics.py)
    pagerank                REAL,
    betweenness             REAL,
    closeness               REAL,
    bridge_score            REAL,
    community_id            INTEGER,

    -- Geocoding (T6: datasette-cluster-map)
    latitude                REAL,
    longitude               REAL,

    FOREIGN KEY (startup_id) REFERENCES entities(entity_id)
);

CREATE INDEX IF NOT EXISTS idx_sx_scope ON startup_extended(scope_decision);
CREATE INDEX IF NOT EXISTS idx_sx_macro ON startup_extended(macro_theme);
CREATE INDEX IF NOT EXISTS idx_sx_cluster ON startup_extended(cluster_id);
CREATE INDEX IF NOT EXISTS idx_sx_community ON startup_extended(community_id);
