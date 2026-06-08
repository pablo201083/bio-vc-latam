import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect("db/bio_latam.db")

total     = conn.execute("SELECT COUNT(*) FROM investors").fetchone()[0]
with_blurb = conn.execute("SELECT COUNT(*) FROM investors WHERE profile_blurb IS NOT NULL AND profile_blurb != ''").fetchone()[0]
print(f"Total inversores : {total}")
print(f"Con blurb        : {with_blurb}")
print(f"Sin blurb        : {total - with_blurb}")

print("\n--- Spectra Investments ---")
r = conn.execute("""
    SELECT i.investor_id, e.canonical_name, i.investor_type, i.aum_usd_m,
           i.preferred_stages, i.geography_focus,
           length(i.profile_blurb) as blurb_len,
           substr(i.profile_blurb, 1, 200) as preview
    FROM investors i JOIN entities e ON i.investor_id = e.entity_id
    WHERE i.investor_id = 'spectra_investments'
""").fetchone()
if r:
    for label, val in zip(
        ["ID","Nombre","Tipo","AUM_USD_M","Stages","Geo","Blurb chars","Preview"],
        r
    ):
        print(f"  {label:<15}: {val}")
else:
    print("  NO ENCONTRADO")

conn.close()
