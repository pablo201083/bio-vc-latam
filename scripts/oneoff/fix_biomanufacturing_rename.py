"""
fix_biomanufacturing_rename.py
-------------------------------
Reencuadra "Biomanufacturing & Fermentation Economy" →
"Biomanufacturing & Platform Technologies"

Rationale: El tema no es un sector de aplicación final sino una categoría
de plataformas habilitantes (enzimas industriales, digital twins para
bioprocessos, ingeniería genética como servicio, infraestructura de
fermentación). El nombre nuevo refleja esa naturaleza cross-cutting.

Cambios:
  1. bio_theme_primary en startup_extended
  2. cluster_label (prefijo) en startup_extended
  3. bio_theme_primary en audit_log (old_value/new_value donde aplique)
  4. Registro en audit_log de la operación

Ejecutar:
  .venv/Scripts/python.exe fix_biomanufacturing_rename.py
"""

import sqlite3, pathlib, datetime, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OLD = "Biomanufacturing & Fermentation Economy"
NEW = "Biomanufacturing & Platform Technologies"

db  = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

# 1. Contar afectados
n_startups = cur.execute(
    "SELECT COUNT(*) FROM startup_extended WHERE bio_theme_primary=?", (OLD,)
).fetchone()[0]

n_labels = cur.execute(
    "SELECT COUNT(*) FROM startup_extended WHERE cluster_label LIKE ?", (OLD + '%',)
).fetchone()[0]

print(f"  bio_theme_primary a actualizar : {n_startups}")
print(f"  cluster_labels a actualizar    : {n_labels}")

# 2. Actualizar bio_theme_primary
cur.execute(
    "UPDATE startup_extended SET bio_theme_primary=? WHERE bio_theme_primary=?",
    (NEW, OLD)
)
print(f"  bio_theme_primary updated: {cur.rowcount}")

# 3. Actualizar cluster_label (reemplazar prefijo en texto completo)
cur.execute(
    "UPDATE startup_extended SET cluster_label = REPLACE(cluster_label, ?, ?) "
    "WHERE cluster_label LIKE ?",
    (OLD, NEW, OLD + '%')
)
print(f"  cluster_label updated: {cur.rowcount}")

# 4. Actualizar audit_log: old_value y new_value donde aparecía el nombre viejo
cur.execute(
    "UPDATE audit_log SET old_value=REPLACE(old_value,?,?) WHERE old_value=?",
    (OLD, NEW, OLD)
)
cur.execute(
    "UPDATE audit_log SET new_value=REPLACE(new_value,?,?) WHERE new_value=?",
    (OLD, NEW, OLD)
)

# 5. Registrar la operación en audit_log (una fila de resumen)
cur.execute(
    """INSERT INTO audit_log
       (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
       VALUES (?,?,?,?,?,?,?,?)""",
    (now, 'human:curador', '__global__', 'startup_extended',
     'bio_theme_primary', OLD, NEW,
     'Reencuadre editorial: tema no es sector de aplicación final sino plataformas habilitantes. '
     'Rename refleja naturaleza cross-cutting del cluster CL5 (enzimas, digital twins, gene editing, '
     'infraestructura de fermentación) y CROs biosimilares (Cellargen, Neocell).')
)

conn.commit()
conn.close()
print(f"\nCommit OK — '{OLD}' → '{NEW}'")
print("\nProximo paso: regenerar dashboard data")
print("  .venv/Scripts/python.exe -c \"import sqlite3,sys; sys.path.insert(0,'.'); from src.clustering import write_dashboard_data; conn=sqlite3.connect('db/bio_latam.db'); write_dashboard_data(conn); conn.close()\"")
