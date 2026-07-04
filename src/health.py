"""
src/health.py — Semáforo de salud del sistema en una pantalla.

Responde "¿puedo confiar en el sistema hoy?" en 5 segundos. No reemplaza a
`validate` (que es el gate de integridad): esto es la lectura ejecutiva de
volumen, evidencia, consistencia, frescura, cobertura y matchmaker, con
umbrales documentados y un veredicto por línea.

Verde  (OK)   — dentro del umbral sano.
Ámbar  (WARN) — degradado: usable pero con nota.
Rojo   (BAD)  — no confiar en los productos que dependen de esta señal.
"""
from __future__ import annotations

import json
import pathlib
import re
import sqlite3
from datetime import datetime, timezone

from src.utils import load_csv

ROOT = pathlib.Path(__file__).resolve().parent.parent

GREEN, AMBER, RED = "OK ", "WARN", "BAD "


def _verdict(value: float, ok: float, warn: float, higher_is_better: bool = True) -> str:
    """Umbral de dos escalones. ok/warn en la misma unidad que value."""
    if higher_is_better:
        if value >= ok:
            return GREEN
        return AMBER if value >= warn else RED
    if value <= ok:
        return GREEN
    return AMBER if value <= warn else RED


def _line(verdict: str, label: str, detail: str) -> None:
    icon = {GREEN: "+", AMBER: "!", RED: "X"}[verdict]
    print(f"  {icon} [{verdict.strip():<4}] {label:<46} {detail}")


def _find_zombie_pages(root: pathlib.Path, db_mtime: float) -> list[str]:
    """Pages linked from pilot/index.html that serve a *-data.js bundle more
    than 30 days older than the DB, without a `<!-- LEGACY-FROZEN -->` marker
    telling the reader the data is a frozen snapshot on purpose."""
    index_html = root / "pilot" / "index.html"
    if not index_html.exists():
        return []
    index_text = index_html.read_text(encoding="utf-8", errors="replace")
    linked_pages = sorted(set(re.findall(r'href="\./([\w.-]+\.html)"', index_text)))
    warnings: list[str] = []
    for page_name in linked_pages:
        page_path = root / "pilot" / page_name
        if not page_path.exists():
            continue
        page_text = page_path.read_text(encoding="utf-8", errors="replace")
        if "<!-- LEGACY-FROZEN -->" in page_text:
            continue
        for bundle_name in re.findall(r'<script src="\./([\w.-]+-data\.js)', page_text):
            bundle_path = root / "pilot" / bundle_name
            if not bundle_path.exists():
                continue
            age_d = (db_mtime - bundle_path.stat().st_mtime) / 86400
            if age_d > 30:
                warnings.append(f"{page_name}→{bundle_name} ({age_d:.0f}d)")
    return warnings


def run(db_path: pathlib.Path) -> None:
    conn = sqlite3.connect(db_path)
    q1 = lambda s: conn.execute(s).fetchone()[0]

    print(f"\n  SALUD DEL SISTEMA — {db_path.name} — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("  " + "─" * 76)

    # ── Volumen ──────────────────────────────────────────────────────────
    n_inc = q1("SELECT count(*) FROM startup_extended WHERE scope_decision='include'")
    n_inv = q1("SELECT count(*) FROM investors")
    n_edges = q1("SELECT count(*) FROM investment_edges")
    n_outcomes = q1("SELECT count(*) FROM outcomes")
    print("\n  Volumen")
    _line(GREEN, "Startups include", str(n_inc))
    _line(GREEN, "Inversores / edges de inversión", f"{n_inv} / {n_edges}")
    _line(_verdict(n_outcomes, 60, 20), "Outcomes registrados", f"{n_outcomes} (meta ≥60: sin outcomes no hay ground truth)")

    # ── Evidencia ────────────────────────────────────────────────────────
    print("\n  Evidencia")
    pct_src = q1("SELECT avg(source_id IS NOT NULL) FROM investment_edges") or 0
    pct_date = q1("SELECT avg(announced_date IS NOT NULL AND announced_date<>'') FROM investment_edges") or 0
    pct_amount = q1("SELECT avg(amount IS NOT NULL) FROM investment_edges") or 0
    pct_ext = q1("SELECT avg(scope_basis='external_auditable_source') FROM startup_extended WHERE scope_decision='include'") or 0
    pct_thesis = q1("SELECT avg(thesis IS NOT NULL AND thesis<>'') FROM investors") or 0
    _line(_verdict(pct_src, 0.80, 0.60), "Edges con fuente", f"{pct_src:.0%}")
    _line(_verdict(pct_date, 0.60, 0.30), "Edges con fecha", f"{pct_date:.0%} (sin fecha no hay cohortes ni tendencia)")
    _line(_verdict(pct_amount, 0.30, 0.15), "Edges con monto", f"{pct_amount:.0%} (sin monto no hay magnitud)")
    _line(_verdict(pct_ext, 0.70, 0.50), "Includes con fuente externa auditable", f"{pct_ext:.0%}")
    _line(_verdict(pct_thesis, 0.85, 0.60), "Inversores con tesis", f"{pct_thesis:.0%}")

    # ── Consistencia ─────────────────────────────────────────────────────
    print("\n  Consistencia")
    # Métrica refinada: solo los conflictos GENUINOS (aislados) cuentan; los
    # sub-clusters coherentes y temas transversales son esperados. Misma fuente
    # de verdad que `validate` y `reconcile-themes`.
    from src.reconcile_themes import analyze as _analyze_conflicts
    _triage = _analyze_conflicts(conn)
    n_mm = sum(1 for t in _triage if t["verdict"] == "isolated_review")
    n_expected = len(_triage) - n_mm
    n_orphans = q1(
        "SELECT count(*) FROM entities WHERE entity_type='startup' "
        "AND NOT EXISTS (SELECT 1 FROM startup_extended sx WHERE sx.startup_id=entity_id)"
    )
    n_missing_core = q1(
        "SELECT count(*) FROM startup_extended sx WHERE sx.scope_decision='include' "
        "AND NOT EXISTS (SELECT 1 FROM startups s WHERE s.startup_id=sx.startup_id)"
    )
    _line(_verdict(n_mm, 25, 60, higher_is_better=False), "Conflictos theme↔cluster aislados", f"{n_mm} genuinos (+{n_expected} sub-cluster esperados; meta <25)")
    _line(_verdict(n_orphans, 15, 40, higher_is_better=False), "Orphan entities (sin startup_extended)", str(n_orphans))
    _line(_verdict(n_missing_core, 0, 50, higher_is_better=False), "Includes sin fila en tabla startups", f"{n_missing_core} (gap de schema: el universo vive solo en startup_extended)")

    # ── Frescura ─────────────────────────────────────────────────────────
    print("\n  Frescura")
    last_audit = conn.execute("SELECT max(timestamp) FROM audit_log").fetchone()[0] or ""
    db_mtime = db_path.stat().st_mtime
    emb_dir = ROOT / "embeddings"
    emb_files = list(emb_dir.glob("*.npy")) if emb_dir.exists() else []
    if emb_files:
        emb_age_d = (db_mtime - max(f.stat().st_mtime for f in emb_files)) / 86400
        _line(_verdict(max(emb_age_d, 0), 7, 30, higher_is_better=False),
              "Embeddings vs DB", f"{max(emb_age_d, 0):.0f} día(s) más viejos que la DB")
    else:
        _line(RED, "Embeddings", "no existen — correr rebuild --phase embeddings")
    # Solo los bundles generados por el pipeline Python actual
    PIPELINE_BUNDLES = {
        "capital-atlas-data.js",
        "ecosystem-graph-data.js",
        "ecosystem-health-data.js",
        "capital-structure-data.js",
        "coverage-data.js",
        "phylo-tree-data.js",
        "startup-themes-data.js",
        "intelligence-data.js",
        "ecosystem-diagnostics-data.js",
    }
    data_js = [ROOT / "pilot" / name for name in PIPELINE_BUNDLES if (ROOT / "pilot" / name).exists()]
    if data_js:
        stale = [f.name for f in data_js if (db_mtime - f.stat().st_mtime) / 86400 > 7]
        _line(_verdict(len(stale), 0, 2, higher_is_better=False),
              "Bundles JS desactualizados (>7d vs DB)", f"{len(stale)}" + (f" — {', '.join(stale[:4])}…" if stale else ""))
    _line(GREEN, "Última entrada de audit_log", last_audit[:16] or "(vacío)")
    zombies = _find_zombie_pages(ROOT, db_mtime)
    if zombies:
        _line(AMBER, "Páginas con bundle >30d sin marca legacy", f"{len(zombies)} — {', '.join(zombies[:4])}" + ("…" if len(zombies) > 4 else ""))
    else:
        _line(GREEN, "Páginas con bundle >30d sin marca legacy", "0")

    # ── Matchmaker ───────────────────────────────────────────────────────
    print("\n  Matchmaker")
    calib_path = ROOT / "quality" / "score_calibration.json"
    if calib_path.exists():
        calib = json.loads(calib_path.read_text(encoding="utf-8"))
        p5 = calib.get("precision@5", 0)
        _line(_verdict(p5, 0.30, 0.15), "precision@5 (calibrate-scores)", f"{p5:.3f} (meta ≥0.30)")
    else:
        _line(AMBER, "Calibración", "no existe — correr calibrate-scores")

    # ── Cobertura (Frente A) ─────────────────────────────────────────────
    print("\n  Cobertura")
    matrix = load_csv(ROOT / "quality" / "coverage_matrix.csv")
    if matrix:
        counts: dict[str, int] = {}
        for row in matrix:
            counts[row["coverage_label"]] = counts.get(row["coverage_label"], 0) + 1
        latam = [r for r in matrix if r["coverage_label"] != "fuera_de_foco"]
        n_ok = counts.get("bien_mapeado", 0)
        pct_ok = n_ok / len(latam) if latam else 0
        under = sorted({r["country"] for r in matrix if r["country_tier"] == "under_explored"})
        _line(_verdict(pct_ok, 0.40, 0.15), "Celdas LATAM bien mapeadas",
              f"{n_ok}/{len(latam)} ({pct_ok:.0%}) — " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        _line(_verdict(len(under), 4, 8, higher_is_better=False),
              "Países LATAM under_explored", f"{len(under)} — {', '.join(under)}")
    else:
        _line(AMBER, "Matriz de cobertura", "no existe — correr coverage")

    print("\n  " + "─" * 76)
    print("  Gate de integridad estricto: `python pipeline.py validate`")
    print("  Detalle de cobertura y sesgo: `python pipeline.py coverage`\n")
    conn.close()
