import json
with open('scripts/oneoff/sizing_queue.json') as f:
    data = json.load(f)
tier2plus = [d for d in data if d['val_tier'] and float(d['val_tier']) >= 2]
print(f'Tier 2+: {len(tier2plus)} startups')
for d in tier2plus:
    print(f"  [T{d['val_tier']}] {d['name'][:35]:35s} | {d['country']} | {d['website']} | ${d['val_usd']}M | {d['last_funding_at']}")
