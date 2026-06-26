import csv
with open('quality/theme_cluster_mismatch_triage.csv', newline='', encoding='utf-8-sig') as f:
    rows = [r for r in csv.DictReader(f) if r['verdict'] == 'isolated_review']
print(f'Remaining isolated_review: {len(rows)}')
for r in rows:
    sid = r['startup_id']
    bio = r['bio_theme'][:26]
    cl = r['cluster_label_prefix'][:26]
    conf = r['bio_theme_confidence'][:5]
    print(f"  {sid:<42} {bio:<28} -> {cl:<28} conf={conf}")
