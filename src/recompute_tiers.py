"""
Fase pipeline: recompute-tiers
Recalcula valuation_tier en startup_extended desde valuation_estimate_usd.

Breakpoints naturales (sobre distribución de datos reales):
  tier 4  → val >= $200M  (public/unicorn)
  tier 3  → val >= $50M
  tier 2  → val >= $10M
  tier 1.5→ val >= $3M  con ≥1 inversor mapeado  (gridx intermedio)
  tier 1  → resto con val > 0
  None    → sin dato de valuation

Respeta locks manuales: si el último write a valuation_tier en audit_log
fue de un actor humano (actor NOT LIKE 'claude_%' AND actor != 'pipeline'),
no sobreescribe.

Idempotente — safe to re-run.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from src.audit import diff_and_log_update

BREAKS = [
    (200,  "4"),
    (50,   "3"),
    (10,   "2"),
    (3,    "1.5"),   # solo si tiene inversores (chequeado abajo)
    (0,    "1"),
]

def compute_tier(val_usd: float | None, n_investors: int) -> str | None:
    if val_usd is None or val_usd <= 0:
        return None
    if val_usd >= 200:
        return "4"
    if val_usd >= 50:
        return "3"
    if val_usd >= 10:
        return "2"
    if val_usd >= 3 and n_investors >= 1:
        return "1.5"
    return "1"


def _locked_startup_ids(conn: sqlite3.Connection) -> set[str]:
    """Startups donde el último cambio a valuation_tier fue manual."""
    rows = conn.execute("""
        SELECT a.entity_id
        FROM audit_log a
        JOIN (
            SELECT entity_id, MAX(timestamp) AS ts
            FROM audit_log
            WHERE field LIKE '%valuation_tier%'
            GROUP BY entity_id
        ) last ON last.entity_id = a.entity_id AND last.ts = a.timestamp
        WHERE a.field LIKE '%valuation_tier%'
          AND a.actor NOT LIKE 'claude_%'
          AND a.actor NOT LIKE 'pipeline%'
    """).fetchall()
    return {r[0] for r in rows}


def recompute_tiers(db_path: Path = ROOT / "db" / "bio_latam.db") -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    locked = _locked_startup_ids(conn)

    rows = conn.execute("""
        SELECT se.startup_id, se.valuation_estimate_usd, se.valuation_tier,
               COUNT(ie.investment_id) AS n_inv
        FROM startup_extended se
        LEFT JOIN investment_edges ie ON ie.startup_id = se.startup_id
        WHERE se.scope_decision = 'include'
        GROUP BY se.startup_id
    """).fetchall()

    updated = skipped_locked = skipped_same = 0

    for r in rows:
        sid = r["startup_id"]
        if sid in locked:
            skipped_locked += 1
            continue

        new_tier = compute_tier(r["valuation_estimate_usd"], r["n_inv"])
        old_tier = r["valuation_tier"]

        if str(new_tier) == str(old_tier):
            skipped_same += 1
            continue

        diff_and_log_update(
            conn=conn,
            table="startup_extended",
            row_id_col="startup_id",
            row_id=sid,
            new_values={"valuation_tier": new_tier},
            actor="pipeline:recompute_tiers",
            reason=f"auto-tier from val=${r['valuation_estimate_usd']}M, n_inv={r['n_inv']}",
        )
        updated += 1

    conn.commit()
    conn.close()

    result = {
        "updated": updated,
        "skipped_locked": skipped_locked,
        "skipped_same": skipped_same,
        "breaks": {"tier4": ">=200M", "tier3": ">=50M", "tier2": ">=10M",
                   "tier1_5": ">=3M with inv", "tier1": "rest"},
    }
    return result


if __name__ == "__main__":
    r = recompute_tiers()
    print(f"Updated: {r['updated']}  |  Locked (manual): {r['skipped_locked']}  |  Same: {r['skipped_same']}")
