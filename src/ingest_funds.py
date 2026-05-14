"""
src/ingest_funds.py — Ingesta de fondos nuevos y relaciones LP→fondo.

Comandos disponibles (vía pipeline.py):
    python pipeline.py ingest-new-investors       # staging/new_investors.csv → entities + investors
    python pipeline.py ingest-capital-allocators  # quality/capital_allocator_edges.csv → capital_relations

Reglas:
- ingest-new-investors: solo para fondos que NO existen en entities. Si ya existen usar ingest-fund-profiles.
- ingest-capital-allocators: LP→fondo van en capital_relations (tabla separada), NO en investment_edges
  porque investment_edges es un grafo bipartito investor→startup y mezclar capas rompe graph_analytics.
- Toda escritura pasa por src/audit.py:log_change() o diff_and_log_update()
- Migration 008 (capital_relations) se crea automáticamente si no existe
"""
from __future__ import annotations

import csv
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.audit import diff_and_log_update, log_change
from src.ingest import VALID_INVESTOR_TYPES, VALID_STAGES, _load_csv
from src.utils import clean, to_float, to_int

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
STAGING = ROOT / "staging"
QUALITY = ROOT / "quality"


# ─────────────────────────────────────────────
# Migration 008 — capital_relations table
# ─────────────────────────────────────────────

_MIGRATION_008 = """
CREATE TABLE IF NOT EXISTS capital_relations (
    relation_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    target_vehicle   TEXT,
    relation_type    TEXT NOT NULL,
    amount_usd       REAL,
    year             INTEGER,
    sector_lens      TEXT,
    region_lens      TEXT,
    confidence_score REAL,
    source_url       TEXT NOT NULL,
    evidence_note    TEXT,
    added_by         TEXT,
    added_at         TEXT,
    FOREIGN KEY (source_entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (target_entity_id) REFERENCES entities(entity_id)
);
"""


def _ensure_capital_relations(conn: sqlite3.Connection) -> None:
    conn.execute(_MIGRATION_008)
    conn.commit()


# ─────────────────────────────────────────────
# ingest-new-investors
# ─────────────────────────────────────────────

def ingest_new_investors(db_path: Path = DB_PATH) -> dict[str, int]:
    """
    Lee staging/new_investors.csv e inserta inversores net-new en entities + investors.

    Para inversores que YA EXISTEN usar 'ingest-fund-profiles' en su lugar.

    Formato CSV (requeridos: investor_id, canonical_name, investor_type, country_code, website, source_url):
        investor_id, canonical_name, investor_type, country_code, website,
        thesis, preferred_stages, geography_focus, vertical_focus,
        ticket_min_usd, ticket_max_usd, source_url, notes
    """
    path = STAGING / "new_investors.csv"
    if not path.exists():
        print(f"  [skip] {path} no existe")
        return {"processed": 0, "inserted": 0, "skipped_dup": 0, "errors": 0}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    rows = _load_csv(path)
    stats = {"processed": 0, "inserted": 0, "skipped_dup": 0, "errors": 0}
    now = datetime.now(timezone.utc).isoformat()

    for row in rows:
        inv_id = clean(row.get("investor_id"))
        name = clean(row.get("canonical_name"))
        source_url = clean(row.get("source_url"))
        notes_raw = clean(row.get("notes"))

        if not inv_id or not name:
            continue

        if not source_url:
            print(f"  [error] {inv_id}: source_url obligatorio — saltar")
            stats["errors"] += 1
            continue

        inv_type = clean(row.get("investor_type")).lower() or "vc"
        if inv_type not in VALID_INVESTOR_TYPES:
            print(f"  [warn] {inv_id}: investor_type '{inv_type}' desconocido (aceptado igual)")

        country = clean(row.get("country_code")).upper() or None
        website = clean(row.get("website")) or None

        if not country or not website:
            print(f"  [warn] {inv_id}: country_code y website requeridos — saltar")
            stats["errors"] += 1
            continue

        # Si ya existe → skip con aviso
        exists = conn.execute(
            "SELECT entity_type FROM entities WHERE entity_id=?", (inv_id,)
        ).fetchone()
        if exists:
            print(f"  [skip] '{inv_id}' ya existe como '{exists[0]}' — usa ingest-fund-profiles para enriquecer")
            stats["skipped_dup"] += 1
            continue

        # Slug derivado del investor_id
        slug = inv_id

        # ── INSERT entities ───────────────────────────────────────────────────
        conn.execute(
            """INSERT INTO entities
               (entity_id, entity_type, canonical_name, slug, country_code, website, status)
               VALUES (?, 'investor', ?, ?, ?, ?, 'active')""",
            (inv_id, name, slug, country, website),
        )

        # ── INSERT investors ──────────────────────────────────────────────────
        tick_min = to_float(row.get("ticket_min_usd"))
        tick_max = to_float(row.get("ticket_max_usd"))
        if tick_min is not None and tick_max is not None and tick_max < tick_min:
            tick_min, tick_max = tick_max, tick_min

        conn.execute(
            """INSERT INTO investors
               (investor_id, investor_type, thesis, preferred_stages,
                geography_focus, vertical_focus, ticket_min_usd, ticket_max_usd,
                active_status)
               VALUES (?,?,?,?,?,?,?,?,'active')""",
            (
                inv_id, inv_type,
                clean(row.get("thesis")) or None,
                clean(row.get("preferred_stages")) or None,
                clean(row.get("geography_focus")) or None,
                clean(row.get("vertical_focus")) or None,
                tick_min, tick_max,
            ),
        )

        reason = f"staging/new_investors.csv"
        if notes_raw:
            reason += f" — {notes_raw}"

        log_change(
            conn,
            actor="human:curador",
            entity_id=inv_id,
            field="entities.NEW",
            old_value=None,
            new_value=f"investor:{name} ({country})",
            reason=reason,
            evidence_url=source_url,
        )

        stats["inserted"] += 1
        stats["processed"] += 1

    conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# ingest-capital-allocators
# ─────────────────────────────────────────────

def ingest_capital_allocators(db_path: Path = DB_PATH) -> dict[str, int]:
    """
    Lee quality/capital_allocator_edges.csv e inserta en capital_relations.

    Las relaciones LP→fondo van en una tabla separada (NO en investment_edges)
    para preservar la estructura bipartita investor→startup que usa graph_analytics.py.

    Formato CSV:
        allocator_id, allocator_name, allocator_type, target_fund_id, target_fund_name,
        target_vehicle, relation_type, amount_usd, year, sector_lens, region_lens,
        source_url, evidence_note, confidence

    - Crea migration 008 (capital_relations) automáticamente si no existe
    - Dedup por (source_entity_id, target_entity_id, relation_type)
    - Emite warning claro para target_fund_id que no existe en entities (no auto-crea)
    """
    path = QUALITY / "capital_allocator_edges.csv"
    if not path.exists():
        print(f"  [skip] {path} no existe")
        return {"processed": 0, "inserted": 0, "skipped_dup": 0, "skipped_missing_entity": 0, "errors": 0}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_capital_relations(conn)

    rows = _load_csv(path)
    stats = {"processed": 0, "inserted": 0, "skipped_dup": 0, "skipped_missing_entity": 0, "errors": 0}
    now = datetime.now(timezone.utc).isoformat()

    for row in rows:
        src_id = clean(row.get("allocator_id"))
        tgt_id = clean(row.get("target_fund_id"))
        rel_type = clean(row.get("relation_type"))
        source_url = clean(row.get("source_url"))

        if not src_id or not tgt_id or not rel_type:
            continue

        if not source_url:
            print(f"  [error] {src_id}→{tgt_id}: source_url obligatorio — saltar")
            stats["errors"] += 1
            continue

        # Validar FKs en entities
        missing = []
        for eid, label in ((src_id, "allocator"), (tgt_id, "target_fund")):
            if not conn.execute("SELECT 1 FROM entities WHERE entity_id=?", (eid,)).fetchone():
                missing.append((eid, label))

        if missing:
            for eid, label in missing:
                print(
                    f"  [warn] {label} '{eid}' no encontrado en entities — "
                    f"agregar vía staging/new_investors.csv primero"
                )
            stats["skipped_missing_entity"] += 1
            continue

        # Dedup
        dup = conn.execute(
            """SELECT relation_id FROM capital_relations
               WHERE source_entity_id=? AND target_entity_id=? AND relation_type=?""",
            (src_id, tgt_id, rel_type),
        ).fetchone()
        if dup:
            stats["skipped_dup"] += 1
            continue

        # Parse optional fields
        amount = to_float(row.get("amount_usd"))
        year = to_int(row.get("year"))
        conf = to_float(row.get("confidence")) or 0.85
        vehicle = clean(row.get("target_vehicle")) or None
        sector_lens = clean(row.get("sector_lens")) or None
        region_lens = clean(row.get("region_lens")) or None
        evidence_note = clean(row.get("evidence_note")) or None

        conn.execute(
            """INSERT INTO capital_relations
               (source_entity_id, target_entity_id, target_vehicle, relation_type,
                amount_usd, year, sector_lens, region_lens, confidence_score,
                source_url, evidence_note, added_by, added_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                src_id, tgt_id, vehicle, rel_type,
                amount, year, sector_lens, region_lens, conf,
                source_url, evidence_note, "human:curador", now,
            ),
        )

        log_change(
            conn,
            actor="human:curador",
            entity_id=src_id,
            field="capital_relations.NEW",
            old_value=None,
            new_value=f"{src_id}→{tgt_id} [{rel_type}]",
            reason=f"quality/capital_allocator_edges.csv",
            evidence_url=source_url,
        )

        stats["inserted"] += 1
        stats["processed"] += 1

    conn.commit()
    conn.close()
    return stats
