"""
src/graph_analytics.py — análisis de red sobre el ecosistema BIO LATAM.

Reemplaza el degree-count crudo del script PowerShell actual con:
- PageRank ponderado (importancia global en la red de capital)
- Betweenness centrality (detección de cuellos de botella)
- Closeness centrality (acceso al ecosistema)
- Louvain community detection (clusters de capital)
- Bridge detection (edges entre comunidades)
- Bottleneck detection (nodos críticos cuya remoción fragmenta el flujo)
- Whitespace mapping (oportunidades por macro_theme × country)

Lee desde db/bio_latam.db, escribe a:
- startup_extended (pagerank, betweenness, closeness, community_id)
- ecosystem_bridges
- ecosystem_bottlenecks
- ecosystem_whitespace
- audit_log (cada cómputo deja registro)

Uso:
    python -m src.graph_analytics
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import time
from datetime import datetime, timezone
from typing import Any

# Forzar UTF-8 en stdout para Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import networkx as nx
from community import community_louvain

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "db" / "bio_latam.db"


# ---------------------------------------------------------------------------
# Construcción del grafo
# ---------------------------------------------------------------------------

def build_capital_graph(conn: sqlite3.Connection) -> nx.DiGraph:
    """Construye el grafo dirigido de capital.

    Nodos: entities (todos los tipos: startup, capital, institution, etc.)
    Edges: investment_edges con weight = confidence_score (o 0.5 si None)
    """
    G = nx.DiGraph()

    for row in conn.execute("""
        SELECT e.entity_id, e.entity_type, e.canonical_name, e.country_code,
               sx.macro_theme, sx.scope_decision
        FROM entities e
        LEFT JOIN startup_extended sx ON sx.startup_id = e.entity_id
    """):
        entity_id, etype, name, country, theme, scope = row
        G.add_node(
            entity_id,
            type=etype or "unknown",
            name=name or entity_id,
            country=country or "",
            theme=theme or "",
            scope=scope or "",
        )

    edge_count = 0
    for row in conn.execute("""
        SELECT investor_id, startup_id, confidence_score, round_stage, announced_date
        FROM investment_edges
    """):
        inv, st, conf, stage, date = row
        if inv not in G.nodes or st not in G.nodes:
            continue
        G.add_edge(
            inv, st,
            weight=float(conf) if conf is not None else 0.5,
            stage=stage or "",
            date=date or "",
        )
        edge_count += 1

    print(f"  Grafo construido: {G.number_of_nodes()} nodos, {edge_count} edges")
    return G


# ---------------------------------------------------------------------------
# Centralidades
# ---------------------------------------------------------------------------

def compute_centralities(G: nx.DiGraph) -> dict[str, dict[str, float]]:
    """Computa PageRank, betweenness y closeness sobre el grafo."""
    print("  Computando PageRank...")
    pagerank = nx.pagerank(G, alpha=0.85, weight="weight")

    print("  Computando betweenness centrality...")
    betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)

    print("  Computando closeness centrality...")
    closeness = nx.closeness_centrality(G)

    return {
        "pagerank": pagerank,
        "betweenness": betweenness,
        "closeness": closeness,
        "in_degree": dict(G.in_degree(weight="weight")),
        "out_degree": dict(G.out_degree(weight="weight")),
    }


# ---------------------------------------------------------------------------
# Comunidades (Louvain)
# ---------------------------------------------------------------------------

def detect_communities(G: nx.DiGraph, resolution: float = 1.0) -> dict[str, int]:
    """Louvain sobre la versión no dirigida del grafo.

    Retorna entity_id → community_id (entero).
    Aísla nodos con degree=0 en una comunidad sintética '-1' para no contaminar Louvain.
    """
    H = G.to_undirected()
    # Aislar nodos sin edges (Louvain les asignaría comunidades aleatorias)
    isolated = {n for n, d in H.degree() if d == 0}
    H_connected = H.subgraph([n for n in H.nodes() if n not in isolated]).copy()

    if H_connected.number_of_nodes() == 0:
        partition = {}
    else:
        partition = community_louvain.best_partition(
            H_connected, random_state=42, resolution=resolution
        )

    # Asignar comunidad -1 a los aislados
    for n in isolated:
        partition[n] = -1

    n_communities = len(set(v for v in partition.values() if v != -1))
    print(f"  Comunidades detectadas: {n_communities} ({len(isolated)} nodos aislados)")
    return partition


# ---------------------------------------------------------------------------
# Bridges
# ---------------------------------------------------------------------------

def find_bridges(G: nx.DiGraph, communities: dict[str, int]) -> list[dict[str, Any]]:
    """Edges cuyos endpoints pertenecen a comunidades distintas (excluyendo -1)."""
    bridges = []
    for u, v, data in G.edges(data=True):
        cu = communities.get(u)
        cv = communities.get(v)
        if cu is None or cv is None or cu == -1 or cv == -1:
            continue
        if cu != cv:
            bridges.append({
                "source_entity_id": u,
                "target_entity_id": v,
                "source_community": cu,
                "target_community": cv,
                "weight": float(data.get("weight", 0.5)),
            })
    print(f"  Bridges encontrados: {len(bridges)}")
    return bridges


# ---------------------------------------------------------------------------
# Bottlenecks
# ---------------------------------------------------------------------------

def detect_bottlenecks(
    G: nx.DiGraph,
    centralities: dict[str, dict[str, float]],
    communities: dict[str, int],
    min_startups_per_community: int = 4,
) -> list[dict[str, Any]]:
    """Detecta cuellos de botella por dependencia de comunidad.

    El grafo es bipartito (investor → startup), por lo que betweenness es siempre 0.
    En su lugar usamos: un fondo F es bottleneck para la comunidad C si concentra una
    fracción alta de las startups de C. Si F desaparece, esa comunidad pierde mucha cobertura.

    Riesgo:
      - critical: cubre >=50% de las startups de la comunidad
      - high:     cubre >=30%
      - moderate: cubre >=20%

    Se reporta un row por (fondo, comunidad) cuando aplica. Un mismo fondo puede ser
    bottleneck en varias comunidades a la vez.
    """
    # Para cada comunidad, mapear startups que pertenecen
    community_startups: dict[int, set[str]] = {}
    for node_id, com in communities.items():
        if com == -1:
            continue
        node_type = G.nodes[node_id].get("type")
        if node_type == "startup":
            community_startups.setdefault(com, set()).add(node_id)

    bottlenecks: list[dict[str, Any]] = []
    for com, startups in community_startups.items():
        if len(startups) < min_startups_per_community:
            continue

        # Contar cobertura de cada fondo en esta comunidad
        investor_coverage: dict[str, int] = {}
        for st in startups:
            for inv in G.predecessors(st):
                investor_coverage[inv] = investor_coverage.get(inv, 0) + 1

        for inv, cnt in investor_coverage.items():
            coverage = cnt / len(startups)
            if coverage < 0.20:
                continue
            if coverage >= 0.50:
                risk = "critical"
            elif coverage >= 0.30:
                risk = "high"
            else:
                risk = "moderate"
            bottlenecks.append({
                "entity_id": inv,
                "betweenness": coverage,  # reusamos el campo: ahora guarda coverage_fraction
                "in_degree": cnt,         # startups de esta community que dependen del fondo
                "out_degree": len(startups),  # tamaño de la community
                "risk_if_removed": risk,
                "_community": com,
            })

    bottlenecks.sort(key=lambda x: (-x["betweenness"], -x["in_degree"]))
    print(f"  Bottlenecks por dependencia de comunidad: {len(bottlenecks)}")
    return bottlenecks


# ---------------------------------------------------------------------------
# Whitespace
# ---------------------------------------------------------------------------

def detect_whitespace(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Mapa de oportunidad: (macro_theme × country) con startups include vs inversores.

    opportunity_score = startup_count / max(unique_investor_count, 1)
    Alto opportunity_score = mucha actividad de founders, poca cobertura de capital.
    """
    query = """
    WITH startup_buckets AS (
        SELECT sx.macro_theme,
               e.country_code,
               count(DISTINCT sx.startup_id) AS startup_count
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
          AND sx.macro_theme IS NOT NULL AND sx.macro_theme != ''
          AND e.country_code IS NOT NULL AND e.country_code != ''
        GROUP BY sx.macro_theme, e.country_code
    ),
    investors_per_theme_country AS (
        SELECT sx.macro_theme,
               e.country_code,
               count(DISTINCT ie.investor_id) AS investor_count
        FROM investment_edges ie
        JOIN startup_extended sx ON sx.startup_id = ie.startup_id
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
          AND sx.macro_theme IS NOT NULL AND sx.macro_theme != ''
          AND e.country_code IS NOT NULL AND e.country_code != ''
        GROUP BY sx.macro_theme, e.country_code
    )
    SELECT sb.macro_theme, sb.country_code,
           sb.startup_count,
           COALESCE(ipt.investor_count, 0) AS investor_count,
           sb.startup_count * 1.0 / MAX(COALESCE(ipt.investor_count, 0), 1) AS opportunity_score
    FROM startup_buckets sb
    LEFT JOIN investors_per_theme_country ipt
      ON ipt.macro_theme = sb.macro_theme AND ipt.country_code = sb.country_code
    ORDER BY opportunity_score DESC, sb.startup_count DESC;
    """
    rows = conn.execute(query).fetchall()
    whitespace = [
        {
            "macro_theme": r[0],
            "country_code": r[1],
            "startup_count": r[2],
            "investor_count": r[3],
            "opportunity_score": float(r[4]),
        }
        for r in rows
    ]
    print(f"  Celdas (theme × country) analizadas: {len(whitespace)}")
    return whitespace


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

def persist_results(
    conn: sqlite3.Connection,
    centralities: dict[str, dict[str, float]],
    communities: dict[str, int],
    bridges: list[dict[str, Any]],
    bottlenecks: list[dict[str, Any]],
    whitespace: list[dict[str, Any]],
) -> None:
    """Persiste resultados a SQLite. Loguea cada inserción/update en audit_log."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    actor = "graph_analytics"
    cur = conn.cursor()

    # 1. Actualizar startup_extended con métricas por nodo (solo startups)
    print("  Persistiendo métricas en startup_extended...")
    updated_sx = 0
    startup_ids = {row[0] for row in conn.execute("SELECT startup_id FROM startup_extended")}
    for eid in startup_ids:
        pr = centralities["pagerank"].get(eid)
        bw = centralities["betweenness"].get(eid)
        cl = centralities["closeness"].get(eid)
        com = communities.get(eid)
        cur.execute(
            """UPDATE startup_extended
               SET pagerank = ?, betweenness = ?, closeness = ?, community_id = ?
               WHERE startup_id = ?""",
            (pr, bw, cl, com, eid),
        )
        if cur.rowcount > 0:
            updated_sx += 1
    print(f"    {updated_sx} filas actualizadas")

    # 2. Reemplazar ecosystem_bridges
    print("  Reemplazando ecosystem_bridges...")
    cur.execute("DELETE FROM ecosystem_bridges")
    cur.executemany(
        """INSERT INTO ecosystem_bridges
           (source_entity_id, target_entity_id, source_community, target_community, weight, computed_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [(b["source_entity_id"], b["target_entity_id"],
          b["source_community"], b["target_community"], b["weight"], timestamp)
         for b in bridges],
    )

    # 3. Reemplazar ecosystem_bottlenecks
    print("  Reemplazando ecosystem_bottlenecks...")
    cur.execute("DELETE FROM ecosystem_bottlenecks")
    cur.executemany(
        """INSERT INTO ecosystem_bottlenecks
           (entity_id, community_id, coverage_fraction, deals_in_community,
            community_size, risk_if_removed, computed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [(b["entity_id"], b["_community"], b["betweenness"], b["in_degree"],
          b["out_degree"], b["risk_if_removed"], timestamp) for b in bottlenecks],
    )

    # 4. Reemplazar ecosystem_whitespace
    print("  Reemplazando ecosystem_whitespace...")
    cur.execute("DELETE FROM ecosystem_whitespace")
    cur.executemany(
        """INSERT INTO ecosystem_whitespace
           (macro_theme, country_code, startup_count, investor_count, opportunity_score, computed_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [(w["macro_theme"], w["country_code"], w["startup_count"],
          w["investor_count"], w["opportunity_score"], timestamp) for w in whitespace],
    )

    # 5. Audit log: dejar registro del run
    summary = {
        "bridges": len(bridges),
        "bottlenecks": len(bottlenecks),
        "whitespace_cells": len(whitespace),
        "nodes_with_pagerank": len(centralities["pagerank"]),
    }
    cur.execute(
        """INSERT INTO audit_log
           (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?, ?, NULL, ?, ?, NULL, ?, ?)""",
        (timestamp, actor, "ecosystem_graph_outputs", "computed",
         json.dumps(summary, ensure_ascii=False), "graph analytics full rebuild"),
    )

    conn.commit()


# ---------------------------------------------------------------------------
# Reporte humano-legible
# ---------------------------------------------------------------------------

def write_dashboard_data(conn: sqlite3.Connection) -> None:
    """Genera pilot/ecosystem-diagnostics-data.js para consumo del dashboard HTML."""
    from src.utils import write_js_global

    name_for = dict(conn.execute("SELECT entity_id, canonical_name FROM entities").fetchall())
    type_for = dict(conn.execute("SELECT entity_id, entity_type FROM entities").fetchall())
    country_for = dict(conn.execute("SELECT entity_id, country_code FROM entities").fetchall())

    # 1. Bottlenecks rankeados
    bottlenecks_raw = conn.execute("""
        SELECT entity_id, community_id, coverage_fraction, deals_in_community,
               community_size, risk_if_removed
        FROM ecosystem_bottlenecks
        ORDER BY coverage_fraction DESC, deals_in_community DESC
    """).fetchall()
    bottlenecks = [
        {
            "fund_name": name_for.get(eid, eid),
            "fund_country": country_for.get(eid) or "",
            "entity_id": eid,
            "community_id": com,
            "coverage_pct": round(cov * 100, 1),
            "deals": deals,
            "community_size": size,
            "risk": risk,
        }
        for eid, com, cov, deals, size, risk in bottlenecks_raw
    ]

    # 2. Super-conectores (fondos que aparecen como source en muchos bridges)
    sc_raw = conn.execute("""
        SELECT source_entity_id, count(*) AS bridges,
               COUNT(DISTINCT target_community) AS communities_reached
        FROM ecosystem_bridges
        GROUP BY source_entity_id
        HAVING bridges >= 2
        ORDER BY bridges DESC
    """).fetchall()
    super_connectors = [
        {
            "fund_name": name_for.get(eid, eid),
            "entity_id": eid,
            "bridges": br,
            "communities_reached": cr,
        }
        for eid, br, cr in sc_raw
    ]

    # 3. Whitespace ordenado
    ws_raw = conn.execute("""
        SELECT macro_theme, country_code, startup_count, investor_count, opportunity_score
        FROM ecosystem_whitespace
        ORDER BY opportunity_score DESC, startup_count DESC
    """).fetchall()
    whitespace = [
        {
            "macro_theme": t,
            "country_code": c,
            "startup_count": sc,
            "investor_count": ic,
            "opportunity_score": round(os, 2),
            "is_uncovered": ic == 0,
        }
        for t, c, sc, ic, os in ws_raw
    ]

    # 4. Estadísticas agregadas
    total_nodes = conn.execute("SELECT count(*) FROM entities").fetchone()[0]
    total_edges = conn.execute("SELECT count(*) FROM investment_edges").fetchone()[0]
    community_count = conn.execute(
        "SELECT count(DISTINCT community_id) FROM startup_extended WHERE community_id IS NOT NULL AND community_id != -1"
    ).fetchone()[0]
    isolated_startups = conn.execute(
        "SELECT count(*) FROM startup_extended WHERE community_id = -1 OR community_id IS NULL"
    ).fetchone()[0]
    critical_count = sum(1 for b in bottlenecks if b["risk"] == "critical")
    high_count = sum(1 for b in bottlenecks if b["risk"] == "high")
    moderate_count = sum(1 for b in bottlenecks if b["risk"] == "moderate")

    # 5. Computed-at timestamp
    computed_at = conn.execute(
        "SELECT computed_at FROM ecosystem_bottlenecks ORDER BY computed_at DESC LIMIT 1"
    ).fetchone()
    computed_at = computed_at[0] if computed_at else None

    payload = {
        "computed_at": computed_at,
        "stats": {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "communities": community_count,
            "isolated_startups": isolated_startups,
            "bridges": len(super_connectors),
            "bottlenecks_critical": critical_count,
            "bottlenecks_high": high_count,
            "bottlenecks_moderate": moderate_count,
            "whitespace_cells": len(whitespace),
            "uncovered_cells": sum(1 for w in whitespace if w["is_uncovered"]),
        },
        "bottlenecks": bottlenecks,
        "super_connectors": super_connectors,
        "whitespace": whitespace,
    }

    out_path = ROOT / "pilot" / "ecosystem-diagnostics-data.js"
    write_js_global(out_path, "ECOSYSTEM_DIAGNOSTICS_DATA", payload)
    print(f"  Dashboard data: {out_path.relative_to(ROOT)} ({out_path.stat().st_size // 1024} KB)")


def print_top_insights(
    conn: sqlite3.Connection,
    bottlenecks: list[dict[str, Any]],
    bridges: list[dict[str, Any]],
    whitespace: list[dict[str, Any]],
) -> None:
    """Muestra los hallazgos top en consola."""
    name_for = dict(conn.execute("SELECT entity_id, canonical_name FROM entities").fetchall())
    type_for = dict(conn.execute("SELECT entity_id, entity_type FROM entities").fetchall())

    print("\n=== TOP 12 BOTTLENECKS por dependencia de comunidad ===")
    print(f"{'#':>3} {'Riesgo':>10}  {'Cov%':>6}  {'Deals':>5}/{'Total':>5}  Comm  Entidad")
    print("-" * 90)
    for i, b in enumerate(bottlenecks[:12], 1):
        nm = name_for.get(b["entity_id"], b["entity_id"])
        tp = type_for.get(b["entity_id"], "?")
        com_str = f"#{b.get('_community','?'):>2}"
        print(f"{i:>3} {b['risk_if_removed']:>10}  "
              f"{b['betweenness']*100:>5.1f}%  "
              f"{b['in_degree']:>5}/{b['out_degree']:>5}  {com_str}  {nm} ({tp})")

    # Bridges agrupados por nodo "super-conector"
    bridge_appearances: dict[str, int] = {}
    for br in bridges:
        bridge_appearances[br["source_entity_id"]] = bridge_appearances.get(br["source_entity_id"], 0) + 1
    super_connectors = sorted(bridge_appearances.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\n=== TOP 10 SUPER-CONECTORES (fondos que invierten en multiples comunidades) ===")
    print(f"{'#':>3} {'Bridges':>8}  Entidad")
    print("-" * 60)
    for i, (eid, count) in enumerate(super_connectors, 1):
        if count < 2:
            continue
        nm = name_for.get(eid, eid)
        tp = type_for.get(eid, "?")
        print(f"{i:>3} {count:>8}  {nm} ({tp})")

    print("\n=== TOP 12 WHITESPACE (oportunidad estrategica) ===")
    print(f"{'#':>3}  {'Startups':>8} {'Inv.':>5} {'Score':>6}  Theme x Country")
    print("-" * 100)
    for i, w in enumerate(whitespace[:12], 1):
        score = w["opportunity_score"]
        marker = " !!!" if w["investor_count"] == 0 else ""
        print(f"{i:>3}  {w['startup_count']:>8} {w['investor_count']:>5} {score:>6.2f}  "
              f"{w['macro_theme'][:50]} x {w['country_code']}{marker}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(db_path: pathlib.Path = DB_PATH) -> dict[str, Any]:
    """Entry point: corre el pipeline completo de graph analytics."""
    t0 = time.time()
    print(f"\n=== Graph analytics over {db_path.name} ===")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    print("\n[1/6] Construyendo grafo desde investment_edges...")
    G = build_capital_graph(conn)

    print("\n[2/6] Computando centralidades...")
    centralities = compute_centralities(G)

    print("\n[3/6] Detectando comunidades (Louvain)...")
    communities = detect_communities(G)

    print("\n[4/6] Encontrando bridges...")
    bridges = find_bridges(G, communities)

    print("\n[5/6] Detectando bottlenecks...")
    bottlenecks = detect_bottlenecks(G, centralities, communities)

    print("\n[6/6] Mapeando whitespace estrategico...")
    whitespace = detect_whitespace(conn)

    print("\n=== Persistiendo resultados a SQLite ===")
    persist_results(conn, centralities, communities, bridges, bottlenecks, whitespace)

    print("\n=== Generando data file para dashboard ===")
    write_dashboard_data(conn)

    print_top_insights(conn, bottlenecks, bridges, whitespace)

    conn.close()
    elapsed = time.time() - t0
    print(f"\n[OK] Graph analytics done in {elapsed:.1f}s")

    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "communities": len(set(v for v in communities.values() if v != -1)),
        "bridges": len(bridges),
        "bottlenecks": len(bottlenecks),
        "whitespace_cells": len(whitespace),
    }


if __name__ == "__main__":
    run()
