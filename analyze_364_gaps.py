import sqlite3
import csv

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("ANALYZING 364 UNCLUSTERED STARTUPS - DATA GAPS")
print("=" * 80)

# Get the 364 unclustered startups
c.execute('''
SELECT
  startup_id,
  cluster_id,
  business_one_liner,
  startup_summary_en,
  tech_codes,
  industry_codes,
  bio_theme_primary
FROM startup_extended
WHERE cluster_id = -1
ORDER BY startup_id
''')

unclustered = c.fetchall()
print(f"\nTotal unclustered: {len(unclustered)}\n")

# Analyze gaps
gaps = {
    'no_desc': 0,
    'no_summary': 0,
    'no_tech': 0,
    'no_industry': 0,
    'no_theme': 0,
    'complete_null': 0
}

by_gap_type = {}

for sid, cid, desc, summary, tech, industry, theme in unclustered:
    gap_profile = []

    if not desc or desc.strip() == '':
        gaps['no_desc'] += 1
        gap_profile.append('desc')
    if not summary or summary.strip() == '':
        gaps['no_summary'] += 1
        gap_profile.append('summary')
    if not tech or tech.strip() == '':
        gaps['no_tech'] += 1
        gap_profile.append('tech')
    if not industry or industry.strip() == '':
        gaps['no_industry'] += 1
        gap_profile.append('industry')
    if not theme or theme.strip() == '':
        gaps['no_theme'] += 1
        gap_profile.append('theme')

    gap_key = '|'.join(gap_profile) if gap_profile else 'complete'
    if gap_key == '':
        gaps['complete_null'] += 1
        gap_key = 'complete_null'

    if gap_key not in by_gap_type:
        by_gap_type[gap_key] = []
    by_gap_type[gap_key].append(sid)

print("GAP ANALYSIS:")
print(f"  No description: {gaps['no_desc']}")
print(f"  No summary: {gaps['no_summary']}")
print(f"  No tech_codes: {gaps['no_tech']}")
print(f"  No industry_codes: {gaps['no_industry']}")
print(f"  No bio_theme: {gaps['no_theme']}")
print(f"\nGAP PROFILES (grouped):")
for gap_key in sorted(by_gap_type.keys(), key=lambda x: len(by_gap_type[x]), reverse=True):
    count = len(by_gap_type[gap_key])
    print(f"  {gap_key}: {count} startups")

# Export sample for research
sample_size = min(20, len(unclustered))
print(f"\nExporting first {sample_size} for research...\n")

out_path = 'staging/unclustered_364_for_research.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['startup_id', 'current_description', 'current_summary', 'gaps', 'research_priority'])

    for i, (sid, cid, desc, summary, tech, industry, theme) in enumerate(unclustered[:sample_size]):
        gaps_list = []
        if not desc or desc.strip() == '':
            gaps_list.append('desc')
        if not summary or summary.strip() == '':
            gaps_list.append('summary')
        if not tech or tech.strip() == '':
            gaps_list.append('tech')
        if not industry or industry.strip() == '':
            gaps_list.append('industry')

        gap_str = '|'.join(gaps_list) if gaps_list else 'complete'
        priority = 'CRITICAL' if gap_str == 'desc|summary|tech|industry' else 'HIGH' if 'desc' in gap_str else 'MEDIUM'

        writer.writerow([
            sid,
            desc[:50] if desc else '(empty)',
            summary[:50] if summary else '(empty)',
            gap_str,
            priority
        ])

print(f"Research template saved: {out_path}")
print(f"Total to research: {len(unclustered)}")

conn.close()
