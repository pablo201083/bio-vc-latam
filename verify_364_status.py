import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("VERIFICACION - STATUS DE LOS 364 ORIGINALES")
print("=" * 80)

# Count by review_status for cluster_id = -1
c.execute('''
SELECT review_status, COUNT(*) as cnt
FROM startup_extended
WHERE cluster_id = -1
GROUP BY review_status
ORDER BY cnt DESC
''')

print("\nUNCLUSTERED (cluster_id = -1) POR review_status:")
for status, count in c.fetchall():
    print(f"  {status or '(null)'}: {count}")

# Get the 2 remaining
c.execute('''
SELECT startup_id, review_status, business_one_liner
FROM startup_extended
WHERE cluster_id = -1 AND review_status != 'EXCLUDE'
ORDER BY startup_id
''')

print("\nTHE 2 REMAINING UNCLUSTERED (no EXCLUDE):")
for sid, status, desc in c.fetchall():
    print(f"  {sid} [{status}]")
    if desc:
        print(f"    {desc[:70]}...")

# Count EXCLUDE unclustered
c.execute('''
SELECT COUNT(*) FROM startup_extended
WHERE cluster_id = -1 AND review_status = 'EXCLUDE'
''')
exclude_count = c.fetchone()[0]

print(f"\nEXCLUDED unclustered: {exclude_count}")

# Summary
total_unclustered = 2 + exclude_count
print(f"\nTOTAL UNCLUSTERED (before exclusion): {total_unclustered}")
print(f"After exclusion: {2}")

conn.close()
