"""
scripts/swarm_tag_population.py — Enjambre Haiku para poblar los 4 campos de tags vacíos.

Lee startups 'include' de la DB con tags faltantes y usa Claude Haiku (20 workers)
para asignar tags desde el vocabulario controlado en quality/strategic_tag_dictionary.csv.
No requiere WebFetch — inferencia pura sobre summary + theme + one_liner.

Output: staging/swarm_tags_YYYYMMDD.csv
Luego ingestar: python pipeline.py ingest-entity-enrichments

Uso:
    python scripts/swarm_tag_population.py              # todos los que faltan tags
    python scripts/swarm_tag_population.py --limit 30   # prueba con 30
    python scripts/swarm_tag_population.py --dry-run
    python scripts/swarm_tag_population.py --id outpost
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import datetime
import json
import pathlib
import re
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Load API key from .env if not in environment
import sys as _sys
_sys.path.insert(0, str(ROOT / "scripts"))
from _swarm_auth import ensure_api_key  # noqa: E402
ensure_api_key()
DB_PATH = ROOT / "db" / "bio_latam.db"
TAG_DICT_CSV = ROOT / "quality" / "strategic_tag_dictionary.csv"
STAGING_DIR = ROOT / "staging"
LOGS_DIR = ROOT / "logs"

WORKERS = 20


def load_vocabulary() -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    with open(TAG_DICT_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            g = row["tag_group"]
            groups.setdefault(g, []).append(row)
    return groups


def format_vocab(groups: dict[str, list[dict]]) -> str:
    lines = []
    for group, tags in groups.items():
        lines.append(f"\n{group.upper()} TAGS:")
        for t in tags:
            lines.append(f"  {t['tag_id']} — {t['label']}: {t['definition']}")
    return "\n".join(lines)


def fetch_untagged(conn: sqlite3.Connection, only_id: str | None) -> list[dict]:
    where = """
        sx.scope_decision = 'include'
        AND (
            sx.bio_lens_tags IS NULL OR sx.bio_lens_tags = ''
            OR sx.domain_tags IS NULL OR sx.domain_tags = ''
            OR sx.technology_tags IS NULL OR sx.technology_tags = ''
            OR sx.scale_tags IS NULL OR sx.scale_tags = ''
        )
    """
    params: list = []
    if only_id:
        where += " AND sx.startup_id = ?"
        params.append(only_id)

    cur = conn.cursor()
    cur.execute(f"""
        SELECT sx.startup_id, e.canonical_name, e.country_code,
               coalesce(sx.startup_summary_en, sx.startup_summary_v1, '') as summary,
               coalesce(sx.business_one_liner, '') as one_liner,
               coalesce(sx.macro_theme, '') as macro_theme,
               coalesce(sx.bio_lens_tags, '') as bio_lens_tags,
               coalesce(sx.domain_tags, '') as domain_tags,
               coalesce(sx.technology_tags, '') as technology_tags,
               coalesce(sx.scale_tags, '') as scale_tags
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE {where}
        ORDER BY sx.cluster_confidence ASC
    """, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


PROMPT_TMPL = """\
You are a biotech/agtech taxonomy expert. Assign tags to this startup from the \
controlled vocabulary below. Choose only tag_ids that clearly apply.

STARTUP
Name: {name} | Country: {country} | Theme: {theme}
Summary: {summary}
One-liner: {one_liner}

VOCABULARY{vocab}

RULES
- bio_lens_tags: 1-3 tag_ids that best describe the biological/planetary role
- domain_tags: 1-2 tag_ids for the market domain
- technology_tags: 2-4 tag_ids for core technologies used
- scale_tags: 1-2 tag_ids for the scale of impact
- Use ONLY tag_ids from the vocabulary above, comma-separated.
- If a group clearly does not apply, use empty string.
- Output ONLY valid JSON, no markdown:

{{"bio_lens_tags": "...", "domain_tags": "...", "technology_tags": "...", "scale_tags": "..."}}
"""


async def call_haiku(client, row: dict, vocab_str: str, dry_run: bool) -> dict | None:
    prompt = PROMPT_TMPL.format(
        name=row["canonical_name"],
        country=row["country_code"] or "?",
        theme=row["macro_theme"],
        summary=row["summary"][:400],
        one_liner=row["one_liner"][:150],
        vocab=vocab_str,
    )

    if dry_run:
        print(f"[DRY RUN] {row['startup_id']}: would call Haiku")
        return {
            "startup_id": row["startup_id"],
            "bio_lens_tags": "[dry]",
            "domain_tags": "[dry]",
            "technology_tags": "[dry]",
            "scale_tags": "[dry]",
            "enrichment_source": "swarm_haiku_tags_dry",
            "enrichment_date": datetime.date.today().isoformat(),
        }

    try:
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        # Strip markdown fences if present
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        parsed = json.loads(text)
        return {
            "startup_id": row["startup_id"],
            "bio_lens_tags": parsed.get("bio_lens_tags", ""),
            "domain_tags": parsed.get("domain_tags", ""),
            "technology_tags": parsed.get("technology_tags", ""),
            "scale_tags": parsed.get("scale_tags", ""),
            "enrichment_source": "swarm_haiku_tags_v1",
            "enrichment_date": datetime.date.today().isoformat(),
        }
    except Exception as exc:
        return {"startup_id": row["startup_id"], "_error": str(exc)}


async def run(rows: list[dict], vocab_str: str, dry_run: bool) -> tuple[list[dict], list[str]]:
    import anthropic

    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(WORKERS)
    results: list[dict] = []
    failed: list[str] = []

    async def bounded(row):
        async with sem:
            return await call_haiku(client, row, vocab_str, dry_run)

    try:
        from tqdm.asyncio import tqdm_asyncio
        tasks = [bounded(r) for r in rows]
        outcomes = await tqdm_asyncio.gather(*tasks, desc="Tags")
    except ImportError:
        tasks = [bounded(r) for r in rows]
        outcomes = await asyncio.gather(*tasks)

    for out in outcomes:
        if out is None:
            continue
        if "_error" in out:
            print(f"  ERROR {out['startup_id']}: {out['_error']}", file=sys.stderr)
            failed.append(out["startup_id"])
        else:
            results.append(out)

    return results, failed


def to_enrichment_rows(result: dict) -> list[dict]:
    """Convert tag output to entity_enrichments.csv format (one row per field)."""
    date = result["enrichment_date"]
    rows = []
    for field in ("bio_lens_tags", "domain_tags", "technology_tags", "scale_tags"):
        value = result.get(field, "")
        if value and value != "[dry]":
            rows.append({
                "entity_id": result["startup_id"],
                "table_name": "startup_extended",
                "field_name": field,
                "new_value": value,
                "source_url": result["enrichment_source"],
                "confidence": "0.80",
                "notes": f"swarm_haiku_tags {date}",
            })
    return rows


def write_output(results: list[dict], failed: list[str], dry_run: bool) -> None:
    if dry_run:
        print(f"\n[DRY RUN] {len(results)} rows would be written.")
        return

    STAGING_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    date_str = datetime.date.today().strftime("%Y%m%d")
    out_csv = STAGING_DIR / f"swarm_tags_{date_str}_enrichments.csv"
    fail_log = LOGS_DIR / f"swarm_tags_{date_str}_failed.txt"

    fieldnames = ["entity_id", "table_name", "field_name", "new_value", "source_url", "confidence", "notes"]
    rows = [row for r in results for row in to_enrichment_rows(r)]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    if failed:
        fail_log.write_text("\n".join(failed), encoding="utf-8")
        print(f"  {len(failed)} failed IDs → {fail_log}")

    print(f"\n✓ {len(results)} startups → {len(rows)} tag rows written to {out_csv}")
    print(f"  Merge to staging/entity_enrichments.csv and run:")
    print("  python pipeline.py ingest-entity-enrichments")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--id", dest="only_id", default=None)
    args = parser.parse_args()

    vocab_groups = load_vocabulary()
    vocab_str = format_vocab(vocab_groups)

    conn = sqlite3.connect(DB_PATH)
    rows = fetch_untagged(conn, args.only_id)
    conn.close()

    if args.limit:
        rows = rows[: args.limit]

    print(f"Processing {len(rows)} untagged startups (workers={WORKERS})...")
    results, failed = asyncio.run(run(rows, vocab_str, args.dry_run))
    write_output(results, failed, args.dry_run)


if __name__ == "__main__":
    main()
