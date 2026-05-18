"""
scripts/fix_null_sources.py

Carril C — Asigna source_id a las 227 investment_edges con source_id IS NULL.

Estrategia por tipo de edge:

  Tipo A — URL en notes ("source: https://... |"):
    → Extrae la URL, crea source en tabla sources si no existe,
      actualiza source_id. Confidence se mantiene.

  Tipo B — "edgeseco.csv" en notes:
    → Asigna portfolio URL del inversor (entities.website) como source
      con source_type="historical_graph_import".
      Baja confidence a 0.80 si era > 0.80.

  Tipo C — "inferred_from_valuation_tier" en notes:
    → Asigna source="inferred_valuation_tier", baja confidence a 0.72.
      Estas son inferencias, no relaciones documentadas.

  Tipo D — "latam_coinvest_network_v3.graphml" en notes:
    → Asigna source="latam_coinvest_graphml_v3" con source_type="historical_graph_import".
      Confidence baja a 0.82 si era > 0.82.

  Tipo E — Resto:
    → Asigna portfolio URL del inversor como fallback.

Todo se loguea via audit_log para trazabilidad.

Uso:
  python scripts/fix_null_sources.py
  python scripts/fix_null_sources.py --dry-run
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sqlite3
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT    = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
ACTOR   = "fix_null_sources"
NOW     = datetime.now(timezone.utc).isoformat()


def slugify_url(url: str) -> str:
    """Convierte URL en un slug válido como source_id."""
    slug = re.sub(r"https?://", "", url)
    slug = re.sub(r"[^\w]+", "_", slug)
    slug = slug.strip("_")[:80]
    return f"src_{slug}"


def ensure_source(conn: sqlite3.Connection, source_id: str, url: str,
                  source_type: str, title: str) -> None:
    """Inserta source si no existe."""
    conn.execute("""
        INSERT OR IGNORE INTO sources
            (source_id, source_type, title, url, retrieved_at)
        VALUES (?, ?, ?, ?, ?)
    """, (source_id, source_type, title, url, NOW))


def log_update(conn: sqlite3.Connection, investment_id: str,
               old_src: str | None, new_src: str, old_conf: float, new_conf: float,
               reason: str) -> None:
    conn.execute("""
        INSERT INTO audit_log
            (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason, confidence)
        VALUES (?, ?, ?, 'investment_edges', 'source_id', ?, ?, ?, ?)
    """, (
        NOW, ACTOR, investment_id,
        f"source_id={old_src or 'NULL'} conf={old_conf:.2f}",
        f"source_id={new_src} conf={new_conf:.2f}",
        reason,
        new_conf,
    ))


def extract_url_from_notes(notes: str) -> str | None:
    """Extrae URL del patrón 'source: https://... |' o 'source: https://...'."""
    if not notes:
        return None
    m = re.search(r"source:\s*(https?://[^\s|,]+)", notes)
    return m.group(1).rstrip(".,)") if m else None


def run(dry_run: bool = False) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Obtener todas las edges con source_id IS NULL
    edges = conn.execute("""
        SELECT ie.investment_id, ie.investor_id, ie.startup_id,
               ie.notes, ie.confidence_score, ie.source_id,
               e.website AS inv_website,
               ei.canonical_name AS inv_name
        FROM investment_edges ie
        JOIN entities e ON e.entity_id = ie.investor_id
        JOIN entities ei ON ei.entity_id = ie.investor_id
        WHERE ie.source_id IS NULL
    """).fetchall()
    edges = [dict(r) for r in edges]
    print(f"\n  Edges con source_id NULL: {len(edges)}")

    # Caché de investor portfolio URLs (entities.website como fallback)
    inv_portfolio_urls = {
        # Conocidos con portfolio URL específica
        "GridX":              "https://www.gridexponential.com/portfolio",
        "The Ganesha Lab":    "https://theganeshalab.com/startups/",
        "AIR Capital":        "https://www.aircapital.vc/portfolio",
        "SF500":              "https://sf500.org",
        "DraperCygnus":       "https://www.drapercygnus.com/portfolio",
        "CITES":              "https://cites-gss.com/en/portfolio/",
        "SOSV_IndieBio":      "https://indiebio.co/companies/",
        "Kamay Ventures":     "https://www.kamayventures.com/portfolio",
        "DragonesVP":         "https://www.dragones.vc/portfolio",
        "Antom":              "https://www.antom.la/portfolio-projects-en",
        "GLOCAL":             "https://www.glocalfund.com/portfolio",
        "SP Ventures":        "https://spventures.com.br/portfolio/",
        "Inventure":          "https://www.inventure.fi/portfolio",
        "1200 VC":            "https://www.twelvehundred.vc/investments",
        "The Yield Lab LATAM":"https://theyieldlablatam.com/portfolio/",
        "Corteva Catalyst":   "https://www.corteva.com/who-we-are/corteva-catalyst.html",
    }

    counts = {"tipo_a": 0, "tipo_b": 0, "tipo_c": 0, "tipo_d": 0, "tipo_e": 0, "skip": 0}
    updates: list[dict] = []

    for edge in edges:
        eid  = edge["investment_id"]
        iid  = edge["investor_id"]
        inv  = edge["inv_name"] or iid
        notes = edge["notes"] or ""
        conf  = float(edge["confidence_score"] or 0.90)
        website = edge["inv_website"] or ""

        new_source_id: str | None = None
        new_conf = conf
        tipo = ""
        reason = ""

        # ── Tipo A: URL en notes ────────────────────────────────────────────
        url = extract_url_from_notes(notes)
        if url:
            new_source_id = slugify_url(url)
            tipo = "tipo_a"
            reason = f"url_extracted_from_notes: {url[:80]}"
            # Confidence reflects quality of the URL
            if any(k in url.lower() for k in ["portfolio", "startups", "invest"]):
                new_conf = max(conf, 0.90)
            else:
                new_conf = conf

        # ── Tipo C: inferred_from_valuation_tier ────────────────────────────
        elif "inferred_from_valuation_tier" in notes:
            new_source_id = "src_inferred_valuation_tier"
            new_conf = min(conf, 0.72)
            tipo = "tipo_c"
            reason = "inferred_valuation_tier_no_direct_evidence"

        # ── Tipo D: latam_coinvest_network_v3.graphml ───────────────────────
        elif "latam_coinvest_network_v3.graphml" in notes:
            new_source_id = "src_latam_coinvest_graphml_v3"
            new_conf = min(conf, 0.82)
            tipo = "tipo_d"
            reason = "historical_graphml_import_latam_coinvest_v3"

        # ── Tipo B: edgeseco.csv ─────────────────────────────────────────────
        elif "edgeseco.csv" in notes:
            portfolio_url = inv_portfolio_urls.get(inv) or website
            if portfolio_url:
                new_source_id = slugify_url(portfolio_url)
                url = portfolio_url
            else:
                new_source_id = f"src_edgeseco_{slugify_url(iid)}"
                url = ""
            new_conf = min(conf, 0.80)
            tipo = "tipo_b"
            reason = f"edgeseco_csv_import_fallback_to_portfolio_url"

        # ── Tipo E: otro ─────────────────────────────────────────────────────
        else:
            portfolio_url = inv_portfolio_urls.get(inv) or website
            if portfolio_url:
                new_source_id = slugify_url(portfolio_url)
                url = portfolio_url
                new_conf = min(conf, 0.82)
                tipo = "tipo_e"
                reason = f"fallback_investor_website"
            else:
                print(f"    [SKIP] {eid}: sin URL recuperable — {inv}")
                counts["skip"] += 1
                continue

        updates.append({
            "investment_id": eid,
            "new_source_id": new_source_id,
            "url":           url if tipo != "tipo_c" else "",
            "tipo":          tipo,
            "old_conf":      conf,
            "new_conf":      new_conf,
            "inv_name":      inv,
            "reason":        reason,
        })
        counts[tipo] = counts.get(tipo, 0) + 1

    # ── Resumen ──────────────────────────────────────────────────────────────
    print(f"\n  Clasificación de edges:")
    print(f"    Tipo A (URL en notes)            : {counts['tipo_a']:3d}")
    print(f"    Tipo B (edgeseco.csv → portfolio) : {counts['tipo_b']:3d}")
    print(f"    Tipo C (inferidas valuation_tier) : {counts['tipo_c']:3d}")
    print(f"    Tipo D (graphML import)           : {counts['tipo_d']:3d}")
    print(f"    Tipo E (fallback website)         : {counts['tipo_e']:3d}")
    print(f"    Skip (sin URL)                    : {counts['skip']:3d}")
    print(f"    Total a actualizar                : {sum(counts.values()) - counts['skip']:3d}")

    # Agrupación de confidence changes
    degraded = sum(1 for u in updates if u["new_conf"] < u["old_conf"] - 0.01)
    print(f"\n  Confidence degradada en {degraded} edges de tipo inferido/graphml")

    if dry_run:
        print("\n  [dry-run] Nada escrito. Correr sin --dry-run para aplicar.\n")
        conn.close()
        return

    # ── Crear sources necesarias ─────────────────────────────────────────────
    # Sources especiales fijas
    ensure_source(conn, "src_inferred_valuation_tier",
                  "", "inferred",
                  "Inferred from valuation_tier — no direct investment evidence")
    ensure_source(conn, "src_latam_coinvest_graphml_v3",
                  "", "historical_graph_import",
                  "LATAM Coinvest Network v3 — historical GraphML import")

    # Sources de URLs reales
    urls_seen: set[str] = set()
    for u in updates:
        url = u.get("url", "")
        sid = u["new_source_id"]
        if not url or sid in urls_seen:
            continue
        urls_seen.add(sid)
        # Determinar tipo de source
        ulow = url.lower()
        if "portfolio" in ulow or "startups" in ulow or "invest" in ulow:
            stype = "official_portfolio_profile"
        else:
            stype = "official_website"
        inv = u["inv_name"]
        ensure_source(conn, sid, url, stype, f"{inv} — {stype}")

    # ── Aplicar updates ──────────────────────────────────────────────────────
    updated = 0
    for u in updates:
        conn.execute("""
            UPDATE investment_edges
            SET source_id = ?, confidence_score = ?
            WHERE investment_id = ? AND source_id IS NULL
        """, (u["new_source_id"], u["new_conf"], u["investment_id"]))
        log_update(conn, u["investment_id"],
                   None, u["new_source_id"],
                   u["old_conf"], u["new_conf"], u["reason"])
        updated += 1

    conn.commit()
    conn.close()

    print(f"\n  {updated} edges actualizadas con source_id")
    print("  Verificar: python pipeline.py fund-sweep-status\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
