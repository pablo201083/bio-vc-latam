"""Fix scope_decision and scope_basis for cl-06 and co-02 batch companies.

Issues:
1. Several companies got scope=review because sector strings didn't match BIO_SECTORS.
2. Bee Technology exists as entity with no country_code and no startup_extended row.
3. All new companies have scope_basis=auto_discovery; upgrade to external_auditable_source.
"""
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

DB = ROOT / "db" / "bio_latam.db"

# Companies to promote from review → include (scope_decision fix)
PROMOTE_TO_INCLUDE = [
    "codebreaker-bioscience-cl",
    "ecombio-cl",
    "infood-protein-cl",
    "inkus-biotech-cl",
    "mycoseaweed-cl",
    "viobact-cl",
    "koji-co",
]

# scope_basis upgrades: (entity_id, source_url)
SCOPE_BASIS_UPGRADES = [
    ("nalca-biotech-cl",
     "https://pitchbook.com/profiles/company/721009-45"),
    ("codebreaker-bioscience-cl",
     "https://www.salmonexpert.cl/biotecnologia-codebreaker-bioscience-inteligencia-microbiologica/"
     "codebreaker-bioscience-gana-startup-del-chile-y-proyecta-expansion-con-foco-en-salmonicultura/2074355"),
    ("viobact-cl",
     "https://investigacion.ucn.cl/noticias/"
     "empresa-tecnologica-ucn-que-impacta-en-la-acuicultura-adjudico-fondo-startup-ciencia/"),
    ("mycoseaweed-cl",
     "https://www.cienciaenchile.cl/chile-pionero-en-biotecnologia-con-mycoseaweed"
     "-una-proteina-alternativa-del-futuro/"),
    ("infood-protein-cl",
     "https://www.cienciaenchile.cl/infood-protein-biotechnology-spa-cientificos-presentan"
     "-una-fuente-alternativa-y-sustentable-de-proteinas-que-permitira-la-alimentacion"
     "-de-distintos-seres-vivos-para-el-sustento-del-ser-humano/"),
    ("inkus-biotech-cl",
     "https://www.salmonexpert.cl/alimentos-corfo-cowo/startups-de-base-tecnologica"
     "-desarrollan-innovadoras-soluciones-para-la-salmonicultura/1753757"),
    ("ayni-desert-interaction-cl",
     "https://investigacion.ucn.cl/noticias/"
     "microorganismos-del-desierto-de-atacama-como-solucion-biotecnologica-para-la-agricultura-extrema/"),
    ("pewman-innovation-cl",
     "https://www.cooperativaciencia.cl/radiociencia/2024/10/21/"
     "startup-chilena-usa-bacterias-para-desarrollar-soluciones-en-agricultura-y-otras-industrias/"),
    ("ecombio-cl",
     "https://ecosistemastartup.com/ecombio-reduce-uso-de-antibioticos-en-salmones/"),
    ("koji-co",
     "https://latamlist.com/four-latin-american-startups-join-eatable-adventures-raices-acceleration-program/"),
    # Bee Technology — handled separately below
]

BEE_SOURCE = "https://theganeshalab.com/startup/bee-technology/"
BEE_DESC = (
    "Develops FoodGuard, a biological food sanitizer using antimicrobial peptides that eliminates "
    "Salmonella, E.coli and Enterococci in fresh animal protein without synthetic additives, "
    "extending shelf life by 42%. Founded 2017. SAG-approved. Investors: The Ganesha Lab, "
    "Rio Baker. Eatable Adventures Raices program."
)


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    now = datetime.now(timezone.utc).isoformat()
    total = 0

    # ── 1. Promote review → include ──────────────────────────────────────────
    print("Promoting review to include:")
    for sid in PROMOTE_TO_INCLUDE:
        n = diff_and_log_update(
            conn, "startup_extended", "startup_id", sid,
            {"scope_decision": "include"},
            actor="coverage/fix-cl06-co02-scope",
            reason="Sector tag didn't match BIO_SECTORS at ingest; manually confirmed bio.",
        )
        print(f"  {sid:45s} {'OK' if n else 'skip'}")
        total += n

    # ── 2. Fix Bee Technology ─────────────────────────────────────────────────
    print("\nFixing Bee Technology:")
    # Update entities: set country_code = CL, website
    conn.execute(
        "UPDATE entities SET country_code='CL', website='beetechnology.cl', founded_year=2017 "
        "WHERE entity_id='Bee Technology'",
    )
    from audit import log_change
    log_change(conn, actor="coverage/fix-cl06-co02-scope",
               entity_id="Bee Technology",
               field="entities.country_code",
               old_value=None, new_value="CL",
               reason="Bee Technology is Chilean (beetechnology.cl), missing country_code at creation",
               evidence_url=BEE_SOURCE)

    # Insert startup_extended row if missing
    existing_sx = conn.execute(
        "SELECT 1 FROM startup_extended WHERE startup_id='Bee Technology'"
    ).fetchone()
    if not existing_sx:
        conn.execute(
            """INSERT INTO startup_extended
               (startup_id, scope_decision, scope_status, scope_basis,
                startup_summary_v1, data_quality_score, quality_band,
                review_status, last_reviewed_at, missing_signals)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            ("Bee Technology", "include", "pending_review", "external_auditable_source",
             BEE_DESC, 6.0, "medium", "pending", now,
             "needs_full_taxonomy,needs_bio_theme"),
        )
        log_change(conn, actor="coverage/fix-cl06-co02-scope",
                   entity_id="Bee Technology",
                   field="startup_extended.NEW",
                   old_value=None, new_value="include / external_auditable_source",
                   reason="Missing startup_extended row for pre-existing entity; confirmed Chilean biotech.",
                   evidence_url=BEE_SOURCE)
        print("  Bee Technology: startup_extended row INSERTED")
    else:
        diff_and_log_update(
            conn, "startup_extended", "startup_id", "Bee Technology",
            {"scope_decision": "include", "scope_basis": "external_auditable_source"},
            actor="coverage/fix-cl06-co02-scope",
            reason="Confirmed Chilean bio startup with external source.",
            evidence_url=BEE_SOURCE,
        )
        print("  Bee Technology: startup_extended row UPDATED")
    total += 1

    # ── 3. Upgrade scope_basis → external_auditable_source ───────────────────
    print("\nUpgrading scope_basis:")
    for sid, url in SCOPE_BASIS_UPGRADES:
        n = diff_and_log_update(
            conn, "startup_extended", "startup_id", sid,
            {"scope_basis": "external_auditable_source"},
            actor="coverage/fix-cl06-co02-scope",
            reason="External source verified; upgrading from auto_discovery.",
            evidence_url=url,
        )
        print(f"  {sid:45s} {'OK' if n else 'skip'}")
        total += n

    conn.commit()
    conn.close()
    print(f"\nTotal updates: {total}")


if __name__ == "__main__":
    main()
