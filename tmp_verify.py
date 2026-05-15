import sqlite3
conn = sqlite3.connect('db/bio_latam.db')
cur = conn.cursor()

# Check all candidate startups
candidates = [
    # SP Ventures active
    'genica', 'agrolend', 'verqor', 'blooms', 'lupeon', 'agroadvance',
    # SP Ventures exits (historical but still in DB)
    'jetbov', 'inprenha', 'decoy', 'decoy-smart-control-br',
    # Yield Lab LATAM
    'bemagro', 'culttivo', 'cerradox', 'phagelab', 'kigui', 'incluirtec',
    'produzindo', 'agricapital', 'courageous',
    # Zentynel additional
    'antarka', 'fecundis', 'autem', 'axenya', 'viewmind', 'biomakers',
    'harmony', 'microterra', 'samay', 'xeptiva',
    # Kamay new
    'aerialoop', 'arqlite', 'kilimo', 'auravant', 'wiagro',
    # Savia new
    'strong_by_form', 'living_ink', 'nutrition_from_water', 'mothership',
]

print('=== Entity check ===')
for c in candidates:
    cur.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.entity_type,
               sx.scope_decision
        FROM entities e
        LEFT JOIN startup_extended sx ON sx.startup_id = e.entity_id
        WHERE LOWER(e.entity_id) LIKE ? OR LOWER(e.canonical_name) LIKE ?
    """, (f'%{c.lower()}%', f'%{c.lower()}%'))
    rows = cur.fetchall()
    if rows:
        for r in rows:
            cur.execute("SELECT COUNT(*) FROM investment_edges WHERE startup_id=?", (r[0],))
            ec = cur.fetchone()[0]
            print(f'  FOUND  {r[0]:35s} {str(r[1]):28s} {str(r[2]):4s} scope={str(r[4]):10s} edges={ec}')
    else:
        print(f'  -miss- {c}')

# Check zentynel existing edges
print()
print('=== Zentynel existing edges ===')
cur.execute("SELECT startup_id FROM investment_edges WHERE investor_id='zentynel'")
for r in cur.fetchall():
    cur.execute("SELECT canonical_name FROM entities WHERE entity_id=?", (r[0],))
    name = cur.fetchone()
    print(f'  {r[0]:35s} {str(name[0]) if name else "?"}')

conn.close()
