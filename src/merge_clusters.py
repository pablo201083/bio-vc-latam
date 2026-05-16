"""
src/merge_clusters.py — post-hoc cluster merge.

Fusiona los N clusters de HDBSCAN en k clusters semánticamente coherentes
sin necesidad de re-embeder. Actualiza startup_extended y regenera el JS.

IMPORTANTE: el merge map debe recalibrarse cada vez que cambian los embeddings
o los parámetros de HDBSCAN, ya que los raw IDs se renumeran entre corridas.
Para recalibrar: correr pipeline.py rebuild --phase clustering, inspeccionar
los CLUSTERS DETECTADOS en stdout, y actualizar MERGE_MAP aquí.

Merge map (14 raw → 9) — revisado 2026-05 tras enriquecimiento web de 18 periphery:
  new 0  Therapeutics — Regenerative & Cell Medicine       old 4           (53)
  new 1  Therapeutics — Drug Discovery & Development       old 5           (48)
  new 2  Diagnostics & MedTech                             old 0           (32)
  new 3  Ag Biologicals & Bioinputs                        old 6, 8        (59)
  new 4  Farm Intelligence & Precision Agriculture         old 10, 11      (56)
  new 5  Food Systems & Alt Proteins                       old 1           (27)
  new 6  Biomanufacturing & Precision Fermentation         old 3           (10)
  new 7  Nature, Climate & Ecosystem Tech                  old 7, 9,12,13  (52)
  new 8  Biomaterials & Circular Chemistry                 old 2           (36)
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
# Revisado 2026-05: 14 raw clusters → 9 finales (post enriquecimiento web)
MERGE_MAP: dict[int, int] = {
    4: 0,   # Therapeutics Regenerative (53, 94% Therapeutics)
    5: 1,   # Drug Discovery/mixed (48, 42% Diagnostics + 40% Therapeutics)
    0: 2,   # Diagnostics (32, 97% Diagnostics)
    6: 3,   # Ag Biologicals (40, 70% Bioinputs)
    8: 3,   # Ag Biologicals/Biocontrol (19, 74% Bioinputs)
    10: 4,  # Farm Intelligence (50)
    11: 4,  # Farm Intelligence small (6)
    1: 5,   # Food Novel Ingredients (27, 74% Food)
    3: 6,   # Biomanufacturing/Precision Fermentation (10)
    7: 7,   # Nature/Clean Energy (12, 75% Nature)
    9: 7,   # Nature/Biodiversity (18, 100% Nature)
    12: 7,  # Nature/Traceability (9)
    13: 7,  # Nature/Finance/Climate (13)
    2: 8,   # Biomaterials & Circular Economy (36, 75% Biomaterials)
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
