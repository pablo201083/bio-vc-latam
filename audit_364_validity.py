import sqlite3

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("AUDIT: VALIDEZ DE 364 UNCLUSTERED STARTUPS")
print("=" * 80)

# Get unclustered with any identifying info
c.execute('''
SELECT
  startup_id,
  business_one_liner,
  startup_summary_en,
  (SELECT COUNT(*) FROM founder_edges fe WHERE fe.startup_id = se.startup_id) as founder_count,
  (SELECT COUNT(*) FROM investment_edges ie WHERE ie.startup_id = se.startup_id) as investor_count
FROM startup_extended se
WHERE cluster_id = -1
ORDER BY startup_id
''')

unclustered = c.fetchall()

print(f"\nTOTAL: {len(unclustered)}\n")

# Categorize by validity signals
validity_categories = {
    'with_investors_and_desc': 0,
    'with_investors_no_desc': 0,
    'with_founders_no_investors': 0,
    'with_desc_only': 0,
    'with_summary_only': 0,
    'phantom': 0
}

details_by_category = {}

for sid, desc, summary, founder_count, investor_count in unclustered:
    if investor_count and investor_count > 0 and (desc or summary):
        cat = 'with_investors_and_desc'
    elif investor_count and investor_count > 0:
        cat = 'with_investors_no_desc'
    elif founder_count and founder_count > 0:
        cat = 'with_founders_no_investors'
    elif desc and desc.strip() != '':
        cat = 'with_desc_only'
    elif summary and summary.strip() != '':
        cat = 'with_summary_only'
    else:
        cat = 'phantom'

    validity_categories[cat] += 1

    if cat not in details_by_category:
        details_by_category[cat] = []
    details_by_category[cat].append({
        'id': sid,
        'desc': desc[:50] if desc else None,
        'investors': investor_count
    })

print("VALIDITY BREAKDOWN:\n")

for cat in ['with_investors_and_desc', 'with_investors_no_desc', 'with_founders_no_investors',
            'with_desc_only', 'with_summary_only', 'phantom']:
    count = validity_categories[cat]
    pct = 100 * count // len(unclustered)
    print(f"{cat}: {count} ({pct}%)")

print("\nDETAILES:\n")

# High priority (have investor/founder data)
high_priority = validity_categories['with_investors_and_desc'] + validity_categories['with_investors_no_desc']
print(f"HIGH PRIORITY (have real investor data): {high_priority}")
if high_priority > 0:
    print(f"  - With both investors + description: {validity_categories['with_investors_and_desc']}")
    print(f"  - With investors only: {validity_categories['with_investors_no_desc']}")

# Medium priority
medium_priority = validity_categories['with_desc_only'] + validity_categories['with_founders_no_investors']
print(f"\nMEDIUM PRIORITY (partial data): {medium_priority}")
if medium_priority > 0:
    print(f"  - With description: {validity_categories['with_desc_only']}")
    print(f"  - With founders: {validity_categories['with_founders_no_investors']}")

# Low priority
low_priority = validity_categories['with_summary_only']
print(f"\nLOW PRIORITY (summary only): {low_priority}")

# Phantom entries
phantom = validity_categories['phantom']
print(f"\nPHANTOM ENTRIES (zero signals): {phantom} ({100*phantom//len(unclustered)}%)")
print(f"  These need validation against external sources")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)
print(f"\n1. Research HIGH PRIORITY first ({high_priority} startups)")
print(f"2. Then MEDIUM PRIORITY ({medium_priority})")
print(f"3. Flag {phantom} phantom entries for manual validation")

conn.close()
