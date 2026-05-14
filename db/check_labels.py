import sqlite3
conn = sqlite3.connect("db/bio_latam.db")

names = ['Atarraya','AgroSustain','HIF Global','Neoprospecta','Sistema.bio','Vitales','SoluBio']
for name in names:
    row = conn.execute(
        "SELECT e.canonical_name, sx.cluster_label FROM startup_extended sx "
        "JOIN entities e ON e.entity_id=sx.startup_id "
        "WHERE e.canonical_name LIKE ? LIMIT 1",
        (f"%{name}%",)
    ).fetchone()
    if row:
        label = row[1]
        clean = label.split("||")[0].strip() if label else None
        print(f"{row[0]}: cluster={clean!r}")
    else:
        print(f"{name}: NOT FOUND")

# Also show distinct cluster names to verify exact keys
print("\n=== All distinct cluster clean names ===")
rows = conn.execute(
    "SELECT DISTINCT cluster_label FROM startup_extended WHERE cluster_label IS NOT NULL"
).fetchall()
import sys
for (label,) in sorted(rows):
    clean = label.split("||")[0].strip()
    sys.stdout.buffer.write((clean + "\n").encode("utf-8"))

conn.close()
