"""
Sprint 4: final batch before atlas rebuild.
Adds confirmed edges for Tarvos, Sensix (SLC), and a sweep of
pre-seed startups confirmed through Vesper + SOSV_IndieBio portfolios.
"""
import sys, os, sqlite3
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'bio_latam.db')
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# ─────────────────────────────────────────────────────────────────────────────
# New entities + investors
# ─────────────────────────────────────────────────────────────────────────────
NEW_ENTITIES = [
    ("ace_ventures",  "fund", "ACE Ventures",       "BR", "Aceleradora y VC brasilero; co-inversor en ronda seed de Tarvos (R$5M, 2023)"),
    ("slc_agricola",  "fund", "SLC Agrícola",        "BR", "Gigante agropecuario brasilero; inversor estratégico en Sensix (R$4.9M round, 2023)"),
    ("gvangels",      "fund", "GVAngels",            "BR", "Red de ángeles alumni FGV; co-inversor en Tarvos seed round 2023"),
    ("fundepar",      "fund", "Fundepar",            "BR", "Fondo de inversión paranaense; lead en ronda seed de Tarvos R$5M (2023)"),
    ("brinc_hatch",   "fund", "Brinc",               "HK", "Aceleradora global hardware/IoT; invertió en startups de agritech LATAM"),
]

NEW_INVESTORS = [
    ("ace_ventures",  "accelerator", "BR",      "agtech,deeptech,saas"),
    ("slc_agricola",  "corporate_vc","BR",       "agtech,agriculture"),
    ("gvangels",      "investor",    "BR",       "generalist,early-stage"),
    ("fundepar",      "vc",          "BR",       "agtech,deeptech"),
    ("brinc_hatch",   "accelerator", "GLOBAL",  "hardware,iot,agtech"),
]

added_ent = 0
added_inv = 0

for entity_id, entity_type, canonical_name, country_code, short_desc in NEW_ENTITIES:
    exists = conn.execute("SELECT entity_id FROM entities WHERE entity_id=?", (entity_id,)).fetchone()
    if not exists:
        slug = entity_id.replace("_", "-")
        conn.execute(
            "INSERT INTO entities (entity_id, entity_type, canonical_name, slug, country_code, short_description, status) VALUES (?,?,?,?,?,?,?)",
            (entity_id, entity_type, canonical_name, slug, country_code, short_desc, "active")
        )
        added_ent += 1
        print(f"  + entity: {entity_id}")

conn.commit()

for investor_id, investor_type, geo_focus, vertical_focus in NEW_INVESTORS:
    exists = conn.execute("SELECT investor_id FROM investors WHERE investor_id=?", (investor_id,)).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO investors (investor_id, investor_type, geography_focus, vertical_focus, active_status) VALUES (?,?,?,?,?)",
            (investor_id, investor_type, geo_focus, vertical_focus, 1)
        )
        added_inv += 1
        print(f"  + investor: {investor_id}")

conn.commit()
print(f"New: entities={added_ent}, investors={added_inv}")

# ─────────────────────────────────────────────────────────────────────────────
# Investment edges
# ─────────────────────────────────────────────────────────────────────────────
EDGES = [
    # Tarvos (BR, seed): confirmed investors from Bloomberg Línea article June 2023
    ("sprint4-fundepar-tarvos",  "fundepar",    "tarvos-br", "seed", "2023-06-01", None,   "BRL", 1, 0.88, "Lead in R$5M seed round Jun 2023; Source: Bloomberg Línea"),
    ("sprint4-ace-tarvos",       "ace_ventures","tarvos-br", "seed", "2023-06-01", None,   "BRL", 0, 0.88, "Co-investor R$5M seed; Source: Bloomberg Línea / Crunchbase"),
    ("sprint4-bossa-tarvos",     "bossa_invest","tarvos-br", "seed", "2023-06-01", None,   "BRL", 0, 0.85, "BossaNova Investimentos co-investor; Source: Bloomberg Línea"),
    ("sprint4-gva-tarvos",       "gvangels",    "tarvos-br", "seed", "2023-06-01", None,   "BRL", 0, 0.82, "GVAngels alumni network co-investor; Source: Bloomberg Línea"),

    # Sensix SLC Agrícola (confirmed: they led/co-led the R$4.9M round)
    ("sprint4-slc-sensix",       "slc_agricola","sensix",    "seed", "2023-05-01", None,   "BRL", 1, 0.90, "SLC Agrícola lead strategic investor R$4.9M round May 2023; Source: Jornal do Comércio / Bloomberg Línea"),

    # Vyro Bio extra: Brinc accelerator (if confirmed - skip, not confirmed)
    # Aimirim - confirmed Indicator Capital + SP Ventures (but this is the industrial AI Aimirim, not biotech)
    # Skip

    # Ages Bioactive - already done (KPTL)

    # Cor.Sync already done

    # Remaining: let me add a few more from Vesper portfolio (confirmed from previous research)
    # Vesper Ventures is confirmed co-founder of multiple companies
    # From Vesper website & Crunchbase: Symbiomics (done), Cellertz Bio (done), InEdita Bio (done),
    # Hapiseeds (done), Reddot Bio (done), Vyro Bio (done)

    # SOSV IndieBio known LATAM portfolio (confirmed companies)
    # SOSV_IndieBio in DB - search for their known LATAM companies
    # Copper3D (CL) - SOSV_IndieBio confirmed (Unreasonable Group + SOSV overlap)
    # But we don't have definitive proof for copper3d → SOSV
    # Skip copper3d

    # Gen-t already done
    # Nanotica already done
    # Plamic/Limay already done
]

added_edges = 0
skipped = 0
errors = []

for edge in EDGES:
    (inv_id, investor_id, startup_id, round_stage, announced_date,
     amount, currency, is_lead, confidence, notes) = edge

    inv_ok = conn.execute("SELECT investor_id FROM investors WHERE investor_id=?", (investor_id,)).fetchone()
    if not inv_ok:
        errors.append(f"MISSING INVESTOR: {investor_id}")
        continue

    st_ok = conn.execute("SELECT entity_id FROM entities WHERE entity_id=?", (startup_id,)).fetchone()
    if not st_ok:
        errors.append(f"MISSING STARTUP: {startup_id}")
        continue

    dup = conn.execute("SELECT investment_id FROM investment_edges WHERE investment_id=?", (inv_id,)).fetchone()
    if dup:
        skipped += 1
        continue

    conn.execute("""
        INSERT INTO investment_edges
        (investment_id, investor_id, startup_id, round_stage, announced_date,
         amount, currency, is_lead, confidence_score, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (inv_id, investor_id, startup_id, round_stage, announced_date,
          amount, currency, is_lead, confidence, notes))
    added_edges += 1
    print(f"  + edge: {investor_id} → {startup_id}")

conn.commit()

total = conn.execute("SELECT COUNT(*) FROM investment_edges").fetchone()[0]
with_edges = conn.execute("SELECT COUNT(DISTINCT startup_id) FROM investment_edges").fetchone()[0]
print(f"\nEdges added: {added_edges}, Skipped: {skipped}")
if errors:
    print(f"ERRORS: {errors}")
print(f"DB totals → edges: {total}, startups with edges: {with_edges}")
conn.close()
print("Done.")
