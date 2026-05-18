"""
src/capital_atlas.py — Generador del Capital Network Atlas desde SQLite.

Lee de db/bio_latam.db (entities, investors, investment_edges, capital_relations,
startup_extended) y escribe pilot/capital-atlas-data.js en el formato exacto
que consume capital-atlas.js.

Diseño:
  Startup nodes  → entities WHERE entity_type='startup'
  Fund nodes     → investors: vc, accelerator, company_builder, impact_fund, corporate_vc, association
  Allocator nodes→ investors: development_finance, multilateral, fund_of_funds, angel_network
                   OR entidades que aparecen en capital_relations.source_entity_id
  Investment edges → investment_edges (investor→startup)
  Allocator edges  → capital_relations (LP→fund)

Usage:
    python pipeline.py build-atlas
    python pipeline.py rebuild --phase atlas    (futuro)
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
OUT_PATH = ROOT / "pilot" / "capital-atlas-data.js"

# ─────────────────────────────────────────────────────────────────────────────
# Tipos de inversor
# ─────────────────────────────────────────────────────────────────────────────

_ALLOCATOR_TYPES = {
    "development_finance", "multilateral", "fund_of_funds",
    "angel_network",  # angel networks act as LP-tier in LATAM
}
_FUND_TYPES = {
    "vc", "accelerator", "company_builder", "impact_fund",
    "corporate_vc", "association", "accelerator_fund",
    "investor",  # generic fallback — treat as fund
}

# ─────────────────────────────────────────────────────────────────────────────
# round_name → edge.type
# ─────────────────────────────────────────────────────────────────────────────

_ROUND_TO_EDGE_TYPE = {
    "official_portfolio_investment":    "portfolio_investment",
    "portfolio_page_lead":              "portfolio_investment",
    "investment_or_membership":         "investment_or_membership",
    "investment":                       "portfolio_investment",
    "investment_announcement":          "direct_investment",
    "reported_portfolio_investment":    "portfolio_investment",
    "official_program_investment":      "portfolio_or_acceleration",
    "official_direct_investment":       "direct_investment",
    "secondary_profile_investment":     "portfolio_investment",
    "official_investment_announcement": "direct_investment",
}

# ─────────────────────────────────────────────────────────────────────────────
# Evidence scoring (replica de build_capital_atlas_data.ps1)
# ─────────────────────────────────────────────────────────────────────────────

_ANNOUNCEMENT_PATS = re.compile(
    r"(press|news|release|announce|techcrunch|agfunder|crunchbase|startupbrasil|"
    r"setor biotech|startupbl|sifted|latam startup|idblab|bidlab|jica|gef\.org|"
    r"prnewswire|businesswire|globenewswire|reuters|bloomberg)", re.I
)
_SPECIFIC_PATS = re.compile(
    r"(startup|empresa|compan|company|folio|portfolio\/[a-z])", re.I
)
_PORTFOLIO_PATS = re.compile(
    r"(portfolio|portafolio|investments|investimentos|participadas)", re.I
)


def _evidence_score(source_url: str, round_name: str, notes: str) -> tuple[int, str, str]:
    """Returns (level 0-4, label, note)."""
    url = (source_url or "").strip()
    rname = (round_name or "").lower()
    note = (notes or "").strip()

    if not url or not url.startswith("http"):
        return 0, "missing_or_internal", "No public URL available."

    if _ANNOUNCEMENT_PATS.search(url) or rname in (
        "investment_announcement", "official_investment_announcement", "official_direct_investment"
    ):
        return 4, "investment_announcement", "Public source confirms a specific investment announcement."

    if _SPECIFIC_PATS.search(url):
        return 3, "startup_specific_public", "Public source appears tied to a specific startup-fund relationship."

    if _PORTFOLIO_PATS.search(url):
        return 2, "fund_portfolio_page", "URL points to a fund portfolio page."

    if url.startswith("http"):
        return 1, "historical_graph", "Public URL but not portfolio-specific."

    return 0, "missing_or_internal", "No verifiable public URL."


def _is_public(evidence_tier: str) -> bool:
    return evidence_tier in ("fund_portfolio_page", "startup_specific_public", "investment_announcement")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clean(v) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() == "nan" else s


# ─────────────────────────────────────────────────────────────────────────────
# Main builder
# ─────────────────────────────────────────────────────────────────────────────

def run(db_path: Path = DB_PATH, out_path: Path = OUT_PATH) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # ── 1. Identify allocator entities from capital_relations ────────────────
    # Entities that only appear as LP sources (and never as fund→startup investors)
    # are classified as "allocator" regardless of investor_type.
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
    # Pure allocators: in capital_relations sources but never invest directly in startups
    pure_allocator_ids = allocator_source_ids - startup_investor_ids

    # ── 2. Load investors ────────────────────────────────────────────────────
    inv_rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               i.investor_type, i.thesis, i.geography_focus, i.vertical_focus,
               i.active_status
        FROM entities e
        JOIN investors i ON i.investor_id = e.entity_id
        WHERE e.status != 'excluded'
    """).fetchall()

    investor_nodes: list[dict] = []
    for r in inv_rows:
        eid = r["entity_id"]
        itype = _clean(r["investor_type"]).lower()

        # Determine node type
        if eid in pure_allocator_ids or itype in _ALLOCATOR_TYPES:
            node_type = "allocator"
        else:
            node_type = "fund"

        investor_nodes.append({
            "id": eid,
            "type": node_type,
            "label": _clean(r["canonical_name"]),
            "investor_type": itype,
            "investor_subtype": itype,
            "entity_confidence": 0.9,
            "source_presence": "db_investors",
            "thesis": _clean(r["thesis"]),
            "country": _clean(r["country_code"]).upper(),
            "degree": 0,  # calculated below
        })

    # ── 3. Load startups ─────────────────────────────────────────────────────
    # Load ALL startups from entities first (includes orphans without startup_extended).
    # Enrich with startup_extended data via LEFT JOIN so edges to orphan startups still render.
    st_rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               sx.scope_decision, sx.macro_theme, sx.bio_theme_primary,
               sx.bio_theme_secondary, sx.is_bio_universe,
               sx.startup_summary_en, sx.startup_summary_v1,
               sx.business_one_liner,
               sx.cluster_label,
               COALESCE(sx.valuation_estimate_usd, sx.valuation_bucket_usd, 0) AS valuation_usd
        FROM entities e
        LEFT JOIN startup_extended sx ON sx.startup_id = e.entity_id
        WHERE e.entity_type = 'startup'
          AND e.status != 'excluded'
    """).fetchall()

    startup_nodes: list[dict] = []
    for r in st_rows:
        summary = (
            _clean(r["startup_summary_en"])
            or _clean(r["startup_summary_v1"])
            or _clean(r["business_one_liner"])
        )
        bio_theme = _clean(r["bio_theme_primary"]) or _clean(r["macro_theme"]) or "needs review"
        scope = _clean(r["scope_decision"]) or "review"

        startup_nodes.append({
            "id": r["entity_id"],
            "type": "startup",
            "label": _clean(r["canonical_name"]),
            "country": _clean(r["country_code"]).upper(),
            "scope_decision": scope,
            "theme": bio_theme,
            "legacy_macro_theme": _clean(r["macro_theme"]),
            "emergent_theme": _clean(r["bio_theme_secondary"]),
            "semantic_single_theme": _clean(r["cluster_label"]),
            "semantic_single_confidence": "",
            "semantic_single_score": "",
            "summary": summary,
            "source_url": _clean(r["website"]),
            "review_status": "reviewed" if scope == "include" else "taxonomy_stub",
            "thesis_fit": "core" if r["is_bio_universe"] else "peripheral",
            "taxonomy_source": "bio_theme_v3",
            "evidence_source": "db_startup_extended" if r["scope_decision"] else "db_entities_only",
            "bio_lens_tags": "",
            "domain_tags": "",
            "technology_tags": "",
            "scale_tags": "",
            "valuation_usd": float(r["valuation_usd"] or 0),
            "degree": 0,  # calculated below
            "capital_status": "no_capital_edge",  # updated below
        })

    # Build node lookup
    node_by_id: dict[str, dict] = {}
    for n in investor_nodes + startup_nodes:
        node_by_id[n["id"]] = n

    # ── 4. Build investment edges (investor→startup) ──────────────────────────
    ie_rows = conn.execute("""
        SELECT investment_id, investor_id, startup_id, round_name, round_stage,
               announced_date, amount, confidence_score, notes,
               source_id
        FROM investment_edges
    """).fetchall()

    investment_edges: list[dict] = []
    for r in ie_rows:
        inv_id = r["investor_id"]
        st_id = r["startup_id"]
        round_name = _clean(r["round_name"])
        edge_type = _ROUND_TO_EDGE_TYPE.get(round_name, "portfolio_investment")
        conf = float(r["confidence_score"] or 0.85)
        source_url = _clean(r["source_id"])  # source_id stores URL as proxy
        notes = _clean(r["notes"])

        # Extract URL from notes if source_id is empty
        if not source_url and notes:
            m = re.search(r"https?://\S+", notes)
            if m:
                source_url = m.group(0)

        level, label, ev_note = _evidence_score(source_url, round_name, notes)
        is_public = _is_public(label)

        investment_edges.append({
            "id": _clean(r["investment_id"]),
            "source": inv_id,
            "target": st_id,
            "type": edge_type,
            "confidence": round(conf, 3),
            "source_url": source_url,
            "evidence": ev_note,
            "audited": is_public,
            "evidence_tier": "public_url" if is_public else "canonical_internal",
            "capital_evidence_level": level,
            "capital_evidence_label": label,
            "capital_evidence_note": ev_note,
            "weight": round(0.8 + conf * 1.6, 3),
        })

    # ── 5. Build allocator edges (LP→fund) from capital_relations ────────────
    cr_rows = conn.execute("""
        SELECT relation_id, source_entity_id, target_entity_id, target_vehicle,
               relation_type, amount_usd, year, confidence_score, source_url,
               evidence_note
        FROM capital_relations
    """).fetchall()

    allocator_edges: list[dict] = []
    for r in cr_rows:
        src_id = r["source_entity_id"]
        tgt_id = r["target_entity_id"]
        rel_type = _clean(r["relation_type"])
        conf = float(r["confidence_score"] or 0.85)
        source_url = _clean(r["source_url"])
        ev_note = _clean(r["evidence_note"])
        amount = r["amount_usd"]
        year = r["year"]

        edge: dict = {
            "id": f"{src_id}-{tgt_id}",
            "source": src_id,
            "target": tgt_id,
            "type": rel_type,
            "confidence": round(conf, 3),
            "source_url": source_url,
            "evidence": ev_note,
            "audited": bool(source_url and source_url.startswith("http")),
            "evidence_tier": "public_url" if source_url.startswith("http") else "canonical_internal",
            "capital_evidence_level": 2,
            "capital_evidence_label": "fund_portfolio_page",
            "capital_evidence_note": ev_note,
            "weight": round(0.8 + conf * 1.6, 3),
        }
        if amount:
            edge["amount_usd"] = amount
        if year:
            edge["year"] = str(year)
        allocator_edges.append(edge)

        # Ensure source allocator node exists (may not be in investors table)
        if src_id not in node_by_id:
            node_by_id[src_id] = {
                "id": src_id,
                "type": "allocator",
                "label": src_id.replace("_", " ").title(),
                "investor_subtype": "unknown_lp",
                "entity_confidence": 0.75,
                "source_presence": "capital_allocator_edges",
                "degree": 0,
            }
        # Ensure target fund node exists
        if tgt_id not in node_by_id:
            node_by_id[tgt_id] = {
                "id": tgt_id,
                "type": "fund",
                "label": tgt_id.replace("_", " ").title(),
                "investor_subtype": "vc_or_investor",
                "entity_confidence": 0.8,
                "source_presence": "capital_allocator_edges",
                "degree": 0,
            }

    # ── 6. Calculate degree and capital_status ────────────────────────────────
    all_edges = investment_edges + allocator_edges
    degree_map: dict[str, int] = {}
    for e in all_edges:
        degree_map[e["source"]] = degree_map.get(e["source"], 0) + 1
        degree_map[e["target"]] = degree_map.get(e["target"], 0) + 1

    # Track startups with capital edges
    startups_with_capital: set[str] = set()
    for e in investment_edges:
        if e["target"] in node_by_id and node_by_id[e["target"]]["type"] == "startup":
            startups_with_capital.add(e["target"])

    # Build portfolio valuation per investor (sum of connected startup valuations)
    portfolio_val: dict[str, float] = {}
    for e in investment_edges:
        inv_id = e["source"]
        st_node = node_by_id.get(e["target"])
        if st_node and st_node["type"] == "startup":
            val = float(st_node.get("valuation_usd") or 0)
            portfolio_val[inv_id] = portfolio_val.get(inv_id, 0.0) + val

    for nid, node in node_by_id.items():
        node["degree"] = degree_map.get(nid, 0)
        if node["type"] == "startup":
            node["capital_status"] = "capital_mapped" if nid in startups_with_capital else "no_capital_edge"
        if node["type"] in ("fund", "allocator"):
            node["portfolio_valuation_usd"] = round(portfolio_val.get(nid, 0.0), 1)

    # ── 7. Prune orphan edges (both endpoints must exist) ────────────────────
    valid_investment_edges = [
        e for e in investment_edges
        if e["source"] in node_by_id and e["target"] in node_by_id
    ]
    valid_allocator_edges = [
        e for e in allocator_edges
        if e["source"] in node_by_id and e["target"] in node_by_id
    ]

    # ── 8. Assemble nodes list ────────────────────────────────────────────────
    all_nodes = list(node_by_id.values())

    # ── 9. Summary stats ─────────────────────────────────────────────────────
    n_funds = sum(1 for n in all_nodes if n["type"] == "fund")
    n_allocators = sum(1 for n in all_nodes if n["type"] == "allocator")
    n_startups = sum(1 for n in all_nodes if n["type"] == "startup")
    n_include = sum(1 for n in all_nodes if n["type"] == "startup" and n.get("scope_decision") == "include")
    n_public_edges = sum(1 for e in valid_investment_edges if e.get("evidence_tier") == "public_url")

    summary = {
        "nodes_total": len(all_nodes),
        "funds_total": n_funds,
        "startups_total": n_startups,
        "allocators_total": n_allocators,
        "edges_total": len(valid_investment_edges) + len(valid_allocator_edges),
        "investment_edges_total": len(valid_investment_edges),
        "allocator_edges_total": len(valid_allocator_edges),
        "include_startups_total": n_include,
        "source_backed_include_startups_total": len(startups_with_capital),
        "public_source_edges_total": n_public_edges,
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "pipeline:build-atlas (SQLite)",
        "summary": summary,
        "nodes": all_nodes,
        "edges": valid_investment_edges + valid_allocator_edges,
    }

    conn.close()

    # ── 10. Write JS file ────────────────────────────────────────────────────
    out_path.parent.mkdir(parents=True, exist_ok=True)
    js_body = json.dumps(payload, ensure_ascii=False, indent=2)
    out_path.write_text(
        f"window.CAPITAL_ATLAS_DATA = {js_body};\n",
        encoding="utf-8",
    )

    size_kb = out_path.stat().st_size // 1024
    print(f"  [capital-atlas] {len(all_nodes)} nodes ({n_funds} funds, {n_allocators} allocators, {n_startups} startups)")
    print(f"  [capital-atlas] {len(valid_investment_edges)} investment edges + {len(valid_allocator_edges)} allocator edges")
    print(f"  [capital-atlas] => {out_path.name} ({size_kb} KB)")

    return summary
