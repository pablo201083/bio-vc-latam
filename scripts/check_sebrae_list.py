"""Check SEBRAE 2023 list against our DB"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

sebrae_companies = [
    "3d biotechnology", "biobreyer", "bioin food", "biolambda",
    "biolinker", "biologix", "biopolix", "bioprocess improvement",
    "ecra biotec", "kimera", "life biological control", "lizarbio",
    "neogenys", "rheabiotech", "ziel biosciences",
    # agrotech
    "agriconnected", "agrientech", "dana agro", "especiarias",
    "inceres", "ja fui", "pbf nutrientes", "rubian", "scicrop"
]

print("=== SEBRAE 2023 startups in our DB ===")
for name in sebrae_companies:
    like = f"%{name}%"
    r = conn.execute(
        "SELECT entity_id, canonical_name FROM entities WHERE LOWER(canonical_name) LIKE ? OR entity_id LIKE ?", (like, like)
    ).fetchall()
    if r:
        print(f"  FOUND {name}: {r}")
print("done")
