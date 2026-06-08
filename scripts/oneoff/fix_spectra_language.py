"""
fix_spectra_language.py
-----------------------
Corrige thesis y profile_blurb de Spectra Investments a inglés.
Todos los perfiles de inversores del sistema están en inglés — policy de consistencia.
"""
import sqlite3, sys, os, csv
sys.stdout.reconfigure(encoding="utf-8")
DB  = os.path.join(os.path.dirname(__file__), "..", "..", "db", "bio_latam.db")
CSV = os.path.join(os.path.dirname(__file__), "..", "..", "canonical", "manual_investor_profiles.csv")

THESIS = (
    "Latin America's largest and pioneering fund of funds for Private Equity and Venture Capital. "
    "Multi-pillar strategy: secondaries (40%), anchor LP in selected VC funds (30%), and direct "
    "co-investments alongside search funds and angel investors (30%). Fund VII target: R$1.6B. "
    "Invests across VC, growth, buyout, biotech, mining, and special situations."
)

BLURB = (
    "Spectra Investments is Latin America's largest and first-ever fund of funds for Private Equity "
    "and Venture Capital, founded in 2012 in São Paulo. Manages R$7.1B (≈ US$1.3B) across seven funds "
    "with an indirect portfolio of 730+ companies — including 19 unicorns, 18 IPOs, and 70 acquisitions "
    "(Bitso, Kavak, QuintoAndar among the highlights).\n\n"
    "Fund VII strategy (R$800M initial close, target R$1.6B): 40% secondaries (acquiring stakes in "
    "existing PE/VC funds to provide ecosystem liquidity), 30% anchor LP in specialized Brazilian VC "
    "funds (Big Bets, Cloud9 Capital, Bridge One, Outfield, Laplace), and 30% direct co-investments. "
    "Key innovation: minimum 5% dedicated to co-investing alongside angel investors to access "
    "'invisible startups' before mainstream VC discovery.\n\n"
    "Most active investor in Latin American Search Funds (>50% of all regional funds raised). "
    "Research partnership with Insper and ABVCAP: operates Brazil's most comprehensive PE/VC database. "
    "2025 record: R$750M distributed to LPs across 42 full exits. LP base: 65-70% Brazilian family "
    "offices, first Asian LP onboarded in 2025. Team: Ricardo Kanitz (founder/partner), Renato "
    "Abissamra (managing partner), Frederico Wiesel, Alexander Saller, Caio Longhini, Rafael Bassani, "
    "Jamie Keller (IR), Joana Montenegro (ops) — ~25 professionals."
)

# ── Update DB ──────────────────────────────────────────────────────────────
conn = sqlite3.connect(DB)
conn.execute(
    "UPDATE investors SET thesis = ?, profile_blurb = ? WHERE investor_id = 'spectra_investments'",
    (THESIS, BLURB)
)
conn.commit()
conn.close()
print("✓ DB actualizado (inglés)")

# ── Update CSV ─────────────────────────────────────────────────────────────
rows = []
with open(CSV, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if row and row[0] == "spectra_investments":
            # thesis=col4, profile_blurb=col5
            row[4] = THESIS
            row[5] = BLURB
        rows.append(row)

with open(CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    writer.writerows(rows)
print("✓ CSV actualizado (inglés)")
print("\nPolicy: todos los campos thesis/profile_blurb → inglés. Nombres propios OK en idioma original dentro del texto.")
