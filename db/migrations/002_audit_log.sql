-- Migration 002: audit_log (T4)
-- Razón: el proyecto dice ser "auditable" pero no tiene registro de cambios.
-- Esta tabla captura cada UPDATE realizado por el pipeline o por humanos.
-- src/audit.py:diff_and_log_update() es el único punto de escritura permitido.

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL,              -- ISO 8601 UTC
    actor           TEXT NOT NULL,              -- 'pipeline', 'human:pablo', 'graph_analytics', 'clustering', etc.
    entity_id       TEXT,                       -- puede ser NULL para cambios sistémicos
    table_name      TEXT,                       -- 'entities', 'startup_extended', 'investors', etc.
    field           TEXT NOT NULL,
    old_value       TEXT,
    new_value       TEXT,
    reason          TEXT,                       -- por qué: 'manual_review', 'graph_recompute', 'cluster_assignment', etc.
    evidence_url    TEXT,
    confidence      REAL
);

CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor);
