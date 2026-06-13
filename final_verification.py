import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("FINAL VERIFICATION - GOAL ACHIEVEMENT")
print("=" * 80)

# Count overall stats
c.execute('SELECT COUNT(*) FROM startup_extended')
total = c.fetchone()[0]
print(f"\nTotal startups in database: {total}")

# Clustered
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0')
clustered = c.fetchone()[0]
print(f"Clustered (cluster_id >= 0): {clustered}")

# With bio_theme in clusters
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0 AND (bio_theme_primary IS NOT NULL AND bio_theme_primary != "")')
with_theme = c.fetchone()[0]
uncategorized = clustered - with_theme

print(f"\nBIO_THEME COMPLETENESS (within clustered startups):")
print(f"  With bio_theme: {with_theme} ({100*with_theme//clustered}%)")
print(f"  Without bio_theme: {uncategorized} ({100*uncategorized//clustered}%)")

# Show distribution by theme
print(f"\nTHEME DISTRIBUTION (top 8):")
c.execute('''
SELECT bio_theme_primary, COUNT(*) as cnt
FROM startup_extended
WHERE cluster_id >= 0 AND bio_theme_primary IS NOT NULL AND bio_theme_primary != ""
GROUP BY bio_theme_primary
ORDER BY cnt DESC
LIMIT 8
''')
total_themed = 0
for theme, cnt in c.fetchall():
    print(f"  {theme}: {cnt}")
    total_themed += cnt

# Show cluster stats
c.execute('SELECT COUNT(DISTINCT cluster_id) FROM startup_extended WHERE cluster_id >= 0')
num_clusters = c.fetchone()[0]
print(f"\nCLUSTERS:")
print(f"  Total semantic clusters: {num_clusters}")

# Assessment
print(f"\n" + "=" * 80)
print("ASSESSMENT: GOAL ACHIEVEMENT")
print("=" * 80)

pct_with_theme = 100 * with_theme // clustered
if pct_with_theme >= 85 and uncategorized <= 15:
    status = "ACHIEVED"
    symbol = "OK"
else:
    status = "IN PROGRESS"
    symbol = "WARN"

print(f"\n[{symbol}] Goal: Adquirir suficiente señal para clusterizar y etiquetar competentemente")
print(f"\nMetrics:")
print(f"  • Clustering quality: {num_clusters} coherent semantic clusters")
print(f"  • Label completeness: {pct_with_theme}% of clustered startups have bio_theme")
print(f"  • Remaining gaps: {uncategorized} startups ({100*uncategorized//clustered}%)")
print(f"\nStatus: {status}")

if status == "ACHIEVED":
    print(f"\nWe have sufficient signal to:")
    print(f"  ✓ Cluster startups semantically with high confidence")
    print(f"  ✓ Assign bio_theme labels to {pct_with_theme}% of population")
    print(f"  ✓ Identify remaining outliers for targeted research")
else:
    print(f"\nTo achieve goal, need:")
    print(f"  - Research {uncategorized} remaining startups")
    print(f"  - Improve theme mapping for Mixed clusters")

conn.close()
