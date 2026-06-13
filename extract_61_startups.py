import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Get the 61 Mixed cluster startups
c.execute('''
SELECT startup_id, cluster_id
FROM startup_extended
WHERE cluster_id IN (0, 1)
ORDER BY startup_id
''')

startups = c.fetchall()

print(f"61 STARTUPS IN MIXED CLUSTERS (NEED EXTERNAL DATA):\n")
print("startup_id,cluster_id")
for startup_id, cluster_id in startups:
    print(f"{startup_id},{cluster_id}")

conn.close()
