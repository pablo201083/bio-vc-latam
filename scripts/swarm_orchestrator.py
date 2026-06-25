"""
scripts/swarm_orchestrator.py — Orquestador del enjambre de calidad de datos.

Corre los 4 scripts de enjambre en secuencia lógica y luego ejecuta
los comandos de ingesta del pipeline.

Orden:
  1. swarm_founding_dates    (rápido, sin dependencias de summary)
  2. swarm_tag_population    (rápido, pura inferencia)
  3. swarm_summary_enrichment (el más lento, 283 llamadas)
  4. swarm_discovery          (lento, WebFetch; output requiere curación manual)

Uso:
    python scripts/swarm_orchestrator.py                      # correr todo
    python scripts/swarm_orchestrator.py --only tags,summaries
    python scripts/swarm_orchestrator.py --limit 20           # prueba rápida
    python scripts/swarm_orchestrator.py --dry-run            # sin llamadas API
    python scripts/swarm_orchestrator.py --skip-ingest        # solo genera CSVs
"""
from __future__ import annotations

import argparse
import csv
import datetime
import shutil
import subprocess
import sys
import time
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STAGING = ROOT / "staging"
PYTHON = sys.executable


def run(cmd: list[str], label: str) -> bool:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    t0 = time.time()
    result = subprocess.run(cmd, cwd=ROOT)
    elapsed = time.time() - t0
    ok = result.returncode == 0
    status = "✓ OK" if ok else "✗ FAILED"
    print(f"\n  {status} in {elapsed:.1f}s")
    return ok


def merge_enrichments_to_staging(glob_pattern: str) -> int:
    """Append swarm-generated enrichment rows to staging/entity_enrichments.csv."""
    main_file = STAGING / "entity_enrichments.csv"
    swarm_files = sorted(STAGING.glob(glob_pattern))
    if not swarm_files:
        return 0

    header_written = main_file.exists()
    rows_added = 0
    with open(main_file, "a", newline="", encoding="utf-8") as out_f:
        for src in swarm_files:
            with open(src, encoding="utf-8") as in_f:
                reader = csv.DictReader(in_f)
                writer = csv.DictWriter(out_f, fieldnames=reader.fieldnames or [], extrasaction="ignore")
                if not header_written:
                    writer.writeheader()
                    header_written = True
                for row in reader:
                    writer.writerow(row)
                    rows_added += 1
            print(f"  merged {src.name} ({rows_added} rows so far)")
    return rows_added


def merge_founding_dates(glob_pattern: str) -> int:
    """Append swarm-generated founding dates to staging/founding_years.csv."""
    main_file = STAGING / "founding_years.csv"
    swarm_files = sorted(STAGING.glob(glob_pattern))
    if not swarm_files:
        return 0

    header_written = main_file.exists()
    rows_added = 0
    with open(main_file, "a", newline="", encoding="utf-8") as out_f:
        for src in swarm_files:
            with open(src, encoding="utf-8") as in_f:
                reader = csv.DictReader(in_f)
                writer = csv.DictWriter(out_f, fieldnames=reader.fieldnames or [], extrasaction="ignore")
                if not header_written:
                    writer.writeheader()
                    header_written = True
                for row in reader:
                    writer.writerow(row)
                    rows_added += 1
            print(f"  merged {src.name} ({rows_added} rows so far)")
    return rows_added


def run_pipeline(phase: str, label: str) -> bool:
    return run([PYTHON, "pipeline.py", phase], label)


def run_swarm(script: str, extra_args: list[str]) -> bool:
    cmd = [PYTHON, f"scripts/{script}"] + extra_args
    return run(cmd, script)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        default="dates,tags,summaries,discovery",
        help="Comma-separated subset: dates,tags,summaries,discovery",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip pipeline ingest commands after each swarm script",
    )
    args = parser.parse_args()

    steps = {s.strip() for s in args.only.split(",")}
    extra: list[str] = []
    if args.limit:
        extra += ["--limit", str(args.limit)]
    if args.dry_run:
        extra += ["--dry-run"]

    print("\n🐝 BIO LATAM Data Quality Swarm")
    print(f"   Steps: {', '.join(sorted(steps))}")
    print(f"   Dry run: {args.dry_run}")
    if args.limit:
        print(f"   Limit: {args.limit} per step")

    results: dict[str, bool] = {}

    date_str = datetime.date.today().strftime("%Y%m%d")

    # Step 1: Founding dates
    if "dates" in steps:
        ok = run_swarm("swarm_founding_dates.py", extra)
        results["swarm_founding_dates"] = ok
        if ok and not args.dry_run and not args.skip_ingest:
            n = merge_founding_dates(f"swarm_founding_dates_{date_str}.csv")
            print(f"  Merged {n} date rows into staging/founding_years.csv")
            results["ingest_founding_years"] = run_pipeline(
                "ingest-founding-years", "pipeline.py ingest-founding-years"
            )

    # Step 2: Tag population
    if "tags" in steps:
        ok = run_swarm("swarm_tag_population.py", extra)
        results["swarm_tag_population"] = ok
        if ok and not args.dry_run and not args.skip_ingest:
            n = merge_enrichments_to_staging(f"swarm_tags_{date_str}_enrichments.csv")
            print(f"  Merged {n} tag rows into staging/entity_enrichments.csv")
            results["ingest_tags"] = run_pipeline(
                "ingest-entity-enrichments", "pipeline.py ingest-entity-enrichments (tags)"
            )

    # Step 3: Summary enrichment
    if "summaries" in steps:
        ok = run_swarm("swarm_summary_enrichment.py", extra)
        results["swarm_summary_enrichment"] = ok
        if ok and not args.dry_run and not args.skip_ingest:
            n = merge_enrichments_to_staging(f"swarm_summary_{date_str}_enrichments.csv")
            print(f"  Merged {n} summary rows into staging/entity_enrichments.csv")
            results["ingest_summaries"] = run_pipeline(
                "ingest-entity-enrichments", "pipeline.py ingest-entity-enrichments (summaries)"
            )

    # Step 4: Discovery (no auto-ingest — requires manual curation)
    if "discovery" in steps:
        ok = run_swarm("swarm_discovery.py", extra)
        results["swarm_discovery"] = ok
        if not args.dry_run:
            print("\n  *** Discovery output requires MANUAL CURATION before ingesting ***")
            print("  Review staging/swarm_discovered_*.csv then run:")
            print("  python pipeline.py ingest-discovered")

    # Post-swarm rebuild (if any swarm ran and produced data)
    if not args.dry_run and not args.skip_ingest and any(results.values()):
        print("\n  Running semantic rebuild to re-embed enriched startups...")
        results["rebuild_semantic"] = run_pipeline(
            "rebuild --phase semantic", "pipeline.py rebuild --phase semantic"
        )
        results["intelligence_data"] = run_pipeline(
            "intelligence-data", "pipeline.py intelligence-data"
        )
        results["validate"] = run_pipeline("validate", "pipeline.py validate")
        results["health"] = run_pipeline("health", "pipeline.py health")

    # Summary
    print("\n" + "="*60)
    print("  SWARM SUMMARY")
    print("="*60)
    for step, ok in results.items():
        icon = "✓" if ok else "✗"
        print(f"  {icon} {step}")

    failed = [k for k, v in results.items() if not v]
    if failed:
        print(f"\n  {len(failed)} step(s) failed. Check logs/ for details.")
        sys.exit(1)
    else:
        print("\n  All steps completed successfully.")


if __name__ == "__main__":
    main()
