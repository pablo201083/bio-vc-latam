import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Get the 61 uncategorized startups in clusters
c.execute('''
SELECT
  startup_id,
  cluster_id,
  cluster_label,
  business_one_liner,
  startup_summary_en
FROM startup_extended
WHERE cluster_id >= 0 AND (bio_theme_primary IS NULL OR bio_theme_primary = "")
ORDER BY cluster_id
''')

uncategorized = c.fetchall()
print(f"Total uncategorized in clusters: {len(uncategorized)}\n")

# Group by cluster
by_cluster = {}
for startup_id, cluster_id, cluster_label, bio_line, summary in uncategorized:
    if cluster_id not in by_cluster:
        by_cluster[cluster_id] = []
    by_cluster[cluster_id].append({
        'startup_id': startup_id,
        'bio_line': bio_line,
        'summary': summary,
        'cluster_label': cluster_label
    })

# Show by cluster
for cluster_id in sorted(by_cluster.keys()):
    startups = by_cluster[cluster_id]
    c.execute('SELECT COUNT(*) FROM startup_extended WHERE cluster_id = ? AND (bio_theme_primary IS NOT NULL AND bio_theme_primary != "")', (cluster_id,))
    with_theme = c.fetchone()[0]
    print(f"\n[Cluster {cluster_id}] {startups[0]['cluster_label']}")
    print(f"  With theme: {with_theme} | Without: {len(startups)}")
    for s in startups[:3]:  # Show first 3
        print(f"  - {s['startup_id']}: {s['bio_line'][:50] if s['bio_line'] else '(no desc)'}...")

conn.close()
