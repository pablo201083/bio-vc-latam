import sqlite3
import csv

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("APPLYING EXCLUSIONS TO 311 NON-BIOTECH STARTUPS")
print("=" * 80)

# Read exclusion list
exclusions = []
with open('staging/exclude_non_biotech.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        exclusions.append(row['startup_id'])

print(f"\nExclusions to apply: {len(exclusions)}")

# Update review_status to EXCLUDE for all in exclusion list
update_count = 0
for startup_id in exclusions:
    c.execute('''
    UPDATE startup_extended
    SET review_status = 'EXCLUDE'
    WHERE startup_id = ?
    ''', (startup_id,))
    update_count += 1

conn.commit()

print(f"Updated: {update_count} startups marked as EXCLUDE")

# Verify
c.execute('''
SELECT COUNT(*) FROM startup_extended WHERE review_status = 'EXCLUDE'
''')
total_exclude = c.fetchone()[0]

c.execute('''
SELECT COUNT(*) FROM startup_extended WHERE review_status IN ('INCLUDE', 'REVIEW')
''')
total_active = c.fetchone()[0]

print(f"\nBD STATUS AFTER UPDATE:")
print(f"  EXCLUDE: {total_exclude}")
print(f"  INCLUDE/REVIEW (active): {total_active}")

# Check remaining unclustered
c.execute('''
SELECT COUNT(*) FROM startup_extended
WHERE cluster_id = -1 AND review_status NOT IN ('EXCLUDE')
''')
remaining_unclustered = c.fetchone()[0]

print(f"\nREMAINING UNCLUSTERED (active only): {remaining_unclustered}")
print(f"  Expected: ~53 biotech startups")

conn.close()

print(f"\n" + "=" * 80)
print(f"CLEANUP COMPLETE")
print(f"=" * 80)
print(f"\nNext: Research {remaining_unclustered} biotech startups")
