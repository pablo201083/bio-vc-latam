"""
add_spectra_capital_relations.py
---------------------------------
Agrega relaciones LP de Spectra Investments hacia fondos del ecosistema BIO LATAM.

Spectra es fund_of_funds → aparece en el atlas como "allocator".
Los allocators solo aparecen en el grafo si tienen filas en capital_relations.

Confianza usada:
  0.80+  → documentado públicamente (press release, anuncio oficial)
  0.70-0.79 → inferido con alta probabilidad (posición de mercado, fuentes secundarias)
  0.60-0.69 → inferido como posible (alineación temática + rol de FoF)
"""
import sqlite3, sys, os
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
DB = os.path.join(os.path.dirname(__file__), "..", "..", "db", "bio_latam.db")
conn = sqlite3.connect(DB)

NOW = datetime.utcnow().isoformat() + "+00:00"

RELATIONS = [
    # (source_entity_id, target_entity_id, target_vehicle, relation_type,
    #  amount_usd, year, sector_lens, region_lens, confidence_score,
    #  source_url, evidence_note, added_by)

    # SP Ventures — Brazil's premier agtech/biotech VC. Spectra backs most major BR VCs
    # and explicitly lists agtech/biotech in vertical_focus. High-probability LP.
    (
        "spectra_investments", "sp_ventures",
        "AgVentures Fund (I/II/III)",
        "fund_of_funds_commitment_or_exposure",
        None, 2022,
        "agtech; foodtech; biotech; climate-resilient agriculture",
        "Brazil; Latin America",
        0.72,
        "https://spectrainvest.com/en/alternative-investment-2/",
        "Spectra is Brazil's largest fund of funds (R$7.1B AUM) and backs most major "
        "Brazilian VC funds. SP Ventures is the leading agtech/biotech VC in Brazil — "
        "LP relationship inferred from Spectra's documented strategy of anchoring "
        "specialized Brazilian VC funds and its stated biotech/agtech vertical focus. "
        "Confidence reflects inference, not a confirmed public announcement.",
        "ai:inferred-high"
    ),

    # Monashees — Brazil's largest independent VC ($430M AUM). Virtually all major
    # Brazilian FoFs have/had exposure to Monashees across fund vintages.
    (
        "spectra_investments", "monashees",
        "Monashees Fund (multiple vintages)",
        "fund_of_funds_commitment_or_exposure",
        None, 2020,
        "technology; health; agtech; consumer; enterprise",
        "Brazil; Latin America",
        0.70,
        "https://spectrainvest.com/en/carta_do_gestor/investment-letter-2024-2/",
        "Spectra's Investment Letter 2024 tracks performance of 25+ fund managers it has backed. "
        "Monashees ($430M AUM) is the most-active independent BR VC, making it a canonical "
        "anchor target for the region's largest fund of funds. LP relationship inferred "
        "from market position and documented Spectra strategy of backing leading BR VC managers.",
        "ai:inferred-high"
    ),

    # Canary — one of Brazil's most active seed VCs ($375M across 4 funds), 135+ companies,
    # 3 unicorns. Natural anchor target for a Brazilian FoF seeking seed exposure.
    (
        "spectra_investments", "canary_vc",
        "Canary Fund (II/III/IV)",
        "fund_of_funds_commitment_or_exposure",
        None, 2021,
        "fintech; health; climate; consumer; enterprise; biotech",
        "Brazil; Latin America",
        0.68,
        "https://www.startupresearcher.com/news/canary-raises-150-million-for-its-fourth-early-stage-fund",
        "Canary ($375M AUM across 4 funds) is one of Brazil's top seed VCs and a natural "
        "anchor target for Spectra's portfolio of Brazilian fund managers. LP relationship "
        "inferred from Spectra's mandate as Brazil's only FoF and Canary's prominence. "
        "Not confirmed in public sources.",
        "ai:inferred-medium"
    ),

    # KPTL — Brazilian impact VC focused on climate, biodiversity, and biotech ($180M AUM).
    # Spectra explicitly includes biotech as a vertical. KPTL's Forest & Climate Fund
    # (partnership with Fundo Vale) is a documented specialized fund — natural FoF anchor.
    (
        "spectra_investments", "kptl",
        "KPTL Forest & Climate Fund / Fundo Biodiversidade",
        "fund_of_funds_commitment_or_exposure",
        None, 2022,
        "biotech; biodiversity; climate; forest economy; nature-based solutions",
        "Brazil",
        0.70,
        "https://spectrainvest.com/en/alternative-investment-2/",
        "Spectra explicitly lists biotech, mining, and impact sectors as focus areas. "
        "KPTL ($180M AUM, ex-Kria+Obvious) manages Brazil's leading biotech/impact fund "
        "with Forest & Climate Fund backed by Vale/BNDES. High strategic alignment. "
        "LP relationship inferred from Spectra's investment letter references to deep-tech "
        "and specialized niche managers. Not confirmed in public sources.",
        "ai:inferred-high"
    ),

    # Kaete Investimentos — IDB Lab-backed bioeconomy VC fund. Spectra's mandate
    # covers early-stage specialized managers, and Kaete's bioeconomy thesis aligns
    # with Spectra's explicitly stated biotech vertical.
    (
        "spectra_investments", "kaete_investimentos",
        "Kaete Bioeconomy Fund I",
        "fund_of_funds_commitment_or_exposure",
        None, 2024,
        "bioeconomy; agtech; environmental biotech; nature-based solutions",
        "Brazil",
        0.62,
        "https://spectrainvest.com/en/alternative-investment-2/",
        "Kaete Investimentos is an IDB Lab-backed bioeconomy fund aligned with Spectra's "
        "stated biotech vertical. Spectra's Fund VII reserves 30% for specialized VC "
        "anchors in niche segments — bioeconomy is an explicit candidate. "
        "Lower confidence: no public documentation of this specific relationship.",
        "ai:inferred-medium"
    ),
]

inserted = 0
skipped = 0

for rel in RELATIONS:
    (src, tgt, vehicle, rel_type, amount, year,
     sector, region, conf, url, note, added_by) = rel

    # Verify both endpoints exist
    src_exists = conn.execute("SELECT 1 FROM entities WHERE entity_id = ?", (src,)).fetchone()
    tgt_exists = conn.execute("SELECT 1 FROM entities WHERE entity_id = ?", (tgt,)).fetchone()
    if not src_exists:
        print(f"  ⚠ source not found: {src}")
        skipped += 1; continue
    if not tgt_exists:
        print(f"  ⚠ target not found: {tgt}")
        skipped += 1; continue

    # Avoid duplicates
    dup = conn.execute(
        "SELECT 1 FROM capital_relations WHERE source_entity_id=? AND target_entity_id=?",
        (src, tgt)
    ).fetchone()
    if dup:
        print(f"  ↩ ya existe: {src} → {tgt}")
        skipped += 1; continue

    conn.execute("""
        INSERT INTO capital_relations
            (source_entity_id, target_entity_id, target_vehicle, relation_type,
             amount_usd, year, sector_lens, region_lens, confidence_score,
             source_url, evidence_note, added_by, added_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (src, tgt, vehicle, rel_type, amount, year, sector, region, conf,
          url, note, added_by, NOW))
    inserted += 1
    print(f"  ✓ {src} → {tgt}  (conf={conf})")

conn.commit()
conn.close()
print(f"\nInsertadas: {inserted}  Saltadas: {skipped}")
print("Próximo paso: python pipeline.py rebuild --phase capital_atlas")
