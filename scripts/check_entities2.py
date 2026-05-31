"""Check which Corteva/Bayer/FINEP targets exist in DB"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

# Check corteva_catalyst entity
print("=== Corteva entities ===")
for r in conn.execute(
    "SELECT entity_id, canonical_name, entity_type FROM entities WHERE entity_id LIKE '%corteva%' OR LOWER(canonical_name) LIKE '%corteva%'"
):
    print(" ", r)

# Check Corteva Catalyst portfolio companies that might be LATAM
print("\n=== Corteva Catalyst LATAM candidates ===")
for name in ["puna bio", "puna_bio", "puna-bio", "ibi ag", "ibi-ag", "solasta", "micropep", "tropic"]:
    like = "%" + name + "%"
    r1 = conn.execute(
        "SELECT entity_id, canonical_name FROM entities WHERE LOWER(canonical_name) LIKE ?", (like,)
    ).fetchall()
    r2 = conn.execute(
        "SELECT se.startup_id, se.business_one_liner FROM startup_extended se WHERE se.startup_id LIKE ? OR LOWER(se.business_one_liner) LIKE ?",
        (like, like),
    ).fetchall()
    if r1 or r2:
        print(f"  FOUND {name}: entities={r1} | startups={r2}")

# Check Bayer Legado finalists not already found
print("\n=== Bayer Legado other candidates ===")
for name in ["growcast", "apolo", "b.health", "bhealth", "b-health"]:
    like = "%" + name + "%"
    r1 = conn.execute(
        "SELECT entity_id, canonical_name FROM entities WHERE LOWER(canonical_name) LIKE ?", (like,)
    ).fetchall()
    r2 = conn.execute(
        "SELECT se.startup_id, se.business_one_liner FROM startup_extended se WHERE se.startup_id LIKE ? OR LOWER(se.business_one_liner) LIKE ?",
        (like, like),
    ).fetchall()
    if r1 or r2:
        print(f"  FOUND {name}: entities={r1} | startups={r2}")

# Check what are existing validation_edges for corteva
print("\n=== Existing Corteva validation edges ===")
for r in conn.execute(
    "SELECT * FROM validation_edges WHERE counterparty_entity_id='corteva_catalyst' OR counterparty_entity_id='corteva'"
):
    print(" ", r)

# Check existing Bayer edges
print("\n=== Existing Bayer support/validation edges ===")
for r in conn.execute(
    "SELECT * FROM support_edges WHERE source_entity_id='bayer_crop' OR target_entity_id='bayer_crop'"
):
    print("  support:", r)
for r in conn.execute(
    "SELECT * FROM validation_edges WHERE counterparty_entity_id='bayer_crop'"
):
    print("  validation:", r)

# Check puna_bio specifically
print("\n=== Puna Bio ===")
for r in conn.execute("SELECT entity_id, canonical_name, entity_type FROM entities WHERE entity_id LIKE '%puna%'"):
    print(" entity:", r)
for r in conn.execute("SELECT investment_id, investor_id, startup_id FROM investment_edges WHERE startup_id LIKE '%puna%'"):
    print(" investment:", r)

print("done")
