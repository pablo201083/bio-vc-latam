import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Theme keyword mapping
THEME_KEYWORDS = {
    'Diagnostics & Devices': ['diagnostic', 'device', 'sensor', 'detection', 'screening', 'test', 'imaging', 'portable', 'wearable', 'medtech', 'medical device'],
    'Therapeutics': ['therapeutic', 'treatment', 'cure', 'drug', 'pharma', 'gene therapy', 'regenerative', 'skin care', 'cosmetic', 'cancer'],
    'Food Systems & Alt Proteins': ['protein', 'food', 'cultivated', 'fermented', 'dairy', 'meat', 'alt protein', 'ingredient', 'biofactory'],
    'Bioinputs & Crop Resilience': ['crop', 'agronomic', 'pest', 'bioinput', 'biologics', 'resilience', 'yield', 'fertilizer', 'microbe'],
    'Biomaterials & Green Chemistry': ['material', 'biomaterial', 'packaging', 'mycelium', 'biodegradable', 'chemistry', 'waste', 'leather', 'textile'],
    'Precision Agriculture': ['farm', 'field', 'imaging', 'satellite', 'iot', 'sensor', 'agronomic', 'monitoring', 'prediction'],
    'Nature & Ecosystem Tech': ['nature', 'ecosystem', 'restoration', 'carbon', 'climate', 'biodiversity', 'ocean', 'water', 'environmental'],
    'Biomanufacturing & Platform Technologies': ['bioprocess', 'fermentation', 'platform', 'cdmo', 'manufacturing', 'scale-up', 'bioreactor'],
}

# Get uncategorized in Mixed clusters
c.execute('''
SELECT
  startup_id,
  cluster_id,
  cluster_label,
  business_one_liner,
  startup_summary_en
FROM startup_extended
WHERE cluster_id IN (0, 1)
ORDER BY startup_id
''')

startups = c.fetchall()
print(f"Processing {len(startups)} startups in Mixed clusters\n")

# Score each startup against themes
results = []
for startup_id, cluster_id, cluster_label, bio_line, summary in startups:
    text = f"{bio_line or ''} {summary or ''}".lower()

    if not text.strip():
        results.append((startup_id, cluster_id, None, 0.0, "no_description"))
        continue

    scores = {}
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(text.count(kw) for kw in keywords)
        if score > 0:
            scores[theme] = score

    if scores:
        best_theme = max(scores, key=scores.get)
        confidence = scores[best_theme] / len(text.split())  # normalized
        results.append((startup_id, cluster_id, best_theme, min(confidence, 1.0), "keyword_match"))
    else:
        # Fallback: use cluster context
        if 'aquaculture' in cluster_label.lower() or 'agricultural' in cluster_label.lower():
            results.append((startup_id, cluster_id, 'Bioinputs & Crop Resilience', 0.4, "cluster_context"))
        elif 'biodegradable' in cluster_label.lower():
            results.append((startup_id, cluster_id, 'Biomaterials & Green Chemistry', 0.4, "cluster_context"))
        else:
            results.append((startup_id, cluster_id, None, 0.0, "unknown"))

# Summary
assigned = [r for r in results if r[2] is not None]
print(f"Assigned themes: {len(assigned)}/{len(results)}")
print(f"\nTheme distribution:")
from collections import Counter
themes = Counter(r[2] for r in results if r[2])
for theme, count in themes.most_common():
    print(f"  {theme}: {count}")

# Save to CSV for ingestion
import csv
with open('staging/inferred_mixed_themes.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['entity_id', 'table_name', 'field_name', 'new_value', 'source_url', 'confidence', 'notes'])
    for startup_id, cluster_id, theme, conf, method in results:
        if theme:
            writer.writerow([
                startup_id,
                'startup_extended',
                'bio_theme_primary',
                theme,
                '',
                max(0.5, conf),  # min confidence 0.5
                f"Mixed cluster inference ({method})"
            ])

print(f"\nSaved to: staging/inferred_mixed_themes.csv")
conn.close()
