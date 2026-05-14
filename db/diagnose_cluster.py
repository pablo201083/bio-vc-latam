import sys, sqlite3
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect('db/bio_latam.db')

print('=== Cluster Food Systems — Protein: all companies ===')
rows = conn.execute("""
    SELECT e.canonical_name, sx.bio_theme_primary,
           sx.startup_summary_en, sx.startup_summary_v1
    FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id
    WHERE sx.cluster_label LIKE 'Food Systems%Protein%'
      AND sx.scope_decision='include'
    ORDER BY e.canonical_name
""").fetchall()

ids_in_cluster = set()
for name, theme, en, orig in rows:
    ids_in_cluster.add(name)
    print(f'  {name}')
    print(f'    {(en or orig or "")[:110]}')

print()
print('=== Keyword scorer vs current assignment ===')
from src.reclassify import load_startups, score_startup, classify, _cluster_name, CLUSTER_TO_CATEGORY

all_startups = load_startups(conn)
names_in_cluster = {r[0] for r in rows}

print(f"{'Company':<32} {'Cluster-assigned':<28} {'Scorer says':<28} {'Top score'}")
print('-'*100)
for s in all_startups:
    if s['canonical_name'] in names_in_cluster:
        scores = score_startup(s)
        primary, secondary, conf = classify(scores)
        top3 = sorted(scores.items(), key=lambda x: -x[1])[:3]
        cname = _cluster_name(s.get('cluster_label'))
        cluster_cat = CLUSTER_TO_CATEGORY.get(cname, f'SPLIT:{cname}') if cname else 'none'
        flag = '' if primary == s.get('bio_theme_primary') else '  <-- DISAGREES'
        print(f"  {s['canonical_name']:<30} {cluster_cat[:26]:<28} {(primary or '?'):<28} "
              f"[{top3[0][0][:16]}:{top3[0][1]:.1f}]{flag}")

conn.close()
