import csv
from pathlib import Path

path = Path('canonical/manual_canonical_organizations.csv')
with path.open('r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['node_type'] in ('eso', 'corporate'):
            print(f"id={row['org_id']} | org_type={row.get('org_type')} | eso_type={row.get('eso_type')} | industry={row.get('industry')} | innovation_maturity={row.get('innovation_maturity')} | source_url={row.get('source_url')}")
