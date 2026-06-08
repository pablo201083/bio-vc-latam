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
import math
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

try:
    import networkx as nx
    _HAS_NX = True
except ImportError:
    _HAS_NX = False

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

# ── Angular sectors per bio-theme (for startup initial placement) ────────────
_THEME_ANGLES: dict[str, float] = {
    "bioinputs":          0.0,
    "crop resilience":    0.0,
    "farm intelligence":  math.pi * 0.28,
    "precision":          math.pi * 0.28,
    "nature":             math.pi * 0.56,
    "ecosystem":          math.pi * 0.56,
    "food systems":       math.pi * 0.85,
    "alt proteins":       math.pi * 0.85,
    "biomanufacturing":   math.pi * 1.14,
    "fermentation":       math.pi * 1.14,
    "biomaterials":       math.pi * 1.42,
    "circular":           math.pi * 1.42,
    "diagnostics":        math.pi * 1.71,
    "health access":      math.pi * 1.71,
    "therapeutics":       math.pi * 1.98,
    "regenerative":       math.pi * 1.98,
}


def _theme_angle(theme: str) -> float:
    t = theme.lower()
    best = None
    for keyword, angle in _THEME_ANGLES.items():
        if keyword in t:
            best = angle
            break
    if best is None:
        # Deterministic fallback using hash of theme name
        best = (hash(theme) % 628) / 100.0
    return best


def _compute_layout(nodes: list[dict], edges: list[dict]) -> None:
    """
    Pre-compute stable x,y positions offline using NetworkX Fruchterman-Reingold.

    Strategy:
      1. Eco nodes (org/eso/corporate) fixed on inner ring r=0.22
      2. Funds/allocators initial middle ring r=0.50, sorted by name
      3. Startups outer ring r=0.80, sorted by theme sector
      4. FR layout 200 iters, eco nodes pinned
      5. Post-normalize to [-0.88, 0.88] and store as px, py

    The browser then scales px/py by min(W,H)*0.45 centered on (W/2,H/2).
    """
    if not _HAS_NX:
        print("  [layout] networkx not available — skipping pre-computation")
        return

    rng = random.Random(42)

    eco_layers = {"organization", "eso", "corporate"}
    eco_nodes    = [n for n in nodes if n["layer"] in eco_layers]
    fund_nodes   = [n for n in nodes if n["layer"] in ("fund", "allocator")]
    startup_nodes = [n for n in nodes if n["layer"] == "startup"]

    init_pos: dict[str, tuple[float, float]] = {}
    fixed_ids: list[str] = []

    # ── Eco nodes: fixed inner ring ───────────────────────────────────────────
    n_eco = max(1, len(eco_nodes))
    for i, n in enumerate(eco_nodes):
        angle = 2 * math.pi * i / n_eco - math.pi / 2
        init_pos[n["id"]] = (math.cos(angle) * 0.22, math.sin(angle) * 0.22)
        fixed_ids.append(n["id"])

    # ── Fund/allocator nodes: middle ring sorted by name ──────────────────────
    fund_nodes_sorted = sorted(fund_nodes, key=lambda n: n.get("label", ""))
    n_fund = max(1, len(fund_nodes_sorted))
    for i, n in enumerate(fund_nodes_sorted):
        angle = 2 * math.pi * i / n_fund - math.pi / 2
        r = 0.52 + rng.gauss(0, 0.035)
        init_pos[n["id"]] = (math.cos(angle) * r, math.sin(angle) * r)

    # ── Startups: outer ring in theme sectors, with radial jitter ────────────
    # Sort by theme angle so same-theme nodes start adjacent
    startup_nodes_sorted = sorted(startup_nodes, key=lambda n: _theme_angle(n.get("theme", "")))
    n_start = max(1, len(startup_nodes_sorted))
    for i, n in enumerate(startup_nodes_sorted):
        base = _theme_angle(n.get("theme", ""))
        # Slight sequential spreading within sector to reduce initial overlap
        sector_offset = (i / n_start) * 2 * math.pi * 0.04
        angle = base + sector_offset + rng.gauss(0, 0.14)
        r = 0.80 + rng.gauss(0, 0.07)
        init_pos[n["id"]] = (math.cos(angle) * r, math.sin(angle) * r)

    # ── Build graph ───────────────────────────────────────────────────────────
    G = nx.Graph()
    G.add_nodes_from(init_pos.keys())
    for e in edges:
        if e["source"] in init_pos and e["target"] in init_pos:
            G.add_edge(e["source"], e["target"])

    print(f"  [layout] FR layout: {G.number_of_nodes()} nodes, "
          f"{G.number_of_edges()} edges, {len(fixed_ids)} fixed eco nodes …")

    # ── FR layout: eco nodes pinned ───────────────────────────────────────────
    k_opt = 2.0 / math.sqrt(max(1, G.number_of_nodes()))
    pos = nx.spring_layout(
        G,
        pos=init_pos,
        fixed=fixed_ids if fixed_ids else None,
        k=k_opt,
        iterations=200,
        seed=42,
        weight=None,   # all edges equal
    )

    # ── Normalize to [-0.88, 0.88] ────────────────────────────────────────────
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span = max(max_x - min_x, max_y - min_y, 0.01)
    cx_norm = (min_x + max_x) / 2
    cy_norm = (min_y + max_y) / 2
    scale_n = 1.76 / span  # maps span → 1.76 (≈ [-0.88, 0.88])

    node_map = {n["id"]: n for n in nodes}
    for nid, (x, y) in pos.items():
        if nid in node_map:
            node_map[nid]["px"] = round((x - cx_norm) * scale_n, 4)
            node_map[nid]["py"] = round((y - cy_norm) * scale_n, 4)

    print(f"  [layout] Done. px/py embedded in all {len(pos)} nodes.")


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

    # ── 1. Startups (include only — orphans sin startup_extended excluidos) ────
    st_rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               sx.bio_theme_primary, sx.bio_theme_secondary, sx.macro_theme,
               sx.scope_decision, sx.is_bio_universe,
               sx.startup_summary_en, sx.startup_summary_v1, sx.business_one_liner,
               sx.valuation_estimate_usd, sx.valuation_tier, sx.funding_stage,
               sx.tech_depth, sx.data_quality_score, sx.market_label,
               sx.cluster_id, sx.cluster_label, sx.pagerank, sx.community_id
        FROM entities e
        JOIN startup_extended sx ON sx.startup_id = e.entity_id
        WHERE e.entity_type = 'startup'
          AND sx.scope_decision = 'include'
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
            "valuationUsd": r["valuation_estimate_usd"],
            "valuationTier": r["valuation_tier"],
            "fundingStage": _clean(r["funding_stage"]),
            "techDepth": _clean(r["tech_depth"]),
            "qualityScore": r["data_quality_score"],
            "marketLabel": _clean(r["market_label"]),
            "clusterId": r["cluster_id"],
            "clusterLabel": _clean(r["cluster_label"]),
            "pagerank": r["pagerank"],
            "communityId": r["community_id"],
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

    # ── 11b. Pre-compute stable layout (Python-side FR) ─────────────────────
    _compute_layout(nodes, edges)

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
