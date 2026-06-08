"""
add_spectra.py
--------------
Agrega Spectra Investments al ecosistema BIO LATAM como actor de capital.

Fuentes investigadas:
  - https://spectrainvest.com/en/team/
  - https://spectrainvest.com/en/carta_do_gestor/investment-letter-2024-2/
  - https://inforcapital.com/news/spectra-levanta-r-800-milhoes... (Fund VII)
  - https://www.secondariesinvestor.com/brazils-spectra-raises-secondaries...
  - https://tracxn.com/d/private-equity/spectra-investments/...
  - WebSearch múltiple: equipo, AUM, portafolio, estrategia 2025
"""
import sqlite3, sys, os
sys.stdout.reconfigure(encoding="utf-8")
DB = os.path.join(os.path.dirname(__file__), "..", "..", "db", "bio_latam.db")
conn = sqlite3.connect(DB)

# ── 1. Verificar que no existe ──────────────────────────────────────────
existing = conn.execute(
    "SELECT entity_id FROM entities WHERE entity_id = 'spectra_investments'"
).fetchone()
if existing:
    print("⚠ spectra_investments ya existe en entities. Saliendo.")
    conn.close()
    sys.exit(0)

# ── 2. Insertar en entities ─────────────────────────────────────────────
conn.execute("""
    INSERT INTO entities
        (entity_id, entity_type, canonical_name, slug,
         short_description, country_code, city,
         website, status, founded_year, last_verified_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "spectra_investments",
    "investor",
    "Spectra Investments",
    "spectra-investments",
    "Maior fundo de fundos de Private Equity e Venture Capital da América Latina. R$7,1B AUM, 7 fundos, 730+ empresas no portfólio.",
    "BR",
    "São Paulo",
    "https://spectrainvest.com",
    "active",
    2012,
    "2026-06-08",
))
print("✓ entities: spectra_investments inserido")

# ── 3. Insertar en investors ─────────────────────────────────────────────
THESIS = (
    "Fundo de fundos pioneiro e maior da América Latina. Estratégia multi-pilar: "
    "secondaries (40%), anchor LP em fundos VC selecionados (30%) e co-investimentos "
    "diretos com search funds e investidores anjo (30%). Fundo VII: R$1,6B target. "
    "Investe em venture capital, growth, buyout, biotech, mineração e special situations."
)

BLURB = (
    "Spectra Investments é o maior fundo de fundos de Private Equity e Venture Capital "
    "da América Latina, fundado em 2012 em São Paulo. Gerencia R$7,1 bilhões (≈ US$1,3B) "
    "em 7 fundos, com portfólio indireto de 730+ empresas incluindo 19 unicórnios, 18 IPOs "
    "e 70 aquisições — Bitso, Kavak e QuintoAndar entre os destaques.\n\n"
    "Estratégia de Fund VII (R$800M initial close, target R$1,6B): 40% em secondaries "
    "(compra de cotas em fundos PE/VC no mercado secundário, provendo liquidez ao ecossistema), "
    "30% como anchor LP em fundos VC especializados (Big Bets, Cloud9 Capital, Bridge One, "
    "Outfield, Laplace), e 30% em co-investimentos diretos. Inovação: mínimo de 5% do fundo "
    "dedicado a co-investir ao lado de investidores anjo — tese de acesso a 'startups invisíveis' "
    "antes do radar VC convencional.\n\n"
    "Maior investidor em Search Funds da América Latina (>50% de todos os fundos levantados na região). "
    "Parceria de pesquisa com Insper e ABVCAP: banco de dados de PE/VC brasileiro mais completo do mercado. "
    "Em 2025 distribuiu R$750M aos cotistas (recorde histórico) com 42 exits completos. "
    "Base de LPs: 65-70% family offices brasileiros, primeiro investidor asiático em 2025. "
    "Equipe: Ricardo Kanitz (fundador/sócio), Renato Abissamra (managing partner), "
    "Frederico Wiesel, Alexander Saller, Caio Longhini, Rafael Bassani, Jamie Keller (IR), "
    "Joana Montenegro (ops) — ~25 profissionais."
)

conn.execute("""
    INSERT INTO investors
        (investor_id, investor_type, thesis, preferred_stages,
         geography_focus, vertical_focus,
         ticket_min_usd, ticket_max_usd,
         lead_behavior, active_status, aum_usd_m, profile_blurb)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "spectra_investments",
    "fund_of_funds",                    # tipo principal
    THESIS,
    "seed,series-a,series-b,growth,pe", # accede via fondos que cubren todo el espectro
    "BR,LATAM",
    "venture_capital,pe,biotech,agtech,mining,search_funds,special_situations",
    500_000,                            # co-investments directos (angel co-invest)
    50_000_000,                         # anchor LP tickets en fondos
    "lead_or_follow",
    "active",
    1270,                               # R$7.1B ÷ ~5.6 BRL/USD ≈ USD 1.27B
    BLURB,
))
print("✓ investors: spectra_investments inserido")

conn.commit()
conn.close()
print("\n✅ Spectra Investments agregado exitosamente.")
print("   Próximo paso: python pipeline.py intelligence-data  → regenerar intelligence-data.js")
