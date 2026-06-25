"""
scripts/swarm_discovery.py — Enjambre Haiku para adquirir startups faltantes.

Seeds en orden de prioridad:
  1. Startups referenciadas en investment_edges pero ausentes del master dataset (47 external edges)
  2. Gaps de cobertura por país (Venezuela, Bolivia, Paraguay, Ecuador)
  3. Gaps de cobertura por tema (Biomanufacturing fuera de BR/MX)

Para cada seed: fetch de URL + Haiku valida BIO relevance y construye fila.
Output requiere revisión manual antes de ingestar.

Output: staging/swarm_discovered_YYYYMMDD.csv  (para curación manual)
Luego (después de curar): python pipeline.py ingest-discovered

Uso:
    python scripts/swarm_discovery.py                    # todos los seeds
    python scripts/swarm_discovery.py --source edges     # solo los 47 edges externos
    python scripts/swarm_discovery.py --source gaps      # solo gaps de cobertura
    python scripts/swarm_discovery.py --limit 20 --dry-run
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

WORKERS = 10

# Countries with known coverage gaps (fewer than 5 startups each)
GAP_COUNTRIES = ["VE", "BO", "PY", "EC", "DO", "PE"]

# Themes with geographic gaps
GAP_THEMES = [
    ("Biomanufacturing & Fermentation", ["AR", "CO", "CL", "PE"]),
    ("Therapeutics & Regenerative Bio", ["BO", "PY", "VE", "EC"]),
]


def fetch_url_text(url: str, timeout: int = 10) -> str:
    if not url or not url.startswith("http"):
        return ""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (research bot; bio-latam-tracker)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(8000).decode("utf-8", errors="replace")
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        return raw[:3000]
    except Exception:
        return ""


def get_external_edge_seeds(conn: sqlite3.Connection) -> list[dict]:
    """Return startup stubs referenced in investment_edges but not in entities."""
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ie.target_id, ie.target_name, ie.source_id
        FROM investment_edges ie
        LEFT JOIN entities e ON e.entity_id = ie.target_id
        WHERE e.entity_id IS NULL
          AND ie.target_id IS NOT NULL
          AND ie.target_id != ''
        ORDER BY ie.target_id
    """)
    rows = []
    for target_id, target_name, investor_id in cur.fetchall():
        rows.append({
            "seed_type": "external_edge",
            "startup_id_hint": target_id,
            "name_hint": target_name or target_id,
            "investor_id": investor_id,
            "source_url": "",
        })
    return rows


def get_coverage_gap_seeds(conn: sqlite3.Connection) -> list[dict]:
    """Return known gap contexts as seeds for discovery prompts."""
    seeds = []
    for country in GAP_COUNTRIES:
        seeds.append({
            "seed_type": "country_gap",
            "startup_id_hint": f"gap_{country.lower()}",
            "name_hint": f"Unknown biotech in {country}",
            "country_gap": country,
            "theme_gap": None,
            "source_url": "",
        })
    return seeds


BIO_VALIDATION_PROMPT = """\
You are a BIO VC LATAM analyst. Evaluate whether the startup below belongs in \
a Latin American bioeconomy venture portfolio.

BIO VC LATAM thesis: startups that transform the material economy using living systems, \
biomolecules, or material/planetary-boundary transitions. Themes: therapeutics, \
biomanufacturing, ag biologicals, food systems, biomaterials, ecosystem tech, \
precision agriculture (bio-coupled), nature intelligence.

Startup name: {name}
Investor that referenced it: {investor}
Source URL: {url}
Webpage text (truncated): {page_text}

Evaluate and output ONLY valid JSON:
{{
  "is_bio_relevant": true/false,
  "confidence": "high"/"medium"/"low",
  "macro_theme": "<best matching BIO VC LATAM theme or 'unknown'>",
  "country_code": "<2-letter ISO code or 'XX'>",
  "startup_summary_v1": "<40-70 word description of what they do and why they're BIO relevant>",
  "business_one_liner": "<max 120 chars: what they build and for whom>",
  "source_url": "<best URL for this startup>",
  "rejection_reason": "<if not relevant: why not; else empty string>"
}}
"""


async def call_haiku(client, seed: dict, dry_run: bool) -> dict | None:
    if dry_run:
        print(f"[DRY RUN] {seed['seed_type']}: {seed['name_hint'][:50]}")
        return None

    loop = asyncio.get_event_loop()
    url = seed.get("source_url", "")
    page_text = ""
    if url:
        page_text = await loop.run_in_executor(None, fetch_url_text, url)

    prompt = BIO_VALIDATION_PROMPT.format(
        name=seed["name_hint"],
        investor=seed.get("investor_id", "unknown"),
        url=url or "(no URL available)",
        page_text=page_text or "(no page content fetched)",
    )

    try:
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        parsed = json.loads(text)

        if not parsed.get("is_bio_relevant"):
            return {
                "startup_id_hint": seed["startup_id_hint"],
                "_skip": "not_bio_relevant",
                "rejection_reason": parsed.get("rejection_reason", ""),
            }

        return {
            "startup_id_hint": seed["startup_id_hint"],
            "seed_type": seed["seed_type"],
            "name": seed["name_hint"],
            "macro_theme": parsed.get("macro_theme", ""),
            "country_code": parsed.get("country_code", "XX"),
            "startup_summary_v1": parsed.get("startup_summary_v1", ""),
            "business_one_liner": parsed.get("business_one_liner", ""),
            "source_url": parsed.get("source_url", url),
            "haiku_confidence": parsed.get("confidence", "low"),
            "review_status": "needs_curator_review",
            "enrichment_source": "swarm_haiku_discovery_v1",
            "enrichment_date": datetime.date.today().isoformat(),
        }
    except Exception as exc:
        return {"startup_id_hint": seed["startup_id_hint"], "_error": str(exc)}


async def run(seeds: list[dict], dry_run: bool) -> tuple[list[dict], list[str], int]:
    import anthropic

    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(WORKERS)
    results: list[dict] = []
    failed: list[str] = []
    skipped = 0

    async def bounded(seed):
        async with sem:
            return await call_haiku(client, seed, dry_run)

    try:
        from tqdm.asyncio import tqdm_asyncio
        tasks = [bounded(s) for s in seeds]
        outcomes = await tqdm_asyncio.gather(*tasks, desc="Discovery")
    except ImportError:
        tasks = [bounded(s) for s in seeds]
        outcomes = await asyncio.gather(*tasks)

    for out in outcomes:
        if out is None:
            continue
        if "_skip" in out:
            skipped += 1
            print(f"  skip {out['startup_id_hint']}: {out.get('rejection_reason','')[:80]}")
        elif "_error" in out:
            print(f"  ERROR {out['startup_id_hint']}: {out['_error']}", file=sys.stderr)
            failed.append(out["startup_id_hint"])
        else:
            results.append(out)

    return results, failed, skipped


def write_output(results: list[dict], failed: list[str], skipped: int, dry_run: bool) -> None:
    if dry_run or not results:
        print(f"\n[DRY RUN or no results] {len(results)} candidates found.")
        return

    STAGING_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    date_str = datetime.date.today().strftime("%Y%m%d")
    out_csv = STAGING_DIR / f"swarm_discovered_{date_str}.csv"
    fail_log = LOGS_DIR / f"swarm_discovery_{date_str}_failed.txt"

    fieldnames = [
        "startup_id_hint", "seed_type", "name", "macro_theme", "country_code",
        "startup_summary_v1", "business_one_liner", "source_url",
        "haiku_confidence", "review_status", "enrichment_source", "enrichment_date",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    if failed:
        fail_log.write_text("\n".join(failed), encoding="utf-8")
        print(f"  {len(failed)} failed → {fail_log}")

    print(f"\n✓ {len(results)} BIO-relevant candidates found")
    print(f"  {skipped} rejected as non-BIO, {len(failed)} errors")
    print(f"  Output: {out_csv}")
    print("\n  *** CURACIÓN REQUERIDA antes de ingestar ***")
    print("  Revisar haiku_confidence=low rows y validar source_url antes de:")
    print("  python pipeline.py ingest-discovered")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--source",
        choices=["edges", "gaps", "all"],
        default="all",
        help="Which seed set to use",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    seeds: list[dict] = []

    if args.source in ("edges", "all"):
        edge_seeds = get_external_edge_seeds(conn)
        print(f"  External edge seeds: {len(edge_seeds)}")
        seeds.extend(edge_seeds)

    if args.source in ("gaps", "all"):
        gap_seeds = get_coverage_gap_seeds(conn)
        print(f"  Coverage gap seeds: {len(gap_seeds)}")
        seeds.extend(gap_seeds)

    conn.close()

    if args.limit:
        seeds = seeds[: args.limit]

    print(f"\nTotal seeds to process: {len(seeds)} (workers={WORKERS})")
    results, failed, skipped = asyncio.run(run(seeds, args.dry_run))
    write_output(results, failed, skipped, args.dry_run)


if __name__ == "__main__":
    main()
