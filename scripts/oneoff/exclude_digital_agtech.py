"""Recorte estratégico: excluir Digital AgTech & Agrifintech del corpus BIO VC LATAM (2026-06-12).

Decisión del curador: la capa digital/financiera del agro (agrifintech, crédito, marketplace,
tokenización, logística, cold-chain) tiene una **dinámica de financiamiento distinta** (deuda/
crédito vs equity biotech) que sesga cualquier lectura del corpus bio. Se saca del universo
`include` vía scope_decision='exclude'. NO se borran los datos — siguen como entidades/filas
excluidas, re-incluibles flipeando scope_decision.

No es un juicio de 'no-bio' (ya eran is_bio_universe=0, eco-adjacent): es un **recorte
estratégico de corpus** por encima del eje de intensidad.
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

DB = ROOT / "db" / "bio_latam.db"
THEME = "Digital AgTech & Agrifintech"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    ids = [r[0] for r in conn.execute(
        "SELECT startup_id FROM startup_extended WHERE bio_theme_primary=? AND scope_decision='include'",
        (THEME,),
    ).fetchall()]
    n = 0
    for sid in ids:
        n += diff_and_log_update(
            conn, "startup_extended", "startup_id", sid,
            {"scope_decision": "exclude"},
            actor="taxonomy/strategic-cut-digital-agtech",
            reason="Recorte estratégico de corpus: Digital AgTech & Agrifintech tiene dinámica de "
                   "financiamiento distinta (deuda/fintech vs equity bio); fuera del default BIO VC LATAM. "
                   "Reversible re-incluyendo.",
        )
    conn.commit()
    remaining = conn.execute(
        "SELECT COUNT(*) FROM startup_extended WHERE scope_decision='include'"
    ).fetchone()[0]
    conn.close()
    print(f"Excluidas: {len(ids)} (campos: {n}). Universo include ahora: {remaining}")


if __name__ == "__main__":
    main()
