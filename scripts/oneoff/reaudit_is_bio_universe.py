"""Re-audit is_bio_universe across the universe (P1, 2026-06-12).

El rearme de Farm Intelligence reveló que `is_bio_universe` estaba mal puesto de
forma sistémica, no solo en agri. De los 25 bio=0 fuera de Digital AgTech, 17 son
en realidad bio-core/coupled mal flageados (genómica, diagnóstico molecular,
biomoléculas, fagos, indicadores biológicos, resina de bosque). Se corrigen a 1.

Los 8 genuinamente eco-adjacent se confirman bio=0 (no se tocan): Nexxto (IoT
cold-chain), Pixed (prótesis), CIRCCLO (packaging reusable), MUTA (reciclaje),
nChemi (nanocoatings sin bio), Ecotrace (trazabilidad), ucrop.it (verificación),
Pharmalens (QC visual). Quedan in-theme con flag (decisión "híbrido" del curador).
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from audit import diff_and_log_update

DB = ROOT / "db" / "bio_latam.db"

# (entity_id, rationale) — todos pasan is_bio_universe 0 -> 1
FLIP_TO_BIO = [
    ("biocentis-br",               "genome engineering de insectos self-limiting (bio-core)"),
    ("exacta-bioscience-cl",       "crop protection basado en bacteriófagos (bio-core)"),
    ("hapiseeds-br",               "descubrimiento de genes por bioinformática + breeding (bio-core)"),
    ("patagonia-biotechnology-cl", "compuestos bioactivos de algas para bioestimulantes (bio-core)"),
    ("neoprospecta-br",            "secuenciación de ADN 16S/ITS, mapeo microbiano (bio-core)"),
    ("bioelements-cl",             "packaging biodegradable de materiales bio-based (bio-core)"),
    ("ejido-verde-mx",             "resina de pino de bosques manejados; producto biológico (bio-coupled)"),
    ("giraffe-bio-ar",             "ingeniería de biomoléculas custom con AI (bio-core TechBio)"),
    ("gen-t-br",                   "secuenciación de genoma / diversidad genómica (bio-core)"),
    ("geneprodx-mx",               "diagnóstico molecular genómico de nódulos tiroideos (bio-core)"),
    ("kura-biotec-mx",             "reactivos enzimáticos para prep de muestras (bio-core)"),
    ("reddot-bio-br",              "plataforma point-of-care de detección ADN/ARN (bio-core)"),
    ("terragene-ar",               "indicadores biológicos (esporas) de esterilización (bio-coupled)"),
    ("cellertz-bio-br",            "plataforma de biología generativa, single-cell ML (bio-core TechBio)"),
    ("merken-biotech-cl",          "CRO full-stack de biología molecular/celular (bio-core)"),
    ("mirscience-therapeutics-br", "terapéutica de oligonucleótidos miRNA/siRNA (bio-core)"),
    ("rnatech-ar",                 "ARN bioactivo dietario de leche/hongos; ingredientes funcionales (bio-core)"),
]


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    total = 0
    missing = []
    for sid, reason in FLIP_TO_BIO:
        exists = conn.execute(
            "SELECT 1 FROM startup_extended WHERE startup_id=?", (sid,)
        ).fetchone()
        if not exists:
            missing.append(sid)
            continue
        total += diff_and_log_update(
            conn, "startup_extended", "startup_id", sid,
            {"is_bio_universe": 1},
            actor="taxonomy/reaudit-is-bio",
            reason=f"Flag mal puesto al ingest; {reason}",
        )
    conn.commit()
    conn.close()
    print(f"Flips aplicados: {len(FLIP_TO_BIO) - len(missing)}  (campos: {total})")
    if missing:
        print(f"NO ENCONTRADOS: {missing}")


if __name__ == "__main__":
    main()
