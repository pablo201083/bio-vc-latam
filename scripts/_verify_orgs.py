import sqlite3
conn = sqlite3.connect('db/bio_latam.db')

print('=== entities by type ===')
for row in conn.execute("SELECT entity_type, count(*) FROM entities GROUP BY entity_type ORDER BY entity_type").fetchall():
    print(f'  {row[0]}: {row[1]}')

print('\n=== organizations ===')
for row in conn.execute("SELECT org_id, org_type FROM organizations").fetchall():
    print(f'  {row}')

print('\n=== esos ===')
for row in conn.execute("SELECT eso_id, eso_type FROM esos").fetchall():
    print(f'  {row}')

print('\n=== corporates ===')
for row in conn.execute("SELECT corporate_id, industry FROM corporates").fetchall():
    print(f'  {row}')

print('\n=== support_edges ===')
for row in conn.execute("SELECT support_id, source_entity_id, target_entity_id, support_type FROM support_edges").fetchall():
    print(f'  {row}')
conn.close()
