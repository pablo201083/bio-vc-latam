"""
src/discovery.py — Pipeline de descubrimiento de startups.

Lee staging/discovered_startups.csv y los ingesta a entities + startup_extended
con scope_decision='review' para que el curador valide.

Uso:
    python pipeline.py ingest-discovered
"""
from __future__ import annotations

import csv
import re
import sqlite3
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.audit import log_change
from src.utils import clean, to_int

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
STAGING = ROOT / "staging"

# Sectores bio-relevantes para auto-clasificar scope_decision
BIO_SECTORS = {
    "biotech", "agtech", "agbiotech", "foodtech", "healthtech", "medtech",
    "climatetech", "cleantech", "deepbiotech", "genomics", "diagnostics",
    "biomanufacturing", "synthetic-biology", "cellular-ag", "bioinputs",
    "animal-health", "oncology", "drug-discovery", "precision-medicine",
    "bioplastics", "biomaterials", "bioinformatics", "environmental-biotech",
    "marine-biotech", "plant-biotech", "fermentation", "precision-fermentation",
    "aquatech", "spacetech",
}

MACRO_THEME_MAP = {
    "agtech": "precision agriculture and resource intelligence",
    "agbiotech": "ag biologicals and crop resilience",
    "foodtech": "food biotech and novel ingredients",
    "biotech": "therapeutics and regenerative medicine",
    "healthtech": "diagnostics and medtech",
    "medtech": "diagnostics and medtech",
    "genomics": "computational biology and scientific software",
    "diagnostics": "diagnostics and medtech",
    "cleantech": "climate, energy and resource systems",
    "climatetech": "climate, energy and resource systems",
    "biomanufacturing": "biomanufacturing and bioindustrial platforms",
    "biomaterials": "biobased chemistry and advanced materials",
    "bioplastics": "biobased chemistry and advanced materials",
    "synthetic-biology": "biomanufacturing and bioindustrial platforms",
    "precision-fermentation": "food biotech and novel ingredients",
    "cellular-ag": "food biotech and novel ingredients",
    "animal-health": "ag biologicals and crop resilience",
    "drug-discovery": "therapeutics and regenerative medicine",
    "oncology": "therapeutics and regenerative medicine",
    "precision-medicine": "diagnostics and medtech",
    "bioinformatics": "computational biology and scientific software",
    "deepbiotech": "biomanufacturing and bioindustrial platforms",
    "spacetech": "climate, energy and resource systems",
    "aquatech": "ag biologicals and crop resilience",
}


def _slug(name: str) -> str:
    s = name.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _entity_id(name: str, country: str = "") -> str:
    base = _slug(name)
    if country:
        return f"{base}-{country.lower()}"
    return base


def ingest_discovered(db_path: Path = DB_PATH) -> dict:
    path = STAGING / "discovered_startups.csv"
    if not path.exists():
        print(f"  [skip] {path} no existe")
        return {}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    now = datetime.now(timezone.utc).isoformat()

    rows = _load_csv(path)
    stats = {"processed": 0, "inserted": 0, "skipped_dup": 0, "errors": 0}

    for row in rows:
        name = clean(row.get("name"))
        country = clean(row.get("country_code", "")).upper()
        sector = clean(row.get("sector", "")).lower()
        desc = clean(row.get("description", ""))
        website = clean(row.get("website", ""))
        source_url = clean(row.get("source_url", ""))
        founded = to_int(row.get("founded_year"))
        scope_rec = clean(row.get("scope_recommendation", "review")).lower()

        if not name:
            continue

        # Generate stable entity_id
        eid = _entity_id(name, country)

        # Dedup check by canonical_name (case-insensitive)
        existing = conn.execute(
            "SELECT entity_id FROM entities WHERE lower(canonical_name)=lower(?)",
            (name,),
        ).fetchone()
        if existing:
            stats["skipped_dup"] += 1
            continue

        # Also check slug collision
        if conn.execute("SELECT 1 FROM entities WHERE entity_id=?", (eid,)).fetchone():
            eid = f"{eid}-{uuid.uuid4().hex[:4]}"

        # Infer macro_theme from sector
        macro = ""
        for s in sector.replace(";", ",").split(","):
            s = s.strip()
            if s in MACRO_THEME_MAP:
                macro = MACRO_THEME_MAP[s]
                break
        if not macro and desc:
            # crude fallback from description keywords
            dl = desc.lower()
            for kw, theme in [
                ("agro", "precision agriculture and resource intelligence"),
                ("crop", "ag biologicals and crop resilience"),
                ("food", "food biotech and novel ingredients"),
                ("cancer", "therapeutics and regenerative medicine"),
                ("diagnos", "diagnostics and medtech"),
                ("climate", "climate, energy and resource systems"),
                ("manufactur", "biomanufacturing and bioindustrial platforms"),
            ]:
                if kw in dl:
                    macro = theme
                    break

        # Determine scope
        sector_set = {s.strip() for s in sector.replace(";", ",").split(",") if s.strip()}
        is_bio = bool(sector_set & BIO_SECTORS)
        if scope_rec == "include" and is_bio:
            scope = "include"
        elif scope_rec == "exclude":
            scope = "exclude"
        else:
            scope = "review"

        try:
            # Insert into entities
            conn.execute(
                """INSERT INTO entities
                   (entity_id, entity_type, canonical_name, slug, country_code,
                    website, founded_year, status)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (eid, "startup", name, _slug(name), country or None,
                 website or None, founded, "active"),
            )

            # Insert into startup_extended
            conn.execute(
                """INSERT INTO startup_extended
                   (startup_id, scope_decision, scope_status, scope_basis,
                    macro_theme, startup_summary_v1, data_quality_score,
                    quality_band, review_status, last_reviewed_at, missing_signals)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (eid, scope, "pending_review", "auto_discovery",
                 macro or None,
                 desc or f"Discovered via systematic search. Sector: {sector}.",
                 5.0,  # baseline score for auto-discovered
                 "medium",
                 "pending",
                 now,
                 "needs_full_review,needs_website_verification"),
            )

            log_change(
                conn,
                actor="pipeline:discovery",
                entity_id=eid,
                field="entities.NEW",
                old_value=None,
                new_value=f"{name} ({country}) [{scope}]",
                reason=f"auto_discovery from {source_url or 'web_search'}",
                evidence_url=source_url or None,
            )

            stats["inserted"] += 1
        except Exception as e:
            print(f"  [error] {name}: {e}")
            stats["errors"] += 1

        stats["processed"] += 1

    conn.commit()
    conn.close()
    return stats


def _load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))
