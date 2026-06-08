"""
Enriquecimiento del Capital Atlas — Capa 2 + Capa 3.

- Agrega columna aum_usd_m a investors (schema upgrade)
- Limpia ghost shells: marca inactive los 0-deal sin datos
- Corrige investor_type para Grupo Insud y SOSV
- Agrega websites faltantes (AIR Capital, OneVC, Blue Horizon, Hatch, etc.)
- Completa thesis / preferred_stages / ticket / geography / verticals
- Todo via diff_and_log_update para audit trail

Fuentes: websites oficiales verificados 2026-06-07 via WebSearch.
"""

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

DB   = ROOT / "db" / "bio_latam.db"
ACTOR = "curator:enrich_capital_atlas"


# ── 1. Schema migration: add aum_usd_m if missing ────────────────────────────

def _add_column_if_missing(conn, table, col, col_type="REAL"):
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        print(f"  + columna {table}.{col} creada")
    except Exception:
        pass  # ya existe


# ── 2. Ghost shells — 0-deal type=investor sin datos ─────────────────────────

GHOST_SHELLS = [
    "duhau", "flia_duhau", "fundacion_para_el_progreso_de_la_medicina",
    "genesis_consortium", "grupo_peruanos", "happiness", "innogen_capital",
    "invariantes_fund", "jeff_wilke", "KEM Ventures", "kairetsu_angels",
    "kwb", "lartirigoyen", "losa_group", "managro", "other_angels",
    "other_small_investors", "paul_mcewan", "peruanos", "photon_fund",
    "sillicon_catalyst", "thrive", "vectr", "veronorte", "vx_fund",
]


# ── 3. Entity corrections (website + country) ─────────────────────────────────
#   Formato: entity_id -> {field: value}

ENTITY_UPDATES = {
    "AIR Capital": {
        "website": "https://www.aircapital.vc",
    },
    "onevc": {
        "website": "https://www.onevc.vc",
    },
    "blue_horizon": {
        "website": "https://www.bluehorizonventures.com",
        "country_code": "CH",
    },
    "hatch": {
        "website": "https://www.hatch.blue",
        "country_code": "NO",
    },
    "salkantay_ventures": {
        "website": "https://www.salkantay.vc",
        "country_code": "PE",
    },
    "araucaria_venture": {
        "website": "https://www.araucaria.vc",
        "country_code": "CL",
    },
    "varana_capital": {
        "website": "https://varanacapital.com",
        "country_code": "US",
    },
    "sosv": {
        "website": "https://sosv.com",
        "country_code": "US",
    },
    "grupo_insud": {
        "website": "https://www.grupoinsud.com",
        "country_code": "AR",
    },
    "500_latam": {
        "website": "https://500.co",
        "country_code": "US",
    },
    "amador": {
        "website": "https://amador.vc",
        "country_code": "CR",
    },
    "cantos": {
        "website": "https://cantos.vc",
        "country_code": "US",
    },
    "conservation_international": {
        "website": "https://www.conservation.org",
        "country_code": "US",
        "canonical_name": "Conservation International",
    },
}


# ── 4. Investor table updates ──────────────────────────────────────────────────
#   Formato: investor_id -> {field: value}
#   Campos disponibles: investor_type, thesis, preferred_stages, geography_focus,
#                       vertical_focus, ticket_min_usd, ticket_max_usd,
#                       lead_behavior, active_status, aum_usd_m

INVESTOR_UPDATES = {

    # ── AIR Capital (33 deals, $213M portfolio — más activo sin web) ───────────
    "AIR Capital": {
        "investor_type": "vc",
        "thesis": (
            "Argentine deep tech VC investing pre-seed to Series A in science-based "
            "biotech, agtech, healthtech and frontier technology startups across "
            "Argentina and Latin America. Focuses on disruptive innovation with "
            "global potential: AI, space tech, brain-computer interfaces, biotech "
            "and advanced materials."
        ),
        "preferred_stages": "pre-seed;seed;series-a",
        "geography_focus": "AR;LATAM",
        "vertical_focus": "biotech;agtech;healthtech;deeptech;spacetech",
        "ticket_min_usd": 200000.0,
        "ticket_max_usd": 3000000.0,
        "lead_behavior": "lead",
        "active_status": "active",
    },

    # ── OneVC (2 deals, Brazilian seed VC) ────────────────────────────────────
    "onevc": {
        "investor_type": "vc",
        "thesis": (
            "Brazilian seed and Series A VC run by former operators backing "
            "technology startups in Latin America. 50+ portfolio companies. "
            "Provides capital plus talent and people-strategy support."
        ),
        "preferred_stages": "seed;series-a",
        "geography_focus": "BR;LATAM",
        "vertical_focus": "tech;saas;healthtech;fintech",
        "ticket_min_usd": 500000.0,
        "ticket_max_usd": 5000000.0,
        "lead_behavior": "lead",
        "active_status": "active",
    },

    # ── Blue Horizon (2 deals, Swiss foodtech impact VC) ──────────────────────
    "blue_horizon": {
        "investor_type": "impact_fund",
        "thesis": (
            "Swiss impact VC (Zurich) backing the future of sustainable food systems. "
            "Fund I closed at EUR 183M; expanding with a planned $750M growth fund. "
            "Invests in alt proteins, cell-based food, fermentation and food waste "
            "reduction ventures globally including Latin America."
        ),
        "preferred_stages": "seed;series-a;series-b",
        "geography_focus": "EU;LATAM;Global",
        "vertical_focus": "foodtech;alt-protein;fermentation;sustainable-food",
        "ticket_min_usd": 1000000.0,
        "ticket_max_usd": 20000000.0,
        "lead_behavior": "lead",
        "active_status": "active",
        "aum_usd_m": 220.0,
    },

    # ── Hatch Blue (1 deal, Norwegian aquaculture accelerator) ────────────────
    "hatch": {
        "investor_type": "accelerator",
        "thesis": (
            "World's first aquaculture-focused accelerator. Bergen, Norway. "
            "3 funds totaling >€100M AUM, 60+ portfolio companies. "
            "Backs early-stage ventures reinventing aquaculture: nutrition, "
            "breeding, health, processing and monitoring technology. "
            "$130K ticket per cohort company ($75K cash + $55K in-kind)."
        ),
        "preferred_stages": "pre-seed;seed",
        "geography_focus": "NO;Global;LATAM",
        "vertical_focus": "aquaculture;foodtech;marinetech;biosensors",
        "ticket_min_usd": 75000.0,
        "ticket_max_usd": 200000.0,
        "lead_behavior": "lead",
        "active_status": "active",
        "aum_usd_m": 110.0,
    },

    # ── Salkantay Ventures (1 deal, Peruvian VC) ──────────────────────────────
    "salkantay_ventures": {
        "investor_type": "vc",
        "thesis": (
            "Peru-based early-stage VC (est. 2012) investing in technology founders "
            "building solutions for Latin America. Pre-seed through Series A. "
            "Pioneer institutional VC fund in Peru, backed by Swiss EP program."
        ),
        "preferred_stages": "pre-seed;seed;series-a",
        "geography_focus": "PE;LATAM",
        "vertical_focus": "agtech;foodtech;tech;fintech",
        "ticket_min_usd": 150000.0,
        "ticket_max_usd": 1500000.0,
        "lead_behavior": "both",
        "active_status": "active",
    },

    # ── Araucaria Venture (0 deals, Chilean agtech VC) ────────────────────────
    "araucaria_venture": {
        "investor_type": "vc",
        "thesis": (
            "Chilean VC fund based in Temuco (La Araucanía), led by women, "
            "backing Foodtech, Agtech and Climatech startups. Fund size ~$18M. "
            "Focus on aquaculture, fruit, livestock and seed industries in "
            "southern Chile and broader LATAM. Seed to late-seed."
        ),
        "preferred_stages": "seed;series-a",
        "geography_focus": "CL;LATAM",
        "vertical_focus": "agtech;foodtech;climate;aquaculture",
        "ticket_min_usd": 50000.0,
        "ticket_max_usd": 2000000.0,
        "lead_behavior": "lead",
        "active_status": "active",
        "aum_usd_m": 18.0,
    },

    # ── Varana Capital (1 deal, US/global deeptech VC — led Stämm's $17M) ─────
    "varana_capital": {
        "investor_type": "vc",
        "thesis": (
            "US-based asset manager (Denver, est. 2012) investing across VC, PE "
            "and public markets. Led Stämm Biotech's $17M Series A (2022). "
            "Active in global deeptech and biotech with selective LATAM exposure."
        ),
        "preferred_stages": "series-a;series-b",
        "geography_focus": "US;IL;AR;Global",
        "vertical_focus": "biotech;deeptech;technology",
        "lead_behavior": "lead",
        "active_status": "active",
    },

    # ── SOSV (main fund — parent of IndieBio, HAX, etc.) ─────────────────────
    "sosv": {
        "investor_type": "fund_of_funds",
        "thesis": (
            "New York-based multi-program VC ($1B+ AUM). Runs IndieBio (life sciences), "
            "HAX (hardware), dlab (China) and other accelerator programs. "
            "Pre-seed and seed focus globally. Parent entity — SOSV_IndieBio handles "
            "the biotech/LATAM pipeline specifically."
        ),
        "preferred_stages": "pre-seed;seed",
        "geography_focus": "US;Global;LATAM",
        "vertical_focus": "biotech;hardtech;agtech;foodtech;climate",
        "ticket_min_usd": 250000.0,
        "ticket_max_usd": 2000000.0,
        "lead_behavior": "lead",
        "active_status": "active",
        "aum_usd_m": 1000.0,
    },

    # ── Grupo Insud (3 deals, Argentine pharma/biotech group) ─────────────────
    "grupo_insud": {
        "investor_type": "corporate_vc",
        "thesis": (
            "Argentine pharmaceutical and biotech conglomerate (Insud Pharma + mAbxience). "
            "Founded 1977 by Hugo Sigman & Silvia Gold. Operations in 50 countries, "
            "20 production plants. Makes strategic investments in biotech and pharma "
            "startups aligned with its industrial capabilities."
        ),
        "preferred_stages": "seed;series-a;series-b",
        "geography_focus": "AR;LATAM;EU",
        "vertical_focus": "pharma;biotech;biosimilars;biomanufacturing",
        "lead_behavior": "follow",
        "active_status": "active",
    },

    # ── 500 LatAm (0 deals, US/global seed VC) ────────────────────────────────
    "500_latam": {
        "investor_type": "vc",
        "thesis": (
            "LATAM-focused program of 500 Global (formerly 500 Startups). "
            "Pre-seed and seed stage. Backed by IDB Lab. "
            "Invests across tech sectors in Latin America."
        ),
        "preferred_stages": "pre-seed;seed",
        "geography_focus": "LATAM",
        "vertical_focus": "tech;fintech;agtech;healthtech",
        "ticket_min_usd": 100000.0,
        "ticket_max_usd": 500000.0,
        "lead_behavior": "both",
        "active_status": "active",
    },

    # ── Amador (0 deals, Costa Rican VC) ─────────────────────────────────────
    "amador": {
        "investor_type": "vc",
        "thesis": (
            "Costa Rican early-stage VC backed by IDB Lab. "
            "Invests in technology and innovation startups in Central America "
            "and broader Latin America."
        ),
        "preferred_stages": "pre-seed;seed",
        "geography_focus": "CR;LATAM",
        "vertical_focus": "tech;agtech;healthtech",
        "lead_behavior": "lead",
        "active_status": "active",
    },

    # ── IDB Natural Capital Lab (0 deals, multilateral) ──────────────────────
    "idb_natural_capital_lab": {
        "investor_type": "multilateral",
        "thesis": (
            "IDB Group lab focused on natural capital and biodiversity finance "
            "in Latin America. LP in Kaete Investimentos (Amazonia ReGenerate). "
            "Provides early-stage catalytic capital for ecosystem-positive ventures."
        ),
        "preferred_stages": "seed;series-a",
        "geography_focus": "LATAM",
        "vertical_focus": "bioeconomy;biodiversity;climate;nature-tech",
        "lead_behavior": "both",
        "active_status": "active",
    },

    # ── Bago (0 deals, Argentine pharma corporate VC) ────────────────────────
    "bago": {
        "investor_type": "corporate_vc",
        "thesis": (
            "Argentine pharmaceutical company Laboratorio Bagó with strategic "
            "investments in biotech and health innovation startups in Argentina "
            "and Latin America."
        ),
        "preferred_stages": "seed;series-a",
        "geography_focus": "AR;LATAM",
        "vertical_focus": "pharma;biotech;healthtech",
        "active_status": "active",
    },

    # ── LAVCA (association — no investable thesis) ────────────────────────────
    "lavca": {
        "thesis": (
            "Latin American Venture Capital Association — industry body for VC/PE "
            "in Latin America. Not a direct investor; provides advocacy, research "
            "and LP/GP networking for the LATAM private capital ecosystem."
        ),
        "active_status": "active",
    },
}


# ── Ghost shell cleanup ───────────────────────────────────────────────────────
# Mark as inactive + set investor_type to investor (keep type, just deactivate)
GHOST_INVESTOR_UPDATES = {
    eid: {"active_status": "inactive"}
    for eid in GHOST_SHELLS
}


# ─────────────────────────────────────────────────────────────────────────────

def run(dry_run=False):
    conn = sqlite3.connect(str(DB))

    # 1. Schema migration
    print("=== 1. Schema migration ===")
    if not dry_run:
        _add_column_if_missing(conn, "investors", "aum_usd_m", "REAL")
        conn.commit()

    # 2. Ghost shells
    print("\n=== 2. Ghost shell cleanup ===")
    ghosts_done = 0
    for eid, updates in GHOST_INVESTOR_UPDATES.items():
        exists = conn.execute(
            "SELECT 1 FROM investors WHERE investor_id=?", (eid,)
        ).fetchone()
        if not exists:
            continue
        if dry_run:
            print(f"  [DRY] {eid} -> inactive")
        else:
            n = diff_and_log_update(
                conn, "investors", "investor_id", eid, updates,
                actor=ACTOR, reason="ghost_shell:0_deals_no_data"
            )
            if n:
                print(f"  OK {eid} -> inactive")
                ghosts_done += 1
    if not dry_run:
        conn.commit()
        print(f"  {ghosts_done} ghost shells marcados inactive")

    # 3. Entity updates (website, country)
    print("\n=== 3. Entity updates (website / country) ===")
    ent_done = 0
    for eid, updates in ENTITY_UPDATES.items():
        exists = conn.execute(
            "SELECT 1 FROM entities WHERE entity_id=?", (eid,)
        ).fetchone()
        if not exists:
            print(f"  SKIP (no existe): {eid}")
            continue
        if dry_run:
            print(f"  [DRY] {eid}: {list(updates.keys())}")
        else:
            n = diff_and_log_update(
                conn, "entities", "entity_id", eid, updates,
                actor=ACTOR, reason="enrich_capital_atlas:website_country"
            )
            if n:
                print(f"  OK {eid}: {n} campo(s)")
                ent_done += 1
    if not dry_run:
        conn.commit()
        print(f"  {ent_done} entidades actualizadas")

    # 4. Investor table updates
    print("\n=== 4. Investor updates (thesis / stages / ticket / aum) ===")
    inv_done = 0
    for eid, updates in INVESTOR_UPDATES.items():
        exists = conn.execute(
            "SELECT 1 FROM investors WHERE investor_id=?", (eid,)
        ).fetchone()
        if not exists:
            print(f"  SKIP (no existe): {eid}")
            continue
        if dry_run:
            print(f"  [DRY] {eid}: {list(updates.keys())}")
        else:
            n = diff_and_log_update(
                conn, "investors", "investor_id", eid, updates,
                actor=ACTOR, reason="enrich_capital_atlas:thesis_stages_ticket_aum"
            )
            if n:
                print(f"  OK {eid}: {n} campo(s)")
                inv_done += 1
    if not dry_run:
        conn.commit()
        print(f"  {inv_done} inversores actualizados")

    conn.close()

    if not dry_run:
        print("\n=== Regenerar capital-atlas-data.js ===")
        print("  Correr: python pipeline.py rebuild --phase atlas")
        print("  O bien: python -c \"from src.atlas import write_atlas_data; ...\"")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(dry_run=args.dry_run)
