"""
src/intelligence.py  —  Motor de inteligencia ecosistémica BIO LATAM.

Tres capacidades:

  1. build_intelligence_data()
       Genera pilot/intelligence-data.js con:
       - Metadatos ricos de startups include
       - Vectores semánticos (Float32Array base64, listo para coseno en browser)
       - Centroides de portfolio por inversor + potencial latente pre-computado
       - Índice cross-entidad para búsqueda unificada

  2. semantic_search(query, top_k, filters)
       Codifica el texto libre con intfloat/multilingual-e5-small y busca
       por coseno contra los 487+ vectores normalizados. Filtros opcionales:
       theme, country, stage, funded.

  3. latent_potential(entity_id, top_k)
       Para inversores: startups con fit temático/geográfico sin edge.
       Para startups:  inversores con portfolio alignment sin edge.
       Para orgs/esos/corporates: startups temáticamente cercanas.

Uso:
    python pipeline.py intelligence-data          # genera el .js
    python pipeline.py query "biopesticidas BR"   # búsqueda semántica CLI
    python pipeline.py latent GridX               # potencial latente CLI
    python pipeline.py query "..." --json         # salida JSON (para server.js)
"""
from __future__ import annotations

import base64
import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
VECTORS_PATH = ROOT / "embeddings" / "startup_vectors.npy"
META_PATH = ROOT / "embeddings" / "startup_vectors_meta.json"
OUT_PATH = ROOT / "pilot" / "intelligence-data.js"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── scoring ──────────────────────────────────────────────────────────────────

def _get_weights(portfolio_size: int) -> tuple[float, float, float]:
    """Adaptive weights (W_SEMANTIC, W_THEME, W_COUNTRY) by portfolio size.

    Small portfolios have unreliable centroids (1–2 startups → centroid ≈ mean
    vector of just those startups), so we trust theme/country overlap more.
    Large portfolios have stable centroids and semantic similarity is meaningful.
    """
    if portfolio_size <= 2:
        return 0.20, 0.60, 0.20
    elif portfolio_size <= 5:
        return 0.35, 0.45, 0.20
    else:
        return 0.50, 0.35, 0.15


# 8 sealed bio themes — adjacency matrix (pairs not listed default to 0.0)
_T = {
    "Bioinputs & Crop Resilience":          "bioinputs",
    "Precision Agriculture":                     "farmintel",
    "Nature & Ecosystem Tech":               "nature",
    "Food Systems & Alt Proteins":           "food",
    "Biomanufacturing & Platform Technologies": "biomanuf",
    "Biomaterials & Green Chemistry":       "biomater",
    "Therapeutics":                          "therapeutics",
    "Diagnostics & Devices":           "diagnostics",
}
_THEME_ADJ_RAW: dict[tuple[str, str], float] = {
    # Agriculture cluster
    ("bioinputs",     "farmintel"):     0.40,
    ("bioinputs",     "nature"):        0.38,
    ("bioinputs",     "food"):          0.30,
    ("farmintel",     "nature"):        0.35,
    ("farmintel",     "food"):          0.25,
    # Food / biomanuf
    ("food",          "biomanuf"):      0.45,
    ("food",          "biomater"):      0.28,
    # Biomanuf / biomater
    ("biomanuf",      "biomater"):      0.38,
    ("biomanuf",      "therapeutics"):  0.35,
    ("biomanuf",      "diagnostics"):   0.25,
    # Health cluster
    ("therapeutics",  "diagnostics"):   0.42,
    ("therapeutics",  "biomater"):      0.22,
    ("diagnostics",   "bioinputs"):     0.15,
    # Nature / circular
    ("nature",        "biomanuf"):      0.28,
    ("nature",        "biomater"):      0.32,
}
# Reverse short keys to full theme names
_SHORT_TO_THEME = {v: k for k, v in _T.items()}
BIO_THEME_ADJACENCY: dict[tuple[str, str], float] = {}
for (a_short, b_short), score in _THEME_ADJ_RAW.items():
    a = _SHORT_TO_THEME[a_short]
    b = _SHORT_TO_THEME[b_short]
    BIO_THEME_ADJACENCY[(a, b)] = score
    BIO_THEME_ADJACENCY[(b, a)] = score


def _theme_overlap(t1: str, t2: str) -> float:
    """Graduated theme similarity between two bio themes (0.0–1.0)."""
    if not t1 or not t2:
        return 0.0
    if t1 == t2:
        return 1.0
    return BIO_THEME_ADJACENCY.get((t1, t2), 0.0)


# ─────────────────────────────────────────────────────────────────────────────
#  Structural eligibility — can this fund actually write this cheque?
#  Theme/semantics answer "would they like it"; stage + ticket answer "could
#  it even happen". Applied as a multiplier so a perfect thematic match at an
#  impossible stage is demoted, not surfaced as "Encaje fuerte".
#  Neutral (factor 1.0) whenever either side's data is missing — we never
#  penalize a fund for an unknown.
# ─────────────────────────────────────────────────────────────────────────────
_STAGE_ORD = {
    "pre-seed": 0, "accelerator": 0,
    "seed": 1,
    "series-a": 2,
    "series-b": 3,
    "series-c": 4, "series-c+": 4,
    "growth": 5, "corporate": 5,
    "pe": 6,
}
# Implied round-size band per stage (USD) — rough LATAM bio reference, used only
# to detect a hard ticket mismatch (fund writes far bigger/smaller than the round).
_STAGE_TICKET = {
    "pre-seed":   (50_000, 600_000),
    "accelerator":(20_000, 200_000),
    "seed":       (300_000, 2_500_000),
    "series-a":   (1_500_000, 9_000_000),
    "series-b":   (6_000_000, 25_000_000),
    "series-c":   (15_000_000, 60_000_000),
    "series-c+":  (15_000_000, 60_000_000),
    "growth":     (20_000_000, 120_000_000),
}


def _parse_pref_stages(s: str) -> set[int]:
    """Parse an investor's preferred_stages string (delimiter is ';' OR ',')
    into a set of stage ordinals."""
    out: set[int] = set()
    for tok in re.split(r"[;,]", (s or "").lower()):
        tok = tok.strip()
        if tok in _STAGE_ORD:
            out.add(_STAGE_ORD[tok])
    return out


def _stage_factor(stage: str, pref_ords: set[int]) -> tuple[float, str]:
    """Eligibility multiplier by funding-stage distance (graduated, never zero)."""
    stage = (stage or "").lower()
    if stage not in _STAGE_ORD or not pref_ords:
        return 1.0, ""  # unknown on either side → neutral, no penalty
    d = min(abs(_STAGE_ORD[stage] - p) for p in pref_ords)
    if d == 0: return 1.0,  f"stage_fit:{stage}"
    if d == 1: return 0.72, f"stage_near:{stage}"
    if d == 2: return 0.48, f"stage_off:{stage}"
    return 0.32, f"stage_mismatch:{stage}"


def _ticket_factor(stage: str, tmin, tmax) -> tuple[float, str]:
    """Soft penalty when the fund's ticket range is disjoint from the round size
    implied by the startup's stage. Mild on purpose — stage already carries most
    of the signal and ticket is only ~55% covered."""
    rng = _STAGE_TICKET.get((stage or "").lower())
    if not rng or not tmin or not tmax:
        return 1.0, ""
    lo, hi = rng
    if tmax >= lo and tmin <= hi:
        return 1.0, ""                       # ranges overlap → fine
    if tmin > hi:
        return 0.55, "ticket_too_large"      # fund writes bigger than this round
    return 0.70, "ticket_too_small"          # fund too small to lead (can co-invest)


def _rescale_scores(candidates: list[dict]) -> list[dict]:
    """Map raw scores from [min, max] → [0.10, 0.95] with ^0.7 power curve.

    Preserves ranking but stretches the distribution so top candidate ≈ 0.95
    and weakest ≈ 0.10, regardless of absolute score levels.
    Applied after sorting so it doesn't change order.
    """
    if len(candidates) <= 1:
        return candidates
    scores = [c["score"] for c in candidates]
    s_min, s_max = min(scores), max(scores)
    rng = s_max - s_min
    if rng < 1e-6:
        # All equal — distribute evenly
        n = len(candidates)
        for i, c in enumerate(candidates):
            c["score_raw"] = c["score"]
            c["score"] = round(0.95 - 0.85 * i / max(n - 1, 1), 3)
        return candidates
    for c in candidates:
        c["score_raw"] = round(c["score"], 4)
        normalized = (c["score"] - s_min) / rng      # 0..1, best=1
        c["score"] = round(0.10 + 0.85 * (normalized ** 0.7), 3)
    return candidates

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_vectors() -> tuple[np.ndarray, list[str]]:
    """Returns (matrix [N,384], ordered list of startup_ids)."""
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    vecs = np.load(VECTORS_PATH).astype(np.float32)
    return vecs, meta["ids"]


def _vec_index(ids: list[str]) -> dict[str, int]:
    return {sid: i for i, sid in enumerate(ids)}


def _to_b64(arr: np.ndarray) -> str:
    return base64.b64encode(arr.astype(np.float32).tobytes()).decode("ascii")


def _load_startup_meta(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               e.founded_year,
               sx.bio_theme_primary, sx.bio_theme_secondary,
               sx.macro_theme, sx.emergent_theme,
               sx.funding_stage, sx.data_quality_score,
               sx.business_one_liner, sx.startup_summary_en,
               sx.startup_summary_v1, sx.scale_tags, sx.technology_tags
        FROM entities e
        JOIN startup_extended sx ON sx.startup_id = e.entity_id
        WHERE sx.scope_decision = 'include' AND e.status != 'excluded'
        ORDER BY e.entity_id
    """).fetchall()
    out = {}
    for r in rows:
        sid = r[0]
        out[sid] = {
            "id":       sid,
            "name":     r[1],
            "country":  (r[2] or "").upper(),
            "website":  r[3] or "",
            "founded":  r[4],
            "theme":    r[5] or r[7] or "",
            "theme2":   r[6] or "",
            "emergent": r[8] or "",
            "stage":    r[9] or "",
            "quality":  round(float(r[10] or 0), 1),
            "one_liner": r[11] or "",
            "summary":  (r[12] or r[13] or "")[:400],
            "scale":    r[14] or "",
            "tech":     r[15] or "",
            "investors": [],
            "funded":   False,
        }
    return out


def _enrich_with_investors(conn: sqlite3.Connection,
                           startups: dict[str, dict]) -> None:
    rows = conn.execute("""
        SELECT ie.startup_id, e.canonical_name
        FROM investment_edges ie
        JOIN entities e ON e.entity_id = ie.investor_id
    """).fetchall()
    for sid, iname in rows:
        if sid in startups:
            startups[sid]["investors"].append(iname)
            startups[sid]["funded"] = True


def _load_org_meta(conn: sqlite3.Connection) -> dict[str, dict]:
    """Load organizations, ESOs, and corporates as unified facilitator profiles."""
    orgs: dict[str, dict] = {}

    # Organizations (gremiales / associations)
    for r in conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               o.focus_area, o.org_type
        FROM entities e JOIN organizations o ON o.org_id = e.entity_id
        WHERE e.status != 'excluded'
    """).fetchall():
        orgs[r[0]] = {
            "id": r[0], "name": r[1], "country": (r[2] or "").upper(),
            "website": r[3] or "", "entity_subtype": "organization",
            "focus_text": f"{r[4] or ''} {r[5] or ''}".strip(),
        }

    # ESOs (Ecosistema de Soporte)
    for r in conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               es.service_profile, es.eso_type, es.geography_focus
        FROM entities e JOIN esos es ON es.eso_id = e.entity_id
        WHERE e.status != 'excluded'
    """).fetchall():
        orgs[r[0]] = {
            "id": r[0], "name": r[1], "country": (r[2] or "").upper(),
            "website": r[3] or "", "entity_subtype": "eso",
            "focus_text": f"{r[4] or ''} {r[5] or ''}".strip(),
            "geo_focus": (r[6] or "").lower(),
        }

    # Corporates
    for r in conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               c.industry, c.demand_profile
        FROM entities e JOIN corporates c ON c.corporate_id = e.entity_id
        WHERE e.status != 'excluded'
    """).fetchall():
        orgs[r[0]] = {
            "id": r[0], "name": r[1], "country": (r[2] or "").upper(),
            "website": r[3] or "", "entity_subtype": "corporate",
            "focus_text": f"{r[4] or ''} {r[5] or ''}".strip(),
        }

    return orgs


# Direct theme keyword matching for org focus-text fit — map theme → relevant keywords
_ORG_FOCUS_THEME_KEYWORDS: dict[str, list[str]] = {
    "Bioinputs & Crop Resilience":             ["bioinputs","biocontrol","agro","agtech","crop","biostimulant","biologicos","semilla","agriculture","agri"],
    "Precision Agriculture":                        ["farm","agro","precision","sensing","datos agro","agriculture","crop monitoring"],
    "Nature & Ecosystem Tech":                  ["climate","nature","ecosystem","regenerat","resource","carbon","water","biodiversidad","ambiental"],
    "Food Systems & Alt Proteins":              ["food","aliment","proteina","ferment","alt protein","novel ingredient","foodtech","cellular"],
    "Biomanufacturing & Platform Technologies":  ["biomanuf","ferment","bioprocess","enzima","biorefin","metabolic","industrial biotech","synthetic bio"],
    "Biomaterials & Green Chemistry":          ["biomaterial","bioplastic","circular","sustainable material","biobased","polymer","bioquimica"],
    "Therapeutics":                             ["therapeut","terapia","drug","oncolog","cancer","cell therapy","gene","immunother","regenerat","farmaco"],
    "Diagnostics & Devices":              ["diagnost","medtech","health","clinical","molecular","genomi","sequencing","salud","biomark"],
}


def _org_theme_overlap(startup_theme: str, focus_text: str) -> float:
    """Score how well a startup's bio_theme_primary fits an org's focus text."""
    if not startup_theme or not focus_text:
        return 0.0
    focus_lower = focus_text.lower()
    keywords = _ORG_FOCUS_THEME_KEYWORDS.get(startup_theme, [])
    matches = sum(1 for kw in keywords if kw in focus_lower)
    if matches >= 3: return 0.90
    if matches == 2: return 0.65
    if matches == 1: return 0.40
    return 0.0


def _load_investor_meta(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               i.investor_type, i.geography_focus,
               i.thesis, i.profile_blurb,
               i.ticket_min_usd, i.ticket_max_usd,
               i.aum_usd_m, i.lead_behavior, i.preferred_stages
        FROM entities e
        JOIN investors i ON i.investor_id = e.entity_id
        WHERE e.status != 'excluded'
    """).fetchall()
    portfolio: dict[str, set] = {}
    for e in conn.execute(
        "SELECT investor_id, startup_id FROM investment_edges"
    ).fetchall():
        portfolio.setdefault(e[0], set()).add(e[1])
    # Convert sets to sorted lists for deterministic output
    portfolio = {k: sorted(v) for k, v in portfolio.items()}
    out = {}
    for r in rows:
        iid = r[0]
        out[iid] = {
            "id":              iid,
            "name":            r[1],
            "country":         (r[2] or "").upper(),
            "website":         r[3] or "",
            "itype":           r[4] or "",
            "geo_focus":       r[5] or "",
            "thesis":          r[6] or "",
            "profile_blurb":   r[7] or "",
            "ticket_min":      r[8],
            "ticket_max":      r[9],
            "aum_usd_m":       r[10],
            "lead_behavior":   r[11] or "",
            "preferred_stages": r[12] or "",
            "portfolio":       portfolio.get(iid, []),
        }
    return out


def _normalize_rows(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms < 1e-9] = 1.0
    return (m / norms).astype(np.float32)


def _build_portfolio_profile(
    inv: dict,
    startups: dict[str, dict],
    vecs: np.ndarray,
    idx: dict[str, int],
) -> dict:
    """Compute portfolio centroid + theme/country sets for one investor.

    Portfolios with more than 8 startups also get sub-centroids (k-means on
    the portfolio's own vectors): a single global mean blurs together
    distinct thematic sub-bets (e.g. a fund with both an agro sleeve and a
    health sleeve), which is exactly what makes large-portfolio matches look
    diffuse. `_score_pair` takes the best-fitting sub-centroid instead of the
    one blurred average.
    """
    mapped = [s for s in inv["portfolio"] if s in startups]
    vec_rows = [vecs[idx[s]] for s in mapped if s in idx]

    centroid: np.ndarray | None = None
    sub_centroids: list[np.ndarray] | None = None
    if vec_rows:
        stacked = np.stack(vec_rows)
        c = np.mean(stacked, axis=0)
        norm = float(np.linalg.norm(c))
        centroid = (c / norm).astype(np.float32) if norm > 1e-9 else c.astype(np.float32)

        if len(vec_rows) > 8:
            k = min(4, max(2, len(vec_rows) // 8))
            from sklearn.cluster import KMeans
            km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(stacked)
            sub_centroids = list(_normalize_rows(km.cluster_centers_))

    themes: set[str] = set()
    countries: set[str] = set()
    for s in mapped:
        st = startups[s]
        if st["theme"]:   themes.add(st["theme"])
        if st["theme2"]:  themes.add(st["theme2"])
        if st["country"]: countries.add(st["country"])

    return {
        "mapped":    set(mapped),
        "centroid":  centroid,
        "sub_centroids": sub_centroids,
        "themes":    themes,
        "countries": countries,
        "size":      len(mapped),
    }


def _score_pair(
    startup: dict,
    profile: dict,
    inv: dict,
    vecs: np.ndarray,
    idx: dict[str, int],
    return_details: bool = False,
) -> float | dict:
    """Score startup→investor fit.

    Returns raw score (float) unless return_details=True, in which case
    returns a dict with score + structured reasons list.
    """
    w_sem, w_th, w_co = _get_weights(profile["size"])

    # Semantic similarity vs portfolio centroid — best-fitting sub-centroid
    # when the portfolio is large enough to have been split (>8 startups),
    # otherwise the single global centroid.
    sim = 0.0
    sim_is_subportfolio = False
    if startup["id"] in idx:
        sv = vecs[idx[startup["id"]]]
        if profile.get("sub_centroids"):
            sim = max(float(np.dot(sv, c)) for c in profile["sub_centroids"])
            sim_is_subportfolio = True
        elif profile["centroid"] is not None:
            sim = float(np.dot(sv, profile["centroid"]))
        sim = max(0.0, sim)

    # Theme score — graduated via adjacency table
    th_score = 0.0
    best_th_reason = ""
    st_theme = startup.get("theme", "") or ""
    st_theme2 = startup.get("theme2", "") or ""
    inv_themes = profile["themes"]

    if st_theme and st_theme in inv_themes:
        th_score = 1.0
        best_th_reason = f"theme_exact:{st_theme}"
    elif st_theme:
        # Best overlap across all investor themes
        best_overlap = 0.0
        best_inv_theme = ""
        for it in inv_themes:
            ov = _theme_overlap(st_theme, it)
            if ov > best_overlap:
                best_overlap, best_inv_theme = ov, it
        if best_overlap > 0:
            th_score = best_overlap
            best_th_reason = f"theme_adjacent:{st_theme}~{best_inv_theme}({best_overlap:.2f})"
        # Also check secondary theme
        if st_theme2 and st_theme2 in inv_themes and 0.6 > th_score:
            th_score = 0.6
            best_th_reason = f"theme2_exact:{st_theme2}"

    # Country / geography score
    co_score = 0.0
    co_reason = ""
    if startup["country"] and startup["country"] in profile["countries"]:
        co_score = 1.0
        co_reason = f"geographic_match:{startup['country']}"
    elif startup["country"] and startup["country"] == inv.get("country", ""):
        co_score = 0.5
        co_reason = f"investor_country:{startup['country']}"

    affinity = w_sem * sim + w_th * th_score + w_co * co_score

    # Structural eligibility gate (can this cheque happen at all?)
    pref_ords = _parse_pref_stages(inv.get("preferred_stages", ""))
    stage_f, stage_reason = _stage_factor(startup.get("stage", ""), pref_ords)
    ticket_f, ticket_reason = _ticket_factor(
        startup.get("stage", ""), inv.get("ticket_min"), inv.get("ticket_max")
    )
    eligibility = max(0.30, stage_f * ticket_f)  # floor so a gem isn't fully buried
    raw = affinity * eligibility

    if not return_details:
        return raw

    reasons = []
    if co_reason:
        reasons.append(co_reason)
    if best_th_reason:
        reasons.append(best_th_reason)
    if sim > 0.50:
        reasons.append(f"semantic_fit_subportfolio:{sim:.2f}" if sim_is_subportfolio
                        else f"semantic_fit:{sim:.2f}")
    if stage_reason:
        reasons.append(stage_reason)
    if ticket_reason:
        reasons.append(ticket_reason)

    return {"score": raw, "reasons": reasons, "sim": sim}


# ─────────────────────────────────────────────────────────────────────────────
#  1. BUILD INTELLIGENCE DATA (JS export)
# ─────────────────────────────────────────────────────────────────────────────

def build_intelligence_data(
    db_path: Path = DB_PATH,
    out_path: Path = OUT_PATH,
) -> dict:
    t0 = time.time()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Load vectors
    if not VECTORS_PATH.exists():
        raise FileNotFoundError(
            "embeddings/startup_vectors.npy not found. "
            "Run: python pipeline.py rebuild --phase embeddings"
        )
    vecs, vec_ids = _load_vectors()
    idx = _vec_index(vec_ids)

    # Load metadata
    startups = _load_startup_meta(conn)
    _enrich_with_investors(conn, startups)
    investors = _load_investor_meta(conn)

    # Non-startup entities for unified search
    orgs_rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.entity_type, e.country_code,
               e.website, o.focus_area, o.org_type
        FROM entities e
        JOIN organizations o ON o.org_id = e.entity_id
        WHERE e.status != 'excluded'
    """).fetchall()
    eso_rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.entity_type, e.country_code,
               e.website, es.service_profile, es.eso_type
        FROM entities e
        JOIN esos es ON es.eso_id = e.entity_id
        WHERE e.status != 'excluded'
    """).fetchall()
    corp_rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.entity_type, e.country_code,
               e.website, c.industry, c.demand_profile
        FROM entities e
        JOIN corporates c ON c.corporate_id = e.entity_id
        WHERE e.status != 'excluded'
    """).fetchall()
    conn.close()

    # ── Startup array (ordered to match vectors) ──────────────────────────
    # Use vec_ids order so row i in IQ_VECTORS_B64 = IQ_STARTUPS[i]
    st_list = []
    for sid in vec_ids:
        if sid not in startups:
            # placeholder for embedding entry without current include status
            st_list.append({
                "id": sid, "name": sid, "country": "", "theme": "",
                "theme2": "", "stage": "", "quality": 0.0,
                "one_liner": "", "summary": "", "scale": "", "tech": "",
                "funded": False, "investors": [], "website": "", "founded": None
            })
        else:
            st_list.append(startups[sid])

    # ── Investor centroids + pre-computed latent potential ────────────────
    inv_list = []
    for iid, inv in investors.items():
        prof = _build_portfolio_profile(inv, startups, vecs, idx)
        if prof["size"] == 0:
            centroid_b64 = ""
        else:
            centroid_b64 = _to_b64(prof["centroid"])

        # Pre-compute top-15 latent candidates (with calibrated scoring)
        gap = []
        if prof["size"] >= 1:
            raw_candidates = []
            for sid, st in startups.items():
                if sid in prof["mapped"]:
                    continue
                detail = _score_pair(st, prof, inv, vecs, idx, return_details=True)
                if detail["score"] > 0.10:  # low threshold before rescale
                    raw_candidates.append({
                        "id":      sid,
                        "name":    st["name"],
                        "country": st["country"],
                        "theme":   st["theme"],
                        "quality": st["quality"],
                        "funded":  st["funded"],
                        "score":   detail["score"],
                        "reasons": detail["reasons"],
                    })
            raw_candidates.sort(key=lambda x: -x["score"])
            raw_candidates = raw_candidates[:30]  # rescale on top-30
            raw_candidates = _rescale_scores(raw_candidates)
            gap = raw_candidates[:15]

        inv_list.append({
            "id":              iid,
            "name":            inv["name"],
            "country":         inv["country"],
            "itype":           inv["itype"],
            "geo_focus":       inv["geo_focus"],
            "website":         inv["website"],
            "thesis":          inv["thesis"],
            "profile_blurb":   inv["profile_blurb"],
            "ticket_min":      inv["ticket_min"],
            "ticket_max":      inv["ticket_max"],
            "aum_usd_m":       inv["aum_usd_m"],
            "lead_behavior":   inv["lead_behavior"],
            "preferred_stages": inv["preferred_stages"],
            "portfolio_size":  prof["size"],
            "portfolio_ids":   sorted(prof["mapped"]),
            "themes":          sorted(prof["themes"]),
            "countries":       sorted(prof["countries"]),
            "centroid_b64":    centroid_b64,
            "gap":             gap,
        })
    inv_list.sort(key=lambda x: -x["portfolio_size"])

    # ── Load entity profiles (rich descriptions from web research) ───────
    import csv as _csv
    _profiles: dict[str, dict] = {}
    _profiles_path = ROOT / "canonical" / "manual_entity_profiles.csv"
    if _profiles_path.exists():
        with open(_profiles_path, encoding="utf-8") as _pf:
            for _row in _csv.DictReader(_pf):
                _profiles[_row["entity_id"]] = _row

    # ── All entities for unified search ──────────────────────────────────
    all_entities: list[dict] = []

    # investors
    for inv in inv_list:
        all_entities.append({
            "id":      inv["id"],
            "name":    inv["name"],
            "type":    "investor",
            "country": inv["country"],
            "focus":   " ".join(inv["themes"][:4]),
            "website": inv["website"],
            "detail":  f"{inv['itype']} · {inv['portfolio_size']} portfolio",
        })

    # organizations
    for r in orgs_rows:
        _p = _profiles.get(r[0], {})
        all_entities.append({
            "id":          r[0],
            "name":        r[1],
            "type":        "organization",
            "country":     (r[3] or "").upper(),
            "focus":       _p.get("bio_themes", r[5] or r[6] or "").split(";")[0],
            "website":     _p.get("website", r[4] or ""),
            "detail":      _p.get("description_es", "Gremial / Asociación"),
            "description_en": _p.get("description_en", ""),
            "bio_themes":  _p.get("bio_themes", ""),
            "demand":      _p.get("demand_signals", ""),
            "presence":    _p.get("latam_presence", ""),
        })

    # esos
    for r in eso_rows:
        _p = _profiles.get(r[0], {})
        all_entities.append({
            "id":          r[0],
            "name":        r[1],
            "type":        "eso",
            "country":     (r[3] or "").upper(),
            "focus":       _p.get("bio_themes", r[5] or r[6] or "").split(";")[0],
            "website":     _p.get("website", r[4] or ""),
            "detail":      _p.get("description_es", "Ecosistema / Soporte"),
            "description_en": _p.get("description_en", ""),
            "bio_themes":  _p.get("bio_themes", ""),
            "demand":      _p.get("demand_signals", ""),
            "presence":    _p.get("latam_presence", ""),
        })

    # corporates
    for r in corp_rows:
        _p = _profiles.get(r[0], {})
        all_entities.append({
            "id":          r[0],
            "name":        r[1],
            "type":        "corporate",
            "country":     (r[3] or "").upper(),
            "focus":       _p.get("bio_themes", r[5] or r[6] or "").split(";")[0],
            "website":     _p.get("website", r[4] or ""),
            "detail":      _p.get("description_es", "Corporate / Adquirente"),
            "description_en": _p.get("description_en", ""),
            "bio_themes":  _p.get("bio_themes", ""),
            "demand":      _p.get("demand_signals", ""),
            "presence":    _p.get("latam_presence", ""),
        })

    # ── Build vectors blob ────────────────────────────────────────────────
    # Only export vectors for startups that are currently "include"
    # (vec_ids order matches st_list order)
    vectors_b64 = _to_b64(vecs)  # full matrix, browser will index by row

    # ── Theme stats for UI filters ────────────────────────────────────────
    from collections import Counter
    theme_counts = Counter(
        st["theme"] for st in startups.values() if st["theme"]
    )

    # ── Write JS ──────────────────────────────────────────────────────────
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
    js_lines = [
        f"// pilot/intelligence-data.js — auto-generated {generated_at}",
        f"// DO NOT EDIT. Regenerate: python pipeline.py intelligence-data",
        "",
        f"const IQ_META = {json.dumps({'generated_at': generated_at, 'startup_count': len(st_list), 'investor_count': len(inv_list), 'vector_dim': int(vecs.shape[1]), 'vec_ids_count': len(vec_ids)}, ensure_ascii=False)};",
        "",
        f"const IQ_STARTUPS = {json.dumps(st_list, ensure_ascii=False)};",
        "",
        f"// Float32Array, shape ({len(vec_ids)}, {vecs.shape[1]}). Row i = IQ_STARTUPS[i].",
        f"const IQ_VECTORS_B64 = \"{vectors_b64}\";",
        "",
        f"const IQ_INVESTORS = {json.dumps(inv_list, ensure_ascii=False)};",
        "",
        f"const IQ_ALL_ENTITIES = {json.dumps(all_entities, ensure_ascii=False)};",
        "",
        f"const IQ_THEME_COUNTS = {json.dumps(dict(theme_counts.most_common()), ensure_ascii=False)};",
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(js_lines), encoding="utf-8")

    elapsed = time.time() - t0
    return {
        "startups":  len(st_list),
        "investors": len(inv_list),
        "entities":  len(all_entities),
        "vec_shape": list(vecs.shape),
        "out":       str(out_path),
        "elapsed":   round(elapsed, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  2. SEMANTIC SEARCH  (CLI / API)
# ─────────────────────────────────────────────────────────────────────────────

def semantic_search(
    query: str,
    top_k: int = 10,
    filters: dict | None = None,
    db_path: Path = DB_PATH,
    as_json: bool = False,
) -> list[dict]:
    """Semantic search over startup embeddings.

    Args:
        query:   free-text query (Spanish, English, or Portuguese)
        top_k:   number of results
        filters: dict with optional keys: theme, country, stage, funded (bool)
        as_json: if True, print JSON to stdout instead of returning
    """
    import os
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    from sentence_transformers import SentenceTransformer

    conn = sqlite3.connect(db_path)
    startups = _load_startup_meta(conn)
    _enrich_with_investors(conn, startups)
    conn.close()

    vecs, vec_ids = _load_vectors()
    idx = _vec_index(vec_ids)

    # Encode query — e5 convention: "query: <text>"
    model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    q_vec = model.encode(
        [f"query: {query}"],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0].astype(np.float32)

    # Score all startups
    results = []
    f = filters or {}
    for sid in vec_ids:
        if sid not in startups:
            continue
        st = startups[sid]

        # Apply filters
        if f.get("theme") and f["theme"].lower() not in st["theme"].lower():
            continue
        if f.get("country") and f["country"].upper() != st["country"]:
            continue
        if f.get("stage") and f.get("stage") != st["stage"]:
            continue
        if "funded" in f and bool(f["funded"]) != st["funded"]:
            continue

        score = float(np.dot(q_vec, vecs[idx[sid]]))
        results.append({
            "rank":     0,
            "score":    round(score, 4),
            "id":       sid,
            "name":     st["name"],
            "country":  st["country"],
            "theme":    st["theme"],
            "quality":  st["quality"],
            "stage":    st["stage"],
            "funded":   st["funded"],
            "investors": st["investors"],
            "one_liner": st["one_liner"],
        })

    results.sort(key=lambda x: -x["score"])
    # Rescale on a wider pool so scores spread meaningfully (0.10–0.95)
    rescale_pool = results[: top_k * 4]
    rescale_pool = _rescale_scores(rescale_pool)
    results = rescale_pool[:top_k]
    for i, r in enumerate(results):
        r["rank"] = i + 1

    if as_json:
        print(json.dumps(results, ensure_ascii=False))
    return results


# ─────────────────────────────────────────────────────────────────────────────
#  3. LATENT POTENTIAL  (CLI / API)
# ─────────────────────────────────────────────────────────────────────────────

def latent_potential(
    entity_id: str,
    top_k: int = 15,
    db_path: Path = DB_PATH,
    as_json: bool = False,
) -> dict:
    """Find high-potential pairs that don't yet have an edge.

    For investors: returns startups with strong portfolio fit.
    For startups:  returns investors likely to be interested.
    """
    conn = sqlite3.connect(db_path)
    startups = _load_startup_meta(conn)
    _enrich_with_investors(conn, startups)
    investors = _load_investor_meta(conn)
    orgs = _load_org_meta(conn)
    # Load existing startup→org support edges to exclude already-connected pairs
    existing_org_edges: dict[str, set[str]] = {}  # org_id → set of startup_ids
    try:
        for r in conn.execute(
            "SELECT startup_id, org_id FROM startup_org_edges"
        ).fetchall():
            existing_org_edges.setdefault(r[1], set()).add(r[0])
    except Exception:
        pass
    conn.close()

    vecs, vec_ids = _load_vectors()
    idx = _vec_index(vec_ids)

    result = {"entity_id": entity_id, "entity_type": None, "matches": []}

    # ── Investor perspective ──────────────────────────────────────────────
    if entity_id in investors:
        inv = investors[entity_id]
        result["entity_type"] = "investor"
        result["entity_name"] = inv["name"]
        prof = _build_portfolio_profile(inv, startups, vecs, idx)
        result["portfolio_size"] = prof["size"]
        result["portfolio_themes"] = sorted(prof["themes"])
        result["portfolio_countries"] = sorted(prof["countries"])

        raw_candidates = []
        for sid, st in startups.items():
            if sid in prof["mapped"]:
                continue
            detail = _score_pair(st, prof, inv, vecs, idx, return_details=True)
            if detail["score"] < 0.05:
                continue
            raw_candidates.append({
                "id":      sid,
                "name":    st["name"],
                "country": st["country"],
                "theme":   st["theme"],
                "quality": st["quality"],
                "stage":   st["stage"],
                "funded":  st["funded"],
                "investors": st["investors"],
                "score":   detail["score"],
                "reasons": detail["reasons"],
            })

        raw_candidates.sort(key=lambda x: -x["score"])
        raw_candidates = raw_candidates[:top_k * 3]  # rescale on broader pool
        raw_candidates = _rescale_scores(raw_candidates)
        result["matches"] = raw_candidates[:top_k]

    # ── Startup perspective ───────────────────────────────────────────────
    elif entity_id in startups:
        st = startups[entity_id]
        result["entity_type"] = "startup"
        result["entity_name"] = st["name"]
        result["theme"] = st["theme"]
        result["country"] = st["country"]

        raw_candidates = []
        for iid, inv in investors.items():
            if entity_id in inv["portfolio"]:
                continue
            prof = _build_portfolio_profile(inv, startups, vecs, idx)
            if prof["size"] == 0:
                continue
            detail = _score_pair(st, prof, inv, vecs, idx, return_details=True)
            if detail["score"] < 0.05:
                continue
            raw_candidates.append({
                "id":      iid,
                "name":    inv["name"],
                "country": inv["country"],
                "itype":   inv["itype"],
                "portfolio_size": prof["size"],
                "themes":  sorted(prof["themes"])[:4],
                "score":   detail["score"],
                "reasons": detail["reasons"],
            })

        raw_candidates.sort(key=lambda x: -x["score"])
        raw_candidates = raw_candidates[:top_k * 3]
        raw_candidates = _rescale_scores(raw_candidates)
        result["matches"] = raw_candidates[:top_k]

    # ── Org / ESO / Corporate perspective ────────────────────────────────
    elif entity_id in orgs:
        org = orgs[entity_id]
        result["entity_type"] = org["entity_subtype"]
        result["entity_name"] = org["name"]
        result["focus_text"] = org["focus_text"]
        result["country"] = org["country"]

        already_connected = existing_org_edges.get(entity_id, set())
        geo_focus = org.get("geo_focus", "").lower()

        raw_candidates = []
        for sid, st in startups.items():
            if sid in already_connected:
                continue
            if not st["theme"]:
                continue

            # Theme overlap with org's focus text
            th_score = _org_theme_overlap(st["theme"], org["focus_text"])
            if th_score == 0.0:
                # Try secondary theme
                th_score = _org_theme_overlap(st.get("theme2", ""), org["focus_text"]) * 0.7

            # Country / geography
            co_score = 0.0
            if st["country"] and st["country"] == org["country"]:
                co_score = 1.0
            elif geo_focus and st["country"] and st["country"].lower() in geo_focus:
                co_score = 0.8
            elif geo_focus and "latam" in geo_focus:
                co_score = 0.3

            # Quality bonus for ESOs (prefer early-stage high-quality candidates)
            quality_bonus = st["quality"] / 100.0  # 0–0.10 range
            if org["entity_subtype"] == "eso" and st["stage"] in ("pre-seed", "seed", ""):
                quality_bonus += 0.05

            raw_score = 0.60 * th_score + 0.30 * co_score + 0.10 * quality_bonus
            if raw_score < 0.05:
                continue

            reasons = []
            if co_score == 1.0:
                reasons.append(f"geographic_match:{st['country']}")
            elif co_score > 0:
                reasons.append(f"geo_focus_match:{st['country']}")
            if th_score >= 0.65:
                reasons.append(f"theme_strong:{st['theme']}")
            elif th_score > 0:
                reasons.append(f"theme_partial:{st['theme']}")
            if st["quality"] >= 7.0:
                reasons.append(f"high_quality:{st['quality']}")

            raw_candidates.append({
                "id":       sid,
                "name":     st["name"],
                "country":  st["country"],
                "theme":    st["theme"],
                "quality":  st["quality"],
                "stage":    st["stage"],
                "funded":   st["funded"],
                "score":    raw_score,
                "reasons":  reasons,
            })

        raw_candidates.sort(key=lambda x: -x["score"])
        raw_candidates = raw_candidates[:top_k * 3]
        raw_candidates = _rescale_scores(raw_candidates)
        result["matches"] = raw_candidates[:top_k]

    else:
        result["error"] = (
            f"Entity '{entity_id}' not found in startups, investors, "
            f"or ecosystem organizations. "
            f"Check: python pipeline.py status"
        )

    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  CLI entry (via pipeline.py)
# ─────────────────────────────────────────────────────────────────────────────

def _print_search_results(results: list[dict], query: str) -> None:
    print(f"\n  Busqueda semantica: \"{query}\"")
    print(f"  Modelo: intfloat/multilingual-e5-small\n")
    print(f"  {'#':<3}  {'Score':<7}  {'Startup':<32}  {'Pais':<5}  {'Tema':<34}  {'Calidad':<8}  Inversores")
    print("  " + "-" * 115)
    for r in results:
        inv_str = ", ".join(r["investors"][:2]) + ("..." if len(r["investors"]) > 2 else "") if r["investors"] else "—"
        theme_short = r["theme"][:32] if r["theme"] else "—"
        print(f"  {r['rank']:<3}  {r['score']:<7.4f}  {r['name']:<32}  {r['country']:<5}  {theme_short:<34}  {r['quality']:<8}  {inv_str}")
    print()


def _print_latent(result: dict) -> None:
    if "error" in result:
        print(f"\n  [ERROR] {result['error']}\n")
        return

    etype = result.get("entity_type", "?")
    ename = result.get("entity_name", result["entity_id"])

    if etype == "investor":
        print(f"\n  Potencial Latente: {ename} (inversor)")
        print(f"  Portfolio actual: {result['portfolio_size']} startups")
        print(f"  Temas: {', '.join(result['portfolio_themes'][:5])}")
        print(f"  Paises activos: {', '.join(result['portfolio_countries'][:5])}")
        print(f"\n  Top startups no mapeadas con mayor fit:\n")
        print(f"  {'#':<3}  {'Score':<7}  {'Startup':<32}  {'Pais':<5}  {'Tema':<30}  {'Razones'}")
        print("  " + "-" * 105)
        for i, m in enumerate(result["matches"], 1):
            print(f"  {i:<3}  {m['score']:<7.3f}  {m['name']:<32}  {m['country']:<5}  {(m['theme'] or '—')[:30]:<30}  {', '.join(m['reasons'])}")

    elif etype == "startup":
        print(f"\n  Potencial Latente: {ename} (startup)")
        print(f"  Tema: {result.get('theme', '—')}  |  Pais: {result.get('country', '—')}")
        print(f"\n  Inversores con mayor fit del portfolio:\n")
        print(f"  {'#':<3}  {'Score':<7}  {'Inversor':<32}  {'Pais':<5}  {'Tipo':<22}  {'Portfolio':<10}  Razones")
        print("  " + "-" * 115)
        for i, m in enumerate(result["matches"], 1):
            reasons_str = ", ".join(m.get("reasons", []))
            print(f"  {i:<3}  {m['score']:<7.3f}  {m['name']:<32}  {m['country']:<5}  {m['itype'][:22]:<22}  {m['portfolio_size']:<10}  {reasons_str}")

    elif etype in ("organization", "eso", "corporate"):
        type_labels = {"organization": "gremial/org", "eso": "ESO", "corporate": "corporate"}
        print(f"\n  Potencial Latente: {ename} ({type_labels.get(etype, etype)})")
        print(f"  Pais: {result.get('country', '—')}  |  Foco: {(result.get('focus_text','') or '')[:60]}")
        print(f"\n  Startups con mayor alineamiento tematico/geografico:\n")
        print(f"  {'#':<3}  {'Score':<7}  {'Startup':<32}  {'Pais':<5}  {'Tema':<30}  {'Cal.':<6}  Razones")
        print("  " + "-" * 110)
        for i, m in enumerate(result["matches"], 1):
            reasons_str = ", ".join(m.get("reasons", []))
            print(f"  {i:<3}  {m['score']:<7.3f}  {m['name']:<32}  {m['country']:<5}  {(m['theme'] or '—')[:30]:<30}  {m['quality']:<6}  {reasons_str}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  4. CALIBRATION AUDIT
# ─────────────────────────────────────────────────────────────────────────────

_PORTFOLIO_BUCKETS = [
    ("2-5", 2, 5),
    ("6-15", 6, 15),
    ("16-40", 16, 40),
    (">40", 41, None),
]


def _portfolio_bucket(size: int) -> str:
    for label, lo, hi in _PORTFOLIO_BUCKETS:
        if size >= lo and (hi is None or size <= hi):
            return label
    return "<2"


def _calibration_audit(db_path: Path = DB_PATH) -> dict:
    """Self-test: for each investor, verify their own portfolio startups
    rank highly among all candidates.

    For each investor with portfolio_size >= 3, scores their actual portfolio
    startups against all include startups, then checks what rank each portfolio
    startup achieves. Outputs precision@k and mean_rank, overall and broken
    down by portfolio-size bucket (2-5, 6-15, 16-40, >40) so improvements can
    be measured where they matter — large funds, not the trivially-easy
    3-4-startup portfolios.
    """
    conn = sqlite3.connect(db_path)
    startups = _load_startup_meta(conn)
    _enrich_with_investors(conn, startups)
    investors = _load_investor_meta(conn)
    conn.close()

    vecs, vec_ids = _load_vectors()
    idx = _vec_index(vec_ids)

    # Only investors with >= 3 mapped portfolio startups in the include set
    qualified = {
        iid: inv for iid, inv in investors.items()
        if sum(1 for s in inv["portfolio"] if s in startups) >= 3
    }

    total_portfolio_startups = 0
    sum_rank = 0
    top3 = top5 = top10 = 0
    per_investor = []
    bucket_stats: dict[str, dict] = {}

    for iid, inv in qualified.items():
        prof = _build_portfolio_profile(inv, startups, vecs, idx)
        mapped_in_include = [s for s in inv["portfolio"] if s in startups]

        # Score ALL include startups (both portfolio and non-portfolio)
        all_scores = []
        for sid, st in startups.items():
            detail = _score_pair(st, prof, inv, vecs, idx, return_details=True)
            all_scores.append((sid, detail["score"]))
        all_scores.sort(key=lambda x: -x[1])
        rank_map = {sid: i + 1 for i, (sid, _) in enumerate(all_scores)}

        ranks = [rank_map.get(s, len(startups)) for s in mapped_in_include]
        bucket = _portfolio_bucket(prof["size"])
        bstat = bucket_stats.setdefault(bucket, {
            "investors": 0, "portfolio_startups_scored": 0,
            "sum_rank": 0, "top3": 0, "top5": 0, "top10": 0,
        })
        bstat["investors"] += 1
        for r in ranks:
            sum_rank += r
            total_portfolio_startups += 1
            bstat["sum_rank"] += r
            bstat["portfolio_startups_scored"] += 1
            if r <= 3:  top3 += 1; bstat["top3"] += 1
            if r <= 5:  top5 += 1; bstat["top5"] += 1
            if r <= 10: top10 += 1; bstat["top10"] += 1

        inv_prec5 = sum(1 for r in ranks if r <= 5) / len(ranks)
        per_investor.append({
            "investor_id":    iid,
            "investor_name":  inv["name"],
            "portfolio_size": prof["size"],
            "precision@5":    round(inv_prec5, 3),
            "mean_rank":      round(sum(ranks) / len(ranks), 1),
        })

    per_investor.sort(key=lambda x: x["precision@5"])

    if total_portfolio_startups == 0:
        return {"error": "No qualified investors found."}

    by_bucket = {}
    for label, _, _ in _PORTFOLIO_BUCKETS:
        b = bucket_stats.get(label)
        if not b or b["portfolio_startups_scored"] == 0:
            continue
        n = b["portfolio_startups_scored"]
        by_bucket[label] = {
            "investors":     b["investors"],
            "portfolio_startups_scored": n,
            "precision@3":   round(b["top3"] / n, 3),
            "precision@5":   round(b["top5"] / n, 3),
            "precision@10":  round(b["top10"] / n, 3),
            "mean_rank":     round(b["sum_rank"] / n, 1),
        }

    report = {
        "investors_evaluated": len(qualified),
        "portfolio_startups_scored": total_portfolio_startups,
        "precision@3":  round(top3  / total_portfolio_startups, 3),
        "precision@5":  round(top5  / total_portfolio_startups, 3),
        "precision@10": round(top10 / total_portfolio_startups, 3),
        "mean_rank":    round(sum_rank / total_portfolio_startups, 1),
        "by_portfolio_size_bucket": by_bucket,
        "worst_investors": per_investor[:5],
        "best_investors":  per_investor[-5:],
    }
    return report


# ── Ecosystem Health Data ─────────────────────────────────────────────────────

HEALTH_OUT_PATH = ROOT / "pilot" / "ecosystem-health-data.js"

_ALL_THEMES = [
    "Bioinputs & Crop Resilience",
    "Precision Agriculture",
    "Nature & Ecosystem Tech",
    "Food Systems & Alt Proteins",
    "Biomanufacturing & Platform Technologies",
    "Biomaterials & Green Chemistry",
    "Therapeutics",
    "Diagnostics & Devices",
]

_TOP_COUNTRIES = ["BR", "AR", "MX", "CL", "CO", "PE"]


def build_ecosystem_health_data(
    db_path: Path = DB_PATH,
    out_path: Path = HEALTH_OUT_PATH,
) -> dict:
    """Generate pilot/ecosystem-health-data.js for the Salud dashboard tab.

    Exports:
      IQ_WHITESPACE   — 8 themes × top countries, with startup_count / funded_count / avg_quality
      IQ_THEME_DEPTH  — per-theme summary: counts, funded_pct, avg_quality, top_investor, top_startup
      IQ_ISOLATED     — startups with quality >= 5.0 and 0 investment_edges, sorted by quality
      IQ_MOMENTUM     — investment_edges grouped by announced_date month+theme (last 18 months)
      IQ_HEALTH_META  — generated_at, total_startups, total_funded
    """
    t0 = time.time()
    conn = sqlite3.connect(db_path)

    # ── Load all include startups ─────────────────────────────────────────
    rows = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code,
               sx.bio_theme_primary, sx.data_quality_score, sx.funding_stage,
               sx.business_one_liner
        FROM entities e
        JOIN startup_extended sx ON sx.startup_id = e.entity_id
        WHERE sx.scope_decision = 'include'
    """).fetchall()

    startups: list[dict] = []
    for r in rows:
        startups.append({
            "id":      r[0],
            "name":    r[1] or r[0],
            "country": (r[2] or "").upper(),
            "theme":   r[3] or "",
            "quality": round(float(r[4] or 0), 1),
            "stage":   r[5] or "",
            "one_liner": r[6] or "",
        })

    # ── Determine funded startups ─────────────────────────────────────────
    funded_ids: set[str] = set()
    inv_per_startup: dict[str, list[str]] = {}
    for row in conn.execute(
        "SELECT startup_id, investor_id FROM investment_edges"
    ).fetchall():
        funded_ids.add(row[0])
        inv_per_startup.setdefault(row[0], []).append(row[1])

    for s in startups:
        s["funded"] = s["id"] in funded_ids
        s["investors"] = inv_per_startup.get(s["id"], [])

    # ── IQ_WHITESPACE: theme × country heatmap ────────────────────────────
    whitespace: list[dict] = []
    # all countries seen (to add any beyond top-6)
    all_countries = sorted({s["country"] for s in startups if s["country"]})
    display_countries = _TOP_COUNTRIES + [c for c in all_countries if c not in _TOP_COUNTRIES]

    for theme in _ALL_THEMES:
        theme_startups = [s for s in startups if s["theme"] == theme]
        for country in display_countries:
            cell = [s for s in theme_startups if s["country"] == country]
            if not cell and country not in _TOP_COUNTRIES:
                continue
            funded_count = sum(1 for s in cell if s["funded"])
            avg_q = round(sum(s["quality"] for s in cell) / len(cell), 1) if cell else 0.0
            whitespace.append({
                "theme":   theme,
                "country": country,
                "total":   len(cell),
                "funded":  funded_count,
                "avg_quality": avg_q,
                "coverage_pct": round(funded_count / len(cell) * 100, 0) if cell else 0,
                "startup_ids": [s["id"] for s in sorted(cell, key=lambda x: -x["quality"])[:5]],
            })

    # ── IQ_THEME_DEPTH: per-theme summary ─────────────────────────────────
    theme_depth: list[dict] = []
    for theme in _ALL_THEMES:
        ts = [s for s in startups if s["theme"] == theme]
        funded_c = sum(1 for s in ts if s["funded"])
        avg_q = round(sum(s["quality"] for s in ts) / len(ts), 1) if ts else 0.0

        # Top investor by portfolio count in this theme
        inv_counts: dict[str, int] = {}
        for s in ts:
            for inv in s["investors"]:
                inv_counts[inv] = inv_counts.get(inv, 0) + 1
        top_investor = max(inv_counts, key=lambda k: inv_counts[k]) if inv_counts else None

        # Top startup by quality
        top_st = max(ts, key=lambda s: s["quality"]) if ts else None

        theme_depth.append({
            "theme":        theme,
            "startup_count": len(ts),
            "funded_count": funded_c,
            "unfunded_count": len(ts) - funded_c,
            "funded_pct":   round(funded_c / len(ts) * 100, 0) if ts else 0,
            "avg_quality":  avg_q,
            "top_investor": top_investor,
            "top_startup":  top_st["name"] if top_st else None,
            "top_startup_id": top_st["id"] if top_st else None,
        })

    # ── IQ_ISOLATED: unfunded high-quality startups ────────────────────────
    isolated = [s for s in startups if not s["funded"] and s["quality"] >= 5.0]
    isolated.sort(key=lambda s: -s["quality"])
    isolated_out = [
        {
            "id":       s["id"],
            "name":     s["name"],
            "country":  s["country"],
            "theme":    s["theme"],
            "quality":  s["quality"],
            "stage":    s["stage"],
            "one_liner": s["one_liner"][:120] if s["one_liner"] else "",
        }
        for s in isolated[:30]
    ]

    # ── IQ_MOMENTUM: investment activity by month+theme ───────────────────
    momentum_raw = conn.execute("""
        SELECT ie.announced_date, sx.bio_theme_primary, COUNT(*) as cnt
        FROM investment_edges ie
        JOIN startup_extended sx ON sx.startup_id = ie.startup_id
        WHERE ie.announced_date IS NOT NULL AND ie.announced_date != ''
          AND sx.scope_decision = 'include'
        GROUP BY substr(ie.announced_date, 1, 7), sx.bio_theme_primary
        ORDER BY ie.announced_date DESC
    """).fetchall()

    momentum: list[dict] = []
    seen_months: set[str] = set()
    for row in momentum_raw:
        month = (row[0] or "")[:7]  # "YYYY-MM"
        if not month or len(month) < 7:
            continue
        seen_months.add(month)
        momentum.append({
            "month": month,
            "theme": row[1] or "Unknown",
            "count": row[2],
        })
    # Limit to last 18 months
    sorted_months = sorted(seen_months, reverse=True)[:18]
    momentum = [m for m in momentum if m["month"] in sorted_months]
    momentum.sort(key=lambda x: x["month"])

    conn.close()

    # ── Assemble metadata ─────────────────────────────────────────────────
    import datetime
    total_funded = len(funded_ids & {s["id"] for s in startups})
    health_meta = {
        "generated_at": datetime.datetime.now().isoformat()[:16],
        "total_startups": len(startups),
        "total_funded": total_funded,
        "funded_pct": round(total_funded / len(startups) * 100, 1) if startups else 0,
        "themes": _ALL_THEMES,
        "countries": _TOP_COUNTRIES,
    }

    # ── Write JS output ───────────────────────────────────────────────────
    lines = [
        "// ecosystem-health-data.js — generated by pipeline.py ecosystem-health-data",
        f"// {health_meta['generated_at']} · {len(startups)} startups · {total_funded} funded",
        "",
        f"const IQ_HEALTH_META = {json.dumps(health_meta, ensure_ascii=False)};",
        "",
        f"const IQ_WHITESPACE = {json.dumps(whitespace, ensure_ascii=False)};",
        "",
        f"const IQ_THEME_DEPTH = {json.dumps(theme_depth, ensure_ascii=False)};",
        "",
        f"const IQ_ISOLATED = {json.dumps(isolated_out, ensure_ascii=False)};",
        "",
        f"const IQ_MOMENTUM = {json.dumps(momentum, ensure_ascii=False)};",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")

    elapsed = round(time.time() - t0, 2)
    return {
        "startups": len(startups),
        "funded": total_funded,
        "whitespace_cells": len(whitespace),
        "isolated": len(isolated_out),
        "momentum_rows": len(momentum),
        "elapsed": elapsed,
    }
