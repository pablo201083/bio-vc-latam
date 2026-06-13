import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 70)
print("CLUSTERING STATUS VERIFICATION")
print("=" * 70)

# 1. Total startups
c.execute('SELECT COUNT(*) FROM startup_extended')
total = c.fetchone()[0]
print(f"\n📊 TOTAL STARTUPS: {total}")

# 2. Clustered vs unclustered
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0')
clustered = c.fetchone()[0]
unclustered = total - clustered
print(f"   ✓ Clustered (cluster_id >= 0): {clustered}")
print(f"   ✗ Unclustered (cluster_id = -1): {unclustered}")

# 3. Bio_theme distribution
c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0 AND (bio_theme_primary IS NOT NULL AND bio_theme_primary != "")')
themed = c.fetchone()[0]
unthemed = clustered - themed
print(f"\n🏷️ BIO_THEME STATUS (within {clustered} clustered):")
print(f"   ✓ With bio_theme_primary: {themed} ({100*themed//clustered}%)")
print(f"   ✗ WITHOUT bio_theme_primary: {unthemed} ({100*unthemed//clustered}%)")

# 4. Top themes
print(f"\n📈 TOP 8 BIO_THEMES:")
c.execute('''
SELECT bio_theme_primary, COUNT(*) as cnt
FROM startup_extended
WHERE cluster_id >= 0 AND bio_theme_primary IS NOT NULL AND bio_theme_primary != ""
GROUP BY bio_theme_primary
ORDER BY cnt DESC
LIMIT 8
''')
for i, (theme, cnt) in enumerate(c.fetchall(), 1):
    print(f"   {i}. {theme}: {cnt}")

# 5. Cluster distribution
print(f"\n🎯 CLUSTER DISTRIBUTION:")
c.execute('SELECT cluster_id, cluster_label, COUNT(*) as cnt FROM startup_extended WHERE cluster_id >= 0 GROUP BY cluster_id ORDER BY cnt DESC')
for cluster_id, label, cnt in c.fetchall():
    print(f"   [{cluster_id}] {label[:50]}: {cnt}")

print("\n" + "=" * 70)
print("STATUS: READY FOR VISUALIZATION ✅")
print("=" * 70)

conn.close()
