"""Rearm Farm Intelligence cluster under the B1 acople gate (2026-06-12).

Splits the old catch-all Farm Intelligence (66) into three cohesive buckets:
  - Farm Intelligence (39): software/sensors/IA con acople B1 a un sistema vivo
    específico (este cultivo, este hato). Muchos pasan bio=0 -> 1 (acople real
    mal flageado al ingest).
  - Digital AgTech & Agrifintech (24): eco-adjacent, is_bio=0. Valor financiero/
    comercial/logístico sin acople biológico (crédito, marketplace, tokenización,
    logística, cold-chain, data-infra).
  - Food Systems & Alt Proteins (3): vertical/urban farming — output ingerido.

Gate: bio_definition_operativa.md §4 (test de acople / gate TechBio, lectura B1).
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

DB = ROOT / "db" / "bio_latam.db"

FARM = "Farm Intelligence"
DIGITAL = "Digital AgTech & Agrifintech"
FOOD = "Food Systems & Alt Proteins"

# (entity_id, target_theme, target_is_bio, one-line rationale)
DECISIONS = [
    # ── Digital AgTech & Agrifintech — eco-adjacent, sin acople (is_bio=0) ──────
    ("agrotools",     DIGITAL, 0, "ESG/compliance/risk/finance intelligence; sin acople a cultivo"),
    ("agricapital",   DIGITAL, 0, "agrifintech crédito"),
    ("agrolend",      DIGITAL, 0, "agrifintech crédito (la propia ficha pide cluster agri-fintech)"),
    ("agroforte",     DIGITAL, 0, "banco digital rural; mecanismo financiero"),
    ("agrofy",        DIGITAL, 0, "marketplace de agronegocios"),
    ("agrired",       DIGITAL, 0, "B2B de compra/venta/logística de insumos"),
    ("agrotoken",     DIGITAL, 0, "tokenización de granos; fintech"),
    ("arado",         DIGITAL, 0, "marketplace/distribución de alimento fresco"),
    ("blooms",        DIGITAL, 0, "trade-finance para exportadores"),
    ("brain_ag",      DIGITAL, 0, "crédito/risk/ESG intelligence"),
    ("culttivo",      DIGITAL, 0, "coffee-finance/crédito (la ficha dice 'not a biotech')"),
    ("incluirtec",    DIGITAL, 0, "agfintech-as-a-service crédito"),
    ("leaf",          DIGITAL, 0, "data-infrastructure API; plomería sin modelo bio"),
    ("nilus",         DIGITAL, 0, "food-rescue/distribución; food-system circularity"),
    ("seedz",         DIGITAL, 0, "loyalty/pagos/crédito; 'infrastructural rather than biological'"),
    ("sette",         DIGITAL, 0, "agrifintech (garantías/CPR/crédito)"),
    ("silohub",       DIGITAL, 0, "última milla del negocio de granos; logística/comercial"),
    ("siloreal",      DIGITAL, 0, "verificación de activos para seguro/finanzas; 'not biotech'"),
    ("terramagna",    DIGITAL, 0, "agrifintech crédito/receivables"),
    ("traive",        DIGITAL, 0, "agrifintech crédito"),
    ("tuplaza",       DIGITAL, 0, "supply-chain/distribución de fresco"),
    ("verqor",        DIGITAL, 0, "agfintech financiamiento"),
    ("goflux",        DIGITAL, 0, "freight SaaS; logística"),
    ("sensify",       DIGITAL, 0, "IoT cold-chain food&bev; precedente Nexxto (acople no específico)"),

    # ── Food Systems — output ingerido (vertical/urban farming) ────────────────
    ("agrourbana",    FOOD, 1, "vertical farming hidropónico; output ingerido (test de output)"),
    ("laurus_ag_tech", FOOD, 1, "urban farming descentralizado; output ingerido"),
    ("pink-farms",    FOOD, 1, "urban vertical farming; 'comes in through biobased food systems'"),

    # ── Farm Intelligence — acople B1 confirmado; flip bio=0 -> 1 los mal flageados ─
    ("tech",          FARM, 1, "IoT sobre producción animal viva"),
    ("aegro",         FARM, 1, "farm-mgmt con pest monitoring/field planning (acople agronómico)"),
    ("agronow-br",    FARM, 1, "remote sensing de cultivo (mecanismo agronómico; uso credit es aplicación)"),
    ("agrosmart",     FARM, 1, "inteligencia climática/agronómica sobre el cultivo (B1/B2)"),
    ("auravant",      FARM, 1, "modelos agronómicos + satélite sobre cultivo"),
    ("bemagro",       FARM, 1, "precision-ag, detección de malezas/plantas (B1/B2)"),
    ("calice",        FARM, 1, "modela genotipo×ambiente×manejo (B2 TechBio)"),
    ("calice-ai-ar",  FARM, 1, "simulaciones G×E×M de performance de producto (B2)"),
    ("cerradox",      FARM, 1, "monitoreo agronómico de producción"),
    ("codebreaker-bioscience-cl", FARM, 1, "inteligencia de microbioma (B2)"),
    ("cowmed-br",     FARM, 1, "sensores sobre hato lechero; detección estro/enfermedad (B1)"),
    ("deepagro",      FARM, 1, "CV de spraying selectivo; actúa sobre el cultivo (B1)"),
    ("digifarmz-br",  FARM, 1, "decisión agronómica con genética+suelo (B1/B2)"),
    ("dymaxion_labs", FARM, 1, "CV/AI de procesos agronómicos (B1)"),
    ("eiwa",          FARM, 1, "análisis de datos agronómicos a escala (B1)"),
    ("farmbox-br",    FARM, 1, "scouting satelital + prescripciones agronómicas (B1)"),
    ("horus_aeronaves", FARM, 1, "drones/imágenes agronómicas (B1)"),
    ("inceres",       FARM, 1, "precision-ag, muestreo de suelo + satélite (B1)"),
    ("inkus-biotech-cl", FARM, 1, "AI+genómica de resistencia a patógenos (B2)"),
    ("inspectral-br", FARM, 1, "bio-optical modeling, enfermedad temprana del cultivo (B2)"),
    ("instacrops-cl", FARM, 1, "IoT 80+ parámetros agronómicos; riego/nutrición (B1)"),
    ("isobar-br",     FARM, 1, "analítica de precisión café/caña (B1)"),
    ("jetbov",        FARM, 1, "manejo de hato de carne (B1, animal vivo)"),
    ("precision_ag",  FARM, 1, "spraying/monitoreo con drones sobre cultivo (B1)"),
    ("rumina",        FARM, 1, "inteligencia de tambo lechero (B1)"),
    ("sensix",        FARM, 1, "decision-agriculture, remote sensing + suelo (B1)"),
    ("sima",          FARM, 1, "monitoreo de cultivo + órdenes de trabajo (B1)"),
    ("sioma",         FARM, 1, "trazabilidad/productividad por planta en banano/palma (B1)"),
    ("smartbreeder",  FARM, 1, "analítica agronómica de productividad (B1)"),
    ("solinftec",     FARM, 1, "operaciones agrícolas en tiempo real sobre cultivo (B1)"),
    ("spaceag",       FARM, 1, "satélite/drones, insights agronómicos (B1)"),
    ("strider-br",    FARM, 1, "monitoreo de plagas/enfermedad fitosanitario (B1/B2)"),
    ("tbit",          FARM, 1, "análisis de imagen de calidad de semilla/grano (acople biológico)"),
    ("tarvos-br",     FARM, 1, "trampas CV para plagas específicas (Spodoptera) (B1/B2)"),
    ("the-earth-says", FARM, 1, "monitoreo AI de colmenas/polinización (B1, abejas vivas)"),
    ("voa",           FARM, 1, "drones, aplicación de agentes biológicos sobre cultivo (B1)"),
    ("wiagro",        FARM, 1, "monitoreo de grano almacenado; micotoxina/deterioro (acople biológico)"),
    ("wiseconn-cl",   FARM, 1, "riego de precisión sobre viñedos/huertos (B1)"),
    ("zoomagri",      FARM, 1, "CV/ML de calidad de grano (lee calidad biológica)"),
]


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    n_fields = 0
    counts = {FARM: 0, DIGITAL: 0, FOOD: 0}
    missing = []

    for sid, theme, is_bio, reason in DECISIONS:
        row = conn.execute(
            "SELECT bio_theme_primary, is_bio_universe FROM startup_extended WHERE startup_id=?",
            (sid,),
        ).fetchone()
        if row is None:
            missing.append(sid)
            continue
        new = {"bio_theme_primary": theme, "is_bio_universe": is_bio}
        n = diff_and_log_update(
            conn, "startup_extended", "startup_id", sid, new,
            actor="taxonomy/rearm-farm-intelligence",
            reason=f"Rearm FI bajo gate B1: {reason}",
        )
        n_fields += n
        counts[theme] += 1

    conn.commit()
    conn.close()
    print(f"Decisiones aplicadas: {len(DECISIONS) - len(missing)}  (campos cambiados: {n_fields})")
    for t, c in counts.items():
        print(f"  {t:34s} {c}")
    if missing:
        print(f"  NO ENCONTRADOS ({len(missing)}): {missing}")


if __name__ == "__main__":
    main()
