"""
Enriquecimiento de founded_year para startups sin dato.

Fase 1: Importar desde GRIDX Excel (matching por dominio o nombre fuzzy).
Fase 2: Web research via Claude API para las que siguen sin dato.

Uso:
    python scripts/enrich_founded_year.py --phase gridx [--dry-run]
    python scripts/enrich_founded_year.py --phase web   [--dry-run] [--limit 50]
    python scripts/enrich_founded_year.py --phase all   [--dry-run]
"""

import argparse
import re
import sqlite3
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

import openpyxl

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

DB   = ROOT / "db" / "bio_latam.db"
GRIDX_XLS = Path(r"F:\Downloads\Analisis GRIDX Deeptech Nueva Ola .xlsx")
ACTOR = "pipeline:enrich_founded_year"


# ── helpers ───────────────────────────────────────────────────────────────────

# Domains that are portfolio/aggregator sites — not unique startup identifiers
_GENERIC_DOMAINS = {
    "gridexponential.com", "linkedin.com", "theyieldlablatam.com",
    "kptl.com.br", "spventures.com.br", "crunchbase.com",
    "facebook.com", "twitter.com", "instagram.com", "youtube.com",
    "startupchile.org", "endeavor.org", "latamlist.com",
}


def _domain(url: str) -> str:
    if not url:
        return ""
    dom = url.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "").lower().strip()
    if dom in _GENERIC_DOMAINS:
        return ""   # treat as no-match
    return dom


def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _load_missing(conn) -> list[dict]:
    rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.website
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include' AND e.founded_year IS NULL
        ORDER BY e.entity_id
    """).fetchall()
    return [{"eid": r[0], "name": r[1], "web": r[2]} for r in rows]


def _load_gridx() -> list[dict]:
    """Parse GRIDX Excel → list of {company, founded, web}."""
    wb = openpyxl.load_workbook(str(GRIDX_XLS), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    out = []
    for r in rows[3:]:  # row0=empty, row1=header, row2=blank
        if not r or not r[0]:
            continue
        company = str(r[0]).strip()
        raw_yr  = r[9] if len(r) > 9 else None
        web     = r[12] if len(r) > 12 else None
        yr = None
        if raw_yr is not None:
            try:
                yr_int = int(float(str(raw_yr)))
                if 1990 <= yr_int <= 2030:
                    yr = yr_int
            except (ValueError, TypeError):
                pass
        out.append({"company": company, "founded": yr, "web": str(web) if web else None})
    return [g for g in out if g["founded"] is not None]


def _match_gridx(missing: list[dict], gridx: list[dict]) -> list[dict]:
    """Return matches: {eid, name, gridx_company, yr, sim, method}."""
    matches = []
    matched_eids = set()

    # Pass 1: domain-exact
    for s in missing:
        s_dom = _domain(s["web"] or "")
        if not s_dom:
            continue
        for g in gridx:
            if _domain(g["web"] or "") == s_dom:
                matches.append({
                    "eid": s["eid"], "name": s["name"],
                    "gridx_company": g["company"], "yr": g["founded"],
                    "sim": 1.0, "method": "domain",
                })
                matched_eids.add(s["eid"])
                break

    # Pass 2: name fuzzy (threshold 0.88 to avoid false positives)
    for s in missing:
        if s["eid"] in matched_eids:
            continue
        best_score, best_g = 0.0, None
        for g in gridx:
            sc = _sim(s["name"], g["company"])
            if sc > best_score:
                best_score, best_g = sc, g
        if best_score >= 0.88 and best_g:
            matches.append({
                "eid": s["eid"], "name": s["name"],
                "gridx_company": best_g["company"], "yr": best_g["founded"],
                "sim": round(best_score, 2), "method": "name",
            })
            matched_eids.add(s["eid"])

    return matches, matched_eids


# ── Phase 1: GRIDX ────────────────────────────────────────────────────────────

def phase_gridx(dry_run: bool = False):
    conn = sqlite3.connect(str(DB))
    missing = _load_missing(conn)
    print(f"Startups sin founded_year: {len(missing)}")

    if not GRIDX_XLS.exists():
        print(f"ERROR: GRIDX Excel no encontrado en {GRIDX_XLS}")
        return

    gridx = _load_gridx()
    print(f"GRIDX records con año válido: {len(gridx)}")

    matches, _ = _match_gridx(missing, gridx)
    dom_matches = [m for m in matches if m["method"] == "domain"]
    name_matches = [m for m in matches if m["method"] == "name"]
    print(f"\nMatches encontrados: {len(matches)} ({len(dom_matches)} domain, {len(name_matches)} name-fuzzy)")

    if dry_run:
        print("\n[DRY RUN] Cambios que se aplicarían:")
        for m in sorted(matches, key=lambda x: x["yr"]):
            print(f"  {m['eid']:32s} founded={m['yr']}  [{m['method']}, sim={m['sim']}]  ~ {m['gridx_company']}")
        conn.close()
        return

    updated = 0
    for m in matches:
        n = diff_and_log_update(
            conn, "entities", "entity_id", m["eid"],
            {"founded_year": m["yr"]},
            actor=ACTOR,
            reason=f"gridx_excel:{m['method']}:sim={m['sim']}:{m['gridx_company']}",
        )
        if n > 0:
            updated += 1
            print(f"  OK {m['eid']:32s} -> {m['yr']}  [{m['method']}]")

    conn.commit()
    conn.close()
    print(f"\nFase GRIDX completa: {updated} startups actualizadas.")


# ── Phase 2: Web research via Claude ─────────────────────────────────────────

def phase_web(dry_run: bool = False, limit: int = 0):
    """Use Claude API to find founding year for remaining startups using training knowledge."""
    import os
    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic SDK no disponible. Activar venv.")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    conn = sqlite3.connect(str(DB))
    missing = _load_missing(conn)
    print(f"Startups sin founded_year despues de GRIDX: {len(missing)}")

    if limit:
        missing = missing[:limit]
        print(f"(limitado a {limit} para este run)")

    if dry_run:
        print(f"\n[DRY RUN] Se investigarian {len(missing)} startups via Claude API:")
        for s in missing[:20]:
            print(f"  {s['eid']:32s} | {s['name']:28s} | {(s['web'] or '')[:50]}")
        if len(missing) > 20:
            print(f"  ... y {len(missing)-20} mas")
        conn.close()
        return

    if not missing:
        print("Nada que hacer.")
        conn.close()
        return

    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY no esta en el entorno.")
        print("  Setear: $env:ANTHROPIC_API_KEY = 'sk-ant-...'")
        conn.close()
        return

    client = anthropic.Anthropic(api_key=api_key)
    results = {}  # eid -> founded_year
    errors = []

    for i, s in enumerate(missing):
        eid  = s["eid"]
        name = s["name"]
        web  = s["web"] or ""

        print(f"[{i+1}/{len(missing)}] {name} ({eid})...", end=" ", flush=True)

        prompt = (
            f'Find the founding year of the company "{name}". '
            f'Website: {web}. '
            "Reply with ONLY a 4-digit year (e.g., 2018) or 'unknown' if you cannot determine it with confidence. "
            "Do not include any other text."
        )

        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=20,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            # Extract 4-digit year from response
            m = re.search(r'\b(19[89]\d|20[012]\d)\b', raw)
            if m:
                yr = int(m.group(1))
                results[eid] = yr
                print(f"-> {yr}")
            else:
                print(f"-> unknown ({raw!r})")
        except Exception as e:
            errors.append((eid, str(e)))
            print(f"-> ERROR: {e}")

        # Small delay to be polite to the API
        if i % 10 == 9:
            time.sleep(1)

    print(f"\nResultados: {len(results)} annos encontrados, {len(errors)} errores")

    updated = 0
    for eid, yr in results.items():
        n = diff_and_log_update(
            conn, "entities", "entity_id", eid,
            {"founded_year": yr},
            actor=ACTOR,
            reason="claude_haiku_web_research:founding_year",
        )
        if n > 0:
            updated += 1

    conn.commit()
    conn.close()
    print(f"\nFase web completa: {updated} startups actualizadas.")
    if errors:
        print(f"Errores ({len(errors)}): {errors[:5]}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=["gridx", "web", "all"], default="all")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="max startups for web phase (0=all)")
    args = ap.parse_args()

    if args.phase in ("gridx", "all"):
        print("=" * 60)
        print("FASE 1: GRIDX Excel")
        print("=" * 60)
        phase_gridx(dry_run=args.dry_run)

    if args.phase in ("web", "all"):
        print()
        print("=" * 60)
        print("FASE 2: Web research (Claude Haiku)")
        print("=" * 60)
        phase_web(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
