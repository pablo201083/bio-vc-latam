"""
src/clustering.py — clustering semántico + auto-labeling.

Pipeline:
  1. Toma embeddings cacheados desde src/embeddings.py
  2. UMAP a 10D para clustering (denso)
  3. sklearn HDBSCAN sobre 10D
  4. UMAP a 2D para visualización (separate reducer)
  5. Auto-label de clusters con TF-IDF sobre los summaries de cada cluster
  6. Persiste a SQLite: cluster_id, cluster_label, cluster_confidence,
     umap_x, umap_y, is_outlier, tech_codes, industry_codes

También extrae los códigos cross-cutting (tech_codes, industry_codes) usando
src/vocabularies.py y persiste en startup_extended como JSON arrays.

Uso:
    python -m src.clustering
    python -m src.clustering --min-cluster-size 5
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import time
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "db" / "bio_latam.db"


# UMAP params para clustering (más denso, captura estructura)
UMAP_CLUSTER_PARAMS = {
    "n_components": 10,
    "n_neighbors": 12,
    "min_dist": 0.05,
    "metric": "cosine",
    "random_state": 42,
}

# UMAP params para visualización 2D
UMAP_VIZ_PARAMS = {
    "n_components": 2,
    "n_neighbors": 15,
    "min_dist": 0.15,
    "metric": "cosine",
    "random_state": 42,
}

HDBSCAN_PARAMS = {
    "min_cluster_size": 6,
    "min_samples": 3,
    "metric": "euclidean",
    "cluster_selection_method": "eom",
}


def run_umap(vectors: np.ndarray, params: dict, label: str) -> np.ndarray:
    import umap
    print(f"  UMAP {label} → {params['n_components']}D...")
    reducer = umap.UMAP(**params)
    return reducer.fit_transform(vectors).astype(np.float32)


def run_hdbscan(reduced_10d: np.ndarray, params: dict) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.cluster import HDBSCAN
    print(f"  HDBSCAN (min_cluster_size={params['min_cluster_size']})...")
    model = HDBSCAN(**params)
    labels = model.fit_predict(reduced_10d)
    # sklearn HDBSCAN expone probabilities_
    probs = getattr(model, "probabilities_", None)
    if probs is None:
        probs = np.zeros(len(labels), dtype=np.float32)
    return labels, probs.astype(np.float32)


def auto_label_clusters(
    labels: np.ndarray,
    texts: list[str],
    tech_map: dict[str, list[str]] | None = None,
    ind_map: dict[str, list[str]] | None = None,
    ids: list[str] | None = None,
    top_k: int = 4,
    min_df: int = 2,
) -> dict[int, str]:
    """Etiqueta cada cluster con TF-IDF sobre summaries (más discriminativo que codes).

    Los códigos de vocabulario se usan sólo para enriquecer casos donde TF-IDF
    produce términos genéricos. TF-IDF ya tiene IDF implícito que descuenta
    términos comunes a todos los clusters, haciendo labels más distintivos.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    unique_clusters = sorted(set(int(c) for c in labels if c != -1))
    if not unique_clusters:
        return {}

    cluster_docs = {c: [] for c in unique_clusters}
    for lbl, txt in zip(labels, texts):
        if lbl != -1:
            cluster_docs[int(lbl)].append(txt or "")
    docs = [" ".join(cluster_docs[c]) for c in unique_clusters]

    stopwords = _load_stopwords()
    vec = TfidfVectorizer(
        max_features=3000,
        ngram_range=(1, 2),
        min_df=min_df,
        stop_words=list(stopwords),
        token_pattern=r"(?u)\b[a-zñáéíóúü]{3,}\b",
        sublinear_tf=True,  # log(1+tf) — suaviza dominio de términos muy frecuentes
    )
    try:
        tfidf = vec.fit_transform(docs)
    except ValueError:
        return {c: f"cluster {c}" for c in unique_clusters}

    vocab = np.array(vec.get_feature_names_out())
    labels_map: dict[int, str] = {}
    for i, c in enumerate(unique_clusters):
        row = tfidf[i].toarray().ravel()
        top_idx = np.argsort(row)[::-1][:top_k * 4]  # extra candidates for dedup
        candidates = [vocab[j] for j in top_idx if row[j] > 0]
        # Dedup: skip term if any of its words already appeared in selected terms
        selected: list[str] = []
        seen_words: set[str] = set()
        for term in candidates:
            words = set(term.split())
            if words & seen_words:  # any overlap → skip
                continue
            selected.append(term)
            seen_words.update(words)
            if len(selected) >= top_k:
                break
        labels_map[c] = " · ".join(selected) if selected else f"cluster {c}"
    return labels_map


def _load_stopwords() -> set[str]:
    """Stopwords español+inglés + términos genéricos del dominio."""
    en = {
        "the", "and", "for", "with", "from", "that", "this", "their", "have", "has",
        "are", "was", "were", "into", "its", "based", "company", "startup", "solution",
        "platform", "technology", "using", "use", "uses", "used", "via", "across",
        "products", "services", "providing", "develop", "developing", "developed",
        "data", "system", "systems", "process", "processes", "work", "working", "works",
        "help", "helps", "helping", "enable", "enables", "build", "builds", "building",
        "make", "makes", "provide", "provides", "focus", "focused", "focuses",
        "tool", "tools", "business", "businesses", "companies", "infrastructure",
        "inside", "outside", "around", "through", "approach", "solution",
        "sector", "market", "industry", "industries", "global", "local", "regional",
        "new", "key", "high", "low", "large", "small", "major", "main", "other",
        "first", "second", "also", "well", "both", "one", "two", "three",
        "include", "including", "includes", "allow", "allows", "ensuring",
        "improve", "improving", "increase", "increasing",
        "care", "search", "busca", "seek", "seeks", "aim", "aims", "aimed",
        "production", "produccion", "producción",
        "biotech", "biotechnology",  # demasiado genérico para este corpus
        "develop", "development", "solution", "solutions", "model", "models",
        "company", "companies", "based", "bases", "level", "levels",
        "management", "optimization", "monitoring", "detection", "analysis",
        "supply", "chain", "chains", "value", "values", "network", "networks",
    }
    es = {
        "que", "para", "con", "una", "los", "las", "del", "por", "como", "sus",
        "este", "esta", "esto", "ese", "esos", "esas", "más", "pero", "muy", "sin",
        "entre", "sobre", "hasta", "tipo", "tipos", "través", "uso", "usa", "usan",
        "permite", "permiten", "ofrece", "ofrecen", "empresa", "compañía",
        "plataforma", "solución", "tecnología", "tecnologías", "productos", "servicios",
        "datos", "sistema", "sistemas", "proceso", "procesos", "aplica", "aplican",
        "desarrolla", "desarrollan", "desarrollo", "genera", "generan",
        "lleva", "llevar", "llevan", "logra", "lograr", "logran",
        "permite", "permiten", "requiere", "requieren", "busca", "buscar", "buscan",
        "mejora", "mejoran", "brinda", "brindan", "ayuda", "ayudan",
        "produce", "producen", "tiene", "tienen", "hace", "hacen",
        "también", "cada", "donde", "cuando", "cual", "cuales", "quien",
        "todo", "toda", "todos", "todas", "mismo", "misma", "nuevo", "nueva",
        "alto", "alta", "bajo", "baja", "gran", "grande", "pequeño",
        "primero", "segundo", "nivel", "sector", "mercado", "industria",
        "red", "redes", "modelo", "modelos", "acceso", "herramienta", "herramientas",
    }
    editorial = {
        "entra", "entran", "tesis", "core", "belongs", "fits", "scope",
        "latam", "bio", "puede", "pueden", "operan", "opera",
        "incluye", "incluida", "incluido", "incluir", "inclusión", "inclusion",
        "explicación", "explicacion", "motivo", "razón", "razon",
        "decision", "scope decision", "bio latam", "tesis bio", "core bio",
    }
    return en | es | editorial


def reassign_outliers(
    vectors: np.ndarray,
    labels: np.ndarray,
    probs: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Reasigna outliers HDBSCAN al cluster más próximo por similitud cosena (384D).

    Los embeddings ya vienen normalizados L2 desde src/embeddings.py, así que
    similitud cosena = producto punto. La confianza del reasignado se mapea al
    rango [0.05, 0.38] para mantenerlo visualmente distinguible de los miembros
    núcleo del cluster (que tienen probs HDBSCAN ≥ 0.5).

    Retorna (new_labels, new_probs) con 0 outliers (-1).
    """
    outlier_mask = labels == -1
    n_out = int(outlier_mask.sum())
    if n_out == 0:
        return labels, probs

    new_labels = labels.copy()
    new_probs = probs.copy()
    unique_clusters = sorted(set(int(l) for l in labels if l != -1))

    # Centroides normalizados de cada cluster en espacio 384D
    centroid_matrix = np.stack([
        (lambda v: v / (np.linalg.norm(v) or 1))(vectors[labels == c].mean(axis=0))
        for c in unique_clusters
    ])  # (n_clusters, 384)

    outlier_idx = np.where(outlier_mask)[0]
    # dot product de vecs normalizados = coseno similarity
    sims = vectors[outlier_idx] @ centroid_matrix.T  # (n_out, n_clusters)
    best_ci = sims.argmax(axis=1)
    best_sim = sims.max(axis=1)

    for i, orig in enumerate(outlier_idx):
        new_labels[orig] = unique_clusters[best_ci[i]]
        # Mapear similitud cosena a rango [0.05, 0.38] (periferia visible pero distinguible)
        sim = float(np.clip(best_sim[i], 0.0, 1.0))
        new_probs[orig] = 0.05 + sim * 0.33

    print(f"  Reasignados por proximidad: {n_out} startups → conf. periferia [0.05-0.38]")
    return new_labels, new_probs


def extract_codes_for_all(conn: sqlite3.Connection, ids: list[str]) -> tuple[dict, dict]:
    """Devuelve dos dicts startup_id → list[code] para tech e industry."""
    from src.vocabularies import load_tech_vocab, load_industry_vocab, extract_codes

    _, tech_lookup = load_tech_vocab()
    _, ind_lookup = load_industry_vocab()

    rows = conn.execute(
        """SELECT startup_id, technical_stack, technology_tags,
                  industry_destination, domain_tags
           FROM startup_extended WHERE startup_id IN ({})""".format(
            ",".join("?" * len(ids))
        ),
        ids,
    ).fetchall()

    tech_map = {}
    ind_map = {}
    for sid, ts, tt, ind, dt in rows:
        tech_blob = (ts or "") + ";" + (tt or "")
        ind_blob = (ind or "") + ";" + (dt or "")
        tech_map[sid] = extract_codes(tech_blob, tech_lookup)
        ind_map[sid] = extract_codes(ind_blob, ind_lookup)
    return tech_map, ind_map


def sync_vocab_tables(conn: sqlite3.Connection) -> None:
    """Sincroniza vocab_technologies / vocab_industries en SQLite desde los CSVs."""
    from src.vocabularies import load_tech_vocab, load_industry_vocab

    tech_vocab, _ = load_tech_vocab()
    ind_vocab, _ = load_industry_vocab()

    cur = conn.cursor()
    cur.execute("DELETE FROM vocab_technologies")
    cur.executemany(
        "INSERT INTO vocab_technologies (code, canonical_label, aliases, grp) VALUES (?, ?, ?, ?)",
        [(v.code, v.canonical_label, ";".join(v.aliases), v.group) for v in tech_vocab],
    )
    cur.execute("DELETE FROM vocab_industries")
    cur.executemany(
        "INSERT INTO vocab_industries (code, canonical_label, aliases, grp) VALUES (?, ?, ?, ?)",
        [(v.code, v.canonical_label, ";".join(v.aliases), v.group) for v in ind_vocab],
    )
    conn.commit()


def persist_results(
    conn: sqlite3.Connection,
    ids: list[str],
    labels: np.ndarray,
    probs: np.ndarray,
    coords2d: np.ndarray,
    cluster_labels: dict[int, str],
    tech_map: dict[str, list[str]],
    ind_map: dict[str, list[str]],
) -> None:
    """Persiste resultados de clustering + códigos a startup_extended."""
    cur = conn.cursor()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for sid, lbl, prob, (x, y) in zip(ids, labels, probs, coords2d):
        c = int(lbl)
        # is_outlier = 1 significa "periferia semántica" (asignado por proximidad, conf baja)
        # Todas las startups tienen un cluster válido — ninguna queda excluida
        is_outlier = 1 if float(prob) < 0.4 else 0
        cluster_label = cluster_labels.get(c, f"cluster {c}")
        tech_json = json.dumps(tech_map.get(sid, []))
        ind_json = json.dumps(ind_map.get(sid, []))
        cur.execute(
            """UPDATE startup_extended
               SET cluster_id = ?, cluster_label = ?, cluster_confidence = ?,
                   umap_x = ?, umap_y = ?, is_outlier = ?,
                   tech_codes = ?, industry_codes = ?
               WHERE startup_id = ?""",
            (c, cluster_label, float(prob), float(x), float(y),
             is_outlier, tech_json, ind_json, sid),
        )

    # Audit log
    n_clusters = len(set(int(l) for l in labels if l != -1))
    n_outliers = int((labels == -1).sum())
    summary = {
        "n_startups": len(ids),
        "n_clusters": n_clusters,
        "n_outliers": n_outliers,
        "outlier_pct": round(n_outliers / max(len(ids), 1) * 100, 1),
    }
    cur.execute(
        """INSERT INTO audit_log
           (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?, 'clustering', NULL, 'startup_extended', 'semantic_cluster', NULL, ?, ?)""",
        (timestamp, json.dumps(summary, ensure_ascii=False),
         "semantic clustering rebuild"),
    )
    conn.commit()


_COUNTRY_NAMES: dict[str, str] = {
    "AR": "Argentina", "BR": "Brazil", "CL": "Chile", "CO": "Colombia",
    "MX": "Mexico", "UY": "Uruguay", "PE": "Peru", "EC": "Ecuador",
    "PY": "Paraguay", "BO": "Bolivia", "VE": "Venezuela", "CR": "Costa Rica",
    "PA": "Panama", "GT": "Guatemala", "US": "USA", "UK": "UK",
    "ES": "Spain", "FR": "France", "NL": "Netherlands", "SG": "Singapore",
    "IL": "Israel", "CA": "Canada", "AE": "UAE",
}
_REGION_SKIP = {"latam", "latinamerica", "latin america", "latam region"}


def _parse_countries(raw: str | None) -> list[str]:
    """Descompone 'AR/US/BR' en ['Argentina', 'USA', 'Brazil'], omitiendo regiones."""
    if not raw:
        return []
    seen: list[str] = []
    for part in str(raw).split("/"):
        token = part.strip()
        if not token or token.lower() in _REGION_SKIP:
            continue
        name = _COUNTRY_NAMES.get(token.upper(), token)
        if name not in seen:
            seen.append(name)
    return seen


def write_dashboard_data(conn: sqlite3.Connection) -> None:
    """Genera pilot/startup-themes-data.js con los datos para el dashboard."""
    from src.utils import write_js_global
    from src.vocabularies import load_tech_vocab, load_industry_vocab, vocab_to_dict

    tech_vocab, _ = load_tech_vocab()
    ind_vocab, _ = load_industry_vocab()

    rows = conn.execute("""
        SELECT sx.startup_id, e.canonical_name, e.country_code, e.website,
               sx.macro_theme, sx.emergent_theme,
               sx.startup_summary_v1, sx.business_one_liner,
               sx.cluster_id, sx.cluster_label, sx.cluster_confidence,
               sx.umap_x, sx.umap_y, sx.is_outlier,
               sx.tech_codes, sx.industry_codes,
               sx.data_quality_score, sx.quality_band,
               sx.community_id, sx.pagerank,
               sx.valuation_tier,
               COUNT(ie.investment_id) AS n_rounds
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        LEFT JOIN investment_edges ie ON ie.startup_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
        GROUP BY sx.startup_id
        ORDER BY sx.cluster_id, sx.startup_id
    """).fetchall()

    startups = []
    for r in rows:
        tier_raw = r[20]
        countries_list = _parse_countries(r[2])
        startups.append({
            "id": r[0],
            "name": r[1],
            "country": countries_list[0] if countries_list else "",   # primario (compat)
            "countries": countries_list,                               # todos los países
            "website": r[3] or "",
            "macro_theme": r[4] or "",
            "emergent_theme": r[5] or "",
            "summary": (r[6] or "")[:600],
            "one_liner": r[7] or "",
            "cluster_id": r[8] if r[8] is not None else -1,
            "cluster_label": r[9] or "",
            "cluster_confidence": round(float(r[10] or 0), 3),
            "x": round(float(r[11] or 0), 3),
            "y": round(float(r[12] or 0), 3),
            "is_outlier": bool(r[13]),
            "tech_codes": json.loads(r[14] or "[]"),
            "industry_codes": json.loads(r[15] or "[]"),
            "quality_score": float(r[16] or 0),
            "quality_band": r[17] or "",
            "community_id": r[18],
            "pagerank": float(r[19] or 0),
            "valuation_tier": float(tier_raw) if tier_raw is not None else None,
            "n_rounds": int(r[21]),
        })

    # Cluster summary con métricas para inversor
    cluster_summary = {}
    for s in startups:
        c = s["cluster_id"]
        if c not in cluster_summary:
            cluster_summary[c] = {
                "cluster_id": c,
                "label": s["cluster_label"],
                "size": 0,
                "macro_themes": {},
                "tech_codes": {},
                "industry_codes": {},
                "countries": {},
                "n_funded": 0,
                "n_featured": 0,
            }
        cs = cluster_summary[c]
        cs["size"] += 1
        m = s["macro_theme"] or "—"
        cs["macro_themes"][m] = cs["macro_themes"].get(m, 0) + 1
        for t in s["tech_codes"]:
            cs["tech_codes"][t] = cs["tech_codes"].get(t, 0) + 1
        for i in s["industry_codes"]:
            cs["industry_codes"][i] = cs["industry_codes"].get(i, 0) + 1
        for co in (s["countries"] or ["—"]):
            cs["countries"][co] = cs["countries"].get(co, 0) + 1
        if s["n_rounds"] > 0:
            cs["n_funded"] += 1
        if s["valuation_tier"] is not None and s["valuation_tier"] >= 2:
            cs["n_featured"] += 1

    clusters_list = sorted(
        [c for c in cluster_summary.values() if c["cluster_id"] != -1],
        key=lambda c: (-c["size"], c["cluster_id"]),
    )

    # ── Network graph data (layout calculado en JS via Force Atlas) ────────────
    investment_rows = conn.execute("""
        SELECT ie.investor_id, e_inv.canonical_name, ie.startup_id,
               COUNT(*) AS n_rounds_inv
        FROM investment_edges ie
        JOIN entities e_inv ON e_inv.entity_id = ie.investor_id
        JOIN startup_extended sx ON sx.startup_id = ie.startup_id
        WHERE ie.round_stage = 'validated_investor_to_startup'
          AND sx.scope_decision = 'include'
        GROUP BY ie.investor_id, ie.startup_id
    """).fetchall()

    startup_id_set = {s["id"] for s in startups}
    investor_meta: dict[str, dict] = {}
    graph_edges: list[dict] = []

    for inv_id, inv_name, st_id, _ in investment_rows:
        if st_id not in startup_id_set:
            continue
        if inv_id not in investor_meta:
            investor_meta[inv_id] = {"name": inv_name, "n": 0}
        investor_meta[inv_id]["n"] += 1
        graph_edges.append({"investor_id": inv_id, "startup_id": st_id})

    investor_nodes = [
        {"id": inv_id, "name": meta["name"], "n_investments": meta["n"]}
        for inv_id, meta in investor_meta.items()
    ]

    print(f"  Grafo: {len(investor_nodes)} inversores, {len(graph_edges)} aristas "
          f"({len([s for s in startups if s['n_rounds']>0])} startups con inversión)")

    payload = {
        "computed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "intfloat/multilingual-e5-small",
        "stats": {
            "total_startups": len(startups),
            "n_clusters": len(clusters_list),
            "featured_count": sum(1 for s in startups if s["valuation_tier"] is not None and s["valuation_tier"] >= 2),
            "funded_count": sum(1 for s in startups if s["n_rounds"] > 0),
        },
        "startups": startups,
        "clusters": clusters_list,
        "vocab_tech": vocab_to_dict(tech_vocab),
        "vocab_industry": vocab_to_dict(ind_vocab),
        "graph": {
            "investor_nodes": investor_nodes,
            "edges": graph_edges,
        },
    }

    out_path = ROOT / "pilot" / "startup-themes-data.js"
    write_js_global(out_path, "STARTUP_THEMES_DATA", payload)
    print(f"  Dashboard data: {out_path.relative_to(ROOT)} ({out_path.stat().st_size // 1024} KB)")


def print_cluster_summary(
    conn: sqlite3.Connection,
    ids: list[str],
    labels: np.ndarray,
    cluster_labels: dict[int, str],
) -> None:
    """Muestra el listado de clusters con tamaño y label."""
    print("\n=== CLUSTERS DETECTADOS ===")
    print(f"{'ID':>4} {'N':>4}  Label")
    print("-" * 80)
    counts: dict[int, int] = {}
    for lbl in labels:
        c = int(lbl)
        counts[c] = counts.get(c, 0) + 1
    for c in sorted(counts.keys()):
        marker = "outlier" if c == -1 else cluster_labels.get(c, f"cluster {c}")
        print(f"{c:>4} {counts[c]:>4}  {marker}")

    # Compare con macro_theme editorial
    names_for = dict(conn.execute("SELECT entity_id, canonical_name FROM entities").fetchall())
    macro_for = dict(conn.execute(
        "SELECT startup_id, macro_theme FROM startup_extended WHERE scope_decision='include'"
    ).fetchall())

    # Para cada cluster (no outlier) mostrar distribución de macro_theme editorial
    print("\n=== CLUSTER vs MACRO_THEME EDITORIAL (top 5 por cluster) ===")
    cluster_to_macros: dict[int, dict[str, int]] = {}
    for sid, lbl in zip(ids, labels):
        c = int(lbl)
        if c == -1: continue
        m = (macro_for.get(sid) or "").strip() or "—"
        cluster_to_macros.setdefault(c, {})[m] = cluster_to_macros.setdefault(c, {}).get(m, 0) + 1

    for c in sorted(cluster_to_macros.keys()):
        cl = cluster_labels.get(c, f"cluster {c}")
        print(f"\n  [{c}] {cl}  ({counts[c]} startups)")
        macros = sorted(cluster_to_macros[c].items(), key=lambda kv: kv[1], reverse=True)
        for m, n in macros[:5]:
            print(f"     {n:>3}  {m[:70]}")


def run(
    db_path: pathlib.Path = DB_PATH,
    min_cluster_size: int = 6,
    force_embeddings: bool = False,
) -> dict:
    """Pipeline completo de clustering."""
    t0 = time.time()
    from src.embeddings import run as run_embeddings

    print(f"\n=== Semantic clustering ===")

    # 1. Embeddings (con cache)
    emb_result = run_embeddings(force=force_embeddings, db_path=db_path)
    vectors = emb_result["vectors"]
    ids = emb_result["ids"]

    # 2. UMAP a 10D para clustering
    reduced_10d = run_umap(vectors, UMAP_CLUSTER_PARAMS, "clustering")

    # 3. UMAP a 2D para visualización
    coords_2d = run_umap(vectors, UMAP_VIZ_PARAMS, "viz")

    # 4. HDBSCAN
    params = dict(HDBSCAN_PARAMS)
    params["min_cluster_size"] = min_cluster_size
    labels, probs = run_hdbscan(reduced_10d, params)

    n_clusters = len(set(int(l) for l in labels if l != -1))
    n_outliers = int((labels == -1).sum())
    print(f"  Clusters: {n_clusters} | Sin asignar (antes de reasignación): {n_outliers}/{len(labels)} ({n_outliers*100//len(labels)}%)")

    # Reasignar outliers — ninguna startup queda sin cluster en el observatorio
    labels, probs = reassign_outliers(vectors, labels, probs)
    assert (labels == -1).sum() == 0, "Quedaron outliers sin reasignar"

    # 5. Auto-label
    conn = sqlite3.connect(db_path)
    texts_for_label = []
    rows_by_id = dict(conn.execute(
        "SELECT startup_id, startup_summary_v1 FROM startup_extended"
    ).fetchall())
    for sid in ids:
        texts_for_label.append(rows_by_id.get(sid) or "")
    # 6. Extraer tech_codes e industry_codes primero (los usamos para mejores labels)
    print("  Extrayendo tech_codes e industry_codes desde vocabularios...")
    tech_map, ind_map = extract_codes_for_all(conn, ids)

    cluster_labels = auto_label_clusters(
        labels, texts_for_label,
        tech_map=tech_map, ind_map=ind_map, ids=ids,
    )
    print(f"  Labels auto-generados: {len(cluster_labels)}")

    # 7. Sincronizar vocab tables
    sync_vocab_tables(conn)

    # 8. Persistir
    print("  Persistiendo a SQLite...")
    persist_results(conn, ids, labels, probs, coords_2d, cluster_labels, tech_map, ind_map)

    # 9. Reporte
    print_cluster_summary(conn, ids, labels, cluster_labels)

    # 10. Dashboard data
    write_dashboard_data(conn)

    conn.close()
    elapsed = time.time() - t0
    print(f"\n[OK] Clustering done in {elapsed:.1f}s")
    return {
        "n_clusters": n_clusters,
        "n_outliers": n_outliers,
        "n_startups": len(ids),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-cluster-size", type=int, default=6)
    parser.add_argument("--force-embeddings", action="store_true")
    args = parser.parse_args()
    run(min_cluster_size=args.min_cluster_size, force_embeddings=args.force_embeddings)
