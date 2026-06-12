"""Upgrade scope_basis to external_auditable_source for cl-06 and co-02 batch companies."""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

UPGRADES = [
    # (startup_id, source_url)
    ("nalca-biotech",          "https://pitchbook.com/profiles/company/721009-45"),
    ("codebreaker-bioscience",
     "https://www.salmonexpert.cl/biotecnologia-codebreaker-bioscience-inteligencia-microbiologica/"
     "codebreaker-bioscience-gana-startup-del-chile-y-proyecta-expansion-con-foco-en-salmonicultura/2074355"),
    ("viobact",
     "https://investigacion.ucn.cl/noticias/"
     "empresa-tecnologica-ucn-que-impacta-en-la-acuicultura-adjudico-fondo-startup-ciencia/"),
    ("mycoseaweed",
     "https://www.cienciaenchile.cl/chile-pionero-en-biotecnologia-con-mycoseaweed"
     "-una-proteina-alternativa-del-futuro/"),
    ("infood-protein",
     "https://www.cienciaenchile.cl/infood-protein-biotechnology-spa-cientificos-presentan"
     "-una-fuente-alternativa-y-sustentable-de-proteinas-que-permitira-la-alimentacion"
     "-de-distintos-seres-vivos-para-el-sustento-del-ser-humano/"),
    ("inkus-biotech",
     "https://www.salmonexpert.cl/alimentos-corfo-cowo/startups-de-base-tecnologica"
     "-desarrollan-innovadoras-soluciones-para-la-salmonicultura/1753757"),
    ("ayni-desert-interaction",
     "https://investigacion.ucn.cl/noticias/"
     "microorganismos-del-desierto-de-atacama-como-solucion-biotecnologica-para-la-agricultura-extrema/"),
    ("pewman-innovation",
     "https://www.cooperativaciencia.cl/radiociencia/2024/10/21/"
     "startup-chilena-usa-bacterias-para-desarrollar-soluciones-en-agricultura-y-otras-industrias/"),
    ("ecombio",
     "https://ecosistemastartup.com/ecombio-reduce-uso-de-antibioticos-en-salmones/"),
    ("bee-technology",
     "https://theganeshalab.com/startup/bee-technology/"),
    ("koji",
     "https://latamlist.com/four-latin-american-startups-join-eatable-adventures-raices-acceleration-program/"),
]

# Also fix existing CO companies that are include but have scope_basis=None
CO_FIXES = [
    ("nanofreeze",  "https://solve.mit.edu/challenges/2024-global-climate-challenge/solutions/86212"),
    ("bialtec",     "https://www.crunchbase.com/organization/bialtec"),
    ("progal",      "https://co.linkedin.com/company/progal-bt"),
]


def main() -> None:
    conn = sqlite3.connect(ROOT / "db" / "bio_latam.db")
    conn.execute("PRAGMA journal_mode=WAL")
    total = 0

    # New companies: set scope_basis = external_auditable_source
    for sid, url in UPGRADES:
        n = diff_and_log_update(
            conn, "startup_extended", "startup_id", sid,
            {"scope_basis": "external_auditable_source"},
            actor="coverage/upgrade-scope-basis-cl06-co02",
            reason="Verified external source exists; upgrading from auto_discovery to external_auditable_source",
            evidence_url=url,
        )
        status = "OK" if n else "skip (not found?)"
        print(f"  {sid:35s} {status}")
        total += n

    # Existing CO companies: set scope_basis = external_auditable_source
    print("\n  Fixing existing CO companies with scope_basis=None:")
    for sid, url in CO_FIXES:
        n = diff_and_log_update(
            conn, "startup_extended", "startup_id", sid,
            {"scope_basis": "external_auditable_source"},
            actor="coverage/fix-co-scope-basis",
            reason="External source confirmed; was missing scope_basis",
            evidence_url=url,
        )
        status = "OK" if n else "skip"
        print(f"  {sid:35s} {status}")
        total += n

    conn.commit()
    conn.close()
    print(f"\nTotal fields updated: {total}")


if __name__ == "__main__":
    main()
