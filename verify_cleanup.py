import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("VERIFYING CLEANUP RESULTS")
print("=" * 80)

# Count by review_status
c.execute('''
SELECT review_status, COUNT(*) as cnt
FROM startup_extended
GROUP BY review_status
ORDER BY cnt DESC
''')

print("\nBD DISTRIBUTION BY review_status:")
for status, count in c.fetchall():
    print(f"  {status or '(null)'}: {count}")

# Check unclustered that are NOT EXCLUDE
c.execute('''
SELECT COUNT(*) FROM startup_extended
WHERE cluster_id = -1 AND (review_status IS NULL OR review_status NOT IN ('EXCLUDE'))
''')
unclustered_active = c.fetchone()[0]

print(f"\nUNCLUSTERED (cluster_id = -1) BY review_status:")
c.execute('''
SELECT review_status, COUNT(*) FROM startup_extended
WHERE cluster_id = -1
GROUP BY review_status
ORDER BY COUNT(*) DESC
''')
for status, count in c.fetchall():
    print(f"  {status or '(null)'}: {count}")

# Get the 28 remaining unclustered
print(f"\nTHE {unclustered_active} REMAINING UNCLUSTERED BIOTECH:")
c.execute('''
SELECT startup_id, business_one_liner, review_status
FROM startup_extended
WHERE cluster_id = -1 AND review_status != 'EXCLUDE'
ORDER BY startup_id
LIMIT 30
''')

for sid, desc, status in c.fetchall():
    print(f"  {sid} [{status}]")
    if desc:
        print(f"    {desc[:60]}...")

conn.close()
