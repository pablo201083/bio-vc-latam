"""
add_missing_websites.py
-----------------------
Agrega websites faltantes en entities para inversores conocidos.
Solo rellena con COALESCE (no pisa datos existentes).
Fuentes: investigación web previa + conocimiento directo.
"""
import sqlite3, sys, os
sys.stdout.reconfigure(encoding="utf-8")
DB = os.path.join(os.path.dirname(__file__), "..", "..", "db", "bio_latam.db")
conn = sqlite3.connect(DB)

# (investor_id, website)
WEBSITES = [
    # inversores con research previo
    ("ace_ventures",            "https://www.ace.vc"),
    ("alexia_ventures",         "https://alexia.vc"),
    ("bago",                    "https://www.bago.com.ar"),
    ("bradesco",                "https://www.bradesco.com.br"),
    ("biominas",                "https://biominas.org.br"),
    ("bossa_invest",            "https://bossanova.vc"),
    ("brinc",                   "https://brinc.io"),
    ("brinc_hatch",             "https://www.hatch.blue"),
    ("caf",                     "https://www.caf.com"),
    ("domo_invest",             "https://www.domoinvest.com.br"),
    ("draper_associates",       "https://draper.vc"),
    ("draper_university",       "https://draperuniversity.com"),
    ("dynamo",                  "https://www.dynamo.com.br"),
    ("eurofarma",               "https://eurofarma.com"),
    ("future_ventures",         "https://future.ventures"),
    ("gavea_investimentos",     "https://www.gaveainvest.com.br"),
    ("hatch_blue",              "https://www.hatch.blue"),
    ("hawthorne_food_ventures", "https://www.hawthornefoodventures.com"),
    ("horizons_ventures",       "https://www.horizonsventures.com"),
    ("ifc",                     "https://www.ifc.org"),
    ("la_turbina",              "https://laturbina.com.ar"),
    ("lanx_capital",            "https://lanxcapital.com.br"),
    ("lavca",                   "https://lavca.org"),
    ("left_lane_capital",       "https://www.leftlane.com"),
    ("oxygea",                  "https://oxygea.com.br"),
    ("ospraie",                 "https://ospraie.com"),
    ("partners_for_growth",     "https://pfgrowth.com"),
    ("positive_ventures",       "https://www.positiveventures.com"),
    ("primatec",                "https://primatec.com.br"),
    ("slc_agricola",            "https://www.slcagricola.com.br"),
    ("svb_financial_group",     "https://www.svb.com"),
    ("third_sphere",            "https://www.thirdsphere.com"),
    ("venturance",              "https://venturance.cl"),
    ("waterlemon",              "https://www.waterlemon.vc"),
    ("biomerieux",              "https://www.biomerieux.com"),
    ("spectra_investments",     "https://spectrainvest.com"),
    ("gvangels",                "https://www.gvangels.com.br"),
    ("idb_natural_capital_lab", "https://bidlab.org"),
    ("innogen_capital",         "https://www.innogen.capital"),
    ("canary_vc",               "https://www.canary.com.br"),
    ("atlantico",               "https://www.atlantico.vc"),
    ("500_latam",               "https://500.co"),
    ("oxygea",                  "https://oxygea.com.br"),
]

updated = 0
skipped = 0
not_found = []

for investor_id, website in WEBSITES:
    row = conn.execute(
        "SELECT entity_id, website FROM entities WHERE entity_id = ?", (investor_id,)
    ).fetchone()
    if not row:
        not_found.append(investor_id)
        continue
    if row[1]:  # ya tiene website
        skipped += 1
        continue
    conn.execute(
        "UPDATE entities SET website = ? WHERE entity_id = ?",
        (website, investor_id)
    )
    updated += 1
    print(f"  ✓ {investor_id:<40} → {website}")

conn.commit()
conn.close()
print(f"\nActualizados: {updated}  Skipped (ya tenían): {skipped}")
if not_found:
    print(f"No encontrados: {not_found}")
