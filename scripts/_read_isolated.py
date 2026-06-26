"""Read DB data for the 38 isolated_review conflicts."""
import sqlite3, csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")

# Load the 38 isolated_review IDs
triage = ROOT / "quality" / "theme_cluster_mismatch_triage.csv"
isolated = []
with open(triage, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if row["verdict"] == "isolated_review":
            isolated.append(row)

print(f"Total isolated_review: {len(isolated)}\n")
print(f"{'ID':<40} {'bio_theme':<30} {'cluster':<30} {'conf':<6} {'summary[:80]'}")
print("-"*160)

for row in isolated:
    sid = row["startup_id"]
    data = conn.execute("""
        SELECT sx.bio_theme_primary, sx.startup_summary_en, sx.bio_theme_confidence,
               e.country_code, sx.macro_theme
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.startup_id = ?
    """, (sid,)).fetchone()
    if data:
        bio_theme, summary, conf, cc, macro = data
        s = (summary or "")[:80].replace("\n", " ")
        print(f"{sid:<40} {(row['bio_theme'])[:28]:<30} {(row['cluster_label_prefix'])[:28]:<30} {str(conf)[:5]:<6} {s}")

conn.close()
