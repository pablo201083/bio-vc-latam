from src.reclassify import load_startups, score_startup, _cluster_name, _resolve_sustainable, CLUSTER_TO_CATEGORY
import sqlite3
conn = sqlite3.connect("db/bio_latam.db")
startups = load_startups(conn)
conn.close()

checks = [
    'Atarraya','Earth Ocean Farms','Food for the Future','Luyef','The Live Green Co',
    'HIF Global','Neoprospecta','Agricapital','Agrolend','Sistema.bio','AgroSustain',
    'Biocentis','Bruna by Altum Lab','Vitales','SoluBio',
]
print(f"{'Company':<38} {'Cluster':<42} -> Category")
print("-"*110)
for s in startups:
    if any(c.lower() in s['canonical_name'].lower() for c in checks):
        cname = _cluster_name(s.get('cluster_label'))
        summary = (s.get('startup_summary_v1') or '').lower()
        if cname == 'Crop & Plant Eng. — Sustainable':
            cat = _resolve_sustainable(summary)
        elif cname in CLUSTER_TO_CATEGORY:
            cat = CLUSTER_TO_CATEGORY[cname]
        else:
            cat = '(keyword fallback)'
        print(f"  {s['canonical_name']:<36} {(cname or 'none'):<42} -> {cat}")
