"""
scripts/swarm_summary_enrichment.py — Enjambre Haiku para reescribir summaries de baja calidad.

Lee quality/semantic_quality_queue.csv, ordena por risk score DESC,
y llama a Claude Haiku en paralelo (15 workers) para producir summaries
EN de 45-80 palabras con señal biológica explícita.

Output: staging/swarm_summary_YYYYMMDD.csv
Luego ingestar: python pipeline.py ingest-entity-enrichments

Uso:
    python scripts/swarm_summary_enrichment.py              # procesa todos
    python scripts/swarm_summary_enrichment.py --limit 20   # prueba con 20
    python scripts/swarm_summary_enrichment.py --dry-run    # imprime prompts sin llamar API
    python scripts/swarm_summary_enrichment.py --id outpost # solo una startup
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import datetime
import json
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(ROOT / "scripts"))
from _swarm_auth import ensure_api_key  # noqa: E402
ensure_api_key()
QUEUE_CSV = ROOT / "quality" / "semantic_quality_queue.csv"
STAGING_DIR = ROOT / "staging"
LOGS_DIR = ROOT / "logs"

PROMPT = """\
You are a biotech/agtech analyst writing seed-round due-diligence notes for \
BIO VC LATAM, a venture fund focused on the bioeconomy of Latin America.

Write a concise English summary (45-80 words) for the startup below, using ONLY \
information that can be verified from the source or the existing summary. \
Follow this template strictly:

"[Startup] develops/operates [product or platform] for [market or use case], \
using [biological mechanism, chemistry, hardware, or software stack]. \
It belongs inside BIO VC LATAM as [bio-core / bio-coupled / eco-adjacent / \
planetary-boundary], because [one concrete, source-backed sentence]."

Rules:
- Avoid generic words: "innovative", "solution", "platform" without context.
- Be specific about the biology or material science.
- Write in present tense, third person.
- Do NOT invent facts not present in the inputs.
- Output only the summary text, no labels or markdown.

---
Startup name: {name}
Country: {country}
BIO theme: {theme}
Current summary (may be thin or in Spanish): {summary}
Business one-liner: {one_liner}
Source URL: {url}
"""

WORKERS = 15


def load_queue(only_id: str | None) -> list[dict]:
    rows = []
    with open(QUEUE_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if only_id and row["startup_id"] != only_id:
                continue
            rows.append(row)
    rows.sort(key=lambda r: float(r.get("semantic_risk_score") or 0), reverse=True)
    return rows


async def call_haiku(client, row: dict, dry_run: bool) -> dict | None:
    prompt = PROMPT.format(
        name=row.get("startup_name", ""),
        country="",
        theme=row.get("current_recommended_theme", ""),
        summary=(row.get("current_summary") or "")[:500],
        one_liner=(row.get("current_one_liner") or "")[:200],
        url=row.get("source_url", ""),
    )

    if dry_run:
        print(f"\n--- DRY RUN: {row['startup_id']} ---")
        print(prompt[:300], "...")
        return {
            "startup_id": row["startup_id"],
            "startup_summary_en": "[DRY RUN]",
            "enrichment_source": "swarm_haiku_dry",
            "enrichment_date": datetime.date.today().isoformat(),
        }

    try:
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        return {
            "startup_id": row["startup_id"],
            "startup_summary_en": text,
            "enrichment_source": "swarm_haiku_summary_v1",
            "enrichment_date": datetime.date.today().isoformat(),
        }
    except Exception as exc:
        return {"startup_id": row["startup_id"], "_error": str(exc)}


async def run(rows: list[dict], dry_run: bool) -> tuple[list[dict], list[str]]:
    import anthropic

    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(WORKERS)
    results: list[dict] = []
    failed: list[str] = []

    async def bounded(row):
        async with sem:
            return await call_haiku(client, row, dry_run)

    try:
        from tqdm.asyncio import tqdm_asyncio
        tasks = [bounded(r) for r in rows]
        outcomes = await tqdm_asyncio.gather(*tasks, desc="Summaries")
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
    """Convert swarm output to entity_enrichments.csv format."""
    return [{
        "entity_id": result["startup_id"],
        "table_name": "startup_extended",
        "field_name": "startup_summary_en",
        "new_value": result["startup_summary_en"],
        "source_url": result["enrichment_source"],
        "confidence": "0.85",
        "notes": f"swarm_haiku_summary {result['enrichment_date']}",
    }]


def write_output(results: list[dict], failed: list[str], dry_run: bool) -> None:
    if dry_run:
        print(f"\n[DRY RUN] {len(results)} rows would be written.")
        return

    STAGING_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    date_str = datetime.date.today().strftime("%Y%m%d")
    out_csv = STAGING_DIR / f"swarm_summary_{date_str}_enrichments.csv"
    fail_log = LOGS_DIR / f"swarm_summary_{date_str}_failed.txt"

    fieldnames = ["entity_id", "table_name", "field_name", "new_value", "source_url", "confidence", "notes"]
    rows = [row for r in results for row in to_enrichment_rows(r)]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    if failed:
        fail_log.write_text("\n".join(failed), encoding="utf-8")
        print(f"  {len(failed)} failed IDs → {fail_log}")

    print(f"\n✓ {len(results)} summaries written to {out_csv}")
    print(f"  Merge to staging/entity_enrichments.csv and run:")
    print("  python pipeline.py ingest-entity-enrichments")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--id", dest="only_id", default=None)
    args = parser.parse_args()

    rows = load_queue(args.only_id)
    if args.limit:
        rows = rows[: args.limit]

    print(f"Processing {len(rows)} startups (workers={WORKERS})...")
    results, failed = asyncio.run(run(rows, args.dry_run))
    write_output(results, failed, args.dry_run)


if __name__ == "__main__":
    main()
