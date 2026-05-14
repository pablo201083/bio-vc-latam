"""
src/embeddings.py — vectorización semántica de startups con cache.

Usa sentence-transformers con modelo multilingual (español + inglés) para vectorizar
las startups include. El texto a embedder combina las 3 señales del dominio:

    text = startup_summary_v1 + business_one_liner + technical_stack
           + industry_destination + bio_lens_tags + domain_tags
           + technology_tags + scale_tags

Esto le da al embedding peso dominante al "qué hace / qué significa" (summary +
one-liner) pero también incorpora tecnologías e industria, así el clustering
captura "significado completo".

Modelo: intfloat/multilingual-e5-small (118 MB, 384 dim, multilingual ES+EN+PT).
La primera corrida descarga el modelo (~120 MB) y deja caché en
~/.cache/huggingface. Las siguientes corridas son instantáneas.

Cache de embeddings en embeddings/startup_vectors.npy + .json (metadatos):
sólo se recomputa si el texto fuente cambió desde la última corrida.

Uso:
    python -m src.embeddings              # genera/actualiza cache
    python -m src.embeddings --force      # ignora cache
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sqlite3
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "db" / "bio_latam.db"
CACHE_DIR = ROOT / "embeddings"
VECTORS_PATH = CACHE_DIR / "startup_vectors.npy"
META_PATH = CACHE_DIR / "startup_vectors_meta.json"

MODEL_NAME = "intfloat/multilingual-e5-small"
DIM = 384


def make_embed_text(row: dict) -> str:
    """Combina los campos del row en un texto para embedding.

    Usa startup_summary_en (inglés normalizado) como señal primaria.
    Cae back a startup_summary_v1 si no hay versión EN todavía.
    Repite el summary para darle más peso (los modelos tipo e5 son sensibles
    a la frecuencia de tokens). El prefijo 'passage:' es la convención de e5
    para indicar que es un documento (no una query).
    """
    # Prefer the English-normalized summary; fall back to original
    summary = (row.get("startup_summary_en") or row.get("startup_summary_v1") or "").strip()
    parts = [
        summary,
        summary,  # double weight on summary
        row.get("business_one_liner") or "",
        row.get("macro_theme") or "",
        row.get("emergent_theme") or "",
        row.get("technical_stack") or "",
        row.get("technology_tags") or "",
        row.get("industry_destination") or "",
        row.get("domain_tags") or "",
        row.get("bio_lens_tags") or "",
        row.get("scale_tags") or "",
    ]
    body = " | ".join(p.strip() for p in parts if p and p.strip())
    return f"passage: {body}"


def fetch_startups(conn: sqlite3.Connection) -> list[dict]:
    """Carga las startups include con todos los campos para embedding."""
    cur = conn.cursor()
    cur.execute(
        """SELECT sx.startup_id,
                  sx.startup_summary_en, sx.startup_summary_v1,
                  sx.business_one_liner,
                  sx.macro_theme, sx.emergent_theme,
                  sx.technical_stack, sx.technology_tags,
                  sx.industry_destination, sx.domain_tags,
                  sx.bio_lens_tags, sx.scale_tags,
                  e.canonical_name, e.country_code
           FROM startup_extended sx
           JOIN entities e ON e.entity_id = sx.startup_id
           WHERE sx.scope_decision = 'include'
           ORDER BY sx.startup_id"""
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_cache() -> tuple[np.ndarray | None, dict | None]:
    if not VECTORS_PATH.exists() or not META_PATH.exists():
        return None, None
    try:
        vectors = np.load(VECTORS_PATH)
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        return vectors, meta
    except Exception:
        return None, None


def save_cache(vectors: np.ndarray, meta: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(VECTORS_PATH, vectors)
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def run(force: bool = False, db_path: pathlib.Path = DB_PATH) -> dict:
    """Genera/actualiza el cache de embeddings."""
    t0 = time.time()
    print(f"\n=== Embeddings con {MODEL_NAME} ===")

    conn = sqlite3.connect(db_path)
    startups = fetch_startups(conn)
    print(f"  Startups include: {len(startups)}")

    # Construir textos
    texts: list[str] = []
    ids: list[str] = []
    hashes: list[str] = []
    for s in startups:
        text = make_embed_text(s)
        texts.append(text)
        ids.append(s["startup_id"])
        hashes.append(content_hash(text))

    # Si hay cache y no se forzó, ver si todos los hashes coinciden
    cached_vectors, cached_meta = load_cache()
    if not force and cached_vectors is not None and cached_meta is not None:
        cached_ids = cached_meta.get("ids", [])
        cached_hashes = cached_meta.get("hashes", [])
        if cached_ids == ids and cached_hashes == hashes:
            print(f"  Cache hit completo. {len(ids)} vectores reutilizados.")
            return {"vectors": cached_vectors, "ids": ids, "model": MODEL_NAME,
                    "cached": True, "elapsed": time.time() - t0}

    # Cargar el modelo (descarga la primera vez)
    print("  Cargando modelo (puede descargar ~120 MB la primera vez)...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)

    print("  Vectorizando...")
    vectors = model.encode(
        texts,
        batch_size=8,
        show_progress_bar=True,
        normalize_embeddings=True,  # importante para cosine
        convert_to_numpy=True,
    ).astype(np.float32)

    meta = {
        "model": MODEL_NAME,
        "dim": int(vectors.shape[1]),
        "count": int(vectors.shape[0]),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ids": ids,
        "hashes": hashes,
    }
    save_cache(vectors, meta)
    print(f"  Vectores: {vectors.shape}, guardados en {VECTORS_PATH.relative_to(ROOT)}")

    elapsed = time.time() - t0
    print(f"\n[OK] Embeddings done in {elapsed:.1f}s")
    return {"vectors": vectors, "ids": ids, "model": MODEL_NAME,
            "cached": False, "elapsed": elapsed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Ignorar cache y re-vectorizar todo")
    args = parser.parse_args()
    run(force=args.force)
