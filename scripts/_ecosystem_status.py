"""Ecosystem graph analytics report — Phase 5."""
import sqlite3

conn = sqlite3.connect('db/bio_latam.db')

print("=" * 58)
print("  ECOSYSTEM GRAPH — Estado v1")
print("=" * 58)

# Node counts by layer
print("\n  NODOS POR CAPA")
for t, label in [
    ("SELECT count(*) FROM entities WHERE entity_type='startup'",           "  startup"),
    ("SELECT count(*) FROM entities WHERE entity_type='investor'",           "  investor"),
    ("SELECT count(*) FROM entities WHERE entity_type='organization'",       "  organization"),
    ("SELECT count(*) FROM entities WHERE entity_type='eso'",               "  eso"),
    ("SELECT count(*) FROM entities WHERE entity_type='corporate'",         "  corporate"),
]:
    n = conn.execute(t).fetchone()[0]
    print(f"    {label:<20} {n:>5}")

total = conn.execute("SELECT count(*) FROM entities").fetchone()[0]
print(f"    {'TOTAL':<20} {total:>5}")

# Edge counts
print("\n  EDGES POR TIPO")
for t, label in [
    ("SELECT count(*) FROM investment_edges",                           "  investment"),
    ("SELECT count(*) FROM capital_relations",                          "  capital allocation"),
    ("SELECT count(*) FROM support_edges WHERE support_type='membership'", "  membership"),
    ("SELECT count(*) FROM support_edges WHERE support_type!='membership'","  support (otros)"),
    ("SELECT count(*) FROM validation_edges",                           "  validation"),
]:
    n = conn.execute(t).fetchone()[0]
    print(f"    {label:<26} {n:>5}")

# Ecosystem connectivity
print("\n  CONECTIVIDAD ECOSISTEMA")
eco_ids = [r[0] for r in conn.execute(
    "SELECT entity_id FROM entities WHERE entity_type IN ('organization','eso','corporate')"
).fetchall()]

for eid in eco_ids:
    name = conn.execute("SELECT canonical_name FROM entities WHERE entity_id=?", (eid,)).fetchone()[0]
    etype = conn.execute("SELECT entity_type FROM entities WHERE entity_id=?", (eid,)).fetchone()[0]
    degree = conn.execute(
        "SELECT count(*) FROM support_edges WHERE source_entity_id=? OR target_entity_id=?", (eid, eid)
    ).fetchone()[0]
    vdegree = conn.execute(
        "SELECT count(*) FROM validation_edges WHERE startup_id=? OR counterparty_entity_id=?", (eid, eid)
    ).fetchone()[0]
    total_deg = degree + vdegree
    status = "CONECTADO" if total_deg > 0 else "aislado"
    print(f"    [{etype:12}] {name:<35} deg={total_deg} {status}")

# Coverage
print("\n  COBERTURA DE INVERSIONES")
include = conn.execute(
    "SELECT count(*) FROM startup_extended WHERE scope_decision='include'"
).fetchone()[0]
funded = conn.execute(
    """SELECT count(DISTINCT ie.startup_id)
       FROM investment_edges ie
       JOIN startup_extended sx ON sx.startup_id=ie.startup_id
       WHERE sx.scope_decision='include'"""
).fetchone()[0]
pct = funded/include*100 if include else 0
print(f"    Startups include: {include}")
print(f"    Con al menos 1 edge: {funded} ({pct:.1f}%)")
print(f"    Sin edge todavia: {include-funded} ({100-pct:.1f}%)")

# ARCAP members
print("\n  MIEMBROS ARCAP REGISTRADOS")
for r in conn.execute(
    """SELECT e.canonical_name FROM support_edges se
       JOIN entities e ON e.entity_id=se.target_entity_id
       WHERE se.source_entity_id='arcap' AND se.support_type='membership'"""
).fetchall():
    print(f"    - {r[0]}")

print("\n  PROXIMOS PASOS")
print("    1. Agregar mas miembros ARCAP en manual_support_edges.csv")
print("    2. Agregar relaciones ESO→startup (incubacion, grants)")
print("    3. Agregar validation edges startup↔corporate (pilotos)")
print("    4. Enriquecer con AAPRESID/CREA member startups")
print()

conn.close()
