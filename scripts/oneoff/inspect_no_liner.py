import sqlite3, pathlib

db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("""
    SELECT sx.startup_id, e.canonical_name, e.country_code,
           sx.cluster_id, sx.cluster_confidence,
           sx.bio_theme_primary,
           coalesce(sx.startup_summary_en, sx.startup_summary_v1, '') as summary,
           sx.business_one_liner,
           sx.macro_theme, sx.emergent_theme,
           sx.tech_codes, sx.technology_tags,
           e.website
    FROM startup_extended sx
    JOIN entities e ON e.entity_id = sx.startup_id
    WHERE sx.scope_decision = 'include'
      AND sx.cluster_confidence < 0.4
      AND (sx.business_one_liner IS NULL OR length(sx.business_one_liner) < 10)
    ORDER BY sx.cluster_id, sx.cluster_confidence
""")
rows = cur.fetchall()
print(f'Startups sin one_liner en periphery: {len(rows)}')
print()
for r in rows:
    sid, name, country, cl, conf, bio, summary, liner, macro, emergent, tech, tech_tags, website = r
    sumlen = len(summary)
    print(f'CL{cl} [{conf:.2f}] {name} ({country}) — id: {sid}')
    print(f'  bio_theme : {bio}')
    print(f'  macro     : {macro}')
    print(f'  emergent  : {emergent}')
    print(f'  tech_tags : {tech_tags}')
    print(f'  website   : {website}')
    print(f'  summary({sumlen}): {summary[:180]}')
    print()
conn.close()
