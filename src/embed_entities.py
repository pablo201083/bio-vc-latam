"""
src/embed_entities.py — Genera embeddings semánticos para entidades no-startup.

Lee canonical/manual_entity_profiles.csv, genera embeddings con
multilingual-e5-small y guarda:
  embeddings/entity_vectors.npy        (N × 384, float32, row-normalized)
  embeddings/entity_vectors_meta.json  {ids, names, types, countries, themes, ...}

Uso:
  python pipeline.py embed-entities
  # o directo:
  python src/embed_entities.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT      = Path(__file__).resolve().parent.parent
CSV_PATH  = ROOT / "canonical" / "manual_entity_profiles.csv"
OUT_NPY   = ROOT / "embeddings" / "entity_vectors.npy"
OUT_META  = ROOT / "embeddings" / "entity_vectors_meta.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def build_passage(row: dict) -> str:
    """Build a rich embedding text from an entity profile row."""
    parts = [
        f"passage: {row['canonical_name']}.",
        row.get("description_en", "").strip(),
    ]
    # Add bio themes for better thematic recall
    themes = row.get("bio_themes", "").replace(";", ", ")
    if themes:
        parts.append(f"Themes: {themes}.")
    # Add demand/service signals
    signals = row.get("demand_signals", "").replace(";", ", ").replace("_", " ")
    if signals:
        parts.append(f"Activities: {signals}.")
    # Add country/geography
    country = row.get("latam_presence", "")
    if country:
        parts.append(f"Geography: {country}.")
    return " ".join(p for p in parts if p and p != "passage: .")


def run():
    print("[embed_entities] Loading multilingual-e5-small…", flush=True)
    import os
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")

    # Read entity profiles
    if not CSV_PATH.exists():
        print(f"[embed_entities] ERROR: {CSV_PATH} not found", flush=True)
        sys.exit(1)

    entities = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entities.append(row)

    print(f"[embed_entities] {len(entities)} entities to embed", flush=True)

    # Build passages
    passages = [build_passage(e) for e in entities]

    # Encode
    vecs = model.encode(
        passages,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
        batch_size=16,
    ).astype(np.float32)

    # Save vectors
    OUT_NPY.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUT_NPY, vecs)
    print(f"[embed_entities] Saved {OUT_NPY.name} — shape {vecs.shape}", flush=True)

    # Save metadata
    meta = {
        "ids":       [e["entity_id"]        for e in entities],
        "names":     [e["canonical_name"]    for e in entities],
        "types":     [e["entity_type"]       for e in entities],
        "countries": [e["country_code"]      for e in entities],
        "themes":    [e.get("bio_themes","") for e in entities],
        "demand":    [e.get("demand_signals","") for e in entities],
        "presence":  [e.get("latam_presence","") for e in entities],
        "websites":  [e.get("website","")    for e in entities],
        "passages":  passages,
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[embed_entities] Saved {OUT_META.name}", flush=True)
    print(f"[embed_entities] Done. {len(entities)} entity vectors ready.", flush=True)


if __name__ == "__main__":
    run()
