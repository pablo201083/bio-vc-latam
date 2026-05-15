"""
src/merge_clusters.py — post-hoc cluster merge.

Fusiona los N clusters de HDBSCAN en k clusters semánticamente coherentes
sin necesidad de re-embeder. Actualiza startup_extended y regenera el JS.

Merge map (17 → 9):
  new 0  Therapeutics — Regenerative & Cell Medicine       old 0
  new 1  Therapeutics — Drug Discovery & Development       old 8
  new 2  Diagnostics & MedTech                             old 9
  new 3  Ag Biologicals & Bioinputs                        old 4, 12, 13
  new 4  Farm Intelligence & Precision Agriculture         old 11, 14
  new 5  Food Systems & Alt Proteins                       old 5
  new 6  Biomanufacturing & Precision Fermentation         old 1, 10
  new 7  Nature, Climate & Ecosystem Tech                  old 6, 7, 15, 16
  new 8  Biomaterials & Circular Chemistry                 old 2, 3
"""
from __future__ import annotations

import pathlib
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"

# Map: old_cluster_id → new_cluster_id
MERGE_MAP: dict[int, int] = {
    0: 0,   # Therapeutics Regenerative (52)
    8: 1,   # Therapeutics Drug (49)
    9: 2,   # Diagnostics (34)
    4: 3,   # Ag Biologicals
    12: 3,  # Ag Biologicals (merge)
    13: 3,  # Ag Biologicals (merge)
    11: 4,  # Farm Intelligence
    14: 4,  # Farm Intelligence (merge)
    5: 5,   # Food & Alt Proteins (24)
    1: 6,   # Biomanufacturing → Precision Fermentation group
    10: 6,  # Precision Fermentation (merge)
    6: 7,   # Nature & Climate
    7: 7,   # Nature & Climate (merge)
    15: 7,  # Nature & Climate (merge)
    16: 7,  # Nature & Climate (merge)
    2: 8,   # Biomaterials
    3: 8,   # Biomaterials (merge)
}

# Labels for merged clusters: "Display Name||kw1 · kw2 · kw3 · kw4"
MERGED_LABELS: dict[int, str] = {
    0: "Therapeutics — Regenerative & Cell Medicine||regenerative medicine · cell therapy · tissue · gene",
    1: "Therapeutics — Drug Discovery & Development||drug discovery · oncology · therapeutics · small molecule",
    2: "Diagnostics & MedTech||diagnostics · medtech · non-invasive · molecular",
    3: "Ag Biologicals & Bioinputs||biologicals · bioinputs · crop resilience · microbial",
    4: "Farm Intelligence & Precision Agriculture||precision agriculture · agtech · satellite · AI",
    5: "Food Systems & Alt Proteins||food biotech · alt proteins · novel ingredients · functional",
    6: "Biomanufacturing & Precision Fermentation||fermentation · synthetic biology · biomanufacturing · platform",
    7: "Nature, Climate & Ecosystem Tech||climate · nature · environmental · circular economy",
    8: "Biomaterials & Circular Chemistry||biomaterials · biobased · circular · sustainable",
}


def apply_merge(db_path: pathlib.Path = DB_PATH) -> dict:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Build a single atomic CASE statement — avoids cascading updates
    # where sequential UPDATEs chain through intermediate values.
    when_id_clauses = "\n        ".join(
        f"WHEN {old} THEN {new}" for old, new in MERGE_MAP.items()
    )
    when_label_clauses = "\n        ".join(
        f"WHEN {old} THEN '{MERGED_LABELS[new]}'" for old, new in MERGE_MAP.items()
    )

    sql = f"""
        UPDATE startup_extended
        SET
          cluster_id = CASE cluster_id
            {when_id_clauses}
            ELSE cluster_id
          END,
          cluster_label = CASE cluster_id
            {when_label_clauses}
            ELSE cluster_label
          END
        WHERE scope_decision = 'include'
          AND cluster_id IN ({','.join(str(k) for k in MERGE_MAP)})
    """
    cur.execute(sql)
    updated = cur.rowcount
    conn.commit()

    # Report per-cluster result
    for new_id in sorted(set(MERGE_MAP.values())):
        cur.execute(
            "SELECT count(*) FROM startup_extended WHERE scope_decision='include' AND cluster_id=?",
            (new_id,),
        )
        n = cur.fetchone()[0]
        old_ids = [str(k) for k, v in MERGE_MAP.items() if v == new_id]
        print(f"  [{new_id}] {MERGED_LABELS[new_id].split('||')[0]:48s} ← old {','.join(old_ids):10s} → {n} startups")

    # Regenerate dashboard JS
    print("\n  Regenerando startup-themes-data.js...")
    from src.clustering import write_dashboard_data
    write_dashboard_data(conn)
    conn.close()

    # Print summary
    conn2 = sqlite3.connect(db_path)
    cur2 = conn2.cursor()
    cur2.execute("""
        SELECT cluster_id, cluster_label, count(*) as n
        FROM startup_extended
        WHERE scope_decision='include' AND cluster_id != -1
        GROUP BY cluster_id ORDER BY n DESC
    """)
    print("\n=== CLUSTERS FINALES ===")
    print(f"  ID    N  Label")
    print(f"  " + "-" * 70)
    for cid, label, n in cur2.fetchall():
        name = label.split("||")[0] if label else "?"
        print(f"  {cid:2d}  {n:3d}  {name}")
    conn2.close()

    return {"updated": updated, "merged_into": len(MERGED_LABELS)}


if __name__ == "__main__":
    print("\n=== Cluster merge (17 → 9) ===")
    result = apply_merge()
    print(f"\n[OK] {result['updated']} startups reasignados a {result['merged_into']} clusters")
