"""Exporta cola de startups para enriquecimiento de valuation, ordenadas por más antiguas."""
import sqlite3, json
db = sqlite3.connect('db/bio_latam.db')

rows = db.execute("""
    SELECT
        e.entity_id,
        e.canonical_name,
        e.country_code,
        e.website,
        se.valuation_estimate_usd,
        se.valuation_estimate_source,
        se.valuation_tier,
        se.funding_stage,
        se.last_funding_at,
        se.bio_theme_primary,
        e.short_description
    FROM startup_extended se
    JOIN entities e ON e.entity_id = se.startup_id
    WHERE se.is_bio_universe = 1
    ORDER BY
        -- Prioridad 1: tier más alto primero (más visibles en el mapa)
        COALESCE(se.valuation_tier, 0) DESC,
        -- Prioridad 2: fecha de funding más antigua
        COALESCE(se.last_funding_at, '2000-01-01') ASC,
        e.canonical_name ASC
""").fetchall()

cols = ['id','name','country','website','val_usd','val_source','val_tier','stage','last_funding_at','theme','description']
data = [dict(zip(cols, r)) for r in rows]

with open('scripts/oneoff/sizing_queue.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Total: {len(data)} startups exportadas")
print(f"\nTop 20 (más prioritarias):")
for d in data[:20]:
    print(f"  [{d['val_tier']}] {d['name']:35s} | {d['country']} | ${d['val_usd']}M ({d['val_source']}) | funding: {d['last_funding_at']}")
db.close()
