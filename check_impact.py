import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Count uncategorized in clusters
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0 AND (bio_theme_primary IS NULL OR bio_theme_primary = "")')
uncategorized = c.fetchone()[0]

# Count total clustered
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0')
total = c.fetchone()[0]

with_theme = total - uncategorized

print("=" * 70)
print("CLUSTERING IMPACT — AFTER RESEARCH DATA INGESTION")
print("=" * 70)
print(f"\nTotal clustered: {total}")
print(f"With bio_theme_primary: {with_theme} ({100*with_theme//total}%)")
print(f"Without bio_theme_primary: {uncategorized} ({100*uncategorized//total}%)")
print(f"\nCOMPARISON TO BEFORE:")
print(f"  Before: 61 uncategorized")
print(f"  Now:    {uncategorized} uncategorized")
if uncategorized < 61:
    print(f"  IMPROVEMENT: {61 - uncategorized} fewer uncategorized (-{100*(61-uncategorized)//61}%)")
elif uncategorized > 61:
    print(f"  REGRESSION: {uncategorized - 61} more uncategorized")
else:
    print(f"  NO CHANGE")

conn.close()
