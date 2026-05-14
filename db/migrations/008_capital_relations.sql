-- Migration 008: capital_relations — relaciones LP→fondo
--
-- Propósito: capturar relaciones de capital entre instituciones LP (IDB Lab, JICA, BID Invest, etc.)
-- y fondos de VC (SP Ventures, 500 LatAm, Amador, etc.).
--
-- Diseño deliberado: tabla SEPARADA de investment_edges.
-- investment_edges es un grafo bipartito investor→startup; mezclarlo con LP→fondo
-- corrompería build_capital_graph() en src/graph_analytics.py (que asume investor→startup).
--
-- Source primaria: quality/capital_allocator_edges.csv (curada, 70+ registros)
-- Comando de carga: python pipeline.py ingest-capital-allocators

CREATE TABLE IF NOT EXISTS capital_relations (
    relation_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entity_id TEXT NOT NULL,   -- el LP, fund-of-funds, o institución que asigna capital
    target_entity_id TEXT NOT NULL,   -- el fondo de VC que recibe capital
    target_vehicle   TEXT,            -- vehículo específico (e.g. "AgVentures III Fund")
    relation_type    TEXT NOT NULL,   -- lp_commitment_to_vc_fund | lp_partner_in_vc_fund |
                                      -- equity_investment_to_growth_fund | fund_of_funds_commitment
    amount_usd       REAL,            -- monto en USD (null si no publicado)
    year             INTEGER,         -- año del commitment/cierre
    sector_lens      TEXT,            -- sectores objetivo del fondo receptor (semicolon-sep)
    region_lens      TEXT,            -- geografía objetivo (semicolon-sep)
    confidence_score REAL,            -- 0–1; 0.96 para fuente oficial, 0.80 para inferida
    source_url       TEXT NOT NULL,   -- URL de evidencia pública — obligatorio
    evidence_note    TEXT,            -- resumen de la evidencia
    added_by         TEXT,            -- "human:curador" o "pipeline:*"
    added_at         TEXT,            -- ISO 8601 UTC
    FOREIGN KEY (source_entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (target_entity_id) REFERENCES entities(entity_id)
);
