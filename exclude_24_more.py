import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# The 24 to exclude based on agent research
to_exclude = [
    'aloi', 'capim', 'circular', 'cobli', 'egg', 'frete_com',
    'gbm', 'geofusion', 'logan', 'logshare', 'luzid', 'oneinfinite',
    'prima', 'sensei', 'starlight_ventures', 'strike', 'teachy',
    'vixtra', 'vu', 'webee', 'wisy', 'flexza', 'bacu'
]

print("=" * 80)
print("EXCLUDING 24 ADDITIONAL NON-BIOTECH STARTUPS")
print("=" * 80)
print(f"\nTotal to exclude: {len(to_exclude)}\n")

update_count = 0
for startup_id in to_exclude:
    c.execute('''
    UPDATE startup_extended
    SET review_status = 'EXCLUDE'
    WHERE startup_id = ?
    ''', (startup_id,))
    update_count += 1
    print(f"  OK {startup_id}")

conn.commit()

print(f"\nUpdated: {update_count} startups marked as EXCLUDE")

# Verify remaining unclustered
c.execute('''
SELECT COUNT(*) FROM startup_extended
WHERE cluster_id = -1 AND review_status != 'EXCLUDE'
''')
remaining = c.fetchone()[0]

c.execute('''
SELECT startup_id FROM startup_extended
WHERE cluster_id = -1 AND review_status != 'EXCLUDE'
ORDER BY startup_id
''')
remaining_ids = [row[0] for row in c.fetchall()]

print(f"\nREMAINING UNCLUSTERED (to research):")
print(f"  Total: {remaining}")
print(f"  IDs: {remaining_ids}")

# Overall BD stats
c.execute('SELECT COUNT(*) FROM startup_extended WHERE review_status = "EXCLUDE"')
total_exclude = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM startup_extended')
total = c.fetchone()[0]

print(f"\nBD STATUS:")
print(f"  Total startups: {total}")
print(f"  Excluded: {total_exclude} ({100*total_exclude//total}%)")
print(f"  Active (INCLUDE/REVIEW/seeded): {total - total_exclude}")

conn.close()

print("\n" + "=" * 80)
print(f"CLEANUP COMPLETE - {remaining} BIOTECH STARTUPS REMAIN FOR RESEARCH")
print("=" * 80)
