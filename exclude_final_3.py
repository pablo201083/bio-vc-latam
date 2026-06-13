import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Exclude final 3
to_exclude = ['agroadvance', 'erural', 'verge_ag']

for sid in to_exclude:
    c.execute("UPDATE startup_extended SET review_status = 'EXCLUDE' WHERE startup_id = ?", (sid,))
    print(f"Excluded: {sid}")

conn.commit()

# Verify
c.execute("SELECT COUNT(*) FROM startup_extended WHERE review_status = 'EXCLUDE'")
total = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM startup_extended WHERE cluster_id = -1 AND review_status != 'EXCLUDE'")
remaining = c.fetchone()[0]

print(f"\nTotal EXCLUDE: {total}")
print(f"Remaining unclustered: {remaining}")

if remaining > 0:
    c.execute("SELECT startup_id FROM startup_extended WHERE cluster_id = -1 AND review_status != 'EXCLUDE' ORDER BY startup_id")
    print(f"IDs: {[r[0] for r in c.fetchall()]}")

conn.close()
