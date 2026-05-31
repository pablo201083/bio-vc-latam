"""
Aplica los datos de enriquecimiento web a startup_extended con audit_log.
"""
import sqlite3, pathlib, datetime, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
now = datetime.datetime.now(datetime.UTC).isoformat()

enrichments = [
    {
        "startup_id": "sistema-bio-mx",
        "business_one_liner": "Designs modular biodigesters that convert animal waste into biogas and organic fertilizer for smallholder farmers.",
        "emergent_theme": "waste-to-energy biodigesters",
        "technology_tags": "modular biodigesters, biogas generation, bioslurry fertilizer, smallholder agriculture",
    },
    {
        "startup_id": "calice-ai-ar",
        "business_one_liner": "Virtual field trials platform that simulates millions of crop product performance scenarios using G×E×M modeling.",
        "emergent_theme": "virtual crop trials AI",
        "technology_tags": "NODES platform, G×E×M modeling, probabilistic simulation, environmental fingerprinting, API integration",
    },
    {
        "startup_id": "hif-global-cl",
        "business_one_liner": "Converts renewable energy and captured CO₂ into drop-in synthetic e-fuels compatible with existing engines and infrastructure.",
        "emergent_theme": "green e-fuels synthesis",
        "technology_tags": "renewable electrolysis, CO₂ capture, e-fuel synthesis, green hydrogen",
    },
    {
        "startup_id": "neoprospecta-br",
        "business_one_liner": "Microbial risk mapping for food and pharma using DNA sequencing, PCR-LAMP and AI to predict contamination before it happens.",
        "emergent_theme": "predictive microbial quality control",
        "technology_tags": "16S/ITS sequencing, PCR-LAMP, whole genome sequencing, AI bioinformatics, next-generation sequencing",
    },
    {
        "startup_id": "ucrop-it-ar",
        "business_one_liner": "Satellite-backed traceability platform that verifies sustainable agricultural practices across agribusiness supply chains.",
        "emergent_theme": "satellite agri-traceability",
        "technology_tags": "satellite remote sensing, NDVI/EVI monitoring, blockchain traceability, land use change detection, EUDR compliance",
    },
    {
        "startup_id": "aimirim-br",
        "business_one_liner": "Digital twin and IoT platform that optimizes industrial fermentation and energy processes in sugarcane biorefineries.",
        "emergent_theme": "industrial bioprocess digital twin",
        "technology_tags": "digital twin, IoT sensors, AI analytics, process automation, industrial integration",
    },
    {
        "startup_id": "food-for-the-future-cl",
        "business_one_liner": "Transforms organic food waste into insect-based protein and biostimulants for aquaculture, poultry and agriculture using black soldier fly.",
        "emergent_theme": "insect bioconversion circular protein",
        "technology_tags": "black soldier fly, protein extraction, oil extraction, biostimulant production, HACCP-certified processing",
    },
    {
        "startup_id": "biofabrica-siglo-xxi-mx",
        "business_one_liner": "Develops microbial biofertilizers and bioinputs using beneficial microorganisms as sustainable alternatives to chemical fertilizers.",
        "emergent_theme": "microbial biofertilizers",
        "technology_tags": "microbial consortia, biofertilizers, agrobiotechnology, beneficial microorganisms, crop bioinputs",
    },
]

def log(cur, entity_id, field, old_val, new_val, reason, now):
    cur.execute(
        """INSERT INTO audit_log (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)""",
        (now, "web:scrape", entity_id, "startup_extended", field, str(old_val) if old_val else None, new_val, reason),
    )

print("=== Aplicando enriquecimiento web ===\n")
applied = 0
for e in enrichments:
    sid = e["startup_id"]
    cur.execute(
        "SELECT canonical_name FROM entities WHERE entity_id=?", (sid,))
    row = cur.fetchone()
    name = row[0] if row else sid

    fields = {k: v for k, v in e.items() if k != "startup_id"}
    set_parts = []
    vals = []
    for field, new_val in fields.items():
        cur.execute(f"SELECT {field} FROM startup_extended WHERE startup_id=?", (sid,))
        r = cur.fetchone()
        old_val = r[0] if r else None
        set_parts.append(f"{field}=?")
        vals.append(new_val)
        log(cur, sid, field, old_val, new_val, "web scraping: enriched from company website", now)

    vals.append(sid)
    cur.execute(f"UPDATE startup_extended SET {', '.join(set_parts)} WHERE startup_id=?", vals)
    print(f"  OK {name}")
    print(f"     one_liner  : {fields['business_one_liner']}")
    print(f"     emergent   : {fields['emergent_theme']}")
    print(f"     tech_tags  : {fields['technology_tags']}")
    print()
    applied += 1

conn.commit()
conn.close()
print(f"Total aplicados: {applied}")
