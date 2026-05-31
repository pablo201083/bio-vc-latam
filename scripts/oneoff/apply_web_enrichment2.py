"""Aplica enriquecimiento web (búsqueda + scraping) para los 10 restantes."""
import sqlite3, pathlib, datetime, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

db = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
now = datetime.datetime.now(datetime.UTC).isoformat()

enrichments = [
    {
        "startup_id": "praxis-biotech-cl",
        "business_one_liner": "Drug discovery company targeting apoptosis and cell survival pathways for cancer and neurodegenerative diseases, spun from UC Chile.",
        "emergent_theme": "apoptosis-targeted drug discovery",
        "technology_tags": "small molecule discovery, apoptosis modulation, cell survival pathways, cancer therapeutics, neurodegenerative drugs",
    },
    {
        "startup_id": "tarvos-br",
        "business_one_liner": "Deploys AI-powered automated traps with computer vision to monitor and predict agricultural pest infestations at 95% accuracy.",
        "emergent_theme": "AI automated pest trap monitoring",
        "technology_tags": "computer vision, automated traps, biostatistical modeling, satellite data, pest identification AI",
    },
    {
        "startup_id": "bioin-br",
        "business_one_liner": "Combines Trichogramma pretiosum biocontrol cards with the SaveIn digital platform to predict and suppress crop pest infestations.",
        "emergent_theme": "integrated biocontrol and digital monitoring",
        "technology_tags": "Trichogramma biocontrol, biological insecticides, digital pest monitoring, predictive analytics, soy and corn crops",
    },
    {
        "startup_id": "rnatech-ar",
        "business_one_liner": "Discovers RNA-based bioactive functional ingredients from natural sources using the Serkanto-AI platform for supplements and functional foods.",
        "emergent_theme": "dietary RNA functional ingredients",
        "technology_tags": "Serkanto-AI, dietary RNA extraction, bioactive ingredients, functional food, AI-guided ingredient discovery",
    },
    {
        "startup_id": "ecotrace-br",
        "business_one_liner": "Blockchain, IoT and AI platform tracking agribusiness commodity supply chains end-to-end, having traced 6M+ tons across Brazil.",
        "emergent_theme": "blockchain agri-commodity traceability",
        "technology_tags": "blockchain, IoT sensors, computer vision, AI/ML, supply chain traceability, commodity tracking",
    },
    {
        "startup_id": "treevia-br",
        "business_one_liner": "Forest intelligence platform using IoT sensors and machine learning to remotely monitor forest growth, health and carbon capture at scale.",
        "emergent_theme": "smart forest IoT carbon monitoring",
        "technology_tags": "IoT forest sensors, machine learning, SmartForest system, carbon quantification, forest inventory, remote sensing",
    },
    {
        "startup_id": "pharmalens-br",
        "business_one_liner": "Applies computer vision and machine learning to automate visual defect detection and quality control in pharmaceutical and biotech manufacturing.",
        "emergent_theme": "AI visual QC in pharma manufacturing",
        "technology_tags": "computer vision, machine learning, defect detection, pharmaceutical QC, biotech manufacturing automation",
    },
    {
        "startup_id": "baxxis-medtech-cl",
        "business_one_liner": "Develops an intelligent knee prosthesis for ACL replacement with embedded sensors for real-time postoperative biomechanical tracking.",
        "emergent_theme": "smart orthopedic implants",
        "technology_tags": "smart prosthetics, embedded sensors, ACL reconstruction, real-time postoperative monitoring, orthopedic medtech",
    },
    {
        "startup_id": "agrosustain-mx",
        "business_one_liner": "Develops eco-friendly biopesticides targeting fungal crop infections to reduce chemical pesticide dependency for Mexican farmers.",
        "emergent_theme": "antifungal biopesticides",
        "technology_tags": "biopesticides, biofungicides, antifungal biotech, crop protection, sustainable agriculture",
    },
    {
        "startup_id": "botanical-solution-inc-cl",
        "business_one_liner": "Cultivates Quillaja saponaria trees via plant tissue culture as biofactories for biofungicide and vaccine adjuvant QS-21.",
        "emergent_theme": "plant tissue culture biofactories",
        "technology_tags": "plant tissue culture, Quillaja saponaria, biofungicide, QS-21 adjuvant, biofactory platform",
    },
]

def log(cur, entity_id, field, old_val, new_val, reason, now):
    cur.execute(
        """INSERT INTO audit_log (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?,?,?,?,?,?,?,?)""",
        (now, "web:search+scrape", entity_id, "startup_extended", field, str(old_val) if old_val else None, new_val, reason),
    )

print("=== Aplicando enriquecimiento web (batch 2) ===\n")
applied = 0
for e in enrichments:
    sid = e["startup_id"]
    cur.execute("SELECT canonical_name FROM entities WHERE entity_id=?", (sid,))
    row = cur.fetchone()
    name = row[0] if row else sid

    fields = {k: v for k, v in e.items() if k != "startup_id"}
    set_parts, vals = [], []
    for field, new_val in fields.items():
        cur.execute(f"SELECT {field} FROM startup_extended WHERE startup_id=?", (sid,))
        r = cur.fetchone()
        old_val = r[0] if r else None
        set_parts.append(f"{field}=?")
        vals.append(new_val)
        log(cur, sid, field, old_val, new_val, "web search/scrape: enriched from public sources", now)

    vals.append(sid)
    cur.execute(f"UPDATE startup_extended SET {', '.join(set_parts)} WHERE startup_id=?", vals)
    print(f"  OK {name}")
    applied += 1

conn.commit()
conn.close()
print(f"\nTotal aplicados: {applied}")
print("\nPróximo paso: python pipeline.py rebuild --phase embeddings")
