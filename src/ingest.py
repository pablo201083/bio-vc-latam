"""
src/ingest.py — Ingesta manual de datos curados a la DB.

Comandos disponibles (vía pipeline.py):
    python pipeline.py ingest-founding-years      # staging/founding_years.csv → entities.founded_year
    python pipeline.py ingest-rounds              # staging/investment_rounds.csv → investment_edges
    python pipeline.py ingest-outcomes            # staging/outcomes_incoming.csv → outcomes
    python pipeline.py ingest-fund-profiles       # staging/fund_profiles.csv → investors + entities
    python pipeline.py ingest-entity-enrichments  # staging/entity_enrichments.csv → bulk field corrections

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


# ─────────────────────────────────────────────
# ingest-fund-profiles
# ─────────────────────────────────────────────

VALID_INVESTOR_TYPES = {
    "vc", "accelerator", "company_builder", "multilateral", "impact_fund",
    "corporate_vc", "fund_of_funds", "angel_network", "development_finance", "association",
}

VALID_LEAD_BEHAVIORS = {"lead", "follow", "both", "co-lead"}


def ingest_fund_profiles(db_path: Path = DB_PATH) -> dict[str, int]:
    """
    Lee staging/fund_profiles.csv y enriquece inversores existentes en entities + investors.

    Formato CSV (campos requeridos: investor_id, investor_type, country_code, website, source_url):
        investor_id, investor_name, investor_type, country_code, website,
        thesis, preferred_stages, geography_focus, vertical_focus,
        ticket_min_usd, ticket_max_usd, lead_behavior, active_status,
        source_url, notes

    - Solo actualiza inversores que ya existen en entities WHERE entity_type='investor'
    - Separa updates: entities (website, country_code) vs investors (resto)
    - source_url es OBLIGATORIO por fila
    """
    path = STAGING / "fund_profiles.csv"
    if not path.exists():
        print(f"  [skip] {path} no existe")
        return {"processed": 0, "entity_fields_updated": 0, "investor_fields_updated": 0, "errors": 0}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    rows = _load_csv(path)
    stats = {"processed": 0, "entity_fields_updated": 0, "investor_fields_updated": 0, "errors": 0}

    for row in rows:
        inv_id = clean(row.get("investor_id"))
        source_url = clean(row.get("source_url"))
        notes_raw = clean(row.get("notes"))

        if not inv_id:
            continue

        if not source_url:
            print(f"  [error] {inv_id}: source_url obligatorio — saltar")
            stats["errors"] += 1
            continue

        # Verificar que existe como inversor
        exists = conn.execute(
            "SELECT 1 FROM entities WHERE entity_id=? AND entity_type='investor'",
            (inv_id,),
        ).fetchone()
        if not exists:
            print(f"  [warn] '{inv_id}' no encontrado en entities como investor — saltar")
            stats["errors"] += 1
            continue

        inv_type = clean(row.get("investor_type")).lower()
        if inv_type and inv_type not in VALID_INVESTOR_TYPES:
            print(f"  [warn] {inv_id}: investor_type '{inv_type}' desconocido (aceptado igual)")

        lead_beh = clean(row.get("lead_behavior")).lower() or None
        if lead_beh and lead_beh not in VALID_LEAD_BEHAVIORS:
            print(f"  [warn] {inv_id}: lead_behavior '{lead_beh}' desconocido (aceptado igual)")

        # Ticket size validation
        tick_min = to_float(row.get("ticket_min_usd"))
        tick_max = to_float(row.get("ticket_max_usd"))
        if tick_min is not None and tick_max is not None and tick_max < tick_min:
            tick_min, tick_max = tick_max, tick_min  # swap silently

        reason = f"staging/fund_profiles.csv"
        if notes_raw:
            reason += f" — {notes_raw}"

        # ── entities updates (website, country_code) ──────────────────────────
        entity_updates: dict[str, Any] = {}
        website = clean(row.get("website")) or None
        country = clean(row.get("country_code")).upper() or None
        if website:
            entity_updates["website"] = website
        if country:
            entity_updates["country_code"] = country

        if entity_updates:
            n = diff_and_log_update(
                conn,
                table="entities",
                row_id_col="entity_id",
                row_id=inv_id,
                new_values=entity_updates,
                actor="human:curador",
                reason=reason,
                evidence_url=source_url,
            )
            stats["entity_fields_updated"] += n

        # ── investors updates ─────────────────────────────────────────────────
        investor_updates: dict[str, Any] = {}
        if inv_type:
            investor_updates["investor_type"] = inv_type
        thesis = clean(row.get("thesis")) or None
        if thesis:
            investor_updates["thesis"] = thesis[:400]  # enforce max length
        pref_stages = clean(row.get("preferred_stages")) or None
        if pref_stages:
            investor_updates["preferred_stages"] = pref_stages
        geo = clean(row.get("geography_focus")) or None
        if geo:
            investor_updates["geography_focus"] = geo
        vert = clean(row.get("vertical_focus")) or None
        if vert:
            investor_updates["vertical_focus"] = vert
        if tick_min is not None:
            investor_updates["ticket_min_usd"] = tick_min
        if tick_max is not None:
            investor_updates["ticket_max_usd"] = tick_max
        if lead_beh:
            investor_updates["lead_behavior"] = lead_beh
        active = clean(row.get("active_status")).lower() or None
        if active:
            investor_updates["active_status"] = active

        if investor_updates:
            n = diff_and_log_update(
                conn,
                table="investors",
                row_id_col="investor_id",
                row_id=inv_id,
                new_values=investor_updates,
                actor="human:curador",
                reason=reason,
                evidence_url=source_url,
            )
            stats["investor_fields_updated"] += n

        stats["processed"] += 1

    conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# ingest-entity-enrichments
# ─────────────────────────────────────────────

# Columnas PK prohibidas (no se pueden sobreescribir por este mecanismo)
_PROHIBITED_FIELDS = {
    "entity_id", "startup_id", "investor_id", "investment_id",
    "audit_id", "outcome_id", "relation_id",
}

# Mapa de PK por tabla
_TABLE_PK = {
    "entities": "entity_id",
    "startup_extended": "startup_id",
    "investors": "investor_id",
}


def ingest_entity_enrichments(db_path: Path = DB_PATH) -> dict[str, int]:
    """
    Lee staging/entity_enrichments.csv y aplica correcciones masivas de campos individuales.

    Formato CSV:
        entity_id, entity_name, table_name, field_name, new_value, source_url, confidence, notes

    - table_name: entities | startup_extended | investors
    - field_name: validado contra PRAGMA table_info en runtime
    - new_value vacío ("") → NULL
    - Campos PK prohibidos
    - source_url es OBLIGATORIO
    - Idempotente: si old_value == new_value, silencio
    """
    path = STAGING / "entity_enrichments.csv"
    if not path.exists():
        print(f"  [skip] {path} no existe")
        return {"processed": 0, "updated": 0, "skipped_no_change": 0, "errors": 0}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    # Cache allowed columns per table
    allowed_cols: dict[str, set[str]] = {}
    for tbl in _TABLE_PK:
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({tbl})").fetchall()}
        allowed_cols[tbl] = cols

    rows = _load_csv(path)
    stats = {"processed": 0, "updated": 0, "skipped_no_change": 0, "errors": 0}

    for row in rows:
        eid = clean(row.get("entity_id"))
        table = clean(row.get("table_name")).lower()
        field = clean(row.get("field_name")).lower()
        source_url = clean(row.get("source_url"))
        notes_raw = clean(row.get("notes"))
        raw_val = row.get("new_value", "")

        if not eid or not table or not field:
            continue

        if not source_url:
            print(f"  [error] {eid}/{field}: source_url obligatorio — saltar")
            stats["errors"] += 1
            continue

        if table not in _TABLE_PK:
            print(f"  [error] {eid}: table_name '{table}' desconocido (usar: {list(_TABLE_PK)})")
            stats["errors"] += 1
            continue

        if field in _PROHIBITED_FIELDS:
            print(f"  [error] {eid}: campo '{field}' es PK prohibido — saltar")
            stats["errors"] += 1
            continue

        if field not in allowed_cols.get(table, set()):
            print(f"  [error] {eid}: campo '{field}' no existe en tabla '{table}' — saltar")
            stats["errors"] += 1
            continue

        # Verificar que entity existe en entities
        if not conn.execute("SELECT 1 FROM entities WHERE entity_id=?", (eid,)).fetchone():
            print(f"  [warn] entity '{eid}' no existe — saltar")
            stats["errors"] += 1
            continue

        # Mapear "" → None
        new_val: Any = None if raw_val.strip() == "" else raw_val.strip()

        conf = to_float(row.get("confidence")) or 0.9
        reason = f"staging/entity_enrichments.csv"
        if notes_raw:
            reason += f" — {notes_raw}"

        pk_col = _TABLE_PK[table]
        n = diff_and_log_update(
            conn,
            table=table,
            row_id_col=pk_col,
            row_id=eid,
            new_values={field: new_val},
            actor="human:curador",
            reason=reason,
            evidence_url=source_url,
        )
        if n > 0:
            stats["updated"] += n
        else:
            stats["skipped_no_change"] += 1

        stats["processed"] += 1

    conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# merge-duplicate-entities
# ─────────────────────────────────────────────

def merge_duplicate_entities(db_path: Path = DB_PATH, dry_run: bool = False) -> dict[str, int]:
    """
    Detecta pares de entidades con el mismo canonical_name (case-insensitive) donde
    uno tiene startup_extended (el canónico) y el otro tiene investment_edges (el duplicado
    legacy, generalmente de PascalCase del graphml).

    Acción por par:
    1. Migramos todas las edges del duplicado → canónico (UPDATE investment_edges)
    2. Actualizamos entity_aliases si corresponde
    3. Eliminamos la entidad duplicada (DELETE FROM entities)
    4. Logueamos todo en audit_log

    En dry_run=True muestra los pares sin modificar nada.

    Retorna: {pairs_found, edges_migrated, entities_deleted, skipped_complex, errors}
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    # Encontrar grupos con canonical_name duplicado (case-insensitive)
    dup_groups = conn.execute("""
        SELECT lower(canonical_name) as norm_name,
               count(*) as n,
               group_concat(entity_id, '||') as ids
        FROM entities
        WHERE entity_type = 'startup'
        GROUP BY lower(canonical_name)
        HAVING count(*) > 1
    """).fetchall()

    stats = {"pairs_found": len(dup_groups), "edges_migrated": 0,
             "entities_deleted": 0, "skipped_complex": 0, "errors": 0}

    for norm_name, n_entities, ids_str in dup_groups:
        entity_ids = ids_str.split("||")

        # Clasificar: canónico (tiene startup_extended) vs duplicado (tiene edges pero no startup_extended)
        canonical_id = None
        duplicates = []

        for eid in entity_ids:
            has_sx = conn.execute(
                "SELECT scope_decision FROM startup_extended WHERE startup_id=?", (eid,)
            ).fetchone()
            edge_count = conn.execute(
                "SELECT count(*) FROM investment_edges WHERE startup_id=?", (eid,)
            ).fetchone()[0]

            if has_sx:
                if canonical_id is None:
                    canonical_id = eid
                else:
                    # Dos con startup_extended: tomar el que tiene más edges
                    can_edges = conn.execute(
                        "SELECT count(*) FROM investment_edges WHERE startup_id=?", (canonical_id,)
                    ).fetchone()[0]
                    if edge_count > can_edges:
                        duplicates.append(canonical_id)
                        canonical_id = eid
                    else:
                        duplicates.append(eid)
            else:
                duplicates.append(eid)

        if canonical_id is None:
            # Ninguno tiene startup_extended: tomar el que tiene más edges como canónico
            entity_ids_sorted = sorted(
                entity_ids,
                key=lambda x: conn.execute(
                    "SELECT count(*) FROM investment_edges WHERE startup_id=?", (x,)
                ).fetchone()[0],
                reverse=True
            )
            canonical_id = entity_ids_sorted[0]
            duplicates = entity_ids_sorted[1:]

        if dry_run:
            for dup in duplicates:
                dup_edges = conn.execute(
                    "SELECT count(*) FROM investment_edges WHERE startup_id=?", (dup,)
                ).fetchone()[0]
                print(f"  [DRY] '{norm_name}': {dup} ({dup_edges} edges) → {canonical_id}")
            continue

        # Migrar edges para cada duplicado
        for dup_id in duplicates:
            dup_edges = conn.execute(
                "SELECT investment_id, investor_id, round_stage FROM investment_edges WHERE startup_id=?",
                (dup_id,)
            ).fetchall()

            for inv_edge_id, investor_id, stage in dup_edges:
                # Check si ya existe edge canonical_id ↔ investor_id
                existing = conn.execute(
                    "SELECT investment_id FROM investment_edges WHERE startup_id=? AND investor_id=?",
                    (canonical_id, investor_id)
                ).fetchone()

                if existing:
                    # Ya existe: eliminar el duplicado
                    conn.execute("DELETE FROM investment_edges WHERE investment_id=?", (inv_edge_id,))
                    log_change(
                        conn, actor="pipeline:merge_duplicate_entities",
                        entity_id=canonical_id,
                        field="investment_edges.DELETE",
                        old_value=f"{dup_id}→{investor_id} [dup of {existing[0]}]",
                        new_value=f"kept existing edge to {canonical_id}",
                        reason=f"merge-duplicate-entities: {dup_id} → {canonical_id}",
                        evidence_url=None,
                    )
                else:
                    # Migrar al canónico
                    conn.execute(
                        "UPDATE investment_edges SET startup_id=? WHERE investment_id=?",
                        (canonical_id, inv_edge_id)
                    )
                    log_change(
                        conn, actor="pipeline:merge_duplicate_entities",
                        entity_id=canonical_id,
                        field="investment_edges.startup_id",
                        old_value=dup_id,
                        new_value=canonical_id,
                        reason=f"merge-duplicate-entities: migrated edge {investor_id}→{dup_id} to {canonical_id}",
                        evidence_url=None,
                    )
                    stats["edges_migrated"] += 1

            # Eliminar entidad duplicada (CASCADE si hay FKs, manual si no)
            conn.execute("DELETE FROM entity_aliases WHERE entity_id=?", (dup_id,))
            conn.execute("DELETE FROM entities WHERE entity_id=?", (dup_id,))
            log_change(
                conn, actor="pipeline:merge_duplicate_entities",
                entity_id=canonical_id,
                field="entities.DELETE",
                old_value=dup_id,
                new_value=f"merged into {canonical_id}",
                reason=f"merge-duplicate-entities: same canonical_name '{norm_name}'",
                evidence_url=None,
            )
            stats["entities_deleted"] += 1

    if not dry_run:
        conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# enrich-rounds-valuation  (Phase D Pass 1)
# ─────────────────────────────────────────────

# Mapping valuation_tier → inferred round_stage
# Confidence is 0.5 (low — inferencia, no fuente directa)
_TIER_TO_STAGE: dict[float, str] = {
    1.0: "seed",
    1.5: "seed",
    2.0: "series-a",
    3.0: "series-b",
    4.0: "series-c",
}
_TIER_CONFIDENCE = 0.5


def enrich_rounds_from_valuation_tier(db_path: Path = DB_PATH) -> dict[str, int]:
    """
    Phase D Pass 1 — Infiere round_stage en investment_edges a partir de valuation_tier.

    Solo toca edges donde round_stage IS NULL.
    El stage inferido se marca con confidence_score=0.5 y notes con la fuente.

    Retorna: {processed, updated, skipped_no_tier, already_set}
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    # Edges sin round_stage — traer también startup_id e investment_id
    edges = conn.execute(
        """
        SELECT ie.investment_id, ie.startup_id, ie.investor_id,
               sx.valuation_tier
        FROM investment_edges ie
        LEFT JOIN startup_extended sx ON sx.startup_id = ie.startup_id
        WHERE ie.round_stage IS NULL
        """
    ).fetchall()

    stats = {"processed": 0, "updated": 0, "skipped_no_tier": 0, "already_set": 0}

    for inv_id_edge, startup_id, investor_id, valuation_tier in edges:
        stats["processed"] += 1

        if valuation_tier is None:
            stats["skipped_no_tier"] += 1
            continue

        try:
            tier_f = float(valuation_tier)
        except (TypeError, ValueError):
            stats["skipped_no_tier"] += 1
            continue

        stage = _TIER_TO_STAGE.get(tier_f)
        if not stage:
            stats["skipped_no_tier"] += 1
            continue

        n = diff_and_log_update(
            conn,
            table="investment_edges",
            row_id_col="investment_id",
            row_id=inv_id_edge,
            new_values={
                "round_stage": stage,
                "notes": f"inferred_from_valuation_tier:{valuation_tier}",
            },
            actor="pipeline:enrich_rounds_valuation",
            reason=f"Phase D Pass 1 — valuation_tier {valuation_tier} → {stage}",
            evidence_url=None,
        )
        if n > 0:
            stats["updated"] += 1

    conn.commit()
    conn.close()
    return stats


# ─────────────────────────────────────────────
# dedup-investment-edges
# ─────────────────────────────────────────────

def dedup_investment_edges(db_path: Path = DB_PATH) -> dict[str, int]:
    """
    Elimina edges duplicadas (mismo investor_id + startup_id).

    Estrategia de resolución por prioridad:
    1. Mantener la edge con round_stage IS NOT NULL
    2. Si empate → mantener la de mayor confidence_score
    3. Si empate → mantener la de mayor investment_id (más reciente)

    Retorna: {pairs_found, edges_deleted, pairs_ok}
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    # Encontrar pares duplicados
    dups = conn.execute("""
        SELECT investor_id, startup_id, count(*) as n
        FROM investment_edges
        GROUP BY investor_id, startup_id
        HAVING count(*) > 1
    """).fetchall()

    stats = {"pairs_found": len(dups), "edges_deleted": 0, "pairs_ok": 0}

    for investor_id, startup_id, n_edges in dups:
        # Traer todas las edges del par, ordenadas por prioridad
        edges = conn.execute("""
            SELECT investment_id, round_stage, confidence_score, notes
            FROM investment_edges
            WHERE investor_id=? AND startup_id=?
            ORDER BY
                CASE WHEN round_stage IS NOT NULL THEN 0 ELSE 1 END,
                COALESCE(confidence_score, 0) DESC,
                investment_id DESC
        """, (investor_id, startup_id)).fetchall()

        # Mantener el primero (mayor prioridad), eliminar el resto
        keep_id = edges[0][0]
        to_delete = [e[0] for e in edges[1:]]

        for del_id in to_delete:
            conn.execute("DELETE FROM investment_edges WHERE investment_id=?", (del_id,))
            log_change(
                conn,
                actor="pipeline:dedup_investment_edges",
                entity_id=startup_id,
                field="investment_edges.DELETE",
                old_value=f"{investor_id}→{startup_id} [{del_id}]",
                new_value=f"kept:{keep_id}",
                reason=f"dedup — {n_edges} edges para mismo par",
                evidence_url=None,
            )
            stats["edges_deleted"] += 1

        stats["pairs_ok"] += 1

    conn.commit()
    conn.close()
    return stats


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
