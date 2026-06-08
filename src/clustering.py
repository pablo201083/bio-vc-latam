"""
src/clustering.py — clustering semántico + auto-labeling.

Pipeline:
  1. Toma embeddings cacheados desde src/embeddings.py
  2. UMAP a 10D para clustering (denso)
  3. sklearn HDBSCAN sobre 10D
  4. UMAP a 2D para visualización (separate reducer)
  5. Auto-label de clusters con TF-IDF sobre los summaries de cada cluster
  6. Persiste a SQLite: cluster_id, cluster_label, cluster_confidence,
     umap_x, umap_y, is_outlier, tech_codes, industry_codes

También extrae los códigos cross-cutting (tech_codes, industry_codes) usando
src/vocabularies.py y persiste en startup_extended como JSON arrays.

Uso:
    python -m src.clustering
    python -m src.clustering --min-cluster-size 5
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import time
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "db" / "bio_latam.db"


# UMAP params para clustering (más denso, captura estructura)
UMAP_CLUSTER_PARAMS = {
    "n_components": 10,
    "n_neighbors": 12,
    "min_dist": 0.05,
    "metric": "cosine",
    "random_state": 42,
}

# UMAP params para visualización 2D — toma el 10D como input (euclidean).
# FIX 2025-05: se usa reduced_10d (no 384D raw) como input para que la
# posición 2D refleje la misma topología que HDBSCAN.  Antes, el viz UMAP
# corría independientemente desde los 384D originales y el eje dominante
# pasaba a codificar longitud de descripción (r=0.73) en lugar de semántica.
UMAP_VIZ_PARAMS = {
    "n_components": 2,
    "n_neighbors": 15,
    "min_dist": 0.15,      # compacto — queremos clusters agrupados, no extendidos
    "metric": "euclidean",  # 10D UMAP output es euclidean, no cosine
    "spread": 1.0,          # default — el 1.5 anterior generaba clusters demasiado distantes
    "random_state": 42,
}

HDBSCAN_PARAMS = {
    "min_cluster_size": 6,    # 6 → 14 clusters con 490 startups; granularidad óptima probada
    "min_samples": 3,
    "metric": "euclidean",
    "cluster_selection_method": "eom",
}

# Overrides de cluster — robustos a reasignación de IDs por HDBSCAN.
# Formato: startup_id -> (bio_theme_esperado, keyword_en_cluster_label)
# El runtime resuelve el cluster_id buscando el cluster cuyo label contenga el keyword
# dentro del bio_theme correcto. Si no hay match exacto, usa el cluster más numeroso del tema.
# Razón de cada override: el embedding semántico no capturó el cluster correcto
# (baja confianza HDBSCAN, ambigüedad de keywords, error histórico de tema).
# Auditado: 2026-05-18.
CLUSTER_OVERRIDES: dict[str, tuple[str, str]] = {
    # startup_id: (bio_theme_esperado, keyword_en_label)
    # ── Biomaterials mal asignados a Diagnostics/Therapeutics ───────────────
    "antarka":       ("Biomaterials & Circular Economy",         "biobased"),
    "hybridon":      ("Biomaterials & Circular Economy",         "antimicrobial"),
    # ── Food Systems en cluster incorrecto ──────────────────────────────────
    "heartbest":     ("Food Systems & Alt Proteins",             "novel"),
    "done_properly": ("Food Systems & Alt Proteins",             "ferment"),
    "future_biome":  ("Food Systems & Alt Proteins",             "novel"),
    "kigui":         ("Food Systems & Alt Proteins",             "novel"),
    # ── Bioinputs en clusters de Nature/Ecosystem o Food ────────────────────
    "seedmatriz":    ("Bioinputs & Crop Resilience",             "seed"),
    "microin":       ("Bioinputs & Crop Resilience",             "biolog"),
    "nanotica":      ("Bioinputs & Crop Resilience",             "crop protect"),
    "beeflow":       ("Bioinputs & Crop Resilience",             "biolog"),
    # ── Therapeutics veterinaria/animal health ──────────────────────────────
    "phagelab":      ("Therapeutics",                            "biopharm"),
    "sciphage":      ("Therapeutics",                            "biopharm"),
    # ── Farm Intelligence mal asignados a Nature/Ecosystem ──────────────────
    "agrired":       ("Farm Intelligence",                       "agron"),
    "agrotoken":     ("Farm Intelligence",                       "agron"),
    # ── Otros ───────────────────────────────────────────────────────────────
    "inner_cosmos":  ("Therapeutics",                            "regenerat"),
    "geoprot":       ("Biomanufacturing & Fermentation Economy", "precis"),
}


# ── Layout editorial: dos ejes con significado analítico ─────────────────────
#
# Eje X: tecnología — de "biológico puro" (-1) a "plataforma digital" (+1)
# Eje Y: escala de la materia — de "molecular" (-1) a "ecosistema" (+1)
#
# Cada bio_theme tiene un centroide fijo que refleja su posición en este grid.
# La posición final de cada startup = centroide_editorial + offset_UMAP_intra-tema.
# El offset UMAP preserva la estructura de sub-clusters dentro de cada tema.
#
# Narrativa del mapa:
#   Diagonal ↙ (bio-molecular): Therapeutics — ciencia de moléculas y células
#   Diagonal ↗ (digital-ecosistema): Farm Intelligence — datos a escala de campo
#   Centro: Biomanufacturing, Biomaterials — plataformas transversales
#   Bioinputs y Farm Intelligence comparten el "piso" de campo/organismo,
#   separados horizontalmente por su paradigma tecnológico.
#
EDITORIAL_CENTROIDS: dict[str, tuple[float, float]] = {
    # Eje X — instrumento activo principal:
    #   -1 = el organismo/molécula/material ES la herramienta (bio-físico)
    #   +1 = el dato/modelo/plataforma ES la herramienta (bio-informacional)
    # Eje Y — escala del sistema intervenido:
    #   -1 = sub-organismo (molécula, célula, tejido)
    #   +1 = supra-organismo (campo, cuenca, mercado, bioma)
    #
    # Cada centroide se deriva del marco, no se elige individualmente.
    # Última revisión sistemática: 2026-05-18.
    #
    "Therapeutics":                            (-0.80, -0.70),  # instrumento=molécula/célula; escala=intraorganismo
    "Diagnostics & Health Access":             (-0.30, -0.65),  # instrumento=biosensor/secuenciador (bio); output=dato; escala=molecular
    "Biomanufacturing & Platform Technologies": (-0.65, -0.15),  # instrumento=microorganismo/bioreactor; escala=proceso industrial
    "Biomaterials & Circular Economy":         (-0.15, +0.10),  # instrumento=síntesis bio+química; escala=material; nodo crosscutting
    "Food Systems & Alt Proteins":             (+0.15, +0.15),  # mix bio+digital; escala=alimento/organismo
    "Bioinputs & Crop Resilience":             (-0.50, +0.45),  # instrumento=biológico (microbio, extracto); escala=campo/planta
    "Nature & Ecosystem Tech":                 (+0.05, +0.75),  # mix monitoreo-bio y plataformas; escala=ecosistema
    "Farm Intelligence":                       (+0.70, +0.60),  # instrumento=modelo/sensor/dato (digital); escala=campo/finca
}

# Radio máximo del offset intra-tema (en unidades editoriales [-1,1]).
# 0.18 → los sub-clusters de cada tema ocupan ~18% del canvas half-width,
# suficiente para distinguir sub-grupos sin solapar temas vecinos.
INTRA_THEME_SCALE = 0.18

# Scatter: radio más grande para mayor spread intra-tema en la visualización
# de dispersión. 0.40 triplica el spread sin solapar temas vecinos (distancia
# mínima entre centroides ≈ 5.6 unidades; spread max = 0.40*14 = 5.6 ≤ gap).
INTRA_SCATTER_SCALE = 0.40

# Escala final: de [-1,1] editorial a coordenadas de canvas.
CANVAS_SCALE = 14.0


def editorial_positions(
    raw_2d: np.ndarray,
    ids: list[str],
    bio_themes_map: dict[str, str],
) -> np.ndarray:
    """Calcula posiciones 2D editoriales: centroide fijo por tema + offset UMAP normalizado.

    raw_2d: coordenadas UMAP 2D sin supervisión (usadas solo para offset intra-tema).
    Startups sin bio_theme conocido se posicionan en el centroide del origen (0,0).
    """
    result = np.zeros((len(ids), 2), dtype=np.float32)

    # Agrupar índices por bio_theme
    theme_indices: dict[str, list[int]] = {}
    for i, sid in enumerate(ids):
        t = bio_themes_map.get(sid, "")
        theme_indices.setdefault(t, []).append(i)

    for theme, indices in theme_indices.items():
        cx, cy = EDITORIAL_CENTROIDS.get(theme, (0.0, 0.0))
        pts = raw_2d[indices]                        # posiciones UMAP brutas del tema
        centroid = pts.mean(axis=0)
        offsets  = pts - centroid                    # offset relativo dentro del tema

        # Normalizar a radio INTRA_THEME_SCALE
        max_r = np.linalg.norm(offsets, axis=1).max() if len(offsets) > 1 else 1.0
        if max_r > 0:
            offsets = offsets / max_r * INTRA_THEME_SCALE

        for local_i, global_i in enumerate(indices):
            result[global_i] = [
                (cx + offsets[local_i, 0]) * CANVAS_SCALE,
                (cy + offsets[local_i, 1]) * CANVAS_SCALE,
            ]

    n_placed = sum(1 for sid in ids if bio_themes_map.get(sid, "") in EDITORIAL_CENTROIDS)
    print(f"  Layout editorial: {n_placed}/{len(ids)} con centroide definido "
          f"({len(ids)-n_placed} en origen)")
    return result


def semantic_positions(
    raw_2d: np.ndarray,
    ids: list[str],
    bio_themes_map: dict[str, str],
    canvas_scale: float = CANVAS_SCALE,
) -> np.ndarray:
    """UMAP semántico puro con alineación Procrustes sobre los 7 temas no-hub.

    El UMAP 2D es rotativamente arbitrario: puede salir girado o reflejado en
    cada corrida. Para que el mapa sea interpretable (ejes bio→digital y
    molecular→ecosistema) se aplica una transformación Procrustes que alinea los
    centroides de los 7 temas 'normales' con sus posiciones editoriales.

    Biomanufacturing se EXCLUYE del fitting Procrustes porque es un tema hub
    semánticamente central (igual de cercano a todos los demás temas). Incluirlo
    en el ajuste distorsiona la rotación para los otros 7. Después de aplicar la
    rotación, Biomanufacturing queda donde el dato lo pone — ese es exactamente
    el hallazgo que queremos mostrar.

    La transformación es un cuerpo rígido (rotación + escala global + traslación):
    NO distorsiona distancias relativas entre startups, dentro ni entre temas.

    Diferencia semántico ↔ editorial:
      1. Biomanufacturing: centro semántico del ecosistema vs. esquina editorial
      2. Spread intra-tema: real (heterogeneidad visible) vs. normalizado uniforme
    """
    try:
        from scipy.linalg import orthogonal_procrustes
    except ImportError:
        max_ext = np.abs(raw_2d).max() or 1.0
        return (raw_2d / max_ext * canvas_scale).astype(np.float32)

    # Temas excluidos del fitting Procrustes (hubs semánticos cuya posición
    # real difiere estructuralmente de la editorial por diseño del ecosistema).
    # Se determina empíricamente: si un tema queda persistentemente lejos de su
    # centroide editorial tras el fit, es candidato a hub.
    # Con las correcciones de bio_theme actuales, incluimos todos los temas.
    HUB_THEMES: set[str] = set()   # ningún hub excluido a priori

    # Agrupar índices por tema
    theme_indices: dict[str, list[int]] = {}
    for i, sid in enumerate(ids):
        t = bio_themes_map.get(sid, "")
        theme_indices.setdefault(t, []).append(i)

    # Calcular centroides UMAP para los temas de fitting (excluye hubs)
    fit_themes = sorted(
        t for t in theme_indices
        if t in EDITORIAL_CENTROIDS and t not in HUB_THEMES
    )
    if len(fit_themes) < 2:
        max_ext = np.abs(raw_2d).max() or 1.0
        return (raw_2d / max_ext * canvas_scale).astype(np.float32)

    A = np.array([raw_2d[theme_indices[t]].mean(axis=0) for t in fit_themes])  # UMAP centroids (raw)
    B = np.array([EDITORIAL_CENTROIDS[t] for t in fit_themes])                  # editorial, en [-1,1]

    # Centrar ambas nubes
    A_mean = A.mean(axis=0)
    B_mean = B.mean(axis=0)
    A_c = A - A_mean
    B_c = B - B_mean

    # Procrustes ortogonal sobre los 7 temas no-hub
    R, _ = orthogonal_procrustes(A_c, B_c)

    # Escala óptima: s = tr(A_c @ R @ B_c^T) / ||A_c||²
    AR    = A_c @ R
    denom = float(np.sum(A_c ** 2))
    s     = float(np.trace(AR @ B_c.T)) / denom if denom > 1e-12 else 1.0
    s     = max(0.01, min(s, 100.0))

    # Aplicar a TODOS los puntos (incluyendo hubs — quedan donde el dato los pone)
    aligned = s * (raw_2d - A_mean) @ R + B_mean   # → espacio [-1, 1]

    # Diagnóstico
    A_aligned = s * A_c @ R + B_mean
    residuals = np.linalg.norm(A_aligned - B, axis=1)
    print(f"  Layout semántico Procrustes (excl. hubs): s={s:.4f}, "
          f"residuo medio={residuals.mean():.3f} ed-units "
          f"({residuals.mean()*canvas_scale:.1f}px)")

    # Mostrar dónde queda Biomanufacturing vs. editorial
    for theme, indices in theme_indices.items():
        if theme in HUB_THEMES:
            hub_sem = aligned[indices].mean(axis=0)
            hub_ed  = np.array(EDITORIAL_CENTROIDS.get(theme, (0.0, 0.0)))
            diff    = np.linalg.norm(hub_sem - hub_ed)
            print(f"  Hub '{theme[:30]}': sem=({hub_sem[0]:+.2f},{hub_sem[1]:+.2f}) "
                  f"ed=({hub_ed[0]:+.2f},{hub_ed[1]:+.2f}) Δ={diff:.2f} ed-units "
                  f"→ {('centro semántico' if diff > 0.2 else 'aprox. editorial')}")

    return (aligned * canvas_scale).astype(np.float32)


def conceptual_positions(
    vectors: np.ndarray,
    ids: list[str],
    canvas_scale: float = CANVAS_SCALE,
) -> np.ndarray:
    """Proyección sobre ejes conceptuales definidos por arquetipos curatoriales.

    Los ejes se derivan de contrastes entre compañías arquetípicas que representan
    claramente los polos de cada dimensión. La posición de cada startup es el
    producto punto de su embedding con el vector de cada eje — completamente
    determinado por el contenido semántico del summary.

    Eje X — Naturaleza del instrumento tecnológico:
      Polo izquierdo (bio-material): el organismo/molécula/material ES la herramienta
      Polo derecho (digital-plataforma): el dato/modelo/software ES la herramienta

    Eje Y — Escala de intervención:
      Polo inferior (molecular-celular): acción dentro del organismo
      Polo superior (ecosistema-mercado): acción a escala de campo/sistema/mercado

    Propiedades del layout:
    - Determinístico: misma startup → misma posición siempre
    - Estable: agregar startups no mueve las existentes (los ejes son fijos)
    - Explicable: "está aquí porque su texto usa vocabulario X más que Y"
    - Sin grupos forzados: la agrupación emerge del dato, no de centroides
    - Ortogonal: los dos ejes son perpendiculares en el espacio de embeddings
    """
    # ── Definición de arquetipos por polo ────────────────────────────────────
    # Cada polo: lista de entity_ids que representan claramente ese extremo.
    # Curados manualmente; revisables si el ecosistema cambia.

    ARCHETYPES: dict[str, list[str]] = {
        # Bio-material: el organismo/molécula/material ES la herramienta activa
        "bio_material": [
            "phagelab",       # bacteriófagos como medicina
            "neocell",        # biosimilares en biorreactor
            "bioheuris",      # edición genómica de cultivos
            "beeflow",        # mejora de abejas polinizadoras
            "bioplastix",     # microorganismos produciendo bioplásticos
            "apexzymes",      # enzimas industriales de hongos filamentosos
            "stamm",          # bioprocesadores para biológicos
            "tintte",         # biopigmentos microbianos
            "arqlite",        # conversión de plásticos con procesos bio
            "alkemio",        # refinación sostenible de tierras raras
        ],
        # Digital-plataforma: el dato/modelo/software ES la herramienta
        "digital_platform": [
            "aegro",          # SaaS de gestión agrícola
            "auravant",       # plataforma de datos de precisión agrícola
            "brain_ag",       # IA para riesgo crediticio agro
            "agrofy",         # marketplace digital agropecuario
            "traive",         # plataforma de crédito agrícola IA
            "nexxto",         # monitoreo IoT temperatura/humedad
            "pharmalens-br",  # visión computacional QC pharma
            "speclab",        # fingerprinting espectral ML
            "agrotools",      # plataforma inteligencia agronegocio
        ],
        # Molecular-celular: acción dentro del organismo (molécula, célula, tejido)
        "molecular": [
            "phagelab",           # bacteriófago → bacteria (sub-celular)
            "fecundis",           # reproducción animal, nivel celular
            "inner_cosmos",       # interfaz cerebro-computadora
            "cellco",             # biología sintética, diseño celular
            "mendelics",          # análisis genómico molecular
            "aplife_biotech",     # síntesis de librerías moleculares
            "circa_therapeutics", # terapéutica molecular
            "dharma_bioscience",  # biociencia molecular
            "libera",             # descubrimiento de fármacos
            "apasomics",          # proteómica y ómicas moleculares
        ],
        # Ecosistema-mercado: acción a escala de campo, cuenca, mercado, bioma
        "ecosystem": [
            "satellogic",               # imágenes satelitales, escala planetaria
            "kilimo",                   # eficiencia hídrica a escala de cuenca
            "agree",                    # trazabilidad de cadenas alimentarias
            "agrojusto",                # acceso a mercados para pequeños productores
            "biodiversity_intelligence",# monitoreo de biodiversidad a escala ecosistema
            "carbonext",                # carbono forestal, escala de bioma
            "courageous_land",          # gestión de tierras, escala territorial
            "sistema-bio-mx",           # biodigestores, infraestructura rural
            "tracestory",               # trazabilidad de cadenas de valor
        ],
    }

    id_to_idx = {eid: i for i, eid in enumerate(ids)}

    def pole_vector(pole_ids: list[str]) -> np.ndarray:
        """Promedio de embeddings para los arquetipos de este polo."""
        valid_idx = [id_to_idx[eid] for eid in pole_ids if eid in id_to_idx]
        missing = [eid for eid in pole_ids if eid not in id_to_idx]
        if missing:
            print(f"    [concept] arquetipos no encontrados: {missing}")
        if not valid_idx:
            raise ValueError("Ningún arquetipo encontrado — verificar entity_ids")
        return vectors[valid_idx].mean(axis=0)

    # ── Calcular vectores de eje ─────────────────────────────────────────────
    bio_vec   = pole_vector(ARCHETYPES["bio_material"])
    dig_vec   = pole_vector(ARCHETYPES["digital_platform"])
    mol_vec   = pole_vector(ARCHETYPES["molecular"])
    eco_vec   = pole_vector(ARCHETYPES["ecosystem"])

    # Eje X: de bio-material (izq) a digital-plataforma (der)
    axis_x = dig_vec - bio_vec
    axis_x = axis_x / (np.linalg.norm(axis_x) + 1e-12)

    # Eje Y: de molecular (abajo) a ecosistema (arriba)
    # Ortogonalización de Gram-Schmidt para garantizar perpendicularidad
    axis_y = eco_vec - mol_vec
    axis_y = axis_y - np.dot(axis_y, axis_x) * axis_x   # quitar componente en eje X
    axis_y = axis_y / (np.linalg.norm(axis_y) + 1e-12)

    # ── Proyectar todos los embeddings ───────────────────────────────────────
    proj_x = vectors @ axis_x    # dot product con eje bio↔digital
    proj_y = vectors @ axis_y    # dot product con eje molecular↔ecosistema

    # ── Normalizar al espacio del canvas ─────────────────────────────────────
    # Centrar en cero y escalar para que el percentil 95 quede a canvas_scale*0.75
    def robust_scale(v: np.ndarray) -> np.ndarray:
        center = np.median(v)
        p95 = np.percentile(np.abs(v - center), 95)
        return (v - center) / (p95 + 1e-12) * canvas_scale * 0.75

    scaled_x = robust_scale(proj_x)
    scaled_y = robust_scale(proj_y)

    # ── Diagnóstico: posición de arquetipos en el nuevo espacio ──────────────
    print(f"  Layout conceptual: ejes derivados de {len(ARCHETYPES['bio_material'])} + "
          f"{len(ARCHETYPES['digital_platform'])} arquetipos X, "
          f"{len(ARCHETYPES['molecular'])} + {len(ARCHETYPES['ecosystem'])} arquetipos Y")

    # Mostrar dónde quedan los temas
    from collections import defaultdict as _dd
    theme_x: dict = _dd(list)
    # (ids here are startup ids, no bio_themes_map available — skip per-theme diag)

    return np.column_stack([scaled_x, scaled_y]).astype(np.float32)


def scatter_positions(
    raw_2d: np.ndarray,
    ids: list[str],
    bio_themes_map: dict[str, str],
) -> np.ndarray:
    """Posiciones para scatter plot: misma lógica que editorial_positions pero con
    INTRA_SCATTER_SCALE más grande para mayor separación visual intra-tema."""
    result = np.zeros((len(ids), 2), dtype=np.float32)
    theme_indices: dict[str, list[int]] = {}
    for i, sid in enumerate(ids):
        t = bio_themes_map.get(sid, "")
        theme_indices.setdefault(t, []).append(i)

    for theme, indices in theme_indices.items():
        cx, cy = EDITORIAL_CENTROIDS.get(theme, (0.0, 0.0))
        pts = raw_2d[indices]
        centroid = pts.mean(axis=0)
        offsets = pts - centroid
        max_r = np.linalg.norm(offsets, axis=1).max() if len(offsets) > 1 else 1.0
        if max_r > 0:
            offsets = offsets / max_r * INTRA_SCATTER_SCALE
        for local_i, global_i in enumerate(indices):
            result[global_i] = [
                (cx + offsets[local_i, 0]) * CANVAS_SCALE,
                (cy + offsets[local_i, 1]) * CANVAS_SCALE,
            ]
    return result


def run_umap(vectors: np.ndarray, params: dict, label: str) -> np.ndarray:
    import umap
    print(f"  UMAP {label} → {params['n_components']}D...")
    reducer = umap.UMAP(**params)
    return reducer.fit_transform(vectors).astype(np.float32)


def run_hdbscan(reduced_10d: np.ndarray, params: dict) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.cluster import HDBSCAN
    print(f"  HDBSCAN (min_cluster_size={params['min_cluster_size']})...")
    model = HDBSCAN(**params)
    labels = model.fit_predict(reduced_10d)
    # sklearn HDBSCAN expone probabilities_
    probs = getattr(model, "probabilities_", None)
    if probs is None:
        probs = np.zeros(len(labels), dtype=np.float32)
    return labels, probs.astype(np.float32)


_BIO_THEME_SHORT: dict[str | None, str] = {
    "Soil & Microbiome":          "Soil & Microbiome",
    "Crop & Plant Engineering":   "Crop & Plant Eng.",
    "Fermentation Economy":       "Fermentation Economy",
    "Protein Transition":         "Protein Transition",
    "Human Diagnostics & Access": "Human Diagnostics",
    "Therapeutics":               "Therapeutics",
    "Planetary Biology":          "Planetary Biology",
    "Bio x Data":                 "Bio x Data",
}


def auto_label_clusters(
    labels: np.ndarray,
    texts: list[str],
    tech_map: dict[str, list[str]] | None = None,
    ind_map: dict[str, list[str]] | None = None,
    ids: list[str] | None = None,
    top_k: int = 4,
    min_df: int = 2,
    bio_themes: dict[str, str] | None = None,
) -> dict[int, str]:
    """Etiqueta cada cluster con un nombre de dos capas:

    - Capa 1 (clean name): bio_theme dominante + top TF-IDF keyword como
      disambiguador. Ej: "Therapeutics — cancer targeting".
    - Capa 2 (keywords): top-4 TF-IDF terms, separados por ·.

    El string retornado usa "||" como separador: "Clean Name||kw1 · kw2 · kw3".
    Si los dos componentes son iguales (fallback), se guarda solo el nombre.
    """
    from collections import Counter
    from sklearn.feature_extraction.text import TfidfVectorizer

    unique_clusters = sorted(set(int(c) for c in labels if c != -1))
    if not unique_clusters:
        return {}

    cluster_docs = {c: [] for c in unique_clusters}
    for lbl, txt in zip(labels, texts):
        if lbl != -1:
            cluster_docs[int(lbl)].append(txt or "")
    docs = [" ".join(cluster_docs[c]) for c in unique_clusters]

    stopwords = _load_stopwords()
    vec = TfidfVectorizer(
        max_features=3000,
        ngram_range=(1, 2),
        min_df=min_df,
        stop_words=list(stopwords),
        token_pattern=r"(?u)\b[a-zñáéíóúü]{3,}\b",
        sublinear_tf=True,
    )
    try:
        tfidf = vec.fit_transform(docs)
    except ValueError:
        return {c: f"cluster {c}" for c in unique_clusters}

    vocab = np.array(vec.get_feature_names_out())

    # Pre-compute bio_theme distribution per cluster
    cluster_bio_dist: dict[int, Counter] = {c: Counter() for c in unique_clusters}
    if bio_themes and ids is not None:
        for sid, lbl in zip(ids, labels):
            c = int(lbl)
            if c != -1:
                cluster_bio_dist[c][bio_themes.get(sid)] += 1

    labels_map: dict[int, str] = {}
    for i, c in enumerate(unique_clusters):
        row = tfidf[i].toarray().ravel()
        top_idx = np.argsort(row)[::-1][:top_k * 4]
        candidates = [vocab[j] for j in top_idx if row[j] > 0]

        # Phrases that are noisy as labels (reversed bigrams, generic verbs, etc.)
        _bad_phrases = {
            "food novel", "novel food", "develops biological", "develops innovative",
            "develops advanced", "sources develops", "indicators sources",
            "sources indicators", "resistant vesper", "includes latam",
            # Translation artifacts from curatorial notes
            "enter thesis", "enters thesis", "entra tesis", "thesis company",
            "thesis startup", "enter thesis company",
            # VC/investor names that leaked into summaries
            "vesper ventures", "gridx", "gridx portfolio", "gridx complex",
            "portfolio company", "portfolio startup",
            "biological based", "based biological",
        }

        # Dedup TF-IDF terms (no word overlap between selected terms)
        selected: list[str] = []
        seen_words: set[str] = set()
        for term in candidates:
            if term in _bad_phrases:
                continue
            words = set(term.split())
            if words & seen_words:
                continue
            selected.append(term)
            seen_words.update(words)
            if len(selected) >= top_k:
                break
        keywords = " · ".join(selected) if selected else ""

        # ── Build clean name ──────────────────────────────────────────
        dist = cluster_bio_dist[c]
        if dist:
            total = sum(dist.values())
            most_common = dist.most_common()
            dominant_theme, dominant_n = most_common[0]
            dominant_pct = dominant_n / total

            base = _BIO_THEME_SHORT.get(dominant_theme, dominant_theme or "Mixed")

            # Top TF-IDF term as disambiguator (prefer bigrams — more specific)
            bigrams = [t for t in selected if " " in t]
            unigrams = [t for t in selected if " " not in t]
            disambig = (bigrams[0] if bigrams else (unigrams[0] if unigrams else "")).title()

            if dominant_pct >= 0.65 and not disambig:
                clean = base
            else:
                clean = f"{base} — {disambig}" if disambig else base
        else:
            # No bio_theme data: fall back to top TF-IDF term
            clean = selected[0].title() if selected else f"Cluster {c}"

        label = f"{clean}||{keywords}" if keywords else clean
        labels_map[c] = label

    return labels_map


def _load_stopwords() -> set[str]:
    """Stopwords español+inglés + términos genéricos del dominio."""
    en = {
        "the", "and", "for", "with", "from", "that", "this", "their", "have", "has",
        "are", "was", "were", "into", "its", "based", "company", "startup", "solution",
        "platform", "technology", "using", "use", "uses", "used", "via", "across",
        "products", "services", "providing", "develop", "developing", "developed",
        "data", "system", "systems", "process", "processes", "work", "working", "works",
        "help", "helps", "helping", "enable", "enables", "build", "builds", "building",
        "make", "makes", "provide", "provides", "focus", "focused", "focuses",
        "tool", "tools", "business", "businesses", "companies", "infrastructure",
        "inside", "outside", "around", "through", "approach", "solution",
        "sector", "market", "industry", "industries", "global", "local", "regional",
        "new", "key", "high", "low", "large", "small", "major", "main", "other",
        "first", "second", "also", "well", "both", "one", "two", "three",
        "include", "including", "includes", "allow", "allows", "ensuring",
        "improve", "improving", "increase", "increasing",
        "care", "search", "busca", "seek", "seeks", "aim", "aims", "aimed",
        "production", "produccion", "producción",
        "biotech", "biotechnology",  # too generic for this corpus
        "develop", "develops", "development", "solution", "solutions", "model", "models",
        "company", "companies", "based", "bases", "level", "levels",
        "management", "optimization", "monitoring", "detection", "analysis",
        "supply", "chain", "chains", "value", "values", "network", "networks",
        # phrases that produce noisy labels
        "develops biological", "develops innovative", "develops advanced",
        "novel food", "food novel", "sources develops", "indicators sources",
        "sources indicators", "resistant vesper",
        # Translation artifacts (from "entra en tesis por" → "enters thesis by")
        "enter", "enters", "thesis", "entra",
        # VC/investor names that leaked into summaries
        "vesper", "gridx", "portfolio",
        # Over-generic in this corpus
        "complex", "synthesis", "backed",
    }
    es = {
        "que", "para", "con", "una", "los", "las", "del", "por", "como", "sus",
        "este", "esta", "esto", "ese", "esos", "esas", "más", "pero", "muy", "sin",
        "entre", "sobre", "hasta", "tipo", "tipos", "través", "uso", "usa", "usan",
        "permite", "permiten", "ofrece", "ofrecen", "empresa", "compañía",
        "plataforma", "solución", "tecnología", "tecnologías", "productos", "servicios",
        "datos", "sistema", "sistemas", "proceso", "procesos", "aplica", "aplican",
        "desarrolla", "desarrollan", "desarrollo", "genera", "generan",
        "lleva", "llevar", "llevan", "logra", "lograr", "logran",
        "permite", "permiten", "requiere", "requieren", "busca", "buscar", "buscan",
        "mejora", "mejoran", "brinda", "brindan", "ayuda", "ayudan",
        "produce", "producen", "tiene", "tienen", "hace", "hacen",
        "también", "cada", "donde", "cuando", "cual", "cuales", "quien",
        "todo", "toda", "todos", "todas", "mismo", "misma", "nuevo", "nueva",
        "alto", "alta", "bajo", "baja", "gran", "grande", "pequeño",
        "primero", "segundo", "nivel", "sector", "mercado", "industria",
        "red", "redes", "modelo", "modelos", "acceso", "herramienta", "herramientas",
    }
    editorial = {
        "entra", "entran", "tesis", "core", "belongs", "fits", "scope",
        "latam", "bio", "puede", "pueden", "operan", "opera",
        "incluye", "incluida", "incluido", "incluir", "inclusión", "inclusion",
        "explicación", "explicacion", "motivo", "razón", "razon",
        "decision", "scope decision", "bio latam", "tesis bio", "core bio",
    }
    return en | es | editorial


def reassign_outliers(
    vectors: np.ndarray,
    labels: np.ndarray,
    probs: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Reasigna outliers HDBSCAN al cluster más próximo por similitud cosena (384D).

    Los embeddings ya vienen normalizados L2 desde src/embeddings.py, así que
    similitud cosena = producto punto. La confianza del reasignado se mapea al
    rango [0.05, 0.38] para mantenerlo visualmente distinguible de los miembros
    núcleo del cluster (que tienen probs HDBSCAN ≥ 0.5).

    Retorna (new_labels, new_probs) con 0 outliers (-1).
    """
    outlier_mask = labels == -1
    n_out = int(outlier_mask.sum())
    if n_out == 0:
        return labels, probs

    new_labels = labels.copy()
    new_probs = probs.copy()
    unique_clusters = sorted(set(int(l) for l in labels if l != -1))

    # Centroides normalizados de cada cluster en espacio 384D
    centroid_matrix = np.stack([
        (lambda v: v / (np.linalg.norm(v) or 1))(vectors[labels == c].mean(axis=0))
        for c in unique_clusters
    ])  # (n_clusters, 384)

    outlier_idx = np.where(outlier_mask)[0]
    # dot product de vecs normalizados = coseno similarity
    sims = vectors[outlier_idx] @ centroid_matrix.T  # (n_out, n_clusters)
    best_ci = sims.argmax(axis=1)
    best_sim = sims.max(axis=1)

    for i, orig in enumerate(outlier_idx):
        new_labels[orig] = unique_clusters[best_ci[i]]
        # Mapear similitud cosena a rango [0.05, 0.38] (periferia visible pero distinguible)
        sim = float(np.clip(best_sim[i], 0.0, 1.0))
        new_probs[orig] = 0.05 + sim * 0.33

    print(f"  Reasignados por proximidad: {n_out} startups → conf. periferia [0.05-0.38]")
    return new_labels, new_probs


def extract_codes_for_all(conn: sqlite3.Connection, ids: list[str]) -> tuple[dict, dict]:
    """Devuelve dos dicts startup_id → list[code] para tech e industry."""
    from src.vocabularies import load_tech_vocab, load_industry_vocab, extract_codes

    _, tech_lookup = load_tech_vocab()
    _, ind_lookup = load_industry_vocab()

    rows = conn.execute(
        """SELECT startup_id, technical_stack, technology_tags,
                  industry_destination, domain_tags
           FROM startup_extended WHERE startup_id IN ({})""".format(
            ",".join("?" * len(ids))
        ),
        ids,
    ).fetchall()

    tech_map = {}
    ind_map = {}
    for sid, ts, tt, ind, dt in rows:
        tech_blob = (ts or "") + ";" + (tt or "")
        ind_blob = (ind or "") + ";" + (dt or "")
        tech_map[sid] = extract_codes(tech_blob, tech_lookup)
        ind_map[sid] = extract_codes(ind_blob, ind_lookup)
    return tech_map, ind_map


def sync_vocab_tables(conn: sqlite3.Connection) -> None:
    """Sincroniza vocab_technologies / vocab_industries en SQLite desde los CSVs."""
    from src.vocabularies import load_tech_vocab, load_industry_vocab

    tech_vocab, _ = load_tech_vocab()
    ind_vocab, _ = load_industry_vocab()

    cur = conn.cursor()
    cur.execute("DELETE FROM vocab_technologies")
    cur.executemany(
        "INSERT INTO vocab_technologies (code, canonical_label, aliases, grp) VALUES (?, ?, ?, ?)",
        [(v.code, v.canonical_label, ";".join(v.aliases), v.group) for v in tech_vocab],
    )
    cur.execute("DELETE FROM vocab_industries")
    cur.executemany(
        "INSERT INTO vocab_industries (code, canonical_label, aliases, grp) VALUES (?, ?, ?, ?)",
        [(v.code, v.canonical_label, ";".join(v.aliases), v.group) for v in ind_vocab],
    )
    conn.commit()


def persist_results(
    conn: sqlite3.Connection,
    ids: list[str],
    labels: np.ndarray,
    probs: np.ndarray,
    coords2d: np.ndarray,
    scatter2d: np.ndarray,
    cluster_labels: dict[int, str],
    tech_map: dict[str, list[str]],
    ind_map: dict[str, list[str]],
    semantic2d: np.ndarray | None = None,
    hybrid2d: np.ndarray | None = None,
    conceptual2d: np.ndarray | None = None,
) -> None:
    """Persiste resultados de clustering + códigos a startup_extended."""
    cur = conn.cursor()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Asegurar columnas adicionales (idempotente)
    for col in ("scatter_x", "scatter_y", "semantic_x", "semantic_y", "hybrid_x", "hybrid_y",
                "conceptual_x", "conceptual_y"):
        try:
            cur.execute(f"ALTER TABLE startup_extended ADD COLUMN {col} REAL")
        except Exception:
            pass

    scatter_map    = {sid: (float(scatter2d[i, 0]),    float(scatter2d[i, 1]))
                      for i, sid in enumerate(ids)}
    semantic_map   = {sid: (float(semantic2d[i, 0]),   float(semantic2d[i, 1]))
                      for i, sid in enumerate(ids)} if semantic2d is not None else {}
    hybrid_map     = {sid: (float(hybrid2d[i, 0]),     float(hybrid2d[i, 1]))
                      for i, sid in enumerate(ids)} if hybrid2d is not None else {}
    conceptual_map = {sid: (float(conceptual2d[i, 0]), float(conceptual2d[i, 1]))
                      for i, sid in enumerate(ids)} if conceptual2d is not None else {}

    for sid, lbl, prob, (x, y) in zip(ids, labels, probs, coords2d):
        c = int(lbl)
        # is_outlier = 1 significa "periferia semántica" (asignado por proximidad, conf baja)
        # Todas las startups tienen un cluster válido — ninguna queda excluida
        is_outlier = 1 if float(prob) < 0.4 else 0
        cluster_label = cluster_labels.get(c, f"cluster {c}")
        tech_json = json.dumps(tech_map.get(sid, []))
        ind_json = json.dumps(ind_map.get(sid, []))
        sx, sy   = scatter_map.get(sid, (x, y))
        ux, uy   = semantic_map.get(sid, (x, y))
        hx, hy   = hybrid_map.get(sid, (x, y))
        cx, cy   = conceptual_map.get(sid, (x, y))
        cur.execute(
            """UPDATE startup_extended
               SET cluster_id = ?, cluster_label = ?, cluster_confidence = ?,
                   umap_x = ?, umap_y = ?, is_outlier = ?,
                   tech_codes = ?, industry_codes = ?,
                   scatter_x = ?, scatter_y = ?,
                   semantic_x = ?, semantic_y = ?,
                   hybrid_x = ?, hybrid_y = ?,
                   conceptual_x = ?, conceptual_y = ?
               WHERE startup_id = ?""",
            (c, cluster_label, float(prob), float(x), float(y),
             is_outlier, tech_json, ind_json, sx, sy, ux, uy, hx, hy, cx, cy, sid),
        )

    # Aplicar overrides manuales — resolución por (bio_theme, keyword) en lugar de ID fijo.
    # Construir índice: (bio_theme_dominant, keyword) -> cluster_id para resolución en runtime.
    # bio_theme_dominant = tema más frecuente dentro del cluster.
    from collections import Counter as _Counter
    cluster_theme_dist: dict[int, _Counter] = {}
    for row in conn.execute(
        "SELECT cluster_id, bio_theme_primary FROM startup_extended WHERE scope_decision='include'"
    ).fetchall():
        c = row[0]
        if c is None:
            continue
        cluster_theme_dist.setdefault(c, _Counter())[row[1] or ""] += 1

    def _resolve_cluster(bio_theme: str, keyword: str) -> tuple[int, str] | None:
        """Encuentra el cluster cuyo label contiene keyword y cuyo tema dominante es bio_theme."""
        kw = keyword.lower()
        candidates = []
        for cid, lbl in cluster_labels.items():
            lbl_low = (lbl or "").lower()
            if kw not in lbl_low:
                continue
            dist = cluster_theme_dist.get(cid, _Counter())
            top = dist.most_common(1)
            dominant = top[0][0] if top else ""
            if dominant == bio_theme:
                candidates.append((dist.total(), cid, lbl))
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1], candidates[0][2]
        # Fallback: mayor cluster del bio_theme sin importar keyword
        fallback = [
            (cluster_theme_dist.get(cid, _Counter()).get(bio_theme, 0), cid, lbl)
            for cid, lbl in cluster_labels.items()
        ]
        fallback.sort(reverse=True)
        for score, cid, lbl in fallback:
            if score > 0:
                return cid, lbl
        return None

    n_overrides = 0
    for startup_id, (bio_theme, keyword) in CLUSTER_OVERRIDES.items():
        result = _resolve_cluster(bio_theme, keyword)
        if result is None:
            print(f"  [cluster-override] {startup_id}: no cluster encontrado para ({bio_theme}, {keyword!r})")
            continue
        target_cluster, target_label = result
        updated = cur.execute(
            """UPDATE startup_extended
               SET cluster_id = ?, cluster_label = ?, cluster_confidence = 0.99
               WHERE startup_id = ?""",
            (target_cluster, target_label, startup_id),
        ).rowcount
        n_overrides += updated
    if n_overrides:
        print(f"  [cluster] {n_overrides} overrides manuales aplicados")

    # Audit log
    n_clusters = len(set(int(l) for l in labels if l != -1))
    n_outliers = int((labels == -1).sum())
    summary = {
        "n_startups": len(ids),
        "n_clusters": n_clusters,
        "n_outliers": n_outliers,
        "outlier_pct": round(n_outliers / max(len(ids), 1) * 100, 1),
    }
    cur.execute(
        """INSERT INTO audit_log
           (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
           VALUES (?, 'clustering', NULL, 'startup_extended', 'semantic_cluster', NULL, ?, ?)""",
        (timestamp, json.dumps(summary, ensure_ascii=False),
         "semantic clustering rebuild"),
    )
    conn.commit()


_COUNTRY_NAMES: dict[str, str] = {
    "AR": "Argentina", "BR": "Brazil", "CL": "Chile", "CO": "Colombia",
    "MX": "Mexico", "UY": "Uruguay", "PE": "Peru", "EC": "Ecuador",
    "PY": "Paraguay", "BO": "Bolivia", "VE": "Venezuela", "CR": "Costa Rica",
    "PA": "Panama", "GT": "Guatemala", "US": "USA", "UK": "UK",
    "ES": "Spain", "FR": "France", "NL": "Netherlands", "SG": "Singapore",
    "IL": "Israel", "CA": "Canada", "AE": "UAE",
}
_REGION_SKIP = {"latam", "latinamerica", "latin america", "latam region"}


def _parse_countries(raw: str | None) -> list[str]:
    """Descompone 'AR/US/BR' en ['Argentina', 'USA', 'Brazil'], omitiendo regiones."""
    if not raw:
        return []
    seen: list[str] = []
    for part in str(raw).split("/"):
        token = part.strip()
        if not token or token.lower() in _REGION_SKIP:
            continue
        name = _COUNTRY_NAMES.get(token.upper(), token)
        if name not in seen:
            seen.append(name)
    return seen


def _build_tokens_vocab(startups: list[dict]) -> dict:
    """Build vocabulary of old-taxonomy tokens with counts, for the filter UI."""
    from collections import Counter
    macro_c: Counter = Counter()
    emergent_c: Counter = Counter()
    lens_c: Counter = Counter()
    domain_c: Counter = Counter()
    tech_c: Counter = Counter()
    scale_c: Counter = Counter()

    for s in startups:
        if s.get("macro_theme"):
            macro_c[s["macro_theme"]] += 1
        if s.get("emergent_theme"):
            emergent_c[s["emergent_theme"]] += 1
        for t in s.get("bio_lens", []):
            lens_c[t] += 1
        for t in s.get("domain_tags", []):
            domain_c[t] += 1
        for t in s.get("tech_tags", []):
            tech_c[t] += 1
        for t in s.get("scale_tags", []):
            scale_c[t] += 1

    def _sorted(counter: Counter) -> list[dict]:
        return [{"v": k, "n": v} for k, v in counter.most_common() if v >= 2]

    return {
        "macro": _sorted(macro_c),
        "bio_lens": _sorted(lens_c),
        "domain": _sorted(domain_c),
        "tech": _sorted(tech_c),
        "scale": _sorted(scale_c),
    }


def _extract_self_categories(text: str) -> list[str]:
    """Extrae etiquetas de autocategorización del texto propio de la startup.

    Analiza el one_liner + summary buscando vocabulario que las startups usan
    para describirse a sí mismas (no la taxonomía curatorial). Retorna hasta 3
    etiquetas ordenadas por confianza.
    """
    import re
    t = text.lower()
    t = re.sub(r"[áàä]", "a", t)
    t = re.sub(r"[éèë]", "e", t)
    t = re.sub(r"[íìï]", "i", t)
    t = re.sub(r"[óòö]", "o", t)
    t = re.sub(r"[úùü]", "u", t)

    # (label, [patterns], weight)
    # Patterns son regex; pesos más altos = más específico / más confiable
    RULES: list[tuple[str, list[str], int]] = [
        # ── Salud ─────────────────────────────────────────────────────────────
        ("Therapeutics",      [r"\btherapeutic", r"\bimmunotherap", r"\bdrug discov",
                               r"\boncolog", r"\banticancer", r"\bbiologics?\b",
                               r"\bgene therap", r"\bcell therap", r"\bbiopharm"], 3),
        ("Diagnostics",       [r"\bdiagnostic", r"\bbiomarker", r"\bliquid biopsy",
                               r"\bpcr\b", r"\bsequenc", r"\bgenomic", r"\bmolecular test",
                               r"\bpoint.of.care", r"\bmedical imag"], 3),
        ("MedTech",           [r"\bmedtech\b", r"\bmed.tech\b", r"\bmedical device",
                               r"\bwearable", r"\bimplant", r"\bprosthes",
                               r"\bsurgical", r"\borthopedic", r"\bin vitro"], 3),
        ("HealthTech",        [r"\bhealthtech\b", r"\bhealth.tech\b", r"\bdigital health",
                               r"\btelemedicine", r"\bremote patient", r"\bhealth platform",
                               r"\bwomens health", r"\bmental health"], 2),
        # ── Agro ──────────────────────────────────────────────────────────────
        ("Ag Biologicals",    [r"\bbiopesticide", r"\bbiocontrol", r"\bbiostimulant",
                               r"\bbiofertiliz", r"\bag biological", r"\bmicrobial input",
                               r"\bbioinput", r"\bentomopathog", r"\bnematode",
                               r"\brhizobium", r"\bplant microbiome"], 4),
        ("Precision Ag",      [r"\bprecision agr", r"\bprecision farm",
                               r"\bremote sensing.*agr", r"\bsatellite.*agr",
                               r"\birrigation.*ai", r"\bai.*crop", r"\bcrop monitor",
                               r"\bfield intelligence", r"\bvariable rate"], 3),
        ("AgTech",            [r"\bagtech\b", r"\bag.tech\b", r"\bagricult.*tech",
                               r"\btech.*agric", r"\bsmart farm", r"\bdigital farm",
                               r"\bfarm.*platform", r"\bfarm management",
                               r"\bcrop.*platform", r"\bfarmer.*platform"], 2),
        # ── Alimentos ─────────────────────────────────────────────────────────
        ("Alt Proteins",      [r"\balt.*protein", r"\bplant.based protein",
                               r"\bcell.cultured", r"\bcultivated meat",
                               r"\bprecision ferment.*protein", r"\binsect.*protein",
                               r"\balt.meat", r"\bmycoprotein", r"\balgae.*protein"], 4),
        ("FoodTech",          [r"\bfoodtech\b", r"\bfood.tech\b", r"\bfood.*platform",
                               r"\bfood.*ingredient", r"\bfunctional food",
                               r"\bnovel ingredient", r"\bfood.*biotech",
                               r"\bfood.*ferment", r"\balt.*food\b"], 2),
        # ── Manufactura bio ───────────────────────────────────────────────────
        ("SynBio",            [r"\bsynthetic biology", r"\bsynbio\b",
                               r"\bgene.*circuit", r"\bcrispr", r"\bgenome.*edit",
                               r"\bmetabolic engineer", r"\bcell.*engineer"], 4),
        ("Precision Ferm",    [r"\bprecision ferment", r"\bferment.*platform",
                               r"\brecombinant.*protein", r"\bbioreactor",
                               r"\bcell.free", r"\bmicrobial.*platform"], 3),
        ("Biomanufacturing",  [r"\bbiomanufactur", r"\bcdmo\b", r"\bbioprocess",
                               r"\bscale.up.*bio", r"\bindustrial.*biotech",
                               r"\bcontract.*manufactur.*bio"], 3),
        ("Biomaterials",      [r"\bbiomaterial", r"\bbiopolymer", r"\bbiobased.*material",
                               r"\bbiodegradable.*material", r"\bbioplastic",
                               r"\bgreen.*chemist", r"\bcircular.*material",
                               r"\bbiobased.*packaging"], 3),
        # ── Clima / naturaleza ────────────────────────────────────────────────
        ("CleanTech",         [r"\bcleantech\b", r"\bclean.tech\b", r"\bclean energy",
                               r"\brenewable energy", r"\bcarbon.*removal",
                               r"\bcarbon.*capture", r"\bnet.zero", r"\bgreen.*hydrogen"], 3),
        ("NatureTech",        [r"\bbiodiversity", r"\becosystem.*restor",
                               r"\bnature.*financ", r"\bcarbon.*credit",
                               r"\bcarbon.*market", r"\bnature.*based",
                               r"\breforestation", r"\bwildlife"], 3),
        # ── Digital / software ────────────────────────────────────────────────
        ("AI / Data",         [r"\bai.powered\b", r"\bai.enabled\b", r"\bai.driven\b",
                               r"\bmachine learning\b", r"\bdeep learning\b",
                               r"\bcomputer vision\b", r"\bllm\b", r"\bai model"], 3),
        ("SaaS / Platform",   [r"\bsaas\b", r"\bsoftware.*platform",
                               r"\bcloud.*platform", r"\bapi.first",
                               r"\bno.code\b", r"\bdata platform"], 2),
        ("FinTech",           [r"\bfintech\b", r"\bfin.tech\b", r"\bdigital.*financ",
                               r"\bpayment.*platform", r"\bembedded.*financ",
                               r"\bcredit.*platform", r"\binsurtech"], 3),
        # ── Infraestructura / hardware ────────────────────────────────────────
        ("Hardware / IoT",    [r"\biot\b", r"\bsensor.*platform", r"\bembedded.*system",
                               r"\bhardware.*platform", r"\bdrone\b", r"\bautonomo",
                               r"\brobot", r"\bdevice.*manufactur"], 2),
        # ── Catch-all bio ──────────────────────────────────────────────────────
        ("Biotech",           [r"\bbiotech\b", r"\bbiotechnology\b",
                               r"\bbio.*platform\b", r"\bbio.*company\b"], 1),
    ]

    scores: dict[str, int] = {}
    for label, patterns, weight in RULES:
        for pat in patterns:
            if re.search(pat, t):
                scores[label] = scores.get(label, 0) + weight
                break  # una vez que matchea un patrón de la categoría, no sumamos más

    # Ordenar por score desc, retornar hasta 3 (min score 1)
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return [lbl for lbl, sc in ranked[:3] if sc >= 1]


def write_dashboard_data(conn: sqlite3.Connection) -> None:
    """Genera pilot/startup-themes-data.js con los datos para el dashboard."""
    from src.utils import write_js_global
    from src.vocabularies import load_tech_vocab, load_industry_vocab, vocab_to_dict

    tech_vocab, _ = load_tech_vocab()
    ind_vocab, _ = load_industry_vocab()

    rows = conn.execute("""
        SELECT sx.startup_id, e.canonical_name, e.country_code, e.website,
               sx.macro_theme, sx.emergent_theme,
               COALESCE(NULLIF(sx.startup_summary_en,''), sx.startup_summary_v1) AS startup_summary_v1,
               sx.business_one_liner,
               sx.cluster_id, sx.cluster_label, sx.cluster_confidence,
               sx.umap_x, sx.umap_y, sx.is_outlier,
               sx.tech_codes, sx.industry_codes,
               sx.data_quality_score, sx.quality_band,
               sx.community_id, sx.pagerank,
               sx.valuation_tier,
               COUNT(ie.investment_id) AS n_investors_mapped,
               sx.bio_theme_primary, sx.bio_theme_secondary, sx.is_bio_universe,
               sx.sub_cluster_label,
               sx.funding_stage, sx.funding_bucket_usd, sx.valuation_bucket_usd,
               sx.valuation_estimate_usd, sx.valuation_estimate_source,
               sx.scatter_x, sx.scatter_y,
               sx.bio_lens_tags, sx.domain_tags, sx.technology_tags, sx.scale_tags,
               sx.market_label,
               sx.tech_depth, sx.tech_depth_confidence,
               e.founded_year,
               sx.semantic_x, sx.semantic_y,
               sx.hybrid_x, sx.hybrid_y
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        LEFT JOIN investment_edges ie ON ie.startup_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
        GROUP BY sx.startup_id
        ORDER BY sx.cluster_id, sx.startup_id
    """).fetchall()

    startups = []
    for r in rows:
        tier_raw = r[20]
        countries_list = _parse_countries(r[2])
        # Split "Clean Name||kw1 · kw2" from cluster_label
        raw_label = r[9] or ""
        if "||" in raw_label:
            cl_name, cl_kw = raw_label.split("||", 1)
        else:
            cl_name, cl_kw = raw_label, ""
        startups.append({
            "id": r[0],
            "name": r[1],
            "country": countries_list[0] if countries_list else "",   # primario (compat)
            "countries": countries_list,                               # todos los países
            "website": r[3] or "",
            "macro_theme": r[4] or "",
            "emergent_theme": r[5] or "",
            "summary": (r[6] or "")[:600],
            "one_liner": r[7] or "",
            "cluster_id": r[8] if r[8] is not None else -1,
            "cluster_label": cl_name.strip(),
            "cluster_keywords": cl_kw.strip(),
            "cluster_confidence": round(float(r[10] or 0), 3),
            "x": round(float(r[11] or 0), 3),
            "y": round(float(r[12] or 0), 3),
            "is_outlier": bool(r[13]),
            "tech_codes": json.loads(r[14] or "[]"),
            "industry_codes": json.loads(r[15] or "[]"),
            "quality_score": float(r[16] or 0),
            "quality_band": r[17] or "",
            "community_id": r[18],
            "pagerank": float(r[19] or 0),
            "valuation_tier": float(tier_raw) if tier_raw is not None else None,
            "n_investors_mapped": int(r[21]),
            "bio_theme": r[22] or "",
            "bio_theme_secondary": r[23] or "",
            "is_bio_universe": r[24],
            "sub_cluster_label": r[25] or "",
            "funding_stage": r[26] or None,
            "funding_bucket_usd": int(r[27]) if r[27] is not None else None,
            "valuation_bucket_usd": int(r[28]) if r[28] is not None else None,
            "valuation_estimate_usd": float(r[29]) if r[29] is not None else None,
            "valuation_estimate_source": r[30] or None,
            "sx": round(float(r[31]), 3) if r[31] is not None else round(float(r[11] or 0), 3),
            "sy": round(float(r[32]), 3) if r[32] is not None else round(float(r[12] or 0), 3),
            # ── Previous taxonomy tokens ──────────────────────────────────────
            "bio_lens": [t.strip() for t in (r[33] or "").split(";") if t.strip()],
            "domain_tags": json.loads(r[34]) if (r[34] or "").startswith("[") else [t.strip() for t in (r[34] or "").split(";") if t.strip()],
            "tech_tags": [t.strip() for t in (r[35] or "").split(";") if t.strip()],
            "scale_tags": [t.strip() for t in (r[36] or "").split(";") if t.strip()],
            "market_label": r[37] or "",
            "self_cats": _extract_self_categories((r[7] or "") + " " + (r[6] or "")[:300]),
            # ── Tech depth classification ─────────────────────────────────────
            "tech_depth": r[38] or "unclassified",
            "tech_depth_confidence": round(float(r[39] or 0.5), 3),
            # ── Temporal data ─────────────────────────────────────────────────
            "founded_year": int(r[40]) if r[40] is not None else None,
            # ── Posiciones alternativas de layout ────────────────────────────
            # ux/uy = semántico puro (UMAP normalizado, sin ejes editoriales)
            # hx/hy = híbrido (semántica + fuerza suave hacia ejes editoriales, α=0.35)
            # x/y   = editorial (centroides fijos bio→digital × molecular→ecosistema)
            "ux": round(float(r[41]), 3) if r[41] is not None else round(float(r[11] or 0), 3),
            "uy": round(float(r[42]), 3) if r[42] is not None else round(float(r[12] or 0), 3),
            "hx": round(float(r[43]), 3) if r[43] is not None else round(float(r[11] or 0), 3),
            "hy": round(float(r[44]), 3) if r[44] is not None else round(float(r[12] or 0), 3),
        })

    # Cluster summary con métricas para inversor
    cluster_summary = {}
    for s in startups:
        c = s["cluster_id"]
        if c not in cluster_summary:
            cluster_summary[c] = {
                "cluster_id": c,
                "label": s["cluster_label"],
                "keywords": s["cluster_keywords"],
                "size": 0,
                "bio_themes": {},
                "tech_codes": {},
                "industry_codes": {},
                "countries": {},
                "n_funded": 0,
                "n_featured": 0,
            }
        cs = cluster_summary[c]
        cs["size"] += 1
        b = s["bio_theme"] or "—"
        cs["bio_themes"][b] = cs["bio_themes"].get(b, 0) + 1
        for t in s["tech_codes"]:
            cs["tech_codes"][t] = cs["tech_codes"].get(t, 0) + 1
        for i in s["industry_codes"]:
            cs["industry_codes"][i] = cs["industry_codes"].get(i, 0) + 1
        for co in (s["countries"] or ["—"]):
            cs["countries"][co] = cs["countries"].get(co, 0) + 1
        if s["n_investors_mapped"] > 0:
            cs["n_funded"] += 1
        if s["valuation_tier"] is not None and s["valuation_tier"] >= 2:
            cs["n_featured"] += 1

    clusters_list = sorted(
        [c for c in cluster_summary.values() if c["cluster_id"] != -1],
        key=lambda c: (-c["size"], c["cluster_id"]),
    )

    # ── Network graph data (layout calculado en JS via Force Atlas) ────────────
    investment_rows = conn.execute("""
        SELECT ie.investor_id, e_inv.canonical_name, ie.startup_id,
               COUNT(*) AS n_rounds_inv
        FROM investment_edges ie
        JOIN entities e_inv ON e_inv.entity_id = ie.investor_id
        JOIN startup_extended sx ON sx.startup_id = ie.startup_id
        WHERE sx.scope_decision = 'include'
        GROUP BY ie.investor_id, ie.startup_id
    """).fetchall()

    startup_id_set = {s["id"] for s in startups}
    investor_meta: dict[str, dict] = {}
    graph_edges: list[dict] = []
    startup_investor_map: dict[str, list[str]] = {}   # startup_id → [investor_ids]

    for inv_id, inv_name, st_id, _ in investment_rows:
        if st_id not in startup_id_set:
            continue
        if inv_id not in investor_meta:
            investor_meta[inv_id] = {"name": inv_name, "n": 0}
        investor_meta[inv_id]["n"] += 1
        graph_edges.append({"investor_id": inv_id, "startup_id": st_id})
        startup_investor_map.setdefault(st_id, []).append(inv_id)

    # Embed investor_ids into each startup object
    for s in startups:
        s["investor_ids"] = startup_investor_map.get(s["id"], [])

    investor_nodes = [
        {"id": inv_id, "name": meta["name"], "n_investments": meta["n"]}
        for inv_id, meta in investor_meta.items()
    ]

    # Fund list for filter UI — sorted by portfolio size, only ≥2 startups
    funds_for_filter = sorted(
        [
            {"id": inv_id, "name": meta["name"], "n": meta["n"]}
            for inv_id, meta in investor_meta.items()
            if meta["n"] >= 2
        ],
        key=lambda f: (-f["n"], f["name"]),
    )

    print(f"  Grafo: {len(investor_nodes)} inversores, {len(graph_edges)} aristas "
          f"({len([s for s in startups if s['n_investors_mapped']>0])} startups con inversión)")

    # Curated one-line descriptions per bio_theme for investor-facing UI
    bio_theme_descriptions = {
        "Therapeutics": (
            "Medicina regenerativa, terapia celular, biologics y desarrollo clínico de fármacos "
            "para oncología, enfermedades crónicas y neurología."
        ),
        "Diagnostics & Health Access": (
            "Diagnóstico molecular, medtech no-invasivo y genómica clínica — incluyendo "
            "diagnósticos guiados por terapia y liquid biopsy."
        ),
        "Food Systems & Alt Proteins": (
            "Proteínas alternativas, ingredientes funcionales, alimentos fermentados y biotech "
            "para sistemas alimentarios sostenibles."
        ),
        "Bioinputs & Crop Resilience": (
            "Biofertilizantes, biocontrol microbiano, bioinsumos CDMO y microbiómica del suelo "
            "para agricultura regenerativa."
        ),
        "Nature & Ecosystem Tech": (
            "Trazabilidad ambiental ESG, climate-fintech, monitoreo satelital y tecnología "
            "para conservación de ecosistemas y carbono."
        ),
        "Farm Intelligence": (
            "Agricultura de precisión con sensores IoT, satélite, visión computacional e IA "
            "para optimización de la producción agropecuaria."
        ),
        "Biomaterials & Circular Economy": (
            "Biomateriales avanzados, química verde y bioprocesos circulares que reemplazan "
            "petroquímicos en packaging, textiles e industria."
        ),
        "Biomanufacturing & Fermentation Economy": (
            "Fermentación de precisión, plataformas de síntesis biológica y biofabricación "
            "industrial para producir moléculas, ingredientes y materiales a escala."
        ),
    }

    payload = {
        "computed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "intfloat/multilingual-e5-small",
        "stats": {
            "total_startups": len(startups),
            "n_clusters": len(clusters_list),
            "featured_count": sum(1 for s in startups if s["valuation_tier"] is not None and s["valuation_tier"] >= 2),
            "funded_count": sum(1 for s in startups if s["n_investors_mapped"] > 0),
        },
        "bio_theme_descriptions": bio_theme_descriptions,
        "startups": startups,
        "clusters": clusters_list,
        "vocab_tech": vocab_to_dict(tech_vocab),
        "vocab_industry": vocab_to_dict(ind_vocab),
        "funds": funds_for_filter,
        "tokens_vocab": _build_tokens_vocab(startups),
        "graph": {
            "investor_nodes": investor_nodes,
            "edges": graph_edges,
        },
    }

    out_path = ROOT / "pilot" / "startup-themes-data.js"
    write_js_global(out_path, "STARTUP_THEMES_DATA", payload)
    print(f"  Dashboard data: {out_path.relative_to(ROOT)} ({out_path.stat().st_size // 1024} KB)")


def _clean_label(raw: str) -> tuple[str, str]:
    """Splits 'Clean Name||kw1 · kw2' → ('Clean Name', 'kw1 · kw2')."""
    if "||" in raw:
        name, kw = raw.split("||", 1)
        return name.strip(), kw.strip()
    return raw.strip(), ""


def print_cluster_summary(
    conn: sqlite3.Connection,
    ids: list[str],
    labels: np.ndarray,
    cluster_labels: dict[int, str],
) -> None:
    """Muestra el listado de clusters con tamaño y label."""
    print("\n=== CLUSTERS DETECTADOS ===")
    print(f"{'ID':>4} {'N':>4}  Label")
    print("-" * 80)
    counts: dict[int, int] = {}
    for lbl in labels:
        c = int(lbl)
        counts[c] = counts.get(c, 0) + 1
    for c in sorted(counts.keys()):
        if c == -1:
            marker = "outlier"
        else:
            raw = cluster_labels.get(c, f"cluster {c}")
            name, kw = _clean_label(raw)
            marker = f"{name}  [{kw}]" if kw else name
        print(f"{c:>4} {counts[c]:>4}  {marker}")

    # Compare con bio_theme_primary
    bio_for = dict(conn.execute(
        "SELECT startup_id, bio_theme_primary FROM startup_extended WHERE scope_decision='include'"
    ).fetchall())

    print("\n=== CLUSTER vs BIO THEME (top 5 per cluster) ===")
    cluster_to_bio: dict[int, dict[str, int]] = {}
    for sid, lbl in zip(ids, labels):
        c = int(lbl)
        if c == -1:
            continue
        b = (bio_for.get(sid) or "").strip() or "—"
        cluster_to_bio.setdefault(c, {})[b] = cluster_to_bio.setdefault(c, {}).get(b, 0) + 1

    for c in sorted(cluster_to_bio.keys()):
        raw = cluster_labels.get(c, f"cluster {c}")
        name, kw = _clean_label(raw)
        print(f"\n  [{c}] {name}  ({counts[c]} startups)")
        if kw:
            print(f"       keywords: {kw}")
        bios = sorted(cluster_to_bio[c].items(), key=lambda kv: kv[1], reverse=True)
        for b, n in bios[:5]:
            pct = round(100 * n / counts[c])
            print(f"     {n:>3}  ({pct:>2}%)  {b[:65]}")


def run(
    db_path: pathlib.Path = DB_PATH,
    min_cluster_size: int = HDBSCAN_PARAMS["min_cluster_size"],
    force_embeddings: bool = False,
) -> dict:
    """Pipeline completo de clustering."""
    t0 = time.time()
    from src.embeddings import run as run_embeddings

    print(f"\n=== Semantic clustering ===")

    # 1. Embeddings (con cache)
    emb_result = run_embeddings(force=force_embeddings, db_path=db_path)
    vectors = emb_result["vectors"]
    ids = emb_result["ids"]

    # 2. UMAP a 10D para clustering
    reduced_10d = run_umap(vectors, UMAP_CLUSTER_PARAMS, "clustering")

    # 3. UMAP 2D puro (sin supervisión) — solo para offset intra-tema.
    # El layout macro lo define editorial_positions(), no este UMAP.
    raw_2d = run_umap(reduced_10d, UMAP_VIZ_PARAMS, "viz-raw")

    # 3b. Cargar bio_themes y calcular posiciones editoriales.
    # Macro: centroide fijo por tema (grid bio→digital × molecular→ecosistema).
    # Micro: offset UMAP normalizado dentro de cada tema (preserva sub-clusters).
    conn_pre = sqlite3.connect(db_path)
    bio_themes_map_pre: dict[str, str] = dict(conn_pre.execute(
        "SELECT startup_id, bio_theme_primary FROM startup_extended "
        "WHERE bio_theme_primary IS NOT NULL AND bio_theme_primary != ''"
    ).fetchall())
    conn_pre.close()
    coords_2d   = editorial_positions(raw_2d, ids, bio_themes_map_pre)
    scatter_2d  = scatter_positions(raw_2d, ids, bio_themes_map_pre)
    semantic_2d    = semantic_positions(raw_2d, ids, bio_themes_map_pre)
    conceptual_2d  = conceptual_positions(vectors, ids)

    # 4. HDBSCAN
    params = dict(HDBSCAN_PARAMS)
    params["min_cluster_size"] = min_cluster_size
    labels, probs = run_hdbscan(reduced_10d, params)

    n_clusters = len(set(int(l) for l in labels if l != -1))
    n_outliers = int((labels == -1).sum())
    print(f"  Clusters: {n_clusters} | Sin asignar (antes de reasignación): {n_outliers}/{len(labels)} ({n_outliers*100//len(labels)}%)")

    # Reasignar outliers — ninguna startup queda sin cluster en el observatorio
    labels, probs = reassign_outliers(vectors, labels, probs)
    assert (labels == -1).sum() == 0, "Quedaron outliers sin reasignar"

    # 5. Auto-label
    conn = sqlite3.connect(db_path)
    texts_for_label = []
    # Prefer English-normalized summary for TF-IDF labels; fall back to original
    rows_by_id = dict(conn.execute(
        "SELECT startup_id, COALESCE(NULLIF(startup_summary_en,''), startup_summary_v1) "
        "FROM startup_extended"
    ).fetchall())
    for sid in ids:
        texts_for_label.append(rows_by_id.get(sid) or "")
    # 6. Extraer tech_codes e industry_codes primero (los usamos para mejores labels)
    print("  Extrayendo tech_codes e industry_codes desde vocabularios...")
    tech_map, ind_map = extract_codes_for_all(conn, ids)

    # Mapa startup_id → bio_theme_primary para enriquecer los cluster labels
    bio_themes_map: dict[str, str] = dict(conn.execute(
        "SELECT startup_id, bio_theme_primary FROM startup_extended "
        "WHERE bio_theme_primary IS NOT NULL AND bio_theme_primary != ''"
    ).fetchall())

    cluster_labels = auto_label_clusters(
        labels, texts_for_label,
        tech_map=tech_map, ind_map=ind_map, ids=ids,
        bio_themes=bio_themes_map,
    )
    print(f"  Labels auto-generados: {len(cluster_labels)}")

    # 7. Sincronizar vocab tables
    sync_vocab_tables(conn)

    # 8. Persistir
    print("  Persistiendo a SQLite...")
    persist_results(conn, ids, labels, probs, coords_2d, scatter_2d, cluster_labels, tech_map, ind_map,
                    semantic2d=semantic_2d, conceptual2d=conceptual_2d)

    # 9. Reporte
    print_cluster_summary(conn, ids, labels, cluster_labels)

    # 10. Dashboard data
    write_dashboard_data(conn)

    conn.close()
    elapsed = time.time() - t0
    print(f"\n[OK] Clustering done in {elapsed:.1f}s")
    return {
        "n_clusters": n_clusters,
        "n_outliers": n_outliers,
        "n_startups": len(ids),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-cluster-size", type=int, default=6)
    parser.add_argument("--force-embeddings", action="store_true")
    args = parser.parse_args()
    run(min_cluster_size=args.min_cluster_size, force_embeddings=args.force_embeddings)
