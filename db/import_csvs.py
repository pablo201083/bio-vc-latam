"""
db/import_csvs.py — one-shot CSV → SQLite importer.

Construye db/bio_latam.db desde cero usando:
  1. schema_observatorio_biotech_v2.sql (schema sellado de 24 tablas)
  2. db/migrations/*.sql (5 extensiones del plan: startup_extended, audit_log, outcomes,
     matchmaking_predictions, ecosystem graph outputs)

Luego importa los CSVs existentes:
  - startup_master_dataset.csv → entities + startups + sources + startup_extended
  - canonical/canonical_entities.csv → entities (UPSERT) + investors/organizations stubs
  - canonical/canonical_aliases.csv → entity_aliases
  - canonical/canonical_investment_edges.csv → investment_edges (+ sources)

Estrategia:
  - FK constraints OFF durante bulk import; al final corremos `PRAGMA foreign_key_check`
    como validación blanda (warnings, no errors).
  - El master_dataset es la fuente de verdad para startups: si una entidad existe en
    canonical pero no en master, se respeta canonical; pero si está en ambos, master gana.

Uso:
    python db/import_csvs.py
"""
from __future__ import annotations

import pathlib
import sqlite3
import sys
import time
from datetime import datetime, timezone
from typing import Any

# Asegurar que src/ es importable cuando se ejecuta desde la raíz
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils import (  # noqa: E402
    clean,
    country_centroid,
    normalize_key,
    repair_mojibake,
    scope_to_entity_status,
    slugify,
    to_float,
    to_int,
    load_csv,
)

DB_PATH = ROOT / "db" / "bio_latam.db"
SCHEMA_BASE = ROOT / "schema_observatorio_biotech_v2.sql"
MIGRATIONS_DIR = ROOT / "db" / "migrations"

# CSVs a importar (ordenados por dependencia)
MASTER_DATASET_CSV = ROOT / "startup_master_dataset.csv"
CANONICAL_ENTITIES_CSV = ROOT / "canonical" / "canonical_entities.csv"
CANONICAL_ALIASES_CSV = ROOT / "canonical" / "canonical_aliases.csv"
CANONICAL_EDGES_CSV = ROOT / "canonical" / "canonical_investment_edges.csv"


# ---------------------------------------------------------------------------
# Schema setup
# ---------------------------------------------------------------------------

def init_schema(conn: sqlite3.Connection) -> None:
    """Crea todas las tablas: schema base + 5 migrations."""
    print(f"  Aplicando schema base: {SCHEMA_BASE.name}")
    conn.executescript(SCHEMA_BASE.read_text(encoding="utf-8"))

    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for mig in migrations:
        print(f"  Aplicando migration: {mig.name}")
        conn.executescript(mig.read_text(encoding="utf-8"))

    conn.commit()


# ---------------------------------------------------------------------------
# Master dataset → entities + startups + sources + startup_extended
# ---------------------------------------------------------------------------

# Mapeo de columnas CSV → tabla destino. Una columna puede ir a varias tablas.
MASTER_TO_ENTITIES = {
    "entity_type": "startup",  # constante para este CSV
}

# Campos del CSV que van a startup_extended (replicamos algunos editoriales clave
# que también se mapean a entities/startups para evitar joins en cada query).
SX_FIELDS = {
    "data_quality_score": "data_quality_score_10",
    "quality_band": "quality_band",
    "review_status": "review_status",
    "bio_lens_tags": "bio_lens_tags",
    "domain_tags": "domain_tags",
    "technology_tags": "technology_tags",
    "scale_tags": "scale_tags",
    "business_one_liner": "business_one_liner",
    "assignment_method": "assignment_method",
    "taxonomy_confidence": "taxonomy_confidence",
    "scope_decision": "scope_decision",
    "scope_status": "scope_status",
    "scope_basis": "scope_basis",
    "scope_reason": "scope_reason",
    "macro_theme": "macro_theme",
    "emergent_theme": "emergent_theme",
    "market_label": "market_label",
    "transition_function": "transition_function",
    "technical_stack": "technical_stack",
    "industry_destination": "industry_destination",
    "thesis_fit": "thesis_fit",
    "materiality_signal": "materiality_signal",
    "thesis_scope_note": "thesis_scope_note",
    "research_priority": "research_priority",
    "missing_signals": "missing_signals",
    "startup_summary_v1": "startup_summary_v1",
    "summary_confidence": "summary_confidence",
    "valuation_tier": "valuation_tier",
    "trl_current_status": "trl_current_status",
    "last_reviewed_at": "last_reviewed_at",
}

# Tipos numéricos en startup_extended
SX_NUMERIC = {"data_quality_score", "taxonomy_confidence"}


def import_master_dataset(conn: sqlite3.Connection) -> dict[str, int]:
    """Importa startup_master_dataset.csv. Retorna conteos por tabla."""
    rows = load_csv(MASTER_DATASET_CSV)
    print(f"  Cargado: {len(rows)} filas desde {MASTER_DATASET_CSV.name}")

    counts = {"entities": 0, "startups": 0, "sources": 0, "startup_extended": 0}
    cur = conn.cursor()

    for row in rows:
        startup_id = clean(row.get("startup_id"))
        startup_name = repair_mojibake(row.get("startup_name"))
        if not startup_id or not startup_name:
            continue

        country = clean(row.get("structured_country")) or None
        website = clean(row.get("source_url")) or None
        scope_decision = clean(row.get("scope_decision"))
        status = scope_to_entity_status(scope_decision)
        summary = repair_mojibake(row.get("startup_summary_v1"))
        slug = slugify(startup_name)

        # entities (INSERT OR REPLACE — master_dataset es fuente de verdad)
        cur.execute(
            """INSERT OR REPLACE INTO entities
               (entity_id, entity_type, canonical_name, slug, short_description,
                country_code, website, status, last_verified_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (startup_id, "startup", startup_name, slug, summary[:500] if summary else None,
             country, website, status, clean(row.get("last_reviewed_at")) or None),
        )
        counts["entities"] += 1

        # startups (schema base)
        cur.execute(
            """INSERT OR REPLACE INTO startups
               (startup_id, biotech_vertical, biotech_subvertical, technology_platform,
                trl_level, validation_status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                startup_id,
                clean(row.get("macro_theme")) or None,
                clean(row.get("emergent_theme")) or None,
                clean(row.get("technical_stack")) or None,
                to_int(row.get("trl_current")),
                clean(row.get("thesis_fit")) or None,
            ),
        )
        counts["startups"] += 1

        # sources (registry de evidencia editorial)
        src_url = clean(row.get("source_url"))
        src_type = clean(row.get("source_type"))
        if src_url and src_type:
            source_id = f"src_{startup_id}"
            cur.execute(
                """INSERT OR REPLACE INTO sources
                   (source_id, source_type, title, url, published_at, retrieved_at, excerpt)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    source_id,
                    src_type,
                    f"Evidencia editorial: {startup_name}",
                    src_url,
                    clean(row.get("source_date")) or None,
                    clean(row.get("last_reviewed_at")) or None,
                    repair_mojibake(row.get("evidence_excerpt"))[:2000] or None,
                ),
            )
            counts["sources"] += 1

        # startup_extended (todos los campos editoriales)
        sx_values: dict[str, Any] = {"startup_id": startup_id}
        for sx_col, csv_col in SX_FIELDS.items():
            raw = row.get(csv_col)
            if sx_col in SX_NUMERIC:
                sx_values[sx_col] = to_float(raw)
            else:
                sx_values[sx_col] = repair_mojibake(raw) or None

        # Geocoding
        if country:
            centroid = country_centroid(country)
            if centroid:
                sx_values["latitude"] = centroid[0]
                sx_values["longitude"] = centroid[1]

        cols = list(sx_values.keys())
        placeholders = ", ".join(["?"] * len(cols))
        cur.execute(
            f"INSERT OR REPLACE INTO startup_extended ({', '.join(cols)}) VALUES ({placeholders})",
            tuple(sx_values.get(c) for c in cols),
        )
        counts["startup_extended"] += 1

    conn.commit()
    return counts


# ---------------------------------------------------------------------------
# canonical_entities.csv → entities (UPSERT) + stubs en investors/organizations
# ---------------------------------------------------------------------------

def import_canonical_entities(conn: sqlite3.Connection) -> dict[str, int]:
    rows = load_csv(CANONICAL_ENTITIES_CSV)
    print(f"  Cargado: {len(rows)} filas desde {CANONICAL_ENTITIES_CSV.name}")

    counts = {"entities_inserted": 0, "entities_skipped": 0, "investors": 0,
              "organizations": 0, "corporates": 0, "esos": 0}
    cur = conn.cursor()

    for row in rows:
        entity_id = clean(row.get("entity_id"))
        entity_type = clean(row.get("entity_type")) or "unknown"
        canonical_name = repair_mojibake(row.get("canonical_name"))
        if not entity_id or not canonical_name:
            continue

        # Skip si ya existe (master_dataset gana)
        existing = cur.execute(
            "SELECT 1 FROM entities WHERE entity_id = ?", (entity_id,)
        ).fetchone()
        if existing:
            counts["entities_skipped"] += 1
        else:
            slug = clean(row.get("slug")) or slugify(canonical_name)
            cur.execute(
                """INSERT INTO entities (entity_id, entity_type, canonical_name, slug, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (entity_id, entity_type, canonical_name, slug, "active"),
            )
            counts["entities_inserted"] += 1

        # Crear stub en la tabla especializada según entity_type
        if entity_type == "capital" or entity_type == "investor":
            cur.execute(
                "INSERT OR IGNORE INTO investors (investor_id, investor_type, active_status) "
                "VALUES (?, ?, ?)",
                (entity_id, entity_type, "unknown"),
            )
            counts["investors"] += 1
        elif entity_type == "organization" or entity_type == "institution":
            cur.execute(
                "INSERT OR IGNORE INTO organizations (org_id, org_type) VALUES (?, ?)",
                (entity_id, entity_type),
            )
            counts["organizations"] += 1
        elif entity_type == "corporate":
            cur.execute(
                "INSERT OR IGNORE INTO corporates (corporate_id) VALUES (?)",
                (entity_id,),
            )
            counts["corporates"] += 1
        elif entity_type == "eso":
            cur.execute(
                "INSERT OR IGNORE INTO esos (eso_id) VALUES (?)",
                (entity_id,),
            )
            counts["esos"] += 1
        elif entity_type == "startup":
            # Si no estaba en master, crear stub minimal en startups
            cur.execute(
                "INSERT OR IGNORE INTO startups (startup_id) VALUES (?)",
                (entity_id,),
            )

    conn.commit()
    return counts


# ---------------------------------------------------------------------------
# canonical_aliases.csv → entity_aliases
# ---------------------------------------------------------------------------

def import_aliases(conn: sqlite3.Connection) -> int:
    rows = load_csv(CANONICAL_ALIASES_CSV)
    print(f"  Cargado: {len(rows)} filas desde {CANONICAL_ALIASES_CSV.name}")

    inserted = 0
    cur = conn.cursor()
    for row in rows:
        alias_id = clean(row.get("alias_id"))
        entity_id = clean(row.get("entity_id"))
        alias = repair_mojibake(row.get("alias"))
        if not alias_id or not entity_id or not alias:
            continue
        # Verificar que entity_id existe
        if not cur.execute("SELECT 1 FROM entities WHERE entity_id = ?", (entity_id,)).fetchone():
            continue
        cur.execute(
            """INSERT OR IGNORE INTO entity_aliases
               (alias_id, entity_id, alias, alias_type, is_preferred)
               VALUES (?, ?, ?, ?, ?)""",
            (alias_id, entity_id, alias, clean(row.get("alias_type")) or "variant",
             to_int(row.get("is_preferred"), 0) or 0),
        )
        if cur.rowcount > 0:
            inserted += 1
    conn.commit()
    return inserted


# ---------------------------------------------------------------------------
# canonical_investment_edges.csv → investment_edges
# ---------------------------------------------------------------------------

def import_investment_edges(conn: sqlite3.Connection) -> dict[str, int]:
    rows = load_csv(CANONICAL_EDGES_CSV)
    print(f"  Cargado: {len(rows)} filas desde {CANONICAL_EDGES_CSV.name}")

    counts = {"inserted": 0, "skipped_missing_endpoint": 0}
    cur = conn.cursor()

    for row in rows:
        investment_id = clean(row.get("investment_id"))
        investor_id = clean(row.get("investor_id"))
        startup_id = clean(row.get("startup_id"))
        if not investment_id or not investor_id or not startup_id:
            counts["skipped_missing_endpoint"] += 1
            continue

        # Verificar que ambos endpoints existen como entidades
        inv_exists = cur.execute("SELECT 1 FROM entities WHERE entity_id = ?", (investor_id,)).fetchone()
        st_exists = cur.execute("SELECT 1 FROM entities WHERE entity_id = ?", (startup_id,)).fetchone()
        if not inv_exists or not st_exists:
            counts["skipped_missing_endpoint"] += 1
            continue

        # Asegurar que investor_id está en investors (FK del schema)
        cur.execute(
            "INSERT OR IGNORE INTO investors (investor_id, active_status) VALUES (?, 'unknown')",
            (investor_id,),
        )
        # Asegurar que startup_id está en startups
        cur.execute(
            "INSERT OR IGNORE INTO startups (startup_id) VALUES (?)",
            (startup_id,),
        )

        notes = repair_mojibake(row.get("notes"))[:1000]
        relation_type = clean(row.get("relation_type_raw")) or None

        cur.execute(
            """INSERT OR REPLACE INTO investment_edges
               (investment_id, investor_id, startup_id, round_name, round_stage,
                announced_date, confidence_score, source_id, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                investment_id,
                investor_id,
                startup_id,
                relation_type,
                clean(row.get("direction_status")) or None,
                None,  # announced_date no está en canonical edges actuales
                to_float(row.get("confidence_score")),
                clean(row.get("source_file")) or None,
                notes or None,
            ),
        )
        counts["inserted"] += 1

    conn.commit()
    return counts


# ---------------------------------------------------------------------------
# Post-import validation
# ---------------------------------------------------------------------------

def post_import_validation(conn: sqlite3.Connection) -> dict[str, Any]:
    """Replica validate_reference_base.ps1 como queries SQL. Warnings, no errors."""
    cur = conn.cursor()
    results: dict[str, Any] = {}

    # 1. Startups 'include' sin source_url
    results["include_without_source"] = cur.execute(
        """SELECT count(*) FROM startup_extended sx
           JOIN entities e ON e.entity_id = sx.startup_id
           WHERE sx.scope_decision = 'include' AND (e.website IS NULL OR e.website = '')"""
    ).fetchone()[0]

    # 2. Nombres normalizados duplicados
    # SQLite no tiene la función normalize_key — la simulamos con LOWER + replace
    # (la dedupe real ya fue hecha por build_canonical_layer; esto es un sanity check)
    duplicates = cur.execute(
        """SELECT lower(canonical_name) AS k, count(*) c
           FROM entities GROUP BY k HAVING c > 1"""
    ).fetchall()
    results["duplicate_names_count"] = len(duplicates)
    results["duplicate_names_sample"] = duplicates[:5]

    # 3. Edges a entidades inexistentes (FK check blando)
    results["edges_to_missing_entities"] = cur.execute(
        """SELECT count(*) FROM investment_edges ie
           WHERE NOT EXISTS (SELECT 1 FROM entities WHERE entity_id = ie.investor_id)
              OR NOT EXISTS (SELECT 1 FROM entities WHERE entity_id = ie.startup_id)"""
    ).fetchone()[0]

    # 4. Aliases con entity_id inexistente
    results["aliases_to_missing_entities"] = cur.execute(
        """SELECT count(*) FROM entity_aliases ea
           WHERE NOT EXISTS (SELECT 1 FROM entities WHERE entity_id = ea.entity_id)"""
    ).fetchone()[0]

    # 5. PRAGMA foreign_key_check (más exhaustivo)
    fk_violations = cur.execute("PRAGMA foreign_key_check").fetchall()
    results["fk_violations"] = len(fk_violations)
    results["fk_violations_sample"] = fk_violations[:5]

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    t0 = time.time()
    print(f"\n=== BIO LATAM SQLite importer ===")
    print(f"Target DB: {DB_PATH}")

    if DB_PATH.exists():
        print(f"  Borrando DB existente: {DB_PATH}")
        DB_PATH.unlink()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")  # OFF durante bulk import

    print("\n[1/5] Aplicando schema base + migrations...")
    init_schema(conn)

    print("\n[2/5] Importando canonical_entities.csv (UPSERT a entities)...")
    ce_counts = import_canonical_entities(conn)
    print(f"  → entities inserted: {ce_counts['entities_inserted']}, "
          f"skipped (already from master): {ce_counts['entities_skipped']}")
    print(f"  → investors stubs: {ce_counts['investors']}, "
          f"organizations: {ce_counts['organizations']}, "
          f"corporates: {ce_counts['corporates']}, esos: {ce_counts['esos']}")

    print("\n[3/5] Importando startup_master_dataset.csv...")
    md_counts = import_master_dataset(conn)
    print(f"  → entities: {md_counts['entities']}, startups: {md_counts['startups']}, "
          f"sources: {md_counts['sources']}, startup_extended: {md_counts['startup_extended']}")

    print("\n[4/5] Importando canonical_aliases.csv...")
    alias_count = import_aliases(conn)
    print(f"  → entity_aliases: {alias_count}")

    print("\n[4b/5] Importando canonical_investment_edges.csv...")
    edge_counts = import_investment_edges(conn)
    print(f"  → investment_edges: {edge_counts['inserted']}, "
          f"skipped: {edge_counts['skipped_missing_endpoint']}")

    print("\n[5/5] Validaciones post-import...")
    validation = post_import_validation(conn)
    print(f"  include startups sin source_url:    {validation['include_without_source']}")
    print(f"  nombres canonicos duplicados:       {validation['duplicate_names_count']}")
    print(f"  edges a entidades inexistentes:     {validation['edges_to_missing_entities']}")
    print(f"  aliases a entidades inexistentes:   {validation['aliases_to_missing_entities']}")
    print(f"  FK violations (PRAGMA check):       {validation['fk_violations']}")
    if validation["fk_violations_sample"]:
        print(f"  FK sample: {validation['fk_violations_sample']}")
    if validation["duplicate_names_sample"]:
        print(f"  Dup names sample: {validation['duplicate_names_sample']}")

    # Activar FK enforcement para futuro uso (validar que el estado actual es válido)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.commit()
    conn.close()

    elapsed = time.time() - t0
    print(f"\n✓ Database built: {DB_PATH} ({elapsed:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
