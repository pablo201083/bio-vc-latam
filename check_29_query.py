import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("Query 1: cluster_id = -1 AND review_status != 'EXCLUDE'")
c.execute("SELECT COUNT(*) FROM startup_extended WHERE cluster_id = -1 AND review_status != 'EXCLUDE'")
print(f"Result: {c.fetchone()[0]}\n")

print("Query 2: cluster_id = -1 AND (review_status IS NULL OR review_status != 'EXCLUDE')")
c.execute("SELECT COUNT(*) FROM startup_extended WHERE cluster_id = -1 AND (review_status IS NULL OR review_status != 'EXCLUDE')")
print(f"Result: {c.fetchone()[0]}\n")

print("Query 3: cluster_id = -1 AND review_status NOT IN ('EXCLUDE')")
c.execute("SELECT COUNT(*) FROM startup_extended WHERE cluster_id = -1 AND review_status NOT IN ('EXCLUDE')")
print(f"Result: {c.fetchone()[0]}\n")

print("Query 4: cluster_id = -1 (all unclustered)")
c.execute("SELECT COUNT(*) FROM startup_extended WHERE cluster_id = -1")
print(f"Result: {c.fetchone()[0]}\n")

print("Query 5: cluster_id = -1 BREAKDOWN BY review_status")
c.execute("SELECT review_status, COUNT(*) FROM startup_extended WHERE cluster_id = -1 GROUP BY review_status")
for status, count in c.fetchall():
    print(f"  {status or '(null)'}: {count}")

conn.close()
