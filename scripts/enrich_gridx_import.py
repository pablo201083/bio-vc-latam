"""
Clasifica y enriquece las 183 startups importadas desde GRIDX (scope_reason='gridx_import').

Para cada startup usa su short_description + nombre + país para:
  1. Determinar si pertenece al universo bio (biotech/agtech/medtech/foodtech/climatetech)
  2. Asignar bio_theme_primary (si es bio)
  3. Generar startup_summary_v1 (2-3 oraciones en inglés)
  4. Fijar scope_decision: 'include' si es bio, 'exclude' si no lo es, 'review' si incierto

Salida: staging/entity_enrichments.csv (append) — ingestar con:
    python pipeline.py ingest-entity-enrichments

Uso:
    python scripts/enrich_gridx_import.py           # dry-run: imprime propuestas
    python scripts/enrich_gridx_import.py --apply   # escribe al CSV staging
    python scripts/enrich_gridx_import.py --apply --limit 20
    python scripts/enrich_gridx_import.py --apply --id <startup_id>
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
import time
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DB_PATH    = ROOT / "db" / "bio_latam.db"
STAGING    = ROOT / "staging" / "entity_enrichments.csv"

BIO_THEMES = [
    "Therapeutics",
    "Diagnostics & Health Access",
    "Bioinputs & Crop Resilience",
    "Food Systems & Alt Proteins",
    "Nature & Ecosystem Tech",
    "Farm Intelligence",
    "Biomaterials & Circular Economy",
    "Biomanufacturing & Fermentation Economy",
]

PROMPT = """\
You are an analyst for a Latin American deep-tech observatory focused on biotech, agtech, medtech, \
foodtech, and climate/nature tech.

Given a startup, decide:
1. Does it belong to our bio universe? Answer yes only if it directly uses or develops biological, \
biochemical, bioprocess, genomic, agricultural biology, food-bio, or nature-based technologies. \
Pure software, logistics, EVs, solar energy, drones, fintech, and retail tech are NOT bio.
2. If yes, pick exactly one bio_theme from this list:
   - Therapeutics
   - Diagnostics & Health Access
   - Bioinputs & Crop Resilience
   - Food Systems & Alt Proteins
   - Nature & Ecosystem Tech
   - Farm Intelligence
   - Biomaterials & Circular Economy
   - Biomanufacturing & Fermentation Economy
3. Write a 2-3 sentence summary in English describing what the company does, for whom, and why it matters.
4. Rate your confidence: high | medium | low

Startup: {name} ({country})
Description: {description}

Respond ONLY with valid JSON, no markdown:
{{
  "is_bio": true | false,
  "bio_theme": "<theme from list above, or null if not bio>",
  "summary": "<2-3 sentence English summary>",
  "confidence": "high" | "medium" | "low",
  "reason": "<one sentence explaining is_bio decision>"
}}"""


def classify(client, startup: dict) -> dict:
    prompt = PROMPT.format(
        name=startup["canonical_name"],
        country=startup["country_code"] or "LatAm",
        description=(startup["short_description"] or "")[:600],
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:]).rstrip("`").strip()
    result = json.loads(text)
    if result.get("is_bio") and result.get("bio_theme") not in BIO_THEMES:
        result["bio_theme"] = None
        result["confidence"] = "low"
    return result


def fetch_targets(conn: sqlite3.Connection, startup_id: str | None, limit: int | None) -> list[dict]:
    cur = conn.cursor()
    where = "se.scope_reason='gridx_import' AND (se.is_bio_universe IS NULL OR se.is_bio_universe=0)"
    params: list = []
    if startup_id:
        where += " AND se.startup_id=?"
        params.append(startup_id)
    lim = f"LIMIT {limit}" if limit else ""
    cur.execute(f"""
        SELECT se.startup_id, e.canonical_name, e.country_code, e.short_description,
               se.funding_stage, se.valuation_estimate_usd
        FROM startup_extended se
        JOIN entities e ON e.entity_id=se.startup_id
        WHERE {where}
        ORDER BY se.valuation_estimate_usd DESC NULLS LAST
        {lim}
    """, params)
    cols = ["startup_id","canonical_name","country_code","short_description","funding_stage","valuation_estimate_usd"]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


CSV_COLS = ["entity_id","entity_name","table_name","field_name","new_value","source_url","confidence","notes"]

def append_enrichments(rows: list[dict], dry_run: bool):
    if dry_run:
        return
    exists = STAGING.exists()
    with STAGING.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        if not exists:
            w.writeheader()
        for row in rows:
            w.writerow(row)


def build_rows(startup: dict, result: dict) -> list[dict]:
    sid   = startup["startup_id"]
    sname = startup["canonical_name"]
    src   = f"gridx_import_classifier:{date.today()}"
    conf  = result["confidence"]
    is_bio = 1 if result["is_bio"] else 0
    scope  = "include" if is_bio else "exclude"
    reason = "gridx_import_classified_bio" if is_bio else "gridx_import_classified_nonbio"

    rows = [
        {"entity_id": sid, "entity_name": sname, "table_name": "startup_extended",
         "field_name": "startup_summary_v1", "new_value": result["summary"],
         "source_url": src, "confidence": conf, "notes": result.get("reason","")},
        {"entity_id": sid, "entity_name": sname, "table_name": "startup_extended",
         "field_name": "is_bio_universe", "new_value": is_bio,
         "source_url": src, "confidence": conf, "notes": ""},
        {"entity_id": sid, "entity_name": sname, "table_name": "startup_extended",
         "field_name": "scope_decision", "new_value": scope,
         "source_url": src, "confidence": conf, "notes": reason},
    ]
    if result.get("bio_theme"):
        rows.append({"entity_id": sid, "entity_name": sname, "table_name": "startup_extended",
                     "field_name": "bio_theme_primary", "new_value": result["bio_theme"],
                     "source_url": src, "confidence": conf, "notes": ""})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--id", dest="startup_id", default=None)
    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        print("DRY RUN — usa --apply para escribir a staging/entity_enrichments.csv\n")

    import anthropic
    client = anthropic.Anthropic()

    conn = sqlite3.connect(DB_PATH)
    targets = fetch_targets(conn, args.startup_id, args.limit)
    conn.close()
    print(f"Targets: {len(targets)}\n")

    stats = {"bio": 0, "nonbio": 0, "error": 0}

    for i, s in enumerate(targets, 1):
        try:
            result = classify(client, s)
            label = "BIO    " if result["is_bio"] else "NON-BIO"
            theme = result.get("bio_theme") or "-"
            print(f"[{i:3}/{len(targets)}] {label} | {result['confidence']:6} | {s['canonical_name'][:35]:35} | {theme}")
            if dry_run:
                print(f"         {result.get('reason','')}")

            rows = build_rows(s, result)
            append_enrichments(rows, dry_run)

            stats["bio" if result["is_bio"] else "nonbio"] += 1

            if i % 10 == 0:
                time.sleep(1)

        except Exception as exc:
            print(f"[{i:3}/{len(targets)}] ERROR  | {s['canonical_name']}: {exc}")
            stats["error"] += 1

    mode = "DRY RUN" if dry_run else f"Escrito a {STAGING.name}"
    print(f"\n{mode} — {stats['bio']} bio, {stats['nonbio']} non-bio, {stats['error']} errores")
    if not dry_run and (stats['bio'] + stats['nonbio']) > 0:
        print("→ Correr: python pipeline.py ingest-entity-enrichments && python pipeline.py rebuild --phase clustering")


if __name__ == "__main__":
    main()
