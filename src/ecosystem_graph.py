"""
src/ecosystem_graph.py — Generador del Ecosystem Graph desde SQLite.

Lee todas las capas del ecosistema BIO LATAM y escribe pilot/ecosystem-graph-data.js.

Capas de nodos:
  startup      → entities WHERE entity_type='startup' AND scope='include'
  fund         → investors (vc, accelerator, impact_fund, ...)
  allocator    → investors (development_finance, multilateral, fund_of_funds, ...)
  organization → organizations (gremiales, asociaciones)
  eso          → esos (institutos, aceleradoras, agencias de financiamiento)
  corporate    → corporates (empresas adquirentes)

Capas de edges:
  investment       → investment_edges (fund/allocator → startup)
  capital          → capital_relations (allocator → fund)
  membership       → support_edges WHERE support_type='membership'
  support          → support_edges WHERE support_type != 'membership'
  validation       → validation_edges

Usage:
    python pipeline.py build-ecosystem-graph
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
OUT_PATH = ROOT / "pilot" / "ecosystem-graph-data.js"

_ALLOCATOR_TYPES = {
    "development_finance", "multilateral", "fund_of_funds",
    "angel_network",
}

# ── Theme colors (mirrors capital-atlas) ────────────────────────────────────
THEME_COLORS = {
    "Agrifood Systems":                 "#5FA05E",
    "Nature-Based Tech":                "#4A8FA8",
    "Precision & Digital Farming":      "#9FB85A",
    "Therapeutic & Diagnostics":        "#C4737A",
    "Therapeutics":                     "#C4737A",
    "Diagnostics":                      "#D4878E",
    "Bioinputs":                        "#7EC8A0",
    "Biomaterials":                     "#C4A85A",
    "Biomanufacturing":                 "#9FA8E8",
    "Food Systems":                     "#5FA05E",
}
DEFAULT_STARTUP_COLOR = "#A0A0A0"


def _clean(v) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() == "nan" else s


def _theme_color(theme: str) -> str:
    for k, v in THEME_COLORS.items():
        if k.lower() in theme.lower() or theme.lower() in k.lower():
            return v
    return DEFAULT_STARTUP_COLOR


def run(db_path: Path = DB_PATH, out_path: Path = OUT_PATH) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    nodes: list[dict] = []
    node_ids: set[str] = set()

    # ── 1. Startups (include only) ───────────────────────────────────────────
    st_rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               sx.bio_theme_primary, sx.bio_theme_secondary, sx.macro_theme,
               sx.scope_decision, sx.is_bio_universe,
               sx.startup_summary_en, sx.startup_summary_v1, sx.business_one_liner
        FROM entities e
        LEFT JOIN startup_extended sx ON sx.startup_id = e.entity_id
        WHERE e.entity_type = 'startup'
          AND e.status != 'excluded'
          AND (sx.scope_decision = 'include' OR sx.scope_decision IS NULL)
    """).fetchall()

    for r in st_rows:
        theme = _clean(r["bio_theme_primary"]) or _clean(r["macro_theme"]) or "Unknown"
        # Normalize short theme name
        short_theme = theme.split("&")[0].split("—")[0].strip()
        summary = (
            _clean(r["startup_summary_en"])
            or _clean(r["startup_summary_v1"])
            or _clean(r["business_one_liner"])
        )
        node = {
            "id": r["entity_id"],
            "type": "startup",
            "layer": "startup",
            "label": _clean(r["canonical_name"]),
            "country": _clean(r["country_code"]).upper(),
            "website": _clean(r["website"]),
            "theme": theme,
            "shortTheme": short_theme,
            "color": _theme_color(theme),
            "summary": summary[:180] if summary else "",
            "degree": 0,
        }
        nodes.append(node)
        node_ids.add(r["entity_id"])

    # ── 2. Investors ─────────────────────────────────────────────────────────
    # Identify which investor IDs appear as LP sources in capital_relations
    allocator_source_ids: set[str] = set(
        r[0] for r in conn.execute(
            "SELECT DISTINCT source_entity_id FROM capital_relations"
        ).fetchall()
    )
    startup_investor_ids: set[str] = set(
        r[0] for r in conn.execute(
            "SELECT DISTINCT investor_id FROM investment_edges"
        ).fetchall()
    )
    pure_allocator_ids = allocator_source_ids - startup_investor_ids

    inv_rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               i.investor_type, i.thesis, i.geography_focus, i.vertical_focus
        FROM entities e
        JOIN investors i ON i.investor_id = e.entity_id
        WHERE e.status != 'excluded'
    """).fetchall()

    for r in inv_rows:
        eid = r["entity_id"]
        itype = _clean(r["investor_type"]).lower()
        if eid in pure_allocator_ids or itype in _ALLOCATOR_TYPES:
            layer = "allocator"
            color = "#3B4FA8"
        else:
            layer = "fund"
            color = "#3B82F6"

        node = {
            "id": eid,
            "type": "investor",
            "layer": layer,
            "label": _clean(r["canonical_name"]),
            "country": _clean(r["country_code"]).upper(),
            "website": _clean(r["website"]),
            "investorType": itype,
            "thesis": _clean(r["thesis"])[:120] if r["thesis"] else "",
            "geoFocus": _clean(r["geography_focus"]),
            "color": color,
            "degree": 0,
        }
        nodes.append(node)
        node_ids.add(eid)

    # ── 3. Organizations ─────────────────────────────────────────────────────
    try:
        org_rows = conn.execute("""
            SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
                   o.org_type, o.focus_area, o.source_url
            FROM entities e
            JOIN organizations o ON o.org_id = e.entity_id
            WHERE e.status != 'excluded'
        """).fetchall()
        for r in org_rows:
            node = {
                "id": r["entity_id"],
                "type": "organization",
                "layer": "organization",
                "label": _clean(r["canonical_name"]),
                "country": _clean(r["country_code"]).upper(),
                "website": _clean(r["website"]),
                "orgType": _clean(r["org_type"]),
                "focusArea": _clean(r["focus_area"]),
                "color": "#7C3AED",
                "degree": 0,
            }
            nodes.append(node)
            node_ids.add(r["entity_id"])
    except Exception as e:
        print(f"  [warn] organizations: {e}")

    # ── 4. ESOs ──────────────────────────────────────────────────────────────
    try:
        eso_rows = conn.execute("""
            SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
                   es.eso_type, es.service_profile, es.geography_focus
            FROM entities e
            JOIN esos es ON es.eso_id = e.entity_id
            WHERE e.status != 'excluded'
        """).fetchall()
        for r in eso_rows:
            node = {
                "id": r["entity_id"],
                "type": "eso",
                "layer": "eso",
                "label": _clean(r["canonical_name"]),
                "country": _clean(r["country_code"]).upper(),
                "website": _clean(r["website"]),
                "esoType": _clean(r["eso_type"]),
                "serviceProfile": _clean(r["service_profile"]),
                "color": "#0D9488",
                "degree": 0,
            }
            nodes.append(node)
            node_ids.add(r["entity_id"])
    except Exception as e:
        print(f"  [warn] esos: {e}")

    # ── 5. Corporates ────────────────────────────────────────────────────────
    try:
        corp_rows = conn.execute("""
            SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
                   c.industry, c.demand_profile, c.innovation_maturity
            FROM entities e
            JOIN corporates c ON c.corporate_id = e.entity_id
            WHERE e.status != 'excluded'
        """).fetchall()
        for r in corp_rows:
            node = {
                "id": r["entity_id"],
                "type": "corporate",
                "layer": "corporate",
                "label": _clean(r["canonical_name"]),
                "country": _clean(r["country_code"]).upper(),
                "website": _clean(r["website"]),
                "industry": _clean(r["industry"]),
                "demandProfile": _clean(r["demand_profile"]),
                "color": "#D97706",
                "degree": 0,
            }
            nodes.append(node)
            node_ids.add(r["entity_id"])
    except Exception as e:
        print(f"  [warn] corporates: {e}")

    # ── 6. Investment edges ──────────────────────────────────────────────────
    edges: list[dict] = []

    ie_rows = conn.execute("""
        SELECT investment_id, investor_id, startup_id, round_stage,
               confidence_score, source_id, notes
        FROM investment_edges
    """).fetchall()

    for r in ie_rows:
        src, tgt = r["investor_id"], r["startup_id"]
        if src not in node_ids or tgt not in node_ids:
            continue
        edges.append({
            "id": _clean(r["investment_id"]),
            "source": src,
            "target": tgt,
            "edgeType": "investment",
            "round": _clean(r["round_stage"]),
            "confidence": round(float(r["confidence_score"] or 0.85), 3),
            "sourceUrl": _clean(r["source_id"]),
        })

    # ── 7. Capital allocation edges ──────────────────────────────────────────
    cr_rows = conn.execute("""
        SELECT relation_id, source_entity_id, target_entity_id,
               relation_type, confidence_score, source_url, amount_usd, year
        FROM capital_relations
    """).fetchall()

    for r in cr_rows:
        src, tgt = r["source_entity_id"], r["target_entity_id"]
        # Auto-add missing entities as stubs
        for eid in (src, tgt):
            if eid not in node_ids:
                node_ids.add(eid)
                nodes.append({
                    "id": eid,
                    "type": "investor",
                    "layer": "allocator",
                    "label": eid.replace("_", " ").title(),
                    "country": "",
                    "color": "#3B4FA8",
                    "degree": 0,
                })
        edges.append({
            "id": f"cr-{r['relation_id']}",
            "source": src,
            "target": tgt,
            "edgeType": "capital",
            "relationType": _clean(r["relation_type"]),
            "confidence": round(float(r["confidence_score"] or 0.85), 3),
            "sourceUrl": _clean(r["source_url"]),
            "amountUsd": r["amount_usd"],
            "year": r["year"],
        })

    # ── 8. Support edges ─────────────────────────────────────────────────────
    try:
        sup_rows = conn.execute("""
            SELECT support_id, source_entity_id, target_entity_id,
                   support_type, confidence_score, source_url, started_at
            FROM support_edges
        """).fetchall()
        for r in sup_rows:
            src, tgt = r["source_entity_id"], r["target_entity_id"]
            if src not in node_ids or tgt not in node_ids:
                continue
            stype = _clean(r["support_type"])
            edges.append({
                "id": _clean(r["support_id"]),
                "source": src,
                "target": tgt,
                "edgeType": "membership" if stype == "membership" else "support",
                "supportType": stype,
                "confidence": round(float(r["confidence_score"] or 0.85), 3),
                "sourceUrl": _clean(r["source_url"]),
                "startedAt": _clean(r["started_at"]),
            })
    except Exception as e:
        print(f"  [warn] support_edges: {e}")

    # ── 9. Validation edges ──────────────────────────────────────────────────
    try:
        val_rows = conn.execute("""
            SELECT validation_id, startup_id, counterparty_entity_id,
                   validation_type, status, confidence_score, source_url
            FROM validation_edges
        """).fetchall()
        for r in val_rows:
            src, tgt = r["startup_id"], r["counterparty_entity_id"]
            if src not in node_ids or tgt not in node_ids:
                continue
            edges.append({
                "id": _clean(r["validation_id"]),
                "source": src,
                "target": tgt,
                "edgeType": "validation",
                "validationType": _clean(r["validation_type"]),
                "status": _clean(r["status"]),
                "confidence": round(float(r["confidence_score"] or 0.85), 3),
                "sourceUrl": _clean(r["source_url"]),
            })
    except Exception as e:
        print(f"  [warn] validation_edges: {e}")

    # ── 10. Compute degrees ──────────────────────────────────────────────────
    node_map = {n["id"]: n for n in nodes}
    for e in edges:
        for eid in (e["source"], e["target"]):
            if eid in node_map:
                node_map[eid]["degree"] = node_map[eid].get("degree", 0) + 1

    # ── 11. Summary meta ─────────────────────────────────────────────────────
    by_layer: dict[str, int] = {}
    for n in nodes:
        lyr = n["layer"]
        by_layer[lyr] = by_layer.get(lyr, 0) + 1

    by_edge: dict[str, int] = {}
    for e in edges:
        et = e["edgeType"]
        by_edge[et] = by_edge.get(et, 0) + 1

    # Find isolated org/eso/corporate nodes (no edges)
    connected_ids = set()
    for e in edges:
        connected_ids.add(e["source"])
        connected_ids.add(e["target"])
    isolated_count = sum(
        1 for n in nodes
        if n["layer"] in ("organization", "eso", "corporate")
        and n["id"] not in connected_ids
    )

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "nodesTotal": len(nodes),
        "edgesTotal": len(edges),
        "byLayer": by_layer,
        "byEdgeType": by_edge,
        "isolatedEcosystemNodes": isolated_count,
    }

    # ── 12. Write JS ─────────────────────────────────────────────────────────
    nodes_json = json.dumps(nodes, ensure_ascii=False, separators=(",", ":"))
    edges_json = json.dumps(edges, ensure_ascii=False, separators=(",", ":"))
    meta_json  = json.dumps(meta, ensure_ascii=False, indent=2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        f"// ecosystem-graph-data.js — Auto-generado por src/ecosystem_graph.py\n"
        f"// {meta['generated']}\n"
        f"const EG_NODES = {nodes_json};\n"
        f"const EG_EDGES = {edges_json};\n"
        f"const EG_META = {meta_json};\n",
        encoding="utf-8",
    )

    conn.close()
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "by_layer": by_layer,
        "by_edge": by_edge,
        "isolated_eco": isolated_count,
        "out": str(out_path),
    }
