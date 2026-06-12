"""
src/phylo_tree.py — árbol evolutivo (phylo) de ecosystem-phylo.html.

Genera pilot/phylo-tree-data.js (window.IQ_PHYLO_TREE): jerarquía anidada
root → mega → macro → theme → sub_cluster → startup, con conteos por nivel.

El generador original era un one-off que no quedó versionado, por lo que el
árbol quedó desfasado tras los cambios de bio_theme. Esto lo reconstruye como
comando reproducible y, de paso, unifica la taxonomía con la del dendrograma de
startup-themes.html (MEGA_ORDER/MACRO_ORDER): una sola taxonomía mega/macro para
todo el producto, en vez de dos sistemas de nombres divergentes.

El árbol NO requiere linkage Ward: es la taxonomía editorial anidada con la
membresía actual; el layout radial lo computa ecosystem-phylo.html desde la
estructura. La taxonomía mega/macro fue *descubierta* con Ward en su momento,
pero acá es un contrato editorial estable.

Uso:
    python pipeline.py phylo-tree
"""
from __future__ import annotations

import pathlib
import sqlite3

from src.utils import write_js_global

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Taxonomía autoritativa — idéntica a MEGA_ORDER/MACRO_ORDER en startup-themes.html.
# Orden: mega -> [(macro, color, [themes])]. Mantener sincronizado con el dendrograma.
TAXONOMY: list[dict] = [
    {
        "mega": "BioMedicina", "color": "#5A4FCF",
        "macros": [
            {"name": "Diagnóstico · Terapéutica", "color": "#5A4FCF",
             "themes": ["Diagnostics & Devices", "Therapeutics"]},
        ],
    },
    {
        "mega": "BioIndustria & Territorio", "color": "#2E7D52",
        "macros": [
            {"name": "Bioplatforma Industrial", "color": "#8B6D14",
             "themes": ["Food Systems & Alt Proteins", "Biomaterials & Green Chemistry",
                        "Biomanufacturing & Platform Technologies"]},
            {"name": "Agroecosistemas", "color": "#2A7A42",
             "themes": ["Bioinputs & Crop Resilience", "Nature & Ecosystem Tech"]},
            {"name": "Inteligencia de Campo", "color": "#2E4E8C",
             "themes": ["Precision Agriculture"]},
            {"name": "AgTech Digital (eco-adjacent)", "color": "#8C8FA3",
             "themes": ["Digital AgTech & Agrifintech"]},
        ],
    },
]


def _load_startups(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """startup dicts agrupados por bio_theme_primary (solo includes)."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT sx.startup_id AS id, e.canonical_name AS name,
               sx.bio_theme_primary AS bio_theme,
               COALESCE(NULLIF(sx.sub_cluster_label,''), sx.bio_theme_primary) AS sub_cluster_label,
               sx.funding_stage, sx.computed_quality_score AS quality_score,
               sx.tech_depth, e.country_code AS country, e.founded_year,
               sx.is_bio_universe
        FROM startup_extended sx JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include' AND sx.bio_theme_primary IS NOT NULL
        ORDER BY e.canonical_name
        """
    ).fetchall()
    conn.row_factory = None
    by_theme: dict[str, list[dict]] = {}
    for r in rows:
        d = dict(r)
        by_theme.setdefault(d["bio_theme"], []).append(d)
    return by_theme


def _theme_node(theme: str, startups: list[dict]) -> dict:
    """theme → subs (por sub_cluster_label) → startups."""
    subs: dict[str, list[dict]] = {}
    for s in startups:
        subs.setdefault(s["sub_cluster_label"] or theme, []).append(s)

    sub_nodes = []
    for sub_name, members in sorted(subs.items(), key=lambda kv: -len(kv[1])):
        leaves = [{
            "level": "startup", "id": m["id"], "name": m["name"],
            "bio_theme": m["bio_theme"], "sub_cluster_label": m["sub_cluster_label"],
            "funding_stage": m["funding_stage"],
            "quality_score": round(float(m["quality_score"]), 1) if m["quality_score"] is not None else None,
            "tech_depth": m["tech_depth"], "country": m["country"],
            "founded_year": m["founded_year"],
            "is_bio_universe": m["is_bio_universe"],
        } for m in members]
        sub_nodes.append({"name": sub_name, "level": "sub", "_theme": theme,
                          "n": len(leaves), "children": leaves})
    return {"name": theme, "level": "theme", "n": len(startups), "children": sub_nodes}


def run(db_path: pathlib.Path) -> dict:
    conn = sqlite3.connect(db_path)
    by_theme = _load_startups(conn)
    conn.close()

    mega_nodes = []
    total = 0
    used_themes: set[str] = set()
    for mega in TAXONOMY:
        macro_nodes = []
        mega_n = 0
        for macro in mega["macros"]:
            theme_nodes = []
            macro_n = 0
            for theme in macro["themes"]:
                used_themes.add(theme)
                startups = by_theme.get(theme, [])
                if not startups:
                    continue
                tn = _theme_node(theme, startups)
                theme_nodes.append(tn)
                macro_n += tn["n"]
            if theme_nodes:
                macro_nodes.append({"name": macro["name"], "level": "macro",
                                    "color": macro["color"], "n": macro_n, "children": theme_nodes})
                mega_n += macro_n
        mega_nodes.append({"name": mega["mega"], "level": "mega", "color": mega["color"],
                           "n": mega_n, "children": macro_nodes})
        total += mega_n

    # Salvaguarda: ningún bio_theme de la DB debe quedar fuera de la taxonomía.
    orphan_themes = set(by_theme) - used_themes
    if orphan_themes:
        raise ValueError(f"bio_themes fuera de la taxonomía phylo: {orphan_themes} — "
                         "actualizar TAXONOMY en src/phylo_tree.py")

    tree = {"name": "BIO LATAM", "level": "root", "n": total, "children": mega_nodes}
    write_js_global(ROOT / "pilot" / "phylo-tree-data.js", "IQ_PHYLO_TREE", tree)

    return {
        "total_startups": total,
        "megas": [(m["name"], m["n"]) for m in mega_nodes],
        "output": "pilot/phylo-tree-data.js",
    }
