"""Check Ganesha Lab investments"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== Ganesha Lab investment_edges ===")
for r in conn.execute("SELECT investor_id, startup_id, investment_type FROM investment_edges WHERE investor_id LIKE '%ganesha%'"):
    print(" ", r)

print("\n=== innovai support/investment ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='innovai'"):
    print("  inv:", r)
for r in conn.execute("SELECT * FROM support_edges WHERE target_entity_id='innovai'"):
    print("  sup:", r)

print("\n=== patagon-fiber support/investment ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='patagon-fiber'"):
    print("  inv:", r)
for r in conn.execute("SELECT * FROM support_edges WHERE target_entity_id='patagon-fiber'"):
    print("  sup:", r)

# Also check if phagelab has any CORFO or Start-Up Chile edges
print("\n=== phagelab full edge history ===")
for r in conn.execute("SELECT investor_id, startup_id, investment_type FROM investment_edges WHERE startup_id='phagelab'"):
    print("  inv:", r)
for r in conn.execute("SELECT source_entity_id, target_entity_id, support_type FROM support_edges WHERE target_entity_id='phagelab'"):
    print("  sup:", r)
