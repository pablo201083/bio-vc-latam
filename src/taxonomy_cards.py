"""
src/taxonomy_cards.py — Frente B: fichas de taxonomía legibles para terceros.

Emite quality/taxonomy_cards.md: una ficha por cada uno de los 8 bio_themes con
definición, fronteras con temas vecinos, startups arquetípicas (las de mayor
confianza y con fuente externa), y qué queda explícitamente afuera.

Es el artefacto que hace la taxonomía entendible para un inversor o policymaker
que no conoce el repo, y a la vez el estándar contra el que se valida cada
clasificación futura. Las descripciones salen de src/reclassify.py (THEMES) para
que ficha y clasificador no se desincronicen; los arquetipos se leen de la DB en
cada corrida.

Uso:
    python pipeline.py taxonomy-cards
"""
from __future__ import annotations

import pathlib
import sqlite3
from datetime import date

from src.reclassify import THEMES

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Descripciones suplementarias para bio_themes que existen en la DB pero no en el
# clasificador de keywords (THEMES). Biomanufacturing se asigna por curaduría
# aparte; ver nota en taxonomy_cards.md. Mantener acá hasta unificar el clasificador.
SUPPLEMENTARY_DESC: dict[str, str] = {
    "Biomanufacturing & Platform Technologies": (
        "Plataformas y capacidades de producción biológica que sirven a múltiples verticales: "
        "fermentación de precisión, biología sintética/cell-free, enzimas, escalado de bioprocesos, "
        "biofoundries y digital twins de bioproceso. El valor es la capacidad de *producir* lo "
        "biológico, no un producto final de consumo."
    ),
}

# Fronteras explícitas: dónde un tema se confunde con su vecino y cómo se decide.
# Codifica el principio de desambiguación del clasificador (output-destination).
BOUNDARIES: dict[str, list[str]] = {
    "Precision Agriculture": [
        "vs **Bioinputs & Crop Resilience**: Precision Agriculture es *software/datos* "
        "(sensores, satélite, agrofintech); Bioinputs es un *producto biológico* aplicado al cultivo.",
        "vs **Nature & Ecosystem Tech**: si el objeto es el rendimiento del productor → Farm "
        "Intelligence; si el objeto es el ecosistema/carbono/biodiversidad → Nature.",
    ],
    "Bioinputs & Crop Resilience": [
        "vs **Precision Agriculture**: el output es un insumo biológico (biofertilizante, biocontrol, "
        "semilla editada), no una plataforma digital.",
        "vs **Food Systems**: si la biología termina en el cultivo/suelo → Bioinputs; si el output "
        "se ingiere → Food Systems.",
    ],
    "Food Systems & Alt Proteins": [
        "vs **Biomaterials**: misma biología (fermentación), distinto destino — si el producto final "
        "se **ingiere** (alimento, ingrediente, suplemento) → Food; si es material/químico/energía → Biomaterials.",
        "vs **Bioinputs**: el output es comida/nutrición humana o animal, no un insumo de campo.",
    ],
    "Biomaterials & Green Chemistry": [
        "vs **Food Systems**: el output es un **material, químico industrial o vector energético** "
        "(bioplástico, enzima industrial, e-fuel), no alimento.",
        "vs **Biomanufacturing**: Biomaterials nombra el *producto* (material/circular); Biomanufacturing "
        "nombra la *plataforma/capacidad* de producción transversal.",
    ],
    "Nature & Ecosystem Tech": [
        "vs **Precision Agriculture**: el objeto es el ecosistema natural (carbono, biodiversidad, agua, "
        "bosque, océano), no la productividad agrícola.",
        "vs **Bioinputs**: la biorremediación y el monitoreo ambiental van acá; la intervención sobre "
        "el cultivo va a Bioinputs.",
    ],
    "Diagnostics & Devices": [
        "vs **Therapeutics**: Diagnostics *detecta/mide/monitorea* enfermedad; Therapeutics *interviene "
        "para tratar*. Un test molecular → Diagnostics; una terapia celular → Therapeutics.",
        "vs **Biomanufacturing**: si el core es un ensayo biológico de detección → Diagnostics; si es "
        "producir el biológico → Biomanufacturing.",
    ],
    "Therapeutics": [
        "vs **Diagnostics & Devices**: el output es un tratamiento (droga, biológico, terapia "
        "celular/génica), no una medición.",
        "vs **Biomanufacturing**: descubrir/desarrollar la terapia → Therapeutics; producir el biológico "
        "a escala como plataforma → Biomanufacturing.",
    ],
    "Biomanufacturing & Platform Technologies": [
        "Tema **transversal**: plataformas de producción biológica (fermentación de precisión, biología "
        "sintética, enzimas, escalado de bioprocesos) que sirven a varios verticales.",
        "Regla: si la empresa *vende la capacidad/plataforma* → Biomanufacturing; si vende el *producto "
        "final* (alimento, material, terapia) → el tema de ese producto.",
    ],
}

# Qué queda explícitamente AFUERA del universo (refleja thesis_scope_definition + NON_BIO_SIGNALS).
OUT_OF_SCOPE: dict[str, list[str]] = {
    "Precision Agriculture": ["Fintech agrícola sin acople biológico ni de recursos (crédito puro, marketplace).",
                          "Logística/trading de commodities como software horizontal."],
    "Bioinputs & Crop Resilience": ["Agroquímicos sintéticos convencionales sin componente biológico."],
    "Food Systems & Alt Proteins": ["Marcas de alimentos sin tecnología bio/proceso novedoso.",
                                    "Delivery/retail de comida."],
    "Biomaterials & Green Chemistry": ["Reciclaje mecánico o gestión de residuos sin transformación biológica.",
                                       "Energía renovable sin componente bio/material (paneles, software de red puro)."],
    "Nature & Ecosystem Tech": ["Mercados de carbono puramente financieros sin base natural/tecnológica.",
                               "ESG/reporting como software horizontal."],
    "Diagnostics & Devices": ["Telemedicina/EHR sin ensayo biológico como core.",
                                   "Wearables de consumo sin valor diagnóstico clínico."],
    "Therapeutics": ["Wellness/suplementos sin desarrollo terapéutico.",
                    "Software de salud sin intervención biológica."],
    "Biomanufacturing & Platform Technologies": ["Manufactura industrial sin base biológica.",
                                                "Automatización genérica de laboratorio sin foco bio."],
}


def _archetypes(conn: sqlite3.Connection, theme: str, limit: int = 5) -> list[tuple]:
    return conn.execute(
        """
        SELECT e.canonical_name, e.country_code, sx.bio_theme_confidence, sx.business_one_liner
        FROM startup_extended sx JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include' AND sx.bio_theme_primary = ?
          AND sx.scope_basis = 'external_auditable_source'
          AND sx.business_one_liner IS NOT NULL AND sx.business_one_liner <> ''
        ORDER BY sx.bio_theme_confidence DESC, e.canonical_name
        LIMIT ?
        """,
        (theme, limit),
    ).fetchall()


def run(db_path: pathlib.Path) -> dict:
    conn = sqlite3.connect(db_path)

    # Orden por tamaño del tema (descendente), para que la ficha abra con lo más grande.
    sizes = dict(conn.execute(
        "SELECT bio_theme_primary, count(*) FROM startup_extended "
        "WHERE scope_decision='include' AND bio_theme_primary IS NOT NULL GROUP BY 1"
    ).fetchall())
    # Universo real de temas = los presentes en la DB (8), no solo los del
    # clasificador de keywords (7). Biomanufacturing existe en datos pero no en THEMES.
    descriptions = {t: td["description"] for t, td in THEMES.items()}
    descriptions.update(SUPPLEMENTARY_DESC)
    themes = sorted(sizes.keys(), key=lambda t: -sizes.get(t, 0))

    lines: list[str] = []
    lines.append("# Fichas de Taxonomía — Universo BIO VC LATAM\n")
    lines.append(f"_Generado {date.today().isoformat()} desde `src/reclassify.py` (THEMES) + la DB. "
                 "Regenerar con `python pipeline.py taxonomy-cards`._\n")
    lines.append("La taxonomía operativa es **single-level**: un tema primario por startup. Estas 8 "
                 "fichas son la referencia legible para terceros y el estándar contra el que se valida "
                 "cada clasificación. El principio de desambiguación es **el destino del output**, no el "
                 "mecanismo biológico.\n")
    total = sum(sizes.get(t, 0) for t in themes)
    lines.append(f"**{total} startups `include`** distribuidas en 8 temas.\n")
    lines.append("| Tema | n | Cross-cutting |")
    lines.append("|------|---|---------------|")
    for t in themes:
        cc = "transversal" if t == "Biomanufacturing & Platform Technologies" else "—"
        lines.append(f"| {t} | {sizes.get(t, 0)} | {cc} |")
    lines.append("")

    for t in themes:
        lines.append("\n---\n")
        lines.append(f"## {t}  ·  {sizes.get(t, 0)} startups\n")
        desc = descriptions.get(t, "_(sin definición en el clasificador — pendiente de unificar)_")
        lines.append(f"**Definición.** {desc}\n")
        if t not in THEMES:
            lines.append("> ⚠️ Este tema existe en la DB pero **no** en el clasificador "
                         "`src/reclassify.py`. Correr `reclassify-themes` reasignaría estas "
                         "startups a uno de los otros 7. Unificar antes de un rebuild de temas.\n")

        lines.append("**Fronteras (cómo se decide en casos límite).**\n")
        for b in BOUNDARIES.get(t, []):
            lines.append(f"- {b}")
        lines.append("")

        arch = _archetypes(conn, t)
        if arch:
            lines.append("**Startups arquetípicas** (mayor confianza, con fuente externa):\n")
            for name, cc, conf, ol in arch:
                lines.append(f"- **{name}** ({cc or '—'}) — {(ol or '').strip()}")
            lines.append("")

        lines.append("**Queda explícitamente afuera.**\n")
        for o in OUT_OF_SCOPE.get(t, []):
            lines.append(f"- {o}")
        lines.append("")

    out = ROOT / "quality" / "taxonomy_cards.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    conn.close()
    return {"themes": len(themes), "total_startups": total, "output": str(out.relative_to(ROOT))}
