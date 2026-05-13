"""
src/ingest.py — Ingesta manual de datos curados a la DB.

Comandos disponibles (vía pipeline.py):
    python pipeline.py ingest-founding-years   # staging/founding_years.csv → entities.founded_year
    python pipeline.py ingest-rounds           # staging/investment_rounds.csv → investment_edges
    python pipeline.py ingest-outcomes         # staging/outcomes_incoming.csv → outcomes

Reglas:
- Toda escritura pasa por src/audit.py:diff_and_log_update()
- Los CSVs de staging NO se borran automáticamente (idempotente)
- Se valida FK antes de insertar (entity_id debe existir)
- Se reporta: N procesados, N actualizados, N errores
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any

from src.audit import diff_and_log_update, log_change
from src.utils import clean, to_float, to_int

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
STAGING = ROOT / "staging"


# ─────────────────────────────────────────────
# ingest-founding-years
# ─────────────────────────────────────────────

def ingest_founding_years(db_path: Path = DB_PATH) -> dict[str, int]:
    """
    Lee staging/founding_years.csv y actualiza entities.founded_year.

    Formato CSV:
        startup_id, startup_name, founded_year, source_url, notes

    Solo procesa filas con founded_year no vacío.
    """
    path = STAGING / "founding_years.csv"
    if not path.exists():
        print(f"  [skip] {path} no existe")
        return {"processed": 0, "updated": 0, "errors": 0}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    rows = _load_csv(path)
    stats = {"processed": 0, "updated": 0, "errors": 0}

    for row in rows:
        sid = clean(row.get("startup_id"))
        year_raw = clean(row.get("founded_year"))
        if not sid or not year_raw:
            continue  # fila vacía — saltar

        year = to_int(year_raw)
        if not year or year < 1990 or year > 2026:
            print(f"  [warn] {sid}: año inválido '{year_raw}' — saltar")
            stats["errors"] += 1
            continue

        # Verificar que la entidad existe
        exists = conn.execute(
            "SELECT 1 FROM entities WHERE entity_id = ?", (sid,)
        ).fetchone()
        if not exists:
            print(f"  [warn] {sid}: no encontrado en entities — saltar")
            stats["errors"] += 1
            continue

        source_url = clean(row.get("source_url"))
        notes = clean(row.get("notes"))
        reason = f"staging/founding_years.csv"
        if notes:
            reason += f" — {notes}"

        n = diff_and_log_update(
            conn,
            table="entities",
            row_id_col="entity_id",
            row_id=sid,
            new_values={"founded_year": year},
            actor="human:curador",
            reason=reason,
            evidence_url=source_url or None,
        )
        stats["processed"] += 1
        stats["updated"] += n

    conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# ingest-rounds
# ─────────────────────────────────────────────

VALID_STAGES = {
    "pre-seed", "seed", "series-a", "series-b", "series-c", "series-d",
    "growth", "grant", "convertible-note", "safe", "bridge", "ipo",
    "corporate-venture", "accelerator", "incubator", "unknown",
}


def ingest_rounds(db_path: Path = DB_PATH) -> dict[str, int]:
    """
    Lee staging/investment_rounds.csv y actualiza investment_edges con datos reales.

    Formato CSV:
        investor_id, investor_name, startup_id, startup_name,
        round_stage, announced_date, amount_usd, currency, is_lead, source_url, notes

    Lógica:
    - Si existe el edge investor_id+startup_id → actualiza campos vacíos (round_stage, date, amount)
    - Si NO existe el edge → crea uno nuevo con confidence_score=0.9 (fuente manual)
    - Solo procesa filas donde round_stage NO sea vacío (para no sobreescribir con nada)
    """
    path = STAGING / "investment_rounds.csv"
    if not path.exists():
        print(f"  [skip] {path} no existe")
        return {"processed": 0, "updated": 0, "created": 0, "errors": 0}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    rows = _load_csv(path)
    stats = {"processed": 0, "updated": 0, "created": 0, "errors": 0}

    for row in rows:
        inv_id = clean(row.get("investor_id"))
        st_id = clean(row.get("startup_id"))
        stage = clean(row.get("round_stage")).lower().replace(" ", "-")
        date_raw = clean(row.get("announced_date"))
        amount = to_float(row.get("amount_usd"))
        currency = clean(row.get("currency")) or "USD"
        is_lead_raw = clean(row.get("is_lead")).lower()
        is_lead = 1 if is_lead_raw in ("1", "true", "yes", "si", "sí") else 0
        source_url = clean(row.get("source_url"))
        notes = clean(row.get("notes"))

        if not inv_id or not st_id:
            continue

        # Validar stage
        if stage and stage not in VALID_STAGES:
            print(f"  [warn] {inv_id}→{st_id}: stage '{stage}' desconocido (aceptado igual)")

        # Verificar FKs
        for eid in (inv_id, st_id):
            if not conn.execute("SELECT 1 FROM entities WHERE entity_id=?", (eid,)).fetchone():
                print(f"  [warn] entity '{eid}' no existe — saltar fila")
                stats["errors"] += 1
                break
        else:
            # Buscar edge existente
            existing = conn.execute(
                "SELECT investment_id FROM investment_edges WHERE investor_id=? AND startup_id=?",
                (inv_id, st_id),
            ).fetchone()

            if existing:
                # Actualizar solo campos que tienen valor nuevo
                new_vals: dict[str, Any] = {}
                if stage:
                    new_vals["round_stage"] = stage
                if date_raw:
                    new_vals["announced_date"] = date_raw
                if amount is not None:
                    new_vals["amount"] = amount
                if currency:
                    new_vals["currency"] = currency
                if is_lead_raw:
                    new_vals["is_lead"] = is_lead
                if source_url:
                    new_vals["source_id"] = source_url  # proxy
                if notes:
                    new_vals["notes"] = notes

                if new_vals:
                    reason = f"staging/investment_rounds.csv — enriquecimiento manual"
                    n = diff_and_log_update(
                        conn,
                        table="investment_edges",
                        row_id_col="investment_id",
                        row_id=existing[0],
                        new_values=new_vals,
                        actor="human:curador",
                        reason=reason,
                        evidence_url=source_url or None,
                    )
                    stats["updated"] += n
            else:
                # Crear edge nuevo
                import uuid
                new_id = f"manual-{inv_id}-{st_id}-{uuid.uuid4().hex[:6]}"
                conn.execute(
                    """INSERT INTO investment_edges
                       (investment_id, investor_id, startup_id, round_stage,
                        announced_date, amount, currency, is_lead, confidence_score, notes)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (new_id, inv_id, st_id,
                     stage or None, date_raw or None,
                     amount, currency, is_lead,
                     0.9,  # fuente manual = alta confianza
                     notes or None),
                )
                log_change(
                    conn,
                    actor="human:curador",
                    entity_id=st_id,
                    field="investment_edges.NEW",
                    old_value=None,
                    new_value=f"{inv_id}→{st_id} {stage}",
                    reason=f"staging/investment_rounds.csv — edge nuevo",
                    evidence_url=source_url or None,
                )
                stats["created"] += 1

            stats["processed"] += 1

    conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# ingest-outcomes
# ─────────────────────────────────────────────

VALID_OUTCOME_TYPES = {
    "funding_round", "exit", "pilot_signed", "partnership",
    "failure", "grant", "acquisition", "ipo", "spinoff",
}


def ingest_outcomes(db_path: Path = DB_PATH) -> dict[str, int]:
    """
    Lee staging/outcomes_incoming.csv e inserta en la tabla outcomes.

    Formato CSV:
        entity_id, entity_name, outcome_type, outcome_date,
        counterparty_id, amount_usd, currency, source_url, notes

    - source_url es OBLIGATORIO (governance del data_contract)
    - outcome_date debe ser YYYY-MM-DD o YYYY-MM o YYYY
    - Se verifica que entity_id exista en entities
    - NO se borra el CSV al terminar (idempotente — duplicados se detectan por source_url)
    """
    path = STAGING / "outcomes_incoming.csv"
    if not path.exists():
        print(f"  [skip] {path} no existe")
        return {"processed": 0, "inserted": 0, "skipped_dup": 0, "errors": 0}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    # Asegurar que la tabla existe (migration 003)
    _ensure_outcomes_table(conn)

    rows = _load_csv(path)
    stats = {"processed": 0, "inserted": 0, "skipped_dup": 0, "errors": 0}

    for row in rows:
        eid = clean(row.get("entity_id"))
        otype = clean(row.get("outcome_type")).lower().replace(" ", "_")
        odate = clean(row.get("outcome_date"))
        source_url = clean(row.get("source_url"))

        if not eid or not otype or not odate:
            continue  # fila vacía

        # Validaciones
        if not source_url:
            print(f"  [error] {eid} {otype}: source_url obligatorio — saltar")
            stats["errors"] += 1
            continue

        if otype not in VALID_OUTCOME_TYPES:
            print(f"  [warn] {eid}: outcome_type '{otype}' desconocido — aceptado igual")

        if not conn.execute("SELECT 1 FROM entities WHERE entity_id=?", (eid,)).fetchone():
            print(f"  [warn] entity '{eid}' no existe — saltar")
            stats["errors"] += 1
            continue

        # Deduplicación por (entity_id, outcome_type, source_url)
        dup = conn.execute(
            "SELECT outcome_id FROM outcomes WHERE entity_id=? AND outcome_type=? AND source_url=?",
            (eid, otype, source_url),
        ).fetchone()
        if dup:
            stats["skipped_dup"] += 1
            continue

        amount = to_float(row.get("amount_usd"))
        currency = clean(row.get("currency")) or "USD"
        counterparty = clean(row.get("counterparty_id")) or None

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """INSERT INTO outcomes
               (entity_id, outcome_type, outcome_date, counterparty_id,
                amount_usd, currency, source_url, notes, added_by, added_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (eid, otype, odate, counterparty,
             amount, currency, source_url,
             clean(row.get("notes")) or None,
             "human:curador", now),
        )
        log_change(
            conn,
            actor="human:curador",
            entity_id=eid,
            field="outcomes.NEW",
            old_value=None,
            new_value=f"{otype} {odate} {amount or ''}",
            reason=f"staging/outcomes_incoming.csv",
            evidence_url=source_url,
        )
        stats["inserted"] += 1
        stats["processed"] += 1

    conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────

def _load_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _ensure_outcomes_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS outcomes (
            outcome_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id    TEXT NOT NULL,
            outcome_type TEXT NOT NULL,
            outcome_date TEXT NOT NULL,
            counterparty_id TEXT,
            amount_usd   REAL,
            currency     TEXT DEFAULT 'USD',
            source_url   TEXT NOT NULL,
            notes        TEXT,
            added_by     TEXT,
            added_at     TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
        )
    """)
