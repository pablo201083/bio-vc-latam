"""
scripts/swarm_founding_dates.py — Enjambre Haiku para recuperar founding_year.

Lee startups 'include' sin founding_year de la DB, intenta extraer el año
de la source_url mediante WebFetch + Haiku.

Output: staging/swarm_founding_dates_YYYYMMDD.csv
Luego ingestar: python pipeline.py ingest-founding-years

Uso:
    python scripts/swarm_founding_dates.py
    python scripts/swarm_founding_dates.py --limit 30
    python scripts/swarm_founding_dates.py --dry-run
    python scripts/swarm_founding_dates.py --id cellco
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
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(ROOT / "scripts"))
from _swarm_auth import ensure_api_key  # noqa: E402
ensure_api_key()
DB_PATH = ROOT / "db" / "bio_latam.db"
STAGING_DIR = ROOT / "staging"
LOGS_DIR = ROOT / "logs"

WORKERS = 8  # WebFetch is slower; keep conservative


def fetch_url_text(url: str, timeout: int = 10) -> str:
    """Fetch plain text from a URL, truncated to 3000 chars."""
    if not url or not url.startswith("http"):
        return ""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (research bot; bio-latam-tracker)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(8000).decode("utf-8", errors="replace")
        # Strip HTML tags
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        return raw[:3000]
    except Exception:
        return ""


def fetch_missing(conn: sqlite3.Connection, only_id: str | None) -> list[dict]:
    # source_url lives in entities.website; founded_year in entities.founded_year
    where = """
        sx.scope_decision = 'include'
        AND e.founded_year IS NULL
        AND e.website IS NOT NULL AND e.website LIKE 'http%'
    """
    params: list = []
    if only_id:
        where += " AND sx.startup_id = ?"
        params.append(only_id)

    cur = conn.cursor()
    cur.execute(f"""
        SELECT sx.startup_id, e.canonical_name, e.country_code,
               e.website AS source_url,
               coalesce(sx.startup_summary_en, sx.startup_summary_v1, '') as summary
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE {where}
        ORDER BY e.canonical_name
    """, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


PROMPT = """\
You are a research analyst. From the webpage text below, extract the founding year \
of the startup.

Startup: {name} ({country})
Summary: {summary}

Webpage text (truncated):
{page_text}

Instructions:
- Look for phrases like "founded in", "fundada en", "since YYYY", "established YYYY", \
"año de fundación", "incorporated in", "launched in", or years in an "About" section.
- Output ONLY valid JSON, no markdown:
{{"founding_year": 2018, "confidence": "high", "evidence": "Founded in 2018 according to..."}}
- confidence: "high" if year is stated explicitly; "medium" if inferred from context.
- If no year found, output: {{"founding_year": null, "confidence": "none", "evidence": ""}}
"""


async def call_haiku(client, row: dict, dry_run: bool) -> dict | None:
    if dry_run:
        print(f"[DRY RUN] {row['startup_id']}: would fetch {row['source_url'][:60]}")
        return {
            "startup_id": row["startup_id"],
            "founding_year": None,
            "confidence": "none",
            "evidence_snippet": "[dry run]",
            "enrichment_source": "swarm_haiku_dates_dry",
            "enrichment_date": datetime.date.today().isoformat(),
        }

    loop = asyncio.get_event_loop()
    page_text = await loop.run_in_executor(None, fetch_url_text, row["source_url"])

    if not page_text:
        return {
            "startup_id": row["startup_id"],
            "_error": "fetch_failed",
        }

    prompt = PROMPT.format(
        name=row["canonical_name"],
        country=row["country_code"] or "?",
        summary=row["summary"][:200],
        page_text=page_text,
    )

    try:
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        parsed = json.loads(text)

        if parsed.get("founding_year") is None:
            return {"startup_id": row["startup_id"], "_skip": "no_year_found"}

        return {
            "startup_id": row["startup_id"],
            "startup_name": row["canonical_name"],
            "founded_year": int(parsed["founding_year"]),
            "confidence": parsed.get("confidence", "medium"),
            "source_url": url or "swarm_haiku_dates_v1",
            "notes": parsed.get("evidence", "")[:200],
            "enrichment_date": datetime.date.today().isoformat(),
        }
    except Exception as exc:
        return {"startup_id": row["startup_id"], "_error": str(exc)}


async def run(rows: list[dict], dry_run: bool) -> tuple[list[dict], list[str], int]:
    import anthropic

    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(WORKERS)
    results: list[dict] = []
    failed: list[str] = []
    skipped = 0

    async def bounded(row):
        async with sem:
            return await call_haiku(client, row, dry_run)

    try:
        from tqdm.asyncio import tqdm_asyncio
        tasks = [bounded(r) for r in rows]
        outcomes = await tqdm_asyncio.gather(*tasks, desc="Dates")
    except ImportError:
        tasks = [bounded(r) for r in rows]
        outcomes = await asyncio.gather(*tasks)

    for out in outcomes:
        if out is None:
            continue
        if "_skip" in out:
            skipped += 1
        elif "_error" in out:
            print(f"  ERROR {out['startup_id']}: {out['_error']}", file=sys.stderr)
            failed.append(out["startup_id"])
        else:
            results.append(out)

    return results, failed, skipped


def write_output(results: list[dict], failed: list[str], skipped: int, dry_run: bool) -> None:
    if dry_run:
        print(f"\n[DRY RUN] {len(results)} rows would be written.")
        return

    STAGING_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    date_str = datetime.date.today().strftime("%Y%m%d")
    out_csv = STAGING_DIR / f"swarm_founding_dates_{date_str}.csv"
    fail_log = LOGS_DIR / f"swarm_dates_{date_str}_failed.txt"

    fieldnames = [
        "startup_id", "startup_name", "founded_year", "source_url", "notes",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    if failed:
        fail_log.write_text("\n".join(failed), encoding="utf-8")
        print(f"  {len(failed)} failed → {fail_log}")

    print(f"\n✓ {len(results)} dates found, {skipped} not found, {len(failed)} errors")
    print(f"  Output: {out_csv}")
    print("  Next: python pipeline.py ingest-founding-years")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--id", dest="only_id", default=None)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    rows = fetch_missing(conn, args.only_id)
    conn.close()

    if args.limit:
        rows = rows[: args.limit]

    print(f"Processing {len(rows)} startups without founding_year (workers={WORKERS})...")
    results, failed, skipped = asyncio.run(run(rows, args.dry_run))
    write_output(results, failed, skipped, args.dry_run)


if __name__ == "__main__":
    main()
