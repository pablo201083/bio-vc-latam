"""
Agrega la fila de Spectra Investments a canonical/manual_investor_profiles.csv
"""
import csv, os, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
CSV_PATH = os.path.join(ROOT, "canonical", "manual_investor_profiles.csv")

SPECTRA_ROW = [
    "spectra_investments",
    "Spectra Investments",
    "BR",
    "fund_of_funds",
    # thesis
    ("Fundo de fundos pioneiro e maior da América Latina. Estratégia multi-pilar: "
     "secondaries (40%), anchor LP em fundos VC selecionados (30%) e co-investimentos "
     "diretos com search funds e investidores anjo (30%). Fundo VII: R$1,6B target. "
     "Investe em VC, growth, buyout, biotech, mineração e special situations."),
    # profile_blurb
    ("Spectra Investments é o maior fundo de fundos de PE/VC da América Latina (fundado 2012, São Paulo). "
     "Gerencia R$7,1B (~US$1,3B) em 7 fundos com portfólio indireto de 730+ empresas — 19 unicórnios, "
     "18 IPOs, 70 aquisições (Bitso, Kavak, QuintoAndar). Fund VII: R$800M initial close (target R$1,6B): "
     "40% secondaries, 30% anchor LP em Big Bets/Cloud9/Bridge One/Outfield/Laplace, 30% co-investimentos. "
     "Inovação: mín. 5% co-investe com angels para acessar 'startups invisíveis'. Maior investidor em "
     "Search Funds da LatAm (>50% dos fundos levantados). Parceria de pesquisa Insper+ABVCAP. "
     "2025: R$750M distribuídos (recorde), 42 exits. Equipe: Ricardo Kanitz (fundador), "
     "Renato Abissamra (managing partner), Frederico Wiesel, Alexander Saller, Caio Longhini."),
    500000,         # ticket_min_usd (angel co-invest floor)
    50000000,       # ticket_max_usd (anchor LP tickets)
    1270,           # aum_usd_m (R$7.1B ÷ ~5.6)
    "lead_or_follow",
    "seed,series-a,series-b,growth,pe",
    "BR,LATAM",
    "https://spectrainvest.com",
    "2026-06-08",
]

# Lee el CSV existente para verificar que Spectra no está ya
existing_ids = set()
with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        if row:
            existing_ids.add(row[0])

if "spectra_investments" in existing_ids:
    print("⚠ spectra_investments ya existe en el CSV. No se agrega duplicado.")
else:
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(SPECTRA_ROW)
    print("✓ spectra_investments agregado a manual_investor_profiles.csv")
