"""
Merge duplicate entities que tienen version enriquecida (base) y version vacia (sufijo-pais).

Pares confirmados:
  stamm-ar  → stamm    (Stämm, Argentine biomanufacturing)
  solubio-br → solubio  (Solubio, Brazilian ag biologicals)

Para cada par:
  1. Migra investment_edges del duplicado al original (si el inversor no existe ya)
  2. Excluye el duplicado via audit trail
  3. Deja el original intacto

Uso: python scripts/merge_duplicate_entities.py
"""
import sys
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.audit import diff_and_log_update  # noqa: E402

DB_PATH = ROOT / "db" / "bio_latam.db"

PAIRS = [
    ("stamm-ar",    "stamm"),
    ("solubio-br",  "solubio"),
]

ACTOR  = "merge_duplicate_entities"
REASON = "duplicate-entity-con-sufijo-pais — version base enriquecida es la canonical"


def merge(conn: sqlite3.Connection, dup_id: str, base_id: str) -> None:
    c = conn.cursor()

    # Verificar que ambos existen y ambos son include
    c.execute("SELECT scope_decision FROM startup_extended WHERE startup_id=?", (dup_id,))
    dup_row = c.fetchone()
    c.execute("SELECT scope_decision FROM startup_extended WHERE startup_id=?", (base_id,))
    base_row = c.fetchone()

    if not dup_row:
        print(f"  SKIP: {dup_id} no existe en startup_extended")
        return
    if not base_row:
        print(f"  SKIP: {base_id} no existe en startup_extended")
        return
    if dup_row[0] == "exclude":
        print(f"  SKIP: {dup_id} ya está excluido")
        return

    # 1. Migrar investment_edges únicas (inversores que no están ya en base)
    c.execute("SELECT investor_id FROM investment_edges WHERE startup_id=?", (base_id,))
    base_investors = {r[0] for r in c.fetchall()}

    c.execute("SELECT investment_id, investor_id, round_name, round_stage, amount, "
              "currency, is_lead, confidence_score, source_id, notes "
              "FROM investment_edges WHERE startup_id=?", (dup_id,))
    dup_edges = c.fetchall()

    migrated = 0
    skipped  = 0
    for edge in dup_edges:
        inv_id  = edge[1]
        if inv_id in base_investors:
            print(f"    edge {inv_id} ya existe en {base_id} — skip")
            skipped += 1
            continue
        # Generar nuevo investment_id para el base
        new_inv_id = f"merged-{dup_id}-{inv_id[:20]}"
        c.execute("""INSERT OR IGNORE INTO investment_edges
                     (investment_id, investor_id, startup_id, round_name, round_stage,
                      amount, currency, is_lead, confidence_score, source_id, notes)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                  (new_inv_id, inv_id, base_id, edge[2], edge[3],
                   edge[4], edge[5], edge[6], edge[7], edge[8],
                   (edge[9] or "") + f" | migrated from {dup_id}"))
        base_investors.add(inv_id)
        migrated += 1
        print(f"    migrada edge: {inv_id} → {base_id}")

    print(f"  Edges: {migrated} migradas, {skipped} duplicadas descartadas")

    # 2. Excluir el duplicado via audit trail
    diff_and_log_update(
        conn,
        table="startup_extended",
        row_id_col="startup_id",
        row_id=dup_id,
        new_values={"scope_decision": "exclude",
                    "scope_reason": f"duplicate-of-{base_id}"},
        actor=ACTOR,
        reason=REASON,
    )
    print(f"  Excluido: {dup_id} → scope_decision='exclude'")

    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)

    for dup_id, base_id in PAIRS:
        print(f"\n{'='*60}")
        print(f"Merging {dup_id} → {base_id}")
        merge(conn, dup_id, base_id)

    conn.close()
    print("\nDone. Correr: python pipeline.py rebuild --phase clustering")


if __name__ == "__main__":
    main()
