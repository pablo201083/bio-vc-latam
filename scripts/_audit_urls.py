import sqlite3, csv

conn = sqlite3.connect('db/bio_latam.db')

# Check startup_extended columns
cols = [c[1] for c in conn.execute('PRAGMA table_info(startup_extended)').fetchall()]
print('startup_extended cols:', cols)

# Check evidence/source columns
src_cols = [c for c in cols if any(k in c.lower() for k in ['url','source','web','evidence'])]
print('URL-like cols in startup_extended:', src_cols)

# Sample from entities
rows = conn.execute('''
    SELECT e.canonical_name, e.website
    FROM entities e
    WHERE e.entity_type = 'startup'
    LIMIT 10
''').fetchall()
print('\nentities.website sample:')
for name, web in rows:
    print(f'  {name}: {web}')
conn.close()

# Also check CSV source_url
with open('startup_master_dataset.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader if r.get('scope_decision') == 'include']

print(f'\nCSV source_url sample (included):')
for r in rows[:8]:
    print(f"  {r['startup_id']}: {r.get('source_url','')}")
