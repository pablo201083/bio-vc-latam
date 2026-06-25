"""
scripts/build_quality_queue.py — Genera quality/semantic_quality_queue.csv desde la DB.

Reemplaza al script JS legacy (que dependía de archivos no mantenidos).
Lee startup_extended + entities, calcula un risk score por startup, y exporta
los candidatos ordenados por riesgo DESC.

Criterios de riesgo (acumulativos):
  +35  summary_en ausente o < 20 palabras
  +25  cluster_confidence < 0.30 (baja confianza semántica)
  +18  cluster_confidence 0.30-0.59 (confianza media)
  +20  summary_v1 en español (heurística: mayoría de tokens no-ASCII o palabras ES)
  +15  summary < 30 palabras (muy corto)
  +10  business_one_liner ausente
  + 5  macro_theme ausente

Uso:
    python scripts/build_quality_queue.py           # todos los include
    python scripts/build_quality_queue.py --top 100 # solo los 100 de mayor riesgo
    python scripts/build_quality_queue.py --min-risk 10  # solo risk >= 10
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
OUT_CSV = ROOT / "quality" / "semantic_quality_queue.csv"

# Simple Spanish word heuristic
_ES_WORDS = {
    "de", "la", "el", "en", "y", "del", "las", "los", "una", "con", "para",
    "que", "se", "es", "su", "por", "al", "un", "son", "este", "esta",
    "pero", "hay", "como", "más", "también", "ha", "han", "fue", "ser",
    "lo", "le", "sus", "no", "si", "ya", "o", "a", "e", "u",
}


def _word_count(text: str) -> int:
    return len(re.findall(r"\w+", text or ""))


def _is_spanish(text: str) -> bool:
    """Heuristic: > 20% of tokens are common Spanish words."""
    if not text:
        return False
    tokens = re.findall(r"[a-záéíóúüñ]+", text.lower())
    if not tokens:
        return False
    es_count = sum(1 for t in tokens if t in _ES_WORDS)
    return es_count / len(tokens) > 0.20


def _risk_score(row: dict) -> tuple[int, list[str]]:
    risk = 0
    reasons: list[str] = []

    summary_en = (row.get("startup_summary_en") or "").strip()
    summary_v1 = (row.get("startup_summary_v1") or "").strip()
    wc_en = _word_count(summary_en)
    wc_v1 = _word_count(summary_v1)
    conf = float(row.get("cluster_confidence") or 0)

    if not summary_en or wc_en < 20:
        risk += 35
        reasons.append("missing_or_thin_summary_en")

    if conf < 0.30:
        risk += 25
        reasons.append("low_cluster_confidence")
    elif conf < 0.60:
        risk += 18
        reasons.append("medium_cluster_confidence")

    if _is_spanish(summary_v1) and not summary_en:
        risk += 20
        reasons.append("summary_in_spanish")

    wc = wc_en if summary_en else wc_v1
    if wc < 30:
        risk += 15
        reasons.append("summary_too_short")

    if not (row.get("business_one_liner") or "").strip():
        risk += 10
        reasons.append("missing_one_liner")

    if not (row.get("macro_theme") or "").strip():
        risk += 5
        reasons.append("missing_macro_theme")

    return risk, reasons


def build_queue(min_risk: int = 0, top: int | None = None) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT sx.startup_id,
               e.canonical_name AS startup_name,
               e.website AS source_url,
               coalesce(sx.startup_summary_en, '') AS startup_summary_en,
               coalesce(sx.startup_summary_v1, '') AS startup_summary_v1,
               coalesce(sx.business_one_liner, '') AS current_one_liner,
               coalesce(sx.macro_theme, '') AS macro_theme,
               coalesce(sx.bio_theme_primary, sx.macro_theme, '') AS current_recommended_theme,
               coalesce(sx.cluster_confidence, 0) AS cluster_confidence,
               coalesce(sx.bio_theme_confidence, '') AS bio_theme_confidence,
               coalesce(sx.review_status, '') AS review_status
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
        ORDER BY sx.cluster_confidence ASC
    """).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        risk, reasons = _risk_score(d)
        if risk < min_risk:
            continue
        results.append({
            "semantic_risk_score": risk,
            "startup_id": d["startup_id"],
            "startup_name": d["startup_name"],
            "current_recommended_theme": d["current_recommended_theme"],
            "recommended_confidence": d["bio_theme_confidence"] or (
                "low" if float(d["cluster_confidence"]) < 0.30 else
                "medium" if float(d["cluster_confidence"]) < 0.60 else "high"
            ),
            "recommended_margin": round(float(d["cluster_confidence"]) * 20, 1),
            "semantic_override": "no",
            "semantic_override_reason": "",
            "source_url": d["source_url"] or "",
            "summary_words": _word_count(d["startup_summary_en"] or d["startup_summary_v1"]),
            "risk_reasons": "; ".join(reasons),
            "recommended_action": (
                "rewrite source-backed English summary and verify cluster/category"
                if risk >= 35 else "review cluster assignment"
            ),
            "current_one_liner": d["current_one_liner"],
            "current_summary": (d["startup_summary_en"] or d["startup_summary_v1"])[:400],
            "review_status": d["review_status"],
        })

    results.sort(key=lambda x: x["semantic_risk_score"], reverse=True)
    if top:
        results = results[:top]
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-risk", type=int, default=0)
    parser.add_argument("--top", type=int, default=None)
    args = parser.parse_args()

    rows = build_queue(min_risk=args.min_risk, top=args.top)

    fieldnames = [
        "semantic_risk_score", "startup_id", "startup_name",
        "current_recommended_theme", "recommended_confidence", "recommended_margin",
        "semantic_override", "semantic_override_reason",
        "source_url", "summary_words", "risk_reasons", "recommended_action",
        "current_one_liner", "current_summary", "review_status",
    ]

    OUT_CSV.parent.mkdir(exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ {len(rows)} startups en quality queue → {OUT_CSV}")
    hi = sum(1 for r in rows if r["semantic_risk_score"] >= 50)
    med = sum(1 for r in rows if 20 <= r["semantic_risk_score"] < 50)
    print(f"  Alto riesgo (≥50): {hi}  |  Medio (20-49): {med}  |  Bajo (<20): {len(rows)-hi-med}")


if __name__ == "__main__":
    main()
