"""Enriquece las 11 startups stub de Food Systems con descripciones reales."""
import sqlite3
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parents[2]))
from src.audit import diff_and_log_update

ROOT = __import__('pathlib').Path(__file__).parents[2]
db = sqlite3.connect(ROOT / 'db' / 'bio_latam.db')

# Primero ver los IDs actuales
rows = db.execute("""
    SELECT e.entity_id, e.canonical_name, e.short_description, e.country_code
    FROM startup_extended se
    JOIN entities e ON e.entity_id = se.startup_id
    WHERE se.bio_theme_primary = 'Food Systems & Alt Proteins'
    AND se.umap_x > 10
    ORDER BY e.canonical_name
""").fetchall()

print(f"{'ID':<40} {'Name':<30} {'Country'} | Current description")
print("-"*120)
for r in rows:
    print(f"{r[0]:<40} {r[1]:<30} {r[3]}     | {r[2]}")

db.close()
