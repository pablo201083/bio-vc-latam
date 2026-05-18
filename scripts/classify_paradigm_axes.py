"""
classify_paradigm_axes.py
--------------------------
Classifies 488 BIO LATAM startups on two axes for the Espacio de Paradigmas chart:

  mscale    (1-6): Escala de la Materia
    1 Molecular      Å→nm   genes, proteins, molecules, drug discovery
    2 Celular        µm→mm  fermentation, bioreactors, cell culture, biopharma mfg
    3 Organismo      mm→m   individual patient, individual plant, animal health
    4 Lote/Producto  m→10m  food products, media, formulated inputs, ingredients
    5 Campo/Sistema  100m→km farm management, soil systems, watersheds, irrigation
    6 Paisaje/Planeta km→∞  ecosystems, carbon, satellites, biodiversity, global

  mparadigm (1.0–3.0 float): Paradigma Tecnológico
    1.0 = 100% Bio-Material   (IP lives in biology/material)
    2.0 = Bio-Digital hybrid
    3.0 = 100% Digital-Comp.  (IP lives in algorithm/data)

Output: quality/paradigm_classification.csv
"""

import sqlite3
import json
import csv
import os
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE, "db", "bio_latam.db")
OUT_PATH = os.path.join(BASE, "quality", "paradigm_classification.csv")

# ── taxonomy ────────────────────────────────────────────────────────────────
SCALE_NAMES = {
    1: "Molecular",
    2: "Celular",
    3: "Organismo",
    4: "Lote/Producto",
    5: "Campo/Sistema",
    6: "Paisaje/Planeta",
}

# Chart X positions for each level (evenly spaced -12 to +12)
SCALE_X = {1: -12.0, 2: -7.2, 3: -2.4, 4: 2.4, 5: 7.2, 6: 12.0}

# ── mscale keywords (points added per hit in combined text) ─────────────────
SCALE_KW = {
    1: [  # Molecular — genes, proteins, small molecules
        'antibod', 'monoclonal', 'protein ', 'peptide', ' rna ', 'mrna', ' dna ', 'gene ',
        'genomic', 'metabolit', 'small molecule', 'crispr', 'drug discovery', 'compound ',
        'nucleotid', 'molecular target', 'ligand', 'receptor', 'drug design',
        'molecular diagnostic', 'sequencing kit', 'biomarker detection', 'assay kit',
        'reagent', 'enzyme ', 'enzymatic', 'proteomic', 'transcriptom', 'lipidom',
        'immunolog', 'biologics ', 'biomolecul', 'nanoparticle', 'oligonucleotide',
        'aptamer', 'molecular assay', 'recombinant protein', 'biosimilar',
        'cell-free', 'synthetic biology platform', 'molecular tool',
    ],
    2: [  # Celular — fermentation, bioprocesses, cell culture
        'fermentation', 'bioreactor', 'cell culture', 'precision fermentation',
        'bioprocess', 'cell therapy', 'biopharma manufactur', 'culture medium',
        'microbial strain', 'yeast', 'fungal production', 'biologic manufactur',
        'ferment', 'biorefinery', 'microorganism', 'bioproduction',
        'microbial platform', 'solid-state ferment', 'submerged ferment',
        'downstream processing', 'upstream process', 'fed-batch', 'cell line',
        'microbiology', 'bacteria strain', 'microbial engineerin', 'biosynthesis',
        'microbial biosynthes', 'continuous culture', 'inoculant manufactur',
        'microalgae', 'algae production', 'bioreactor design', 'culture optimization',
        'bio-manufacturing', 'industrial biotechnology',
    ],
    3: [  # Organismo — individual patient, individual plant, animal
        'patient', 'clinical trial', 'clinical use', 'individual treatment',
        'human health', 'veterinary', 'animal health', 'livestock health',
        'personalized medicine', 'medical device', 'point-of-care', 'diagnostic device',
        'therapeutic ', 'drug candidate', 'healthcare', 'hospital', 'surgery',
        'wound care', 'dermatology', 'oncology', 'pediatric', 'geriatric',
        'per-plant', 'plant disease treatment', 'crop protection application',
        'foliar application', 'seed treatment', 'individual crop', 'per-animal',
        'companion animal', 'pet health', 'animal nutrition', 'poultry health',
        'aquaculture health', 'livestock management per',
    ],
    4: [  # Lote/Producto — food products, inputs as product, batch output
        'food product', 'food ingredient', 'alt protein', 'alternative protein',
        'plant-based', 'plant based', 'fermented food', 'functional food',
        'food tech', 'foodtech', 'culture medium product', 'growth medium',
        'fermentation medium', 'dairy alternative', 'alt meat', 'meat alternative',
        'food formulation', 'food production', 'food system',
        'consumer product', 'finished product', 'packaged food',
        'crop input product', 'bio-input', 'biopesticide product',
        'formulated bio', 'shelf-ready', 'end product', 'ready-to-use',
        'nutraceutical', 'supplement product', 'cosmetic ingredient',
        'food ingredient', 'probiotic product', 'prebiotic', 'food brand',
        'ingredient company', 'food company', 'protein ingredient',
        'ingredient platform', 'novel food', 'novel ingredient',
    ],
    5: [  # Campo/Sistema — farm, field, soil, irrigation, crop system
        'farm', 'field', 'crop management', 'irrigation', 'soil health', 'farmer',
        'precision agriculture', 'agronomic', 'agroecosystem', 'pest management',
        'harvest', 'field monitoring', 'crop monitoring', 'farming',
        'smallholder', 'grain', 'soybean', 'corn ', 'wheat ', 'sugar cane', 'coffee',
        'citrus', 'cotton', 'agribusiness', 'agtech', 'precision farming',
        'field data', 'farm management', 'crop disease', 'soil nutrient',
        'crop stress', 'water use efficiency', 'agricultural production',
        'field-level', 'plot management', 'land management', 'crop yield',
        'agro-input management', 'agronomist', 'agronomy platform',
        'farm operation', 'supply chain agriculture', 'rural credit',
        'agricultural finance', 'smallholder farmer',
    ],
    6: [  # Paisaje/Planeta — ecosystems, carbon, satellites, global
        'ecosystem', 'landscape', 'carbon credit', 'deforestation', 'satellite imager',
        'biodiversity', 'climate change', 'planetary', 'global supply chain',
        'reforestation', 'forest monitoring', 'conservation', 'ocean', 'watershed management',
        'territorial', 'carbon market', 'nature-based', 'carbon offset',
        'carbon sequestration', 'remote sensing', 'earth observation', 'satellite data',
        'geospatial', 'ecosystem service', 'habitat', 'wildlife', 'forestry',
        'mangrove', 'cerrado', 'amazon', 'deforest', 'carbon stock',
        'nature tech', 'environmental monitoring', 'climate risk', 'net zero',
        'scope 3', 'land use change', 'resilient landscape', 'planetary boundary',
        'global food system', 'biome', 'global carbon', 'environmental intelligence',
    ],
}

# tech_codes → scale bonus points
SCALE_TC = {
    1: {'synbio', 'nanotech', 'genomics', 'bioinformatics', 'computational_bio'},
    2: {'biomanufacturing', 'fermentation', 'microbial'},
    3: {'therapeutics', 'diagnostics', 'medical_devices'},
    4: {'formulation'},                                   # formulated product
    5: {'ag_inputs', 'iot', 'plant_breeding', 'water_tech'},
    6: {'carbon_tech', 'remote_sensing'},
}

# scale_tags → level
TAG_MAP = {
    'molecular-scale':    1,
    'industrial-scale':   2,   # bioreactor / manufacturing context
    'human-scale':        3,
    'product-scale':      4,
    'agroecosystem-scale':5,
    'territorial-scale':  6,
    'planetary-scale':    6,
}

# ── mparadigm — bio/digital ratio ────────────────────────────────────────────
BIO_CODES    = {'therapeutics', 'microbial', 'biomaterials', 'fermentation', 'synbio',
                'nanotech', 'ag_inputs', 'formulation', 'plant_breeding', 'enzymatic',
                'green_chem', 'biomanufacturing'}
DIGITAL_CODES= {'ai_ml', 'iot', 'saas_marketplace', 'remote_sensing',
                 'blockchain', 'bioinformatics', 'computational_bio', 'robotics'}

BIO_KW = [
    'inoculant', 'biopesticide', 'bioplastic', 'enzyme product', 'biological agent',
    'biofertilizer', 'biostimulant', 'biocontrol agent', 'live bacteria', 'microbial product',
    'cell-based therapy', 'gene therapy', 'bio-based product', 'live microbial',
    'recombinant protein', 'biological formul', 'fermentation product', 'microbial formul',
    'biological material', 'biomaterial', 'biologic drug', 'natural product', 'plant extract',
    'active ingredient', 'biological input', 'cell therapy product', 'biosimilar product',
    'develops biologic', 'manufactur biolog', 'produce biopest', 'develop strain',
    'strain-based', 'organism-based', 'biology-based',
]
DIGITAL_KW = [
    'data platform', 'saas', 'analytics platform', 'decision support tool',
    'digital platform', 'marketplace', 'management software', 'dashboard',
    'monitoring platform', 'intelligence platform', 'machine learning platform',
    'predictive model', 'traceability platform', 'software platform', 'digital solution',
    'cloud platform', 'mobile app', 'web platform', 'digital marketplace',
    'b2b platform', 'algorithm', 'automation software', 'api platform',
    'data-driven', 'recommendation engine', 'workflow automation', 'data insights',
    'erp', 'crm', 'fintech', 'agrifintech', 'intelligence software',
]

# ── helpers ──────────────────────────────────────────────────────────────────
def parse_tc(s):
    if not s:
        return []
    try:
        return json.loads(s)
    except Exception:
        return [x.strip().strip('"\'') for x in s.strip('[]').split(',') if x.strip()]

def parse_tags(s):
    return [t.strip().lower() for t in (s or '').split(';') if t.strip()]

def build_text(*fields):
    return ' '.join(str(f).lower() for f in fields if f)

def classify_scale(text, tcs, tags_raw):
    scores = {i: 0 for i in range(1, 7)}
    hits   = []

    for lvl, kws in SCALE_KW.items():
        for kw in kws:
            if kw in text:
                scores[lvl] += 3
                hits.append((kw, lvl))

    for lvl, codes in SCALE_TC.items():
        for c in codes:
            if c in tcs:
                scores[lvl] += 2

    tags = parse_tags(tags_raw)
    has_agro     = 'agroecosystem-scale' in tags
    has_industrial = 'industrial-scale'  in tags
    for tag in tags:
        if tag in TAG_MAP:
            scores[TAG_MAP[tag]] += 2
    if has_agro and has_industrial:
        scores[5] += 1   # prefer operating environment over manufacturing context

    ordered = sorted(scores.items(), key=lambda x: -x[1])
    top, tscore = ordered[0]
    second       = ordered[1][1]

    if tscore == 0:
        return 3, "low", scores, []          # default: Organismo (middle)
    elif tscore > 2 * second:
        conf = "high"
    elif tscore > second:
        conf = "medium"
    else:
        conf = "low"

    top_hits = [kw for kw, lvl in hits if lvl == top][:5]
    return top, conf, scores, top_hits

def classify_paradigm(text, tcs):
    bio_c  = sum(2 for c in tcs if c in BIO_CODES)
    dig_c  = sum(2 for c in tcs if c in DIGITAL_CODES)
    bio_t  = sum(1 for kw in BIO_KW     if kw in text)
    dig_t  = sum(1 for kw in DIGITAL_KW if kw in text)

    bio = bio_c + bio_t
    dig = dig_c + dig_t
    total = bio + dig

    if total == 0:
        return 2.0          # unknown → center hybrid
    ratio = bio / total     # 1.0 = pure bio, 0.0 = pure digital
    # map ratio [0,1] → paradigm score [3.0, 1.0]
    return round(3.0 - ratio * 2.0, 2)

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT e.entity_id AS startup_id, e.canonical_name,
               sx.bio_theme_primary AS bio_theme,
               sx.business_one_liner AS one_liner,
               sx.startup_summary_en, sx.startup_summary_v1,
               sx.macro_theme, sx.emergent_theme,
               sx.cluster_label, sx.sub_cluster_label,
               sx.scale_tags, sx.tech_codes,
               sx.umap_x, sx.umap_y,
               sx.scatter_x, sx.scatter_y
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
        ORDER BY e.canonical_name
    """).fetchall()
    conn.close()

    results = []
    excluded = []

    for row in rows:
        tcs  = parse_tc(row['tech_codes'])

        # Primary text: one_liner + summaries (rich signal)
        primary = build_text(row['one_liner'], row['startup_summary_en'], row['startup_summary_v1'])
        # Secondary text: cluster/theme metadata (weaker signal, used as fallback)
        secondary = build_text(row['macro_theme'], row['emergent_theme'],
                               row['cluster_label'], row['sub_cluster_label'])
        has_primary = bool(primary.strip())

        # Startups with NO primary text AND empty tech_codes → data-poor, exclude
        if not has_primary and not tcs:
            excluded.append({
                'startup_id':    row['startup_id'],
                'canonical_name': row['canonical_name'],
                'bio_theme':     row['bio_theme'] or '',
                'reason':        'no_description_no_techcodes',
            })
            continue

        # Use primary if available, fall back to secondary
        text = primary if has_primary else secondary
        data_source = 'primary' if has_primary else 'cluster_metadata'

        mscale, conf, scores, top_kws = classify_scale(text, tcs, row['scale_tags'])
        mparadigm = classify_paradigm(text, tcs)

        # Downgrade confidence if using only cluster metadata
        if data_source == 'cluster_metadata' and conf == 'high':
            conf = 'medium'

        results.append({
            'startup_id':    row['startup_id'],
            'canonical_name': row['canonical_name'],
            'bio_theme':     row['bio_theme'] or '',
            'mscale':        mscale,
            'mscale_name':   SCALE_NAMES[mscale],
            'mscale_x':      SCALE_X[mscale],
            'mparadigm':     mparadigm,
            'confidence':    conf,
            'data_source':   data_source,
            'mscale_scores': str(scores),
            'top_keywords':  '; '.join(top_kws),
            'one_liner':     (row['one_liner'] or '')[:120],
        })

    # ── write CSV ─────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    FIELDS = ['startup_id', 'canonical_name', 'bio_theme',
              'mscale', 'mscale_name', 'mscale_x',
              'mparadigm', 'confidence', 'data_source',
              'mscale_scores', 'top_keywords', 'one_liner']
    with open(OUT_PATH, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(results)

    # ── console report ────────────────────────────────────────────────────────
    sc = Counter(r['mscale']    for r in results)
    cc = Counter(r['confidence'] for r in results)
    ds = Counter(r['data_source'] for r in results)

    print(f"\n{'─'*62}")
    print(f"  PARADIGM CLASSIFICATION — {len(results)} startups classified, {len(excluded)} excluded")
    print(f"{'─'*62}")

    print(f"\n  MSCALE — Escala de la Materia (6 niveles)")
    for lvl in range(1, 7):
        n   = sc.get(lvl, 0)
        bar = '█' * (n // 5) + f' {n}'
        print(f"    {lvl}  {SCALE_NAMES[lvl]:<18}  {bar}")

    # Paradigm histogram (buckets: 1.0-1.5, 1.5-2.0, 2.0-2.5, 2.5-3.0+)
    print(f"\n  MPARADIGM — Paradigma Tecnológico (gradiente 1.0→3.0)")
    buckets = [(1.0, 1.5, "Bio-Material     "),
               (1.5, 2.0, "Bio-Mat/Dig lean "),
               (2.0, 2.5, "Bio-Digital      "),
               (2.5, 3.1, "Digital-Comp     ")]
    for lo, hi, label in buckets:
        n = sum(1 for r in results if lo <= r['mparadigm'] < hi)
        bar = '█' * (n // 5) + f' {n}'
        print(f"    {label}  {bar}")

    print(f"\n  Confidence:  high={cc.get('high',0)}  medium={cc.get('medium',0)}  low={cc.get('low',0)}")
    print(f"  Data source: primary={ds.get('primary',0)}  cluster_metadata={ds.get('cluster_metadata',0)}")
    print(f"  Excluded (data-poor): {len(excluded)}")

    # Samples per level
    by_s = {}
    for r in results:
        by_s.setdefault(r['mscale'], []).append(r)

    print(f"\n  {'─'*62}")
    print("  SAMPLES PER MSCALE LEVEL")
    print(f"  {'─'*62}")
    for lvl in range(1, 7):
        samples = by_s.get(lvl, [])
        hi = [r for r in samples if r['confidence']=='high'][:3]
        lo = [r for r in samples if r['confidence']=='low'][:1]
        print(f"\n  {lvl} {SCALE_NAMES[lvl]} ({len(samples)} startups)")
        for r in (hi + lo):
            flag = '*' if r['confidence']=='low' else ' '
            print(f"    {flag} [{r['bio_theme'][:22]:<22}] {r['canonical_name']:<30} {r['one_liner'][:55]}")

    # Low-confidence sample
    low = [r for r in results if r['confidence'] == 'low']
    print(f"\n  {'─'*62}")
    print(f"  LOW CONFIDENCE ({len(low)}) — sample")
    print(f"  {'─'*62}")
    for r in low[:20]:
        print(f"  {r['canonical_name']:<30} scale={r['mscale']} par={r['mparadigm']}  {r['one_liner'][:55]}")
        print(f"    scores={r['mscale_scores']}")

    print(f"\n  CSV: {OUT_PATH}\n")


if __name__ == "__main__":
    main()
