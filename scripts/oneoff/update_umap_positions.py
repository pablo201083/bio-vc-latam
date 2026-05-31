"""
update_umap_positions.py
------------------------
Re-calcula las posiciones UMAP (umap_x, umap_y) usando los embeddings actualizados
y los bio_theme_primary actuales.

NO toca: cluster_id, cluster_label, is_outlier, bio_theme_primary.
Solo actualiza: umap_x, umap_y en startup_extended.

Usar despues de:
  1. Re-generar embeddings (pipeline.py rebuild --phase embeddings)
  2. Correr reclassify-themes (para bio_theme_primary actualizado)

Ejecutar:
  .venv/Scripts/python.exe update_umap_positions.py
"""
import sys, sqlite3, pathlib, datetime, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent
DB   = ROOT / "db" / "bio_latam.db"

# Importar funciones de clustering sin correr el pipeline completo
from src.clustering import (
    run_umap,
    editorial_positions,
    scatter_positions,
    UMAP_CLUSTER_PARAMS,
    UMAP_VIZ_PARAMS,
)
from src.embeddings import run as run_embeddings

t0 = time.time()
print("=== update_umap_positions ===")

# 1. Cargar embeddings del cache (ya regenerados)
print("\n1. Cargando embeddings del cache...")
emb = run_embeddings(force=False, db_path=DB)
vectors = emb["vectors"]   # shape (N, 384)
ids     = emb["ids"]       # lista de startup_ids en el mismo orden
print(f"   {len(ids)} vectores cargados")

# 2. UMAP 10D (para estructura de clustering)
print("\n2. UMAP 10D...")
reduced_10d = run_umap(vectors, UMAP_CLUSTER_PARAMS, "clustering")

# 3. UMAP 2D (offset intra-tema)
print("\n3. UMAP 2D...")
raw_2d = run_umap(reduced_10d, UMAP_VIZ_PARAMS, "viz-raw")

# 4. Leer bio_theme_primary ACTUALIZADOS del DB
print("\n4. Leyendo bio_theme_primary actualizados...")
conn = sqlite3.connect(DB)
bio_themes_map: dict[str, str] = dict(conn.execute(
    "SELECT startup_id, bio_theme_primary FROM startup_extended "
    "WHERE bio_theme_primary IS NOT NULL AND bio_theme_primary != ''"
).fetchall())
print(f"   {len(bio_themes_map)} startups con bio_theme_primary")

# 5. Calcular posiciones editoriales con los temas nuevos
print("\n5. Calculando posiciones editoriales...")
coords_2d  = editorial_positions(raw_2d, ids, bio_themes_map)
scatter_2d = scatter_positions(raw_2d, ids, bio_themes_map)

# 6. Actualizar solo umap_x / umap_y en la DB
print("\n6. Actualizando umap_x/umap_y en SQLite...")
now = datetime.datetime.now(datetime.UTC).isoformat()
cur = conn.cursor()
updated = 0
for i, sid in enumerate(ids):
    x, y = float(coords_2d[i, 0]), float(coords_2d[i, 1])
    cur.execute(
        "UPDATE startup_extended SET umap_x=?, umap_y=? WHERE startup_id=?",
        (x, y, sid)
    )
    updated += 1

conn.commit()
conn.close()

print(f"   {updated} posiciones actualizadas")
print(f"\n=== Listo en {time.time()-t0:.1f}s ===")
print("\nProximo paso:")
print("  .venv/Scripts/python.exe -c \"import sqlite3,sys; sys.path.insert(0,'.'); from src.clustering import write_dashboard_data; conn=sqlite3.connect('db/bio_latam.db'); write_dashboard_data(conn); conn.close()\"")
