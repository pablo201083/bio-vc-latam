import sqlite3, pathlib, sys, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
now = datetime.datetime.now(datetime.UTC).isoformat()

# Add column if not exists
try:
    cur.execute("ALTER TABLE startup_extended ADD COLUMN sub_cluster_label TEXT")
    print("Column sub_cluster_label added.")
except Exception as e:
    print(f"Column already exists or error: {e}")

# CL1: Drug Discovery — two semantic sub-groups
# CL1-A: companies with bio_theme='Therapeutics' (drug discovery / biologics end)
# CL1-B: companies with bio_theme='Diagnostics & Health Access' (companion dx / liquid biopsy end)
cur.execute("""
    UPDATE startup_extended
    SET sub_cluster_label = CASE
        WHEN bio_theme_primary = 'Therapeutics' THEN 'Drug Discovery & Biologics'
        WHEN bio_theme_primary = 'Diagnostics & Health Access' THEN 'Diagnostic-Therapeutic Convergence'
        ELSE NULL
    END
    WHERE cluster_id = 1
""")
n = cur.rowcount
print(f"CL1: {n} rows updated with sub_cluster_label")

# Verify
cur.execute("""
    SELECT sub_cluster_label, count(*) FROM startup_extended
    WHERE cluster_id=1 AND scope_decision='include'
    GROUP BY sub_cluster_label
""")
for r in cur.fetchall():
    print(f"  {r[0]} -> {r[1]}")

# Audit
cur.execute("""
    INSERT INTO audit_log (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
    VALUES (?, 'human:curador', 'CL1', 'startup_extended', 'sub_cluster_label', NULL,
            'Drug Discovery & Biologics | Diagnostic-Therapeutic Convergence',
            'CL1 genuinely bimodal: Therapeutics=drug discovery end, Diagnostics=companion dx/liquid biopsy convergence zone')
""", (now,))

conn.commit()

# Regenerate dashboard
print('\n=== Regenerando dashboard JS ===')
import sys as _sys; _sys.path.insert(0, '.')
from src.clustering import write_dashboard_data
write_dashboard_data(conn)
conn.close()
print('Listo.')
