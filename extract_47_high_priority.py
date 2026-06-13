import sqlite3
import csv

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

# Get the 47 HIGH PRIORITY startups (investors + desc)
c.execute('''
SELECT
  se.startup_id,
  se.business_one_liner,
  COUNT(DISTINCT ie.investor_id) as investor_count
FROM startup_extended se
LEFT JOIN investment_edges ie ON ie.startup_id = se.startup_id
WHERE se.cluster_id = -1
  AND se.business_one_liner IS NOT NULL
  AND se.business_one_liner != ""
GROUP BY se.startup_id, se.business_one_liner
HAVING investor_count > 0
ORDER BY investor_count DESC, se.startup_id
''')

high_priority = c.fetchall()

print("=" * 80)
print("47 HIGH PRIORITY STARTUPS (with investor data + description)")
print("=" * 80)
print(f"\nTotal: {len(high_priority)}\n")

# Group by investor count
by_investor_count = {}
for sid, desc, inv_count in high_priority:
    if inv_count not in by_investor_count:
        by_investor_count[inv_count] = []
    by_investor_count[inv_count].append((sid, desc))

# Show distribution
print("Distribution by investor count:")
for inv_count in sorted(by_investor_count.keys(), reverse=True):
    startups = by_investor_count[inv_count]
    print(f"  {inv_count} investors: {len(startups)} startups")

# Export to CSV for research
out_path = 'staging/research_47_high_priority.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['startup_id', 'current_description', 'investor_count', 'research_priority'])

    for sid, desc, inv_count in high_priority:
        priority = 'CRITICAL' if inv_count >= 5 else 'HIGH' if inv_count >= 2 else 'MEDIUM'
        writer.writerow([sid, desc[:100] if desc else '(incomplete)', inv_count, priority])

print(f"\nExported to: {out_path}")
print(f"Sample (first 10):")
for i, (sid, desc, inv_count) in enumerate(high_priority[:10], 1):
    print(f"  {i}. {sid} ({inv_count} investors)")
    print(f"     {desc[:70]}...")

conn.close()
