"""Check Ganesha Lab investments"""
import sqlite3

conn = sqlite3.connect("db/bio_latam.db")

print("=== Ganesha Lab investment_edges ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE LOWER(investor_id) LIKE '%ganesha%'"):
    print(" ", r)

print("\n=== innovai investment ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='innovai'"):
    print("  inv:", r)

print("\n=== patagon-fiber investment ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='patagon-fiber'"):
    print("  inv:", r)

print("\n=== phagelab full edges ===")
for r in conn.execute("SELECT investor_id, startup_id FROM investment_edges WHERE startup_id='phagelab'"):
    print("  inv:", r)
for r in conn.execute("SELECT source_entity_id, target_entity_id, support_type FROM support_edges WHERE target_entity_id='phagelab'"):
    print("  sup:", r)
