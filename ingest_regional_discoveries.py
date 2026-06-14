"""
Ingesta regional discoveries from agent research across LATAM:
  Peru: 20+ startups
  Ecuador: 7 startups
  Dominican Republic: 4 startups
  Venezuela: 2 startups

Inserts into startup_extended with:
  - Generated startup_id (format: startup_name-country_code)
  - cluster_id: -1 (not yet classified)
  - review_status: 'pending'
  - bio_theme_primary: NULL
  - data_quality_score: 0.7 (discovered via external research)
  - scope_decision: 'pending_regional_assessment'

Also inserts investment_edges for known investor-startup pairs with
confidence_score: 0.80-0.90 and source_id: 'REGIONAL_DISCOVERY'

All operations tracked in audit_log via diff_and_log_update()
"""

import sqlite3
import csv
from difflib import SequenceMatcher
from pathlib import Path
from datetime import datetime, timezone

from src.audit import diff_and_log_update, log_change
from src.utils import slugify, clean

DB_PATH = Path(__file__).parent / "db" / "bio_latam.db"
STAGING = Path(__file__).parent / "staging"


# ==========================================
# Regional discoveries by country
# ==========================================

PERU_STARTUPS = [
    # Aquaculture & water biotech
    ('AquaVida Biotech', 'PE', 'water & aquaculture biotech'),
    ('MicroAlgas Peru', 'PE', 'microalgae bioproducts'),
    ('Tilapia Innovations', 'PE', 'aquaculture genetics'),
    
    # Soil & agriculture
    ('SoilLab Peru', 'PE', 'soil microbiome analysis'),
    ('Nutritech Andina', 'PE', 'biofortification inputs'),
    ('TerraBiology Peru', 'PE', 'soil health biotech'),
    ('BioAmazonia', 'PE', 'rainforest-derived biotech'),
    ('PeruGrow Biotech', 'PE', 'precision agriculture biotech'),
    
    # Diagnostics & health
    ('Phage Solutions Peru', 'PE', 'phage therapy diagnostics'),
    ('LabBio Peru', 'PE', 'point-of-care diagnostics'),
    ('Andean Biotech', 'PE', 'altitude-adapted therapeutics'),
    
    # Food systems
    ('CacaoTech Peru', 'PE', 'cacao fermentation biotech'),
    ('AndesCrop Innovations', 'PE', 'andean crop improvement'),
    ('Quechua BioDynamics', 'PE', 'indigenous crop biotech'),
    
    # Manufacturing & ingredients
    ('BioFerment Peru', 'PE', 'fermentation biotech platform'),
    ('NaturalPeru Ingredients', 'PE', 'natural ingredient biotech'),
    ('BioExtracts Andino', 'PE', 'botanical extraction tech'),
    ('PeruChemicals Bio', 'PE', 'bio-based chemical synthesis'),
    ('EcoMyco Peru', 'PE', 'mycelium-based materials'),
    ('BioCatalyst Peru', 'PE', 'enzyme engineering'),
    ('PeruPharma Biotech', 'PE', 'indigenous medicine biotech'),
]

ECUADOR_STARTUPS = [
    ('AquaEcuador', 'EC', 'aquaculture biotech'),
    ('BioDiversidad Ecuador', 'EC', 'biodiversity-based biotech'),
    ('AgTech Andino', 'EC', 'andean agriculture biotech'),
    ('Cacao Innovations', 'EC', 'cacao fermentation'),
    ('EcuadorBio Solutions', 'EC', 'tropical biotech platform'),
    ('AmazonBiotech Ecuador', 'EC', 'amazon-derived compounds'),
    ('QuitoGenomics', 'EC', 'genomics & diagnostics'),
]

DR_STARTUPS = [
    ('SOS Biotech', 'DO', 'tropical medicine biotech'),
    ('Bontix', 'DO', 'biopesticides & biocontrols'),
    ('Agricultic', 'DO', 'agricultural biotech platform'),
    ('AgroDR Solutions', 'DO', 'caribbean agriculture biotech'),
]

VENEZUELA_STARTUPS = [
    ('PEGASI', 'VE', 'distributed biotech platform'),
    ('LataMed AI', 'VE', 'medical AI & diagnostics'),
]


# ==========================================
# Known investor-startup mappings
# (from regional agent research)
# ==========================================

INVESTOR_STARTUP_MAPPINGS = [
    # Peru connections
    ('SoilLab Peru', 'salkantay', 0.85),
    ('MicroAlgas Peru', 'carao', 0.85),
    ('AquaVida Biotech', 'blue_horizon', 0.75),
    ('Phage Solutions Peru', 'gridx', 0.80),
    ('Nutritech Andina', 'greentech_latam', 0.80),
    ('BioAmazonia', 'bluejay_ventures', 0.75),
    ('CacaoTech Peru', 'sosv_indiebio', 0.85),
    
    # Ecuador connections
    ('AquaEcuador', 'carao', 0.80),
    ('BioDiversidad Ecuador', 'bluejay_ventures', 0.80),
    ('AgTech Andino', 'antom', 0.75),
    
    # DR connections
    ('SOS Biotech', 'sosv_indiebio', 0.80),
    ('Bontix', 'gridx', 0.75),
    ('Agricultic', 'antom', 0.75),
]


def normalize_startup_name(name: str) -> str:
    """Normalize startup name: lowercase, hyphens for spaces, no special chars."""
    return slugify(name)


def generate_startup_id(name: str, country_code: str) -> str:
    """Generate startup_id in format: normalized_name-country_code.
    
    Example: 'AquaVida Biotech' + 'PE' -> 'aquavida-biotech-pe'
    """
    normalized = normalize_startup_name(name)
    return f"{normalized}-{country_code.lower()}"


def startup_exists(conn: sqlite3.Connection, startup_id: str) -> bool:
    """Check if startup already exists in startup_extended."""
    exists = conn.execute(
        "SELECT 1 FROM startup_extended WHERE startup_id=?", (startup_id,)
    ).fetchone()
    return exists is not None


def entity_exists(conn: sqlite3.Connection, entity_id: str) -> bool:
    """Check if entity exists in entities table."""
    exists = conn.execute(
        "SELECT 1 FROM entities WHERE entity_id=?", (entity_id,)
    ).fetchone()
    return exists is not None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    
    print("=" * 80)
    print("INGESTING REGIONAL DISCOVERIES")
    print("=" * 80)
    
    all_startups = (
        [(name, code, desc) for name, code, desc in PERU_STARTUPS] +
        [(name, code, desc) for name, code, desc in ECUADOR_STARTUPS] +
        [(name, code, desc) for name, code, desc in DR_STARTUPS] +
        [(name, code, desc) for name, code, desc in VENEZUELA_STARTUPS]
    )
    
    stats = {
        'total_candidates': len(all_startups),
        'new_startups_inserted': 0,
        'startups_skipped_existing': 0,
        'edges_created': 0,
        'edges_skipped_investor_missing': 0,
        'edges_skipped_startup_missing': 0,
        'by_country': {}
    }
    
    # Track inserted startup IDs for edge creation
    inserted_startup_ids = set()
    
    # ==========================================
    # Phase 1: Insert startups into startup_extended & entities
    # ==========================================
    
    print("\n[Phase 1] Inserting discovered startups...\n")
    
    for startup_name, country_code, description in all_startups:
        startup_id = generate_startup_id(startup_name, country_code)
        
        # Initialize country stats
        if country_code not in stats['by_country']:
            stats['by_country'][country_code] = {
                'inserted': 0,
                'skipped': 0,
                'edges': 0
            }
        
        # Check if startup already exists
        if startup_exists(conn, startup_id):
            print(f"  [SKIP] {startup_id:35} (already exists)")
            stats['startups_skipped_existing'] += 1
            stats['by_country'][country_code]['skipped'] += 1
            continue
        
        try:
            # Insert into entities table first
            canonical_name = startup_name
            slug = normalize_startup_name(startup_name)
            
            conn.execute(
                """
                INSERT INTO entities
                    (entity_id, entity_type, canonical_name, slug, country_code, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (startup_id, 'startup', canonical_name, slug, country_code, 'active')
            )
            
            # Insert into startup_extended
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO startup_extended
                    (startup_id, cluster_id, review_status, bio_theme_primary,
                     data_quality_score, scope_decision, last_reviewed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    startup_id,
                    -1,  # not yet classified
                    'pending',
                    None,  # NULL - pending classification
                    0.7,  # discovered via external research
                    'pending_regional_assessment',
                    now
                )
            )
            
            # Log the insertion
            log_change(
                conn,
                actor='pipeline:regional_discovery',
                entity_id=startup_id,
                field='entities.NEW',
                old_value=None,
                new_value=f'{canonical_name} ({country_code})',
                reason='Regional discovery ingest — external research validation',
                evidence_url=None,
            )
            
            log_change(
                conn,
                actor='pipeline:regional_discovery',
                entity_id=startup_id,
                field='startup_extended.NEW',
                old_value=None,
                new_value=f'pending_regional_assessment | {description}',
                reason='Regional discovery ingest — data_quality_score=0.7',
                evidence_url=None,
            )
            
            inserted_startup_ids.add(startup_id)
            stats['new_startups_inserted'] += 1
            stats['by_country'][country_code]['inserted'] += 1
            print(f"  [OK] {startup_id:35} ({startup_name:30}) {country_code}")
            
        except Exception as e:
            print(f"  [ERROR] {startup_id}: {e}")
            conn.rollback()
            conn = sqlite3.connect(DB_PATH)
            conn.execute("PRAGMA journal_mode=WAL")
    
    # ==========================================
    # Phase 2: Create investment edges
    # ==========================================
    
    print(f"\n[Phase 2] Creating investment edges ({len(INVESTOR_STARTUP_MAPPINGS)} mappings)...\n")
    
    for startup_name, investor_id, confidence in INVESTOR_STARTUP_MAPPINGS:
        startup_id = generate_startup_id(startup_name, 'PE')  # Default to Peru for mapping
        country_code = 'PE'
        
        # Check if both investor and startup exist
        if not entity_exists(conn, investor_id):
            print(f"  [SKIP] {investor_id:30} (investor not found)")
            stats['edges_skipped_investor_missing'] += 1
            continue
        
        if startup_id not in inserted_startup_ids:
            # Try to find the startup in the full list to get correct country
            found = False
            for name, code, _ in all_startups:
                if generate_startup_id(name, code) == startup_id:
                    country_code = code
                    found = True
                    break
            
            if not found or not entity_exists(conn, startup_id):
                print(f"  [SKIP] {startup_id:35} (startup not found or not newly inserted)")
                stats['edges_skipped_startup_missing'] += 1
                continue
        
        try:
            investment_id = f"REGIONAL_DISCOVERY_{investor_id}_{startup_id}"
            
            # Check for duplicate
            existing = conn.execute(
                "SELECT investment_id FROM investment_edges WHERE investor_id=? AND startup_id=?",
                (investor_id, startup_id)
            ).fetchone()
            
            if existing:
                print(f"  [SKIP] {investor_id:30} → {startup_id:35} (edge exists)")
                continue
            
            conn.execute(
                """
                INSERT INTO investment_edges
                    (investment_id, investor_id, startup_id, round_name, round_stage,
                     announced_date, amount, currency, is_lead, confidence_score,
                     source_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    investment_id,
                    investor_id,
                    startup_id,
                    'regional_discovery',
                    None,
                    None,
                    None,
                    None,
                    0,
                    confidence,
                    'REGIONAL_DISCOVERY',
                    f'{investor_id.replace("_", " ").title()} portfolio (regional research)'
                )
            )
            
            log_change(
                conn,
                actor='pipeline:regional_discovery',
                entity_id=startup_id,
                field='investment_edges.NEW',
                old_value=None,
                new_value=f'{investor_id} → {startup_id} (confidence={confidence})',
                reason='Regional discovery ingest — investor portfolio mapping',
                evidence_url=None,
            )
            
            stats['edges_created'] += 1
            if country_code in stats['by_country']:
                stats['by_country'][country_code]['edges'] += 1
            print(f"  [OK] {investor_id:30} → {startup_id:35} ({confidence:.2f})")
            
        except Exception as e:
            print(f"  [ERROR] Edge {investor_id} → {startup_id}: {e}")
            conn.rollback()
            conn = sqlite3.connect(DB_PATH)
            conn.execute("PRAGMA journal_mode=WAL")
    
    # ==========================================
    # Commit and report
    # ==========================================
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print("INGESTION SUMMARY")
    print("=" * 80)
    
    print(f"\nStartups ingested:")
    for country in sorted(stats['by_country'].keys()):
        country_stats = stats['by_country'][country]
        print(f"  {country}: {country_stats['inserted']} inserted, "
              f"{country_stats['skipped']} skipped (total edges: {country_stats['edges']})")
    
    print(f"\nTotal Summary:")
    print(f"  New startups inserted: {stats['new_startups_inserted']}")
    print(f"  Startups skipped (already exist): {stats['startups_skipped_existing']}")
    print(f"  Investment edges created: {stats['edges_created']}")
    print(f"  Edges skipped (investor missing): {stats['edges_skipped_investor_missing']}")
    print(f"  Edges skipped (startup missing): {stats['edges_skipped_startup_missing']}")
    
    # Final DB state
    conn = sqlite3.connect(DB_PATH)
    
    total_startups = conn.execute(
        "SELECT COUNT(*) FROM startup_extended"
    ).fetchone()[0]
    
    total_edges = conn.execute(
        "SELECT COUNT(*) FROM investment_edges"
    ).fetchone()[0]
    
    bio_startups = conn.execute(
        "SELECT COUNT(*) FROM startup_extended WHERE cluster_id >= 0"
    ).fetchone()[0]
    
    print(f"\nFinal database state:")
    print(f"  Total startups in startup_extended: {total_startups}")
    print(f"  Total investment edges: {total_edges}")
    print(f"  BIO cluster startups: {bio_startups}")
    
    conn.close()
    
    print("\n[DONE]")


if __name__ == '__main__':
    main()
