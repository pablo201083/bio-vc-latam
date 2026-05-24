"""
src/ingest_orgs.py — Ingesta de organizaciones del ecosistema (gremiales, ESOs, corporates)
y sus edges de relación (support_edges, validation_edges).

Comandos disponibles (vía pipeline.py):
    python pipeline.py ingest-orgs   # canonical/manual_canonical_organizations.csv
                                     # canonical/manual_support_edges.csv
                                     # canonical/manual_validation_edges.csv
                                     # → entities + organizations/esos/corporates
                                     # → support_edges + validation_edges

Diseño:
- manual_canonical_organizations.csv maneja los tres subtipos (organization, eso, corporate)
  usando el campo node_type como discriminador.
- support_edges: relaciones org/eso → startup/fondo (membership, incubation, grant, ...)
- validation_edges: relaciones startup ↔ corporate (pilot, poc, acquisition, ...)
- Toda escritura pasa por src/audit.py:log_change()
- Migration 010 (columnas de trazabilidad) se aplica automáticamente al cargar

Tipos válidos:
    node_type   : organization | eso | corporate
    org_type    : industry_association | government_body | academic_institute |
                  development_finance | ngo | foundation | accelerator | incubator |
                  technology_park
    eso_type    : (libre) — research_institute | accelerator | incubator | grant_agency |
                  technology_park | cluster
    support_type: membership | acceleration | incubation | grant | mentorship |
                  technical_assistance | cohort_participation
    validation_type: pilot | poc | commercial_contract | acquisition |
                     letter_of_intent | supply_agreement
"""
from __future__ import annotations

import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.audit import log_change
from src.utils import clean, to_float

ROOT = Path(__file__).parent.parent
CANONICAL = ROOT / "canonical"

VALID_NODE_TYPES   = {"organization", "eso", "corporate"}
VALID_SUPPORT_TYPES = {
    "membership", "acceleration", "incubation", "grant",
    "mentorship", "technical_assistance", "cohort_participation",
}
VALID_VALIDATION_TYPES = {
    "pilot", "poc", "commercial_contract", "acquisition",
    "letter_of_intent", "supply_agreement",
}


# ─────────────────────────────────────────────
# Migration 010 — trazabilidad en tablas ecosistema
# ─────────────────────────────────────────────

_ALTER_STMTS = [
    # organizations
    "ALTER TABLE organizations ADD COLUMN source_url       TEXT",
    "ALTER TABLE organizations ADD COLUMN confidence_score REAL",
    "ALTER TABLE organizations ADD COLUMN added_by         TEXT",
    "ALTER TABLE organizations ADD COLUMN added_at         TEXT",
    # corporates
    "ALTER TABLE corporates ADD COLUMN source_url          TEXT",
    "ALTER TABLE corporates ADD COLUMN confidence_score    REAL",
    "ALTER TABLE corporates ADD COLUMN added_by            TEXT",
    "ALTER TABLE corporates ADD COLUMN added_at            TEXT",
    # esos
    "ALTER TABLE esos ADD COLUMN source_url                TEXT",
    "ALTER TABLE esos ADD COLUMN confidence_score          REAL",
    "ALTER TABLE esos ADD COLUMN added_by                  TEXT",
    "ALTER TABLE esos ADD COLUMN added_at                  TEXT",
    # support_edges
    "ALTER TABLE support_edges ADD COLUMN source_url       TEXT",
    "ALTER TABLE support_edges ADD COLUMN confidence_score REAL",
    "ALTER TABLE support_edges ADD COLUMN added_by         TEXT",
    "ALTER TABLE support_edges ADD COLUMN added_at         TEXT",
    # validation_edges (ya tiene confidence_score)
    "ALTER TABLE validation_edges ADD COLUMN source_url    TEXT",
    "ALTER TABLE validation_edges ADD COLUMN added_by      TEXT",
    "ALTER TABLE validation_edges ADD COLUMN added_at      TEXT",
]


def _apply_migration_010(conn: sqlite3.Connection) -> None:
    """Agrega columnas de trazabilidad (idempotente — ignora 'duplicate column' errors)."""
    for stmt in _ALTER_STMTS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass  # columna ya existe
    conn.commit()


# ─────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────

def _load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if any(v.strip() for v in r.values())]


def _entity_exists(conn: sqlite3.Connection, entity_id: str) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM entities WHERE entity_id=?", (entity_id,)
    ).fetchone())


# ─────────────────────────────────────────────
# ingest organizations / esos / corporates
# ─────────────────────────────────────────────

def ingest_organizations(
    db_path: Path,
    csv_path: Path | None = None,
) -> dict[str, int]:
    """
    Lee canonical/manual_canonical_organizations.csv e inserta en:
      - entities (base)
      - organizations / esos / corporates (según node_type)

    Campos CSV requeridos: org_id, node_type, canonical_name, country_code, source_url
    Campos opcionales: slug, website, org_type, focus_area, sector_lens, geography_focus,
                       eso_type, service_profile, demand_profile, innovation_maturity,
                       industry, confidence_score, notes
    """
    path = csv_path or CANONICAL / "manual_canonical_organizations.csv"
    rows = _load_csv(path)
    if not rows:
        print(f"  [skip] {path} vacío o no existe")
        return {"processed": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    _apply_migration_010(conn)

    stats = {"processed": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    now = datetime.now(timezone.utc).isoformat()

    for row in rows:
        org_id     = clean(row.get("org_id"))
        node_type  = clean(row.get("node_type", "")).lower()
        name       = clean(row.get("canonical_name"))
        country    = clean(row.get("country_code", "")).upper() or None
        source_url = clean(row.get("source_url"))

        if not org_id or not name:
            continue

        if node_type not in VALID_NODE_TYPES:
            print(f"  [error] {org_id}: node_type '{node_type}' inválido — válidos: {VALID_NODE_TYPES}")
            stats["errors"] += 1
            continue

        if not source_url:
            print(f"  [error] {org_id}: source_url obligatorio — saltar")
            stats["errors"] += 1
            continue

        slug    = clean(row.get("slug")) or org_id
        website = clean(row.get("website")) or None
        conf    = to_float(row.get("confidence_score")) or 0.85
        notes_raw = clean(row.get("notes")) or None

        stats["processed"] += 1

        if _entity_exists(conn, org_id):
            stats["skipped"] += 1
            continue

        # ── INSERT entities ───────────────────────────────────────────────────
        conn.execute(
            """INSERT INTO entities
               (entity_id, entity_type, canonical_name, slug, country_code, website, status)
               VALUES (?, ?, ?, ?, ?, ?, 'active')""",
            (org_id, node_type, name, slug, country, website),
        )

        # ── INSERT subtype table ──────────────────────────────────────────────
        if node_type == "organization":
            org_type   = clean(row.get("org_type")) or None
            focus_area = clean(row.get("focus_area")) or None
            conn.execute(
                """INSERT INTO organizations
                   (org_id, org_type, focus_area, source_url, confidence_score, added_by, added_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (org_id, org_type, focus_area, source_url, conf, "human:curador", now),
            )

        elif node_type == "eso":
            eso_type       = clean(row.get("eso_type")) or None
            service_profile = clean(row.get("service_profile")) or None
            geo_focus      = clean(row.get("geography_focus")) or None
            conn.execute(
                """INSERT INTO esos
                   (eso_id, eso_type, service_profile, geography_focus,
                    source_url, confidence_score, added_by, added_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (org_id, eso_type, service_profile, geo_focus,
                 source_url, conf, "human:curador", now),
            )

        elif node_type == "corporate":
            industry    = clean(row.get("industry")) or None
            demand_prof = clean(row.get("demand_profile")) or None
            innov_mat   = clean(row.get("innovation_maturity")) or None
            conn.execute(
                """INSERT INTO corporates
                   (corporate_id, industry, demand_profile, innovation_maturity,
                    source_url, confidence_score, added_by, added_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (org_id, industry, demand_prof, innov_mat,
                 source_url, conf, "human:curador", now),
            )

        reason = f"canonical/manual_canonical_organizations.csv"
        if notes_raw:
            reason += f" — {notes_raw[:120]}"

        log_change(
            conn,
            actor="human:curador",
            entity_id=org_id,
            field="entities.NEW",
            old_value=None,
            new_value=f"{node_type}:{name} ({country})",
            reason=reason,
            evidence_url=source_url,
        )

        stats["inserted"] += 1

    conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# ingest support_edges
# ─────────────────────────────────────────────

def ingest_support_edges(
    db_path: Path,
    csv_path: Path | None = None,
) -> dict[str, int]:
    """
    Lee canonical/manual_support_edges.csv e inserta en support_edges.

    Campos CSV requeridos: edge_id, source_entity_id, target_entity_id, support_type, source_url
    Campos opcionales: source_name, target_name, started_at, ended_at, confidence_score, notes
    """
    path = csv_path or CANONICAL / "manual_support_edges.csv"
    rows = _load_csv(path)
    if not rows:
        print(f"  [skip] {path} vacío o no existe")
        return {"processed": 0, "inserted": 0, "skipped_dup": 0,
                "skipped_missing_entity": 0, "errors": 0}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    _apply_migration_010(conn)

    stats = {"processed": 0, "inserted": 0, "skipped_dup": 0,
             "skipped_missing_entity": 0, "errors": 0}
    now = datetime.now(timezone.utc).isoformat()

    for row in rows:
        edge_id    = clean(row.get("edge_id"))
        src_id     = clean(row.get("source_entity_id"))
        tgt_id     = clean(row.get("target_entity_id"))
        sup_type   = clean(row.get("support_type", "")).lower()
        source_url = clean(row.get("source_url"))

        if not edge_id or not src_id or not tgt_id or not sup_type:
            continue

        if not source_url:
            print(f"  [error] {edge_id}: source_url obligatorio — saltar")
            stats["errors"] += 1
            continue

        if sup_type not in VALID_SUPPORT_TYPES:
            print(f"  [warn] {edge_id}: support_type '{sup_type}' no reconocido (aceptado igual)")

        stats["processed"] += 1

        # Verificar FKs
        missing = []
        for eid, label in ((src_id, "source"), (tgt_id, "target")):
            if not _entity_exists(conn, eid):
                missing.append((eid, label))
        if missing:
            for eid, label in missing:
                print(f"  [warn] {label} '{eid}' no existe en entities — "
                      f"agregar vía ingest-orgs o staging/new_investors.csv primero")
            stats["skipped_missing_entity"] += 1
            continue

        # Dedup
        dup = conn.execute(
            "SELECT 1 FROM support_edges WHERE support_id=?", (edge_id,)
        ).fetchone()
        if dup:
            stats["skipped_dup"] += 1
            continue

        conf     = to_float(row.get("confidence_score")) or 0.85
        started  = clean(row.get("started_at")) or None
        ended    = clean(row.get("ended_at")) or None
        notes_raw = clean(row.get("notes")) or None

        conn.execute(
            """INSERT INTO support_edges
               (support_id, source_entity_id, target_entity_id, support_type,
                started_at, ended_at, notes, source_url, confidence_score, added_by, added_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (edge_id, src_id, tgt_id, sup_type,
             started, ended, notes_raw, source_url, conf, "human:curador", now),
        )

        log_change(
            conn,
            actor="human:curador",
            entity_id=src_id,
            field="support_edges.NEW",
            old_value=None,
            new_value=f"{src_id}→{tgt_id} [{sup_type}]",
            reason=f"canonical/manual_support_edges.csv",
            evidence_url=source_url,
        )

        stats["inserted"] += 1

    conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# ingest validation_edges
# ─────────────────────────────────────────────

def ingest_validation_edges(
    db_path: Path,
    csv_path: Path | None = None,
) -> dict[str, int]:
    """
    Lee canonical/manual_validation_edges.csv e inserta en validation_edges.

    Campos CSV requeridos: edge_id, startup_id, counterparty_entity_id, validation_type, source_url
    Campos opcionales: startup_name, counterparty_name, started_at, ended_at, status,
                       confidence_score, notes
    """
    path = csv_path or CANONICAL / "manual_validation_edges.csv"
    rows = _load_csv(path)
    if not rows:
        print(f"  [skip] {path} vacío o sin datos (header only)")
        return {"processed": 0, "inserted": 0, "skipped_dup": 0,
                "skipped_missing_entity": 0, "errors": 0}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    _apply_migration_010(conn)

    stats = {"processed": 0, "inserted": 0, "skipped_dup": 0,
             "skipped_missing_entity": 0, "errors": 0}
    now = datetime.now(timezone.utc).isoformat()

    for row in rows:
        edge_id     = clean(row.get("edge_id"))
        startup_id  = clean(row.get("startup_id"))
        counter_id  = clean(row.get("counterparty_entity_id"))
        val_type    = clean(row.get("validation_type", "")).lower()
        source_url  = clean(row.get("source_url"))

        if not edge_id or not startup_id or not counter_id or not val_type:
            continue

        if not source_url:
            print(f"  [error] {edge_id}: source_url obligatorio — saltar")
            stats["errors"] += 1
            continue

        if val_type not in VALID_VALIDATION_TYPES:
            print(f"  [warn] {edge_id}: validation_type '{val_type}' no reconocido (aceptado igual)")

        stats["processed"] += 1

        # Verificar FKs
        missing = []
        for eid, label in ((startup_id, "startup"), (counter_id, "counterparty")):
            if not _entity_exists(conn, eid):
                missing.append((eid, label))
        if missing:
            for eid, label in missing:
                print(f"  [warn] {label} '{eid}' no existe en entities")
            stats["skipped_missing_entity"] += 1
            continue

        # Dedup
        dup = conn.execute(
            "SELECT 1 FROM validation_edges WHERE validation_id=?", (edge_id,)
        ).fetchone()
        if dup:
            stats["skipped_dup"] += 1
            continue

        conf     = to_float(row.get("confidence_score")) or 0.85
        started  = clean(row.get("started_at")) or None
        ended    = clean(row.get("ended_at")) or None
        status   = clean(row.get("status")) or None
        notes_raw = clean(row.get("notes")) or None

        conn.execute(
            """INSERT INTO validation_edges
               (validation_id, startup_id, counterparty_entity_id, validation_type,
                started_at, ended_at, status, confidence_score, notes,
                source_url, added_by, added_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (edge_id, startup_id, counter_id, val_type,
             started, ended, status, conf, notes_raw,
             source_url, "human:curador", now),
        )

        log_change(
            conn,
            actor="human:curador",
            entity_id=startup_id,
            field="validation_edges.NEW",
            old_value=None,
            new_value=f"{startup_id}↔{counter_id} [{val_type}]",
            reason=f"canonical/manual_validation_edges.csv",
            evidence_url=source_url,
        )

        stats["inserted"] += 1

    conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# entry point combinado
# ─────────────────────────────────────────────

def ingest_all(db_path: Path) -> dict[str, dict]:
    """Corre los tres ingestores en secuencia y devuelve stats combinados."""
    print("  ── Organizaciones (entities + organizations/esos/corporates) ──────")
    orgs_stats = ingest_organizations(db_path)
    print(f"  {orgs_stats}")

    print("\n  ── Support edges (membership, incubation, ...) ──────────────────")
    sup_stats = ingest_support_edges(db_path)
    print(f"  {sup_stats}")

    print("\n  ── Validation edges (pilot, poc, acquisition, ...) ──────────────")
    val_stats = ingest_validation_edges(db_path)
    print(f"  {val_stats}")

    return {
        "organizations": orgs_stats,
        "support_edges": sup_stats,
        "validation_edges": val_stats,
    }
