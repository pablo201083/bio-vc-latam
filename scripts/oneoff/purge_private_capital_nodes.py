"""One-off: purga nodos de capital privados/no-fondos (familias, personas, palabras,
buckets placeholder) que provenían de un grafo privado. Limpia DB + CSV fuente.

Decisión del curador 2026-06-15: solo se eliminan ids claramente privados; los
casos borde (grupos de angeles, consorcios, fundaciones) se conservan.

Los ids a purgar contienen PII y NO se versionan: viven en `purge_ids.private.txt`
(una línea por id, gitignored). Sin ese archivo el script aborta.
"""
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "bio_latam.db"
ENTITIES_CSV = ROOT / "canonical" / "canonical_entities.csv"
RAW_EDGES_CSV = ROOT / "staging" / "investment_edges_raw.csv"
PURGE_IDS_FILE = Path(__file__).resolve().parent / "purge_ids.private.txt"


def _load_purge_ids() -> list[str]:
    if not PURGE_IDS_FILE.exists():
        sys.exit(
            f"Falta {PURGE_IDS_FILE.name} (contiene PII, no versionado). "
            "Creá el archivo con un id por línea antes de correr la purga."
        )
    return [
        line.strip()
        for line in PURGE_IDS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


PURGE_IDS = _load_purge_ids()


def purge_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    ph = ",".join("?" * len(PURGE_IDS))
    report = {}
    for table, col in [
        ("investment_edges", "investor_id"),
        ("ecosystem_bridges", "source_entity_id"),
        ("ecosystem_bottlenecks", "entity_id"),
        ("investors", "investor_id"),
        ("entities", "entity_id"),
    ]:
        n = cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IN ({ph})", PURGE_IDS).fetchone()[0]
        cur.execute(f"DELETE FROM {table} WHERE {col} IN ({ph})", PURGE_IDS)
        report[table] = n
    # registrar la purga en audit_log (mejor esfuerzo, según columnas existentes)
    cols = {d[1] for d in cur.execute("PRAGMA table_info(audit_log)")}
    if {"entity_id", "field_name", "old_value", "new_value"} <= cols:
        for eid in PURGE_IDS:
            cur.execute(
                "INSERT INTO audit_log (entity_id, field_name, old_value, new_value) VALUES (?,?,?,?)",
                (eid, "__purged__", "active", "DELETED (privacy: non-public capital node)"),
            )
    con.commit()
    con.close()
    return report


def purge_csv(path, id_fields):
    """Elimina filas cuyo valor en cualquiera de id_fields esté en PURGE_IDS."""
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    if not rows:
        return 0, 0
    fields = list(rows[0].keys())
    kept = [r for r in rows if not any((r.get(f) or "") in PURGE_IDS for f in id_fields)]
    removed = len(rows) - len(kept)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(kept)
    return removed, len(kept)


if __name__ == "__main__":
    print("== DB ==")
    for t, n in purge_db().items():
        print(f"  {t}: -{n}")
    print("== CSV fuente ==")
    r, k = purge_csv(ENTITIES_CSV, ["entity_id"])
    print(f"  canonical_entities.csv: -{r} (quedan {k})")
    r, k = purge_csv(RAW_EDGES_CSV, ["investor_id_candidate", "source_id", "target_id"])
    print(f"  investment_edges_raw.csv: -{r} (quedan {k})")
