-- Migration 010: ecosystem_orgs — organizaciones, ESOs, corporates y sus edges de relación
--
-- Propósito: extender el grafo bipartito investor→startup a un ecosistema completo
-- con capas adicionales:
--   • organizations  → gremiales / asociaciones (ARCAP, CAB, AAPRESID, CREA, ...)
--   • esos           → ecosystem support organizations (INIA, Embrapa, aceleradoras, ...)
--   • corporates     → empresas adquirentes de tecnología (Bunge, Cargill, ...)
--   • support_edges  → relaciones org/eso → startup/fondo (membership, incubation, grant, ...)
--   • validation_edges → relaciones startup ↔ corporate (pilot, poc, acquisition, ...)
--
-- Diseño deliberado:
--   • Las tablas organizations / corporates / esos YA EXISTEN en schema_observatorio_biotech_v2.sql
--     y en db/bio_latam.db (vacías). Esta migración AGREGA columnas de trazabilidad que siguen
--     el patrón de migration 008 (capital_relations): source_url obligatorio + added_by + added_at.
--   • support_edges y validation_edges también ya existen; esta migración agrega las mismas
--     columnas de trazabilidad (ALTER TABLE ADD COLUMN en SQLite = siempre nullable).
--   • La enforcement de NOT NULL sobre source_url se hace en Python (ingest_orgs.py).
--
-- Source primaria: canonical/manual_canonical_organizations.csv
--                  canonical/manual_support_edges.csv
--                  canonical/manual_validation_edges.csv
-- Comando de carga: python pipeline.py ingest-orgs
--
-- NOTA: Las ALTER TABLE de abajo son idempotentes en SQLite — si la columna ya existe,
-- el comando falla silenciosamente. ingest_orgs.py las ejecuta con try/except.

-- ── 1. organizations — añadir columnas de trazabilidad ───────────────────────────────────
ALTER TABLE organizations ADD COLUMN source_url  TEXT;
ALTER TABLE organizations ADD COLUMN confidence_score REAL;
ALTER TABLE organizations ADD COLUMN added_by    TEXT;
ALTER TABLE organizations ADD COLUMN added_at    TEXT;

-- ── 2. corporates — añadir columnas de trazabilidad ─────────────────────────────────────
ALTER TABLE corporates ADD COLUMN source_url     TEXT;
ALTER TABLE corporates ADD COLUMN confidence_score REAL;
ALTER TABLE corporates ADD COLUMN added_by       TEXT;
ALTER TABLE corporates ADD COLUMN added_at       TEXT;

-- ── 3. esos — añadir columnas de trazabilidad ───────────────────────────────────────────
ALTER TABLE esos ADD COLUMN source_url           TEXT;
ALTER TABLE esos ADD COLUMN confidence_score     REAL;
ALTER TABLE esos ADD COLUMN added_by             TEXT;
ALTER TABLE esos ADD COLUMN added_at             TEXT;

-- ── 4. support_edges — añadir columnas de trazabilidad ──────────────────────────────────
-- support_type values: membership | acceleration | incubation | grant | mentorship |
--                       technical_assistance | cohort_participation
ALTER TABLE support_edges ADD COLUMN source_url      TEXT;
ALTER TABLE support_edges ADD COLUMN confidence_score REAL;
ALTER TABLE support_edges ADD COLUMN added_by        TEXT;
ALTER TABLE support_edges ADD COLUMN added_at        TEXT;

-- ── 5. validation_edges — añadir columnas de trazabilidad ───────────────────────────────
-- validation_type values: pilot | poc | commercial_contract | acquisition |
--                          letter_of_intent | supply_agreement
ALTER TABLE validation_edges ADD COLUMN source_url   TEXT;
ALTER TABLE validation_edges ADD COLUMN added_by     TEXT;
ALTER TABLE validation_edges ADD COLUMN added_at     TEXT;
-- (validation_edges ya tiene confidence_score en el schema original)
