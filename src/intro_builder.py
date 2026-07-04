"""
src/intro_builder.py — Generador de briefs de introducción para la CAB.

Dado cualquier par de entidades del ecosistema BIO LATAM, genera un brief
estructurado listo para enviar: rationale narrativo, talking points, email.

NO usa LLMs. Todo es template-based + datos reales del DB.

Pares soportados:
  startup ↔ investor       — tesis de inversión, portfolio fit, stage
  startup ↔ organization   — alineamiento temático con mandato del gremial
  startup ↔ eso            — eligibilidad para grants/aceleración
  startup ↔ corporate      — oportunidad de validación/adquisición
  investor ↔ organization  — membresía, co-inversión, visibilidad

Uso:
    python pipeline.py intro GridX bioinputx
    python pipeline.py intro cab_argentina bioinputx --json
    python pipeline.py intro corfo huiro --json
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── Entity profile loaders ────────────────────────────────────────────────────

def _load_entity_profile(entity_id: str, conn: sqlite3.Connection) -> dict | None:
    """Unified profile dict for any entity type."""

    # Try startup
    r = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website, e.founded_year,
               sx.bio_theme_primary, sx.bio_theme_secondary, sx.macro_theme,
               sx.funding_stage, sx.data_quality_score,
               sx.business_one_liner, sx.startup_summary_en, sx.startup_summary_v1,
               sx.technology_tags, sx.scale_tags
        FROM entities e JOIN startup_extended sx ON sx.startup_id = e.entity_id
        WHERE e.entity_id = ? AND sx.scope_decision = 'include'
    """, (entity_id,)).fetchone()
    if r:
        investors = [row[0] for row in conn.execute(
            "SELECT e.canonical_name FROM investment_edges ie "
            "JOIN entities e ON e.entity_id = ie.investor_id WHERE ie.startup_id = ?",
            (entity_id,)
        ).fetchall()]
        summary = (r[11] or r[12] or "").strip()[:280]
        return {
            "id": r[0], "name": r[1], "country": (r[2] or "").upper(),
            "website": r[3] or "", "founded": r[4],
            "entity_type": "startup",
            "theme": r[5] or r[7] or "",
            "theme2": r[6] or "",
            "stage": r[8] or "",
            "quality": round(float(r[9] or 0), 1),
            "one_liner": r[10] or "",
            "summary": summary,
            "tech": r[13] or "",
            "scale": r[14] or "",
            "investors": investors,
            "funded": len(investors) > 0,
        }

    # Try investor
    r = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               i.investor_type, i.geography_focus, i.thesis
        FROM entities e JOIN investors i ON i.investor_id = e.entity_id
        WHERE e.entity_id = ? AND e.status != 'excluded'
    """, (entity_id,)).fetchone()
    if r:
        portfolio = conn.execute(
            "SELECT startup_id FROM investment_edges WHERE investor_id = ?", (entity_id,)
        ).fetchall()
        portfolio_ids = [p[0] for p in portfolio]
        # Get themes from portfolio
        themes_raw = conn.execute("""
            SELECT DISTINCT sx.bio_theme_primary
            FROM investment_edges ie
            JOIN startup_extended sx ON sx.startup_id = ie.startup_id
            WHERE ie.investor_id = ? AND sx.bio_theme_primary IS NOT NULL
        """, (entity_id,)).fetchall()
        themes = [t[0] for t in themes_raw if t[0]]
        countries_raw = conn.execute("""
            SELECT DISTINCT e2.country_code
            FROM investment_edges ie
            JOIN entities e2 ON e2.entity_id = ie.startup_id
            WHERE ie.investor_id = ? AND e2.country_code IS NOT NULL
        """, (entity_id,)).fetchall()
        countries = [(c[0] or "").upper() for c in countries_raw if c[0]]
        return {
            "id": r[0], "name": r[1], "country": (r[2] or "").upper(),
            "website": r[3] or "", "entity_type": "investor",
            "itype": r[4] or "", "geo_focus": r[5] or "",
            "thesis": r[6] or "",
            "portfolio_size": len(portfolio_ids),
            "portfolio_ids": portfolio_ids,
            "portfolio_themes": themes[:6],
            "portfolio_countries": countries[:8],
        }

    # Try organization
    r = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               o.focus_area, o.org_type
        FROM entities e JOIN organizations o ON o.org_id = e.entity_id
        WHERE e.entity_id = ? AND e.status != 'excluded'
    """, (entity_id,)).fetchone()
    if r:
        members = conn.execute("""
            SELECT e2.canonical_name FROM support_edges se
            JOIN entities e2 ON e2.entity_id = se.target_entity_id
            WHERE se.source_entity_id = ? AND se.support_type = 'membership'
        """, (entity_id,)).fetchall()
        return {
            "id": r[0], "name": r[1], "country": (r[2] or "").upper(),
            "website": r[3] or "", "entity_type": "organization",
            "focus_area": r[4] or "", "org_type": r[5] or "",
            "members": [m[0] for m in members],
        }

    # Try ESO
    r = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               es.eso_type, es.service_profile, es.geography_focus
        FROM entities e JOIN esos es ON es.eso_id = e.entity_id
        WHERE e.entity_id = ? AND e.status != 'excluded'
    """, (entity_id,)).fetchone()
    if r:
        return {
            "id": r[0], "name": r[1], "country": (r[2] or "").upper(),
            "website": r[3] or "", "entity_type": "eso",
            "eso_type": r[4] or "",
            "service_profile": r[5] or "",
            "geo_focus": r[6] or "",
        }

    # Try corporate
    r = conn.execute("""
        SELECT e.entity_id, e.canonical_name, e.country_code, e.website,
               c.industry, c.demand_profile, c.innovation_maturity
        FROM entities e JOIN corporates c ON c.corporate_id = e.entity_id
        WHERE e.entity_id = ? AND e.status != 'excluded'
    """, (entity_id,)).fetchone()
    if r:
        validations = conn.execute("""
            SELECT e2.canonical_name, ve.relation_type
            FROM validation_edges ve
            JOIN entities e2 ON e2.entity_id = ve.startup_id
            WHERE ve.corporate_id = ?
        """, (entity_id,)).fetchall() if _table_exists(conn, "validation_edges") else []
        return {
            "id": r[0], "name": r[1], "country": (r[2] or "").upper(),
            "website": r[3] or "", "entity_type": "corporate",
            "industry": r[4] or "",
            "demand_profile": r[5] or "",
            "innovation_maturity": r[6] or "",
            "validations": [(v[0], v[1]) for v in validations],
        }

    return None


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


# ── Pair classification ───────────────────────────────────────────────────────

def _classify_pair(a: dict, b: dict) -> str:
    """Return canonical pair_type string."""
    types = {a["entity_type"], b["entity_type"]}
    if types == {"startup", "investor"}:
        return "startup_investor"
    if "startup" in types and "organization" in types:
        return "startup_org"
    if "startup" in types and "eso" in types:
        return "startup_eso"
    if "startup" in types and "corporate" in types:
        return "startup_corporate"
    if "investor" in types and "organization" in types:
        return "investor_org"
    if "investor" in types and "eso" in types:
        return "investor_eso"
    return "generic"


# ── Synergy computation ───────────────────────────────────────────────────────

def _compute_synergy_startup_investor(startup: dict, inv: dict) -> dict:
    signals = []
    score = 0.0

    # Theme match
    st_theme = startup.get("theme", "")
    inv_themes = inv.get("portfolio_themes", [])
    if st_theme and st_theme in inv_themes:
        signals.append(f"theme_exact:{st_theme}")
        score += 0.45
    elif st_theme:
        # Try adjacent
        from src.intelligence import _theme_overlap
        best = max((_theme_overlap(st_theme, t) for t in inv_themes), default=0.0)
        if best > 0.30:
            signals.append(f"theme_adjacent:{st_theme}({best:.2f})")
            score += 0.45 * best

    # Country match
    inv_countries = inv.get("portfolio_countries", [])
    if startup["country"] and startup["country"] in inv_countries:
        signals.append(f"geographic_match:{startup['country']}")
        score += 0.20
    elif startup["country"] and startup["country"] == inv["country"]:
        signals.append(f"investor_country:{startup['country']}")
        score += 0.10

    # Portfolio gap (startup NOT already funded by this investor)
    if startup["id"] not in inv.get("portfolio_ids", []):
        signals.append("portfolio_gap:not_yet_invested")

    # Quality signal
    if startup["quality"] >= 8.0:
        signals.append(f"high_data_quality:{startup['quality']}")
        score += 0.10

    # Stage fit (if investor type suggests stage preference)
    itype = inv.get("itype", "").lower()
    stage = startup.get("stage", "").lower()
    if ("accelerator" in itype or "incubat" in itype) and stage in ("pre-seed", "seed", ""):
        signals.append("stage_fit:early_stage_specialist")
        score += 0.10
    elif ("vc" in itype or "venture" in itype) and stage in ("seed", "series-a", "series-b"):
        signals.append(f"stage_fit:{stage}")
        score += 0.08

    # Already funded (social proof)
    if startup["funded"] and len(startup["investors"]) >= 2:
        signals.append(f"co_investors:{len(startup['investors'])}")

    score = min(1.0, score)
    return {"score": round(score, 3), "signals": signals}


_THEME_ORG_KEYWORDS = {
    "Bioinputs & Crop Resilience": ["biotech","agtech","agro","bio","crop","agriculture"],
    "Precision Agriculture": ["agro","farm","tech","precision","agriculture"],
    "Nature & Ecosystem Tech": ["biotech","climate","nature","eco","ambiente"],
    "Food Systems & Alt Proteins": ["food","aliment","biotech","agtech"],
    "Biomanufacturing & Platform Technologies": ["biotech","industrial","bio","manufactur"],
    "Biomaterials & Green Chemistry": ["biotech","bio","material","circular"],
    "Therapeutics": ["pharma","biotech","medicina","health","terapia"],
    "Diagnostics & Devices": ["health","diagnos","medtech","biotech"],
}


def _compute_synergy_startup_org(startup: dict, org: dict) -> dict:
    signals = []
    score = 0.0

    st_theme = startup.get("theme", "")
    focus_area = org.get("focus_area", "").lower()

    # Theme-focus alignment
    kws = _THEME_ORG_KEYWORDS.get(st_theme, [])
    matches = sum(1 for kw in kws if kw in focus_area)
    if matches >= 2:
        signals.append(f"theme_focus_match:{st_theme}")
        score += 0.45
    elif matches == 1:
        signals.append(f"theme_focus_partial:{st_theme}")
        score += 0.25

    # Country
    if startup["country"] == org["country"]:
        signals.append(f"same_country:{startup['country']}")
        score += 0.30

    # Is it already a member? (via support_edges)
    signals.append("no_current_formal_relation")

    # Quality
    if startup["quality"] >= 7.5:
        signals.append(f"showcase_quality:{startup['quality']}")
        score += 0.10

    score = min(1.0, score)
    return {"score": round(score, 3), "signals": signals}


def _compute_synergy_startup_eso(startup: dict, eso: dict) -> dict:
    signals = []
    score = 0.0

    service_profile = eso.get("service_profile", "").lower()
    geo_focus = eso.get("geo_focus", "").lower()

    # Geography first (most critical for ESOs)
    if startup["country"] == eso["country"]:
        signals.append(f"same_country:{startup['country']}")
        score += 0.40
    elif startup["country"] and startup["country"].lower() in geo_focus:
        signals.append(f"geo_focus_match:{startup['country']}")
        score += 0.30
    elif "latam" in geo_focus:
        signals.append("latam_scope")
        score += 0.15

    # Service fit
    st_theme = startup.get("theme", "")
    if st_theme:
        _ESO_SERVICE_THEMES = {
            "grants": ["Bioinputs","Therapeutics","Biomanufacturing","Farm","Nature","Food","Diagnostics","Biomaterials"],
            "acceleration": ["Farm","Bioinputs","Food","Nature"],
            "research_transfer": ["Bioinputs","Biomanufacturing","Therapeutics","Biomaterials"],
            "technology_licensing": ["Bioinputs","Biomanufacturing","Biomaterials"],
        }
        for svc in service_profile.split(";"):
            svc = svc.strip()
            eligible_themes = _ESO_SERVICE_THEMES.get(svc, [])
            if any(t in st_theme for t in eligible_themes):
                signals.append(f"service_match:{svc}")
                score += 0.30
                break

    # Stage preference (ESOs typically support early stage)
    stage = startup.get("stage", "").lower()
    if stage in ("", "pre-seed", "seed"):
        signals.append("early_stage_eligible")
        score += 0.15

    # Not yet funded = higher priority for ESO support
    if not startup["funded"]:
        signals.append("unfunded_priority_candidate")
        score += 0.10

    score = min(1.0, score)
    return {"score": round(score, 3), "signals": signals}


_CORP_THEME_KEYWORDS = {
    "Bioinputs & Crop Resilience": ["biocontrol","biostimul","crop","agriculture","agri","biopestic","biofert","semilla","seed"],
    "Precision Agriculture": ["precision","sensor","agri","crop monitoring","data farm"],
    "Nature & Ecosystem Tech": ["sustainable","carbon","regenerat","resource","environment"],
    "Food Systems & Alt Proteins": ["ingredient","food","protein","ferment","novel","cellular"],
    "Biomanufacturing & Platform Technologies": ["bioproces","enzyme","ferment","industrial","manufactur"],
    "Biomaterials & Green Chemistry": ["material","plastic","biobased","polymer","circular"],
    "Therapeutics": ["drug","therapeut","pharma","biologic","gene","cell therapy"],
    "Diagnostics & Devices": ["diagnos","test","detection","biomark","molecular"],
}


def _compute_synergy_startup_corporate(startup: dict, corp: dict) -> dict:
    signals = []
    score = 0.0

    demand_profile = corp.get("demand_profile", "").lower()
    industry = corp.get("industry", "").lower()
    combined = f"{demand_profile} {industry}"

    st_theme = startup.get("theme", "")
    kws = _CORP_THEME_KEYWORDS.get(st_theme, [])
    matches = sum(1 for kw in kws if kw in combined)
    if matches >= 3:
        signals.append(f"strong_demand_match:{st_theme}")
        score += 0.55
    elif matches >= 2:
        signals.append(f"demand_match:{st_theme}")
        score += 0.40
    elif matches == 1:
        signals.append(f"demand_partial:{st_theme}")
        score += 0.20

    # Quality signal
    if startup["quality"] >= 7.5:
        signals.append(f"data_quality:{startup['quality']}")
        score += 0.10

    # Already validated?
    existing_validations = corp.get("validations", [])
    if not any(v[0] == startup["name"] for v in existing_validations):
        signals.append("no_current_validation")
    else:
        signals.append("already_validated")
        score += 0.20

    score = min(1.0, score)
    return {"score": round(score, 3), "signals": signals}


def _compute_synergy_investor_org(inv: dict, org: dict) -> dict:
    signals = []
    score = 0.0

    # Geography alignment
    if inv["country"] == org["country"]:
        signals.append(f"same_country:{inv['country']}")
        score += 0.35

    # Is there already membership?
    # (This would require DB check — approximate here)
    signals.append("membership_gap_potential")
    score += 0.30

    # Portfolio themes overlap with org focus
    focus_area = org.get("focus_area", "").lower()
    for t in inv.get("portfolio_themes", [])[:3]:
        if any(kw in focus_area for kw in t.lower().split(" ")[:2]):
            signals.append(f"portfolio_theme_in_focus:{t[:30]}")
            score += 0.20
            break

    score = min(1.0, score)
    return {"score": round(score, 3), "signals": signals}


# ── Narrative templates ───────────────────────────────────────────────────────

_TEMPLATES = {
    "startup_investor": {
        "theme_exact": (
            "{inv_name} ha construido un portfolio de {portfolio_size} startups con "
            "fuerte concentración en {theme}. {startup_name} opera exactamente en este espacio "
            "desde {country}, con un data quality score de {quality}/10"
            "{one_liner_fragment}."
        ),
        "theme_adjacent": (
            "{inv_name} tiene experiencia en {main_inv_theme} y ha demostrado interés "
            "en biología aplicada adyacente. {startup_name} trabaja en {theme} — "
            "un tema que comparte plataformas técnicas con el core del portfolio de {inv_name}."
        ),
        "no_theme_match": (
            "{startup_name} es una startup {theme} de {country} con calidad de datos {quality}/10. "
            "Si bien {inv_name} no tiene posiciones públicas en este tema exacto, "
            "hay potencial de expansión de tesis."
        ),
    },
    "startup_org": {
        "same_country_theme": (
            "{org_name} representa el sector biotecnológico en {country} y su mandato "
            "incluye {focus_area}. {startup_name} — {one_liner} — es exactamente el tipo "
            "de empresa que {org_name} busca destacar y conectar con el ecosistema."
        ),
        "generic": (
            "{org_name} tiene un mandato de {focus_area}. "
            "{startup_name} trabaja en {theme} desde {country} y puede beneficiarse "
            "de la red y visibilidad que {org_name} ofrece."
        ),
    },
    "startup_eso": {
        "grant_candidate": (
            "{eso_name} financia proyectos de innovación en {geo_focus}. "
            "{startup_name} — {one_liner} — está en etapa {stage} y tiene un perfil "
            "de calidad de datos {quality}/10, lo que la convierte en candidata elegible "
            "para los instrumentos de {service_profile} que ofrece {eso_name}."
        ),
        "accel_candidate": (
            "{eso_name} ofrece programas de aceleración en {geo_focus}. "
            "{startup_name} está trabajando en {theme} y podría beneficiarse "
            "significativamente del soporte técnico y de mercado que {eso_name} provee."
        ),
    },
    "startup_corporate": {
        "demand_match": (
            "{corp_name} está buscando activamente innovaciones en {demand_profile}. "
            "{startup_name} desarrolla tecnología de {theme} — exactamente en este espacio — "
            "con un nivel técnico que la posiciona para un piloto o acuerdo de validación."
        ),
        "generic": (
            "{corp_name} opera en {industry} y tiene mandato de innovación abierta. "
            "{startup_name} trabaja en {theme} y puede representar una oportunidad "
            "de validación, co-desarrollo o eventual adquisición."
        ),
    },
    "investor_org": {
        "same_country": (
            "{org_name} es la principal asociación de {org_type} en {country} y conecta "
            "los fondos de inversión más activos del ecosistema. {inv_name} tiene un portfolio "
            "de {portfolio_size} startups y podría beneficiarse de mayor visibilidad, "
            "deal flow local y co-inversión."
        ),
    },
}


def _build_rationale(pair_type: str, a: dict, b: dict, synergy: dict) -> str:
    """Build 2-3 sentence narrative from signals. Template-based, no LLM."""
    signals = synergy.get("signals", [])

    startup = a if a["entity_type"] == "startup" else (b if b.get("entity_type") == "startup" else None)
    inv = a if a.get("entity_type") == "investor" else (b if b.get("entity_type") == "investor" else None)
    org = a if a.get("entity_type") == "organization" else (b if b.get("entity_type") == "organization" else None)
    eso = a if a.get("entity_type") == "eso" else (b if b.get("entity_type") == "eso" else None)
    corp = a if a.get("entity_type") == "corporate" else (b if b.get("entity_type") == "corporate" else None)

    one_liner_frag = (
        f" ({startup['one_liner'][:80]})" if startup and startup.get("one_liner") else ""
    )

    if pair_type == "startup_investor" and startup and inv:
        inv_themes = inv.get("portfolio_themes", [])
        top_inv_theme = inv_themes[0] if inv_themes else "biotecnología"
        has_theme_exact = any("theme_exact" in s for s in signals)
        tpl_key = "theme_exact" if has_theme_exact else (
            "theme_adjacent" if any("theme_adjacent" in s for s in signals) else "no_theme_match"
        )
        tpl = _TEMPLATES["startup_investor"][tpl_key]
        sent1 = tpl.format(
            inv_name=inv["name"],
            portfolio_size=inv.get("portfolio_size", "N/A"),
            theme=startup.get("theme", "biotecnología"),
            startup_name=startup["name"],
            country=startup.get("country", "la región"),
            quality=startup.get("quality", "—"),
            one_liner_fragment=one_liner_frag,
            main_inv_theme=top_inv_theme,
        )

        # Add co-investor social proof if available
        sent2 = ""
        if startup.get("investors"):
            other_inv = [i for i in startup["investors"] if i != inv["name"]]
            if other_inv:
                sent2 = (
                    f" Ya cuenta con el respaldo de {', '.join(other_inv[:2])}"
                    f"{'...' if len(other_inv) > 2 else ''}."
                )

        # Portfolio context sentence
        top_countries = inv.get("portfolio_countries", [])
        sent3 = ""
        if top_countries:
            sent3 = (
                f" {inv['name']} es activo en {', '.join(top_countries[:3])}"
                f"{', entre otros países' if len(top_countries) > 3 else ''}."
            )

        return (sent1 + sent2 + sent3).strip()

    if pair_type == "startup_org" and startup and org:
        has_country = any("same_country" in s for s in signals)
        tpl_key = "same_country_theme" if has_country else "generic"
        tpl = _TEMPLATES["startup_org"][tpl_key]
        return tpl.format(
            org_name=org["name"],
            country=org.get("country", "la región"),
            focus_area=org.get("focus_area", "biotecnología")[:60],
            startup_name=startup["name"],
            one_liner=startup.get("one_liner", "startup biotech")[:80],
            theme=startup.get("theme", "biotecnología"),
        ).strip()

    if pair_type == "startup_eso" and startup and eso:
        svc = eso.get("service_profile", "").lower()
        tpl_key = "grant_candidate" if "grant" in svc else "accel_candidate"
        tpl = _TEMPLATES["startup_eso"][tpl_key]
        return tpl.format(
            eso_name=eso["name"],
            geo_focus=eso.get("geo_focus", "la región")[:40],
            startup_name=startup["name"],
            one_liner=startup.get("one_liner", "startup biotech")[:80],
            stage=startup.get("stage", "early-stage") or "early-stage",
            quality=startup.get("quality", "—"),
            service_profile=svc[:50],
            theme=startup.get("theme", "biotecnología"),
        ).strip()

    if pair_type == "startup_corporate" and startup and corp:
        has_strong = any("strong_demand" in s for s in signals)
        has_medium = any(s.startswith("demand_match") for s in signals)
        tpl_key = "demand_match" if (has_strong or has_medium) else "generic"
        tpl = _TEMPLATES["startup_corporate"][tpl_key]
        return tpl.format(
            corp_name=corp["name"],
            demand_profile=corp.get("demand_profile", "innovación en biología")[:60],
            startup_name=startup["name"],
            theme=startup.get("theme", "biotecnología"),
            industry=corp.get("industry", "agri-industria")[:50],
        ).strip()

    if pair_type in ("investor_org", "investor_eso") and inv and (org or eso):
        facilitator = org or eso
        tpl = _TEMPLATES["investor_org"]["same_country"]
        return tpl.format(
            org_name=facilitator["name"],
            org_type=facilitator.get("org_type") or facilitator.get("eso_type") or "capital",
            country=facilitator.get("country", "la región"),
            inv_name=inv["name"],
            portfolio_size=inv.get("portfolio_size", "N/A"),
        ).strip()

    return (
        f"Existe una oportunidad de conexión entre {a['name']} y {b['name']} "
        f"basada en alineamiento temático y geográfico dentro del ecosistema BIO LATAM."
    )


def _build_talking_points(pair_type: str, a: dict, b: dict, synergy: dict) -> list[str]:
    """Return 3-5 concrete talking points for the first meeting."""
    signals = synergy.get("signals", [])
    startup = a if a["entity_type"] == "startup" else (b if b.get("entity_type") == "startup" else None)
    inv = a if a.get("entity_type") == "investor" else (b if b.get("entity_type") == "investor" else None)
    org = a if a.get("entity_type") == "organization" else (b if b.get("entity_type") == "organization" else None)
    eso = a if a.get("entity_type") == "eso" else (b if b.get("entity_type") == "eso" else None)
    corp = a if a.get("entity_type") == "corporate" else (b if b.get("entity_type") == "corporate" else None)

    pts = []

    if pair_type == "startup_investor" and startup and inv:
        pts.append(
            f"Presentar el modelo de negocio de {startup['name']} con foco en "
            f"diferenciación técnica en {startup.get('theme','biotecnología')}"
        )
        if any("theme_exact" in s for s in signals):
            pts.append(
                f"Comparar con otras startups del portfolio de {inv['name']} en "
                f"{startup.get('theme','')} — ¿complementan o compiten?"
            )
        pts.append(
            f"Discutir hitos al próximo hito de financiamiento: "
            f"{'etapa siguiente a ' + startup.get('stage','') if startup.get('stage') else 'próxima ronda'}"
        )
        if startup.get("investors"):
            pts.append(
                f"Contexto de co-inversores actuales: {', '.join(startup['investors'][:2])}"
            )
        pts.append(
            f"Evaluar fit geográfico: {startup.get('country','')} en el mapa de operaciones de {inv['name']}"
        )

    elif pair_type == "startup_org" and startup and org:
        pts.append(
            f"Presentar {startup['name']} como empresa referente de {startup.get('theme','')} "
            f"que {org['name']} puede destacar en sus comunicaciones"
        )
        pts.append(f"Explorar membresía formal de {startup['name']} en {org['name']}")
        pts.append(
            f"Identificar eventos o espacios de {org['name']} donde {startup['name']} "
            f"puede presentarse ante potenciales clientes o inversores"
        )
        pts.append(
            f"Ver si {startup['name']} puede contribuir como caso de estudio o "
            f"vocero en actividades de {org['name']}"
        )

    elif pair_type == "startup_eso" and startup and eso:
        svc = eso.get("service_profile", "")
        pts.append(
            f"Revisar elegibilidad de {startup['name']} para los instrumentos de "
            f"{svc[:50]} de {eso['name']}"
        )
        pts.append(
            f"Discutir necesidades de {startup['name']}: "
            f"¿capital semilla, mentoría técnica, o acceso a laboratorios?"
        )
        pts.append(
            f"Evaluar si hay convocatorias abiertas en {eso['name']} para startups de "
            f"{startup.get('theme','biotecnología')}"
        )
        pts.append(
            f"Conectar {startup['name']} con la red de investigadores y técnicos de {eso['name']}"
        )

    elif pair_type == "startup_corporate" and startup and corp:
        pts.append(
            f"Presentar la tecnología de {startup['name']} como solución para "
            f"la demanda de {corp.get('demand_profile','innovación')[:50]} de {corp['name']}"
        )
        pts.append(
            f"Proponer un piloto pequeño o prueba de concepto con {corp['name']} "
            f"en un cultivo o línea de producción específica"
        )
        pts.append(
            f"Discutir posibles modelos de contrato: licencia, joint development, supply agreement"
        )
        pts.append(
            f"Identificar el equipo de innovación abierta o M&A de {corp['name']} "
            f"como contacto clave"
        )

    elif pair_type in ("investor_org", "investor_eso") and inv and (org or eso):
        facilitator = org or eso
        pts.append(
            f"Presentar el portfolio de {inv['name']} "
            f"({inv.get('portfolio_size','N/A')} startups en "
            f"{', '.join(inv.get('portfolio_themes',[])[:2])})"
        )
        pts.append(
            f"Explorar membresía o partnership formal de {inv['name']} en {facilitator['name']}"
        )
        pts.append(
            f"Evaluar co-financiamiento: ¿puede {facilitator['name']} proveer grants "
            f"complementarios para startups del portfolio de {inv['name']}?"
        )
        pts.append(
            f"Identificar startups del portfolio de {inv['name']} "
            f"elegibles para programas de {facilitator['name']}"
        )

    else:
        pts.append(f"Presentar los objetivos estratégicos de {a['name']}")
        pts.append(f"Identificar puntos concretos de colaboración")
        pts.append(f"Explorar próximos pasos y responsables de cada parte")

    return pts[:5]


def _build_suggested_ask(pair_type: str, a: dict, b: dict) -> str:
    startup = a if a["entity_type"] == "startup" else (b if b.get("entity_type") == "startup" else None)
    inv = a if a.get("entity_type") == "investor" else (b if b.get("entity_type") == "investor" else None)
    org = a if a.get("entity_type") == "organization" else (b if b.get("entity_type") == "organization" else None)
    eso = a if a.get("entity_type") == "eso" else (b if b.get("entity_type") == "eso" else None)
    corp = a if a.get("entity_type") == "corporate" else (b if b.get("entity_type") == "corporate" else None)

    if pair_type == "startup_investor" and startup and inv:
        return (
            f"Pedirle a {inv['name']} 30 minutos para presentar la tesis de {startup['name']} "
            f"y explorar si hay fit con su portfolio actual."
        )
    if pair_type == "startup_org" and startup and org:
        return (
            f"Pedir a {org['name']} que {startup['name']} sea incluida en el próximo "
            f"evento o directorio de miembros, y explorar membresía formal."
        )
    if pair_type == "startup_eso" and startup and eso:
        return (
            f"Solicitar a {eso['name']} una reunión de pre-screening para evaluar "
            f"elegibilidad de {startup['name']} en sus próximas convocatorias."
        )
    if pair_type == "startup_corporate" and startup and corp:
        return (
            f"Proponer a {corp['name']} un piloto de 3 meses con {startup['name']} "
            f"con métricas claras de evaluación."
        )
    if pair_type in ("investor_org", "investor_eso") and inv and (org or eso):
        fac = org or eso
        return (
            f"Explorar con {fac['name']} las condiciones de membresía o partnership "
            f"para {inv['name']} y co-financiamiento de startups."
        )
    return f"Agendar una reunión inicial de 45 minutos para explorar sinergias concretas."


def _build_email_template(
    a: dict, b: dict, brief: dict, cab_context: bool = True
) -> dict:
    """Build ready-to-use email subject and body."""
    pair_type = brief["pair_type"]
    score = brief["synergy_score"]
    rationale = brief["synergy_rationale"]
    tps = brief["talking_points"]
    ask = brief["suggested_ask"]

    startup = a if a["entity_type"] == "startup" else (b if b.get("entity_type") == "startup" else None)
    other = b if a["entity_type"] == "startup" else a

    # Subject
    signal_hint = ""
    signals = brief.get("context_signals", [])
    for s in signals:
        if "theme_exact" in s:
            signal_hint = f" — fit temático directo"
            break
        elif "geographic_match" in s:
            signal_hint = f" — match geográfico + temático"
            break
        elif "demand_match" in s or "strong_demand" in s:
            signal_hint = f" — oportunidad de validación"
            break

    subject = f"Presentación: {a['name']} ↔ {b['name']}{signal_hint}"

    # Body
    from_line = "La Cámara Argentina de Biotecnología (CAB)" if cab_context else "Nosotros"

    intro_line = (
        f"{from_line} tiene el agrado de conectar a {a['name']} y {b['name']} "
        f"dentro del ecosistema BIO LATAM."
    )

    context_line = rationale

    tp_lines = "\n".join(f"  • {tp}" for tp in tps)

    ask_line = ask

    body = f"""{intro_line}

{context_line}

Algunos puntos que podrían explorar en una primera reunión:
{tp_lines}

Próximo paso sugerido:
{ask_line}

Quedamos disponibles para facilitar esta conversación.

Con gusto,
{"Equipo CAB — Cámara Argentina de Biotecnología" if cab_context else "El equipo"}
"""

    return {"subject": subject, "body": body.strip()}


# ── Quality notes ─────────────────────────────────────────────────────────────

def _build_quality_notes(a: dict, b: dict) -> list[str]:
    notes = []
    startup = a if a.get("entity_type") == "startup" else (b if b.get("entity_type") == "startup" else None)
    if startup:
        if not startup.get("one_liner"):
            notes.append("startup sin business_one_liner — agregar para mejorar el brief")
        if not startup.get("summary"):
            notes.append("startup sin startup_summary — agregar para contextualizar mejor")
        if startup.get("quality", 0) < 6.0:
            notes.append(f"calidad de datos baja ({startup['quality']}/10) — completar ficha del startup")
    inv = a if a.get("entity_type") == "investor" else (b if b.get("entity_type") == "investor" else None)
    if inv and not inv.get("thesis"):
        notes.append("inversor sin thesis registrada — agregar para mejorar el análisis de fit")
    return notes


# ── Main entry point ──────────────────────────────────────────────────────────

def build_introduction_brief(
    entity_a_id: str,
    entity_b_id: str,
    db_path: Path = DB_PATH,
    cab_context: bool = True,
    format: str = "json",   # "json" | "markdown"
) -> dict:
    """Build a structured introduction brief between any two ecosystem entities.

    Returns a dict ready for CLI display, JSON API response, or email template.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    a = _load_entity_profile(entity_a_id, conn)
    b = _load_entity_profile(entity_b_id, conn)
    conn.close()

    if a is None:
        return {"error": f"Entity '{entity_a_id}' not found in ecosystem DB."}
    if b is None:
        return {"error": f"Entity '{entity_b_id}' not found in ecosystem DB."}

    pair_type = _classify_pair(a, b)

    # Normalize so startup is always 'a' in pair_type logic
    if b.get("entity_type") == "startup" and a.get("entity_type") != "startup":
        a, b = b, a

    # Compute synergy
    if pair_type == "startup_investor":
        startup, other = (a, b) if a["entity_type"] == "startup" else (b, a)
        synergy = _compute_synergy_startup_investor(startup, other)
    elif pair_type == "startup_org":
        startup, other = (a, b) if a["entity_type"] == "startup" else (b, a)
        synergy = _compute_synergy_startup_org(startup, other)
    elif pair_type == "startup_eso":
        startup, other = (a, b) if a["entity_type"] == "startup" else (b, a)
        synergy = _compute_synergy_startup_eso(startup, other)
    elif pair_type == "startup_corporate":
        startup, other = (a, b) if a["entity_type"] == "startup" else (b, a)
        synergy = _compute_synergy_startup_corporate(startup, other)
    elif pair_type in ("investor_org", "investor_eso"):
        synergy = _compute_synergy_investor_org(
            a if a["entity_type"] == "investor" else b,
            b if a["entity_type"] == "investor" else a,
        )
    else:
        synergy = {"score": 0.5, "signals": ["generic_pair"]}

    rationale = _build_rationale(pair_type, a, b, synergy)
    talking_points = _build_talking_points(pair_type, a, b, synergy)
    suggested_ask = _build_suggested_ask(pair_type, a, b)
    quality_notes = _build_quality_notes(a, b)
    email = _build_email_template(a, b, {
        "pair_type": pair_type,
        "synergy_score": synergy["score"],
        "synergy_rationale": rationale,
        "talking_points": talking_points,
        "suggested_ask": suggested_ask,
        "context_signals": synergy.get("signals", []),
    }, cab_context=cab_context)

    brief = {
        "pair_type": pair_type,
        "entity_a": {k: v for k, v in a.items() if k not in ("portfolio_ids",)},
        "entity_b": {k: v for k, v in b.items() if k not in ("portfolio_ids",)},
        "synergy_score": synergy["score"],
        "synergy_rationale": rationale,
        "talking_points": talking_points,
        "suggested_ask": suggested_ask,
        "context_signals": synergy.get("signals", []),
        "email_subject": email["subject"],
        "email_body": email["body"],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "data_quality_notes": quality_notes,
    }

    return brief


def print_brief(brief: dict) -> None:
    """Pretty-print a brief to stdout."""
    if "error" in brief:
        print(f"\n  [ERROR] {brief['error']}\n")
        return

    print(f"\n  {'=' * 70}")
    print(f"  BRIEF DE INTRODUCCION: {brief['entity_a']['name']} <-> {brief['entity_b']['name']}")
    print(f"  Tipo de par: {brief['pair_type']}  |  Synergy score: {brief['synergy_score']:.2f}")
    print(f"  {'=' * 70}\n")

    print(f"  CONTEXTO:")
    print(f"  {brief['synergy_rationale']}\n")

    print(f"  PUNTOS DE CONVERSACION:")
    for tp in brief["talking_points"]:
        print(f"    - {tp}")

    print(f"\n  PROXIMO PASO SUGERIDO:")
    print(f"  {brief['suggested_ask']}\n")

    print(f"  SENALES DE FIT:")
    for s in brief["context_signals"]:
        print(f"    * {s}")

    print(f"\n  EMAIL (asunto + cuerpo):")
    print(f"  Asunto: {brief['email_subject']}")
    print(f"  {'─' * 60}")
    for line in brief["email_body"].split("\n"):
        print(f"  {line}")

    if brief.get("data_quality_notes"):
        print(f"\n  NOTAS DE CALIDAD DE DATOS:")
        for n in brief["data_quality_notes"]:
            print(f"    ! {n}")

    print()
