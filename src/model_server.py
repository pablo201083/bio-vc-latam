"""
src/model_server.py — Servidor persistente del modelo semántico.

Carga multilingual-e5-small UNA SOLA VEZ al arrancar y lo mantiene en memoria.
Consultas en ~150ms en vez de 5-10s por carga repetida del modelo.

Puerto 4174 (localhost).  server.js lo levanta automáticamente.

Endpoints:
  GET  /health   → {"status":"ready","vectors":487,"ms":0}
  POST /query    → {"query":"...","top_k":20,"filters":{}} → [{rank,score,...}]
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import numpy as np

ROOT              = Path(__file__).resolve().parent.parent
VECTORS_PATH      = ROOT / "embeddings" / "startup_vectors.npy"
META_PATH         = ROOT / "embeddings" / "startup_vectors_meta.json"
ENTITY_VECS_PATH  = ROOT / "embeddings" / "entity_vectors.npy"
ENTITY_META_PATH  = ROOT / "embeddings" / "entity_vectors_meta.json"
DB_PATH           = ROOT / "db" / "bio_latam.db"
PORT              = 4174

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── One-time startup: load everything ────────────────────────────────────────
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

print("[model_server] Cargando multilingual-e5-small…", flush=True)
t0 = time.time()

from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
_vecs  = np.load(VECTORS_PATH).astype(np.float32)   # [N, 384], row-normalized
_meta  = json.loads(META_PATH.read_text(encoding="utf-8"))
_ids   = _meta["ids"]                                # list[str]

# Entity vectors (orgs, ESOs, corporates)
_entity_vecs: np.ndarray | None = None
_entity_meta: dict = {}
if ENTITY_VECS_PATH.exists() and ENTITY_META_PATH.exists():
    _entity_vecs = np.load(ENTITY_VECS_PATH).astype(np.float32)
    _entity_meta = json.loads(ENTITY_META_PATH.read_text(encoding="utf-8"))
    print(f"[model_server] {len(_entity_meta.get('ids', []))} entity vectors loaded.", flush=True)

# Startup metadata for result enrichment
_conn  = sqlite3.connect(DB_PATH)
_rows  = _conn.execute("""
    SELECT e.entity_id, e.canonical_name, e.country_code,
           sx.bio_theme_primary, sx.data_quality_score,
           sx.funding_stage, sx.business_one_liner
    FROM entities e
    JOIN startup_extended sx ON sx.startup_id = e.entity_id
    WHERE sx.scope_decision = 'include' AND e.status != 'excluded'
""").fetchall()
_funded = set(
    r[0] for r in _conn.execute(
        "SELECT DISTINCT startup_id FROM investment_edges"
    ).fetchall()
)
_conn.close()

_startup_meta: dict[str, dict] = {
    r[0]: {
        "name":     r[1],
        "country":  (r[2] or "").upper(),
        "theme":    r[3] or "",
        "quality":  round(float(r[4] or 0), 1),
        "stage":    r[5] or "",
        "one_liner": r[6] or "",
        "funded":   r[0] in _funded,
    }
    for r in _rows
}

_elapsed = round(time.time() - t0, 1)
print(
    f"[model_server] Listo en {_elapsed}s. "
    f"{len(_ids)} vectores · {len(_startup_meta)} startups. "
    f"Escuchando en puerto {PORT}.",
    flush=True,
)


# ── Score rescaling (same logic as intelligence.py) ──────────────────────────

def _rescale(candidates: list[dict]) -> list[dict]:
    if len(candidates) <= 1:
        return candidates
    scores = [c["score"] for c in candidates]
    s_min, s_max = min(scores), max(scores)
    rng = s_max - s_min
    if rng < 1e-6:
        n = len(candidates)
        for i, c in enumerate(candidates):
            c["score_raw"] = c["score"]
            c["score"] = round(0.95 - 0.85 * i / max(n - 1, 1), 3)
        return candidates
    for c in candidates:
        c["score_raw"] = round(c["score"], 4)
        norm = (c["score"] - s_min) / rng
        c["score"] = round(0.10 + 0.85 * (norm ** 0.7), 3)
    return candidates


# ── HTTP handler ──────────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):

    # ── CORS ──
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "http://127.0.0.1:4173")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── Health ──
    def do_GET(self):
        if self.path.rstrip("/") == "/health":
            entity_count = len(_entity_meta.get("ids", [])) if _entity_vecs is not None else 0
            self._json(200, {
                "status":   "ready",
                "vectors":  len(_ids),
                "entities": entity_count,
            })
        else:
            self._json(404, {"error": "not found"})

    # ── Query ──
    def do_POST(self):
        if self.path.rstrip("/") != "/query":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length).decode("utf-8"))
            query  = (body.get("query") or "").strip()
            top_k  = min(int(body.get("top_k", 20)), 100)
            filt   = body.get("filters") or {}

            if not query:
                self._json(400, {"error": "missing query"})
                return

            t1    = time.time()
            q_vec = _model.encode(
                [f"query: {query}"],
                normalize_embeddings=True,
                convert_to_numpy=True,
            )[0].astype(np.float32)

            # ── Startup search ────────────────────────────────────────────────
            scores = _vecs @ q_vec   # [N,384] @ [384] → [N]

            raw: list[dict] = []
            for i, sid in enumerate(_ids):
                if sid not in _startup_meta:
                    continue
                st = _startup_meta[sid]
                # Optional filters
                if filt.get("country") and filt["country"].upper() != st["country"]:
                    continue
                if filt.get("theme") and filt["theme"].lower() not in st["theme"].lower():
                    continue
                if filt.get("stage") and filt["stage"] != st["stage"]:
                    continue
                raw.append({
                    "rank":        0,
                    "score":       float(scores[i]),
                    "score_raw":   float(scores[i]),
                    "id":          sid,
                    "entity_type": "startup",
                    **st,
                })

            raw.sort(key=lambda x: -x["score"])
            pool    = _rescale(raw[: top_k * 4])
            results = pool[:top_k]
            for i, r in enumerate(results):
                r["rank"] = i + 1

            # ── Entity search (orgs, ESOs, corporates) ────────────────────────
            entity_results: list[dict] = []
            if _entity_vecs is not None and len(_entity_meta.get("ids", [])) > 0:
                e_scores = _entity_vecs @ q_vec   # [M,384] @ [384] → [M]
                e_ids      = _entity_meta["ids"]
                e_names    = _entity_meta["names"]
                e_types    = _entity_meta["types"]
                e_countries= _entity_meta["countries"]
                e_themes   = _entity_meta["themes"]
                e_demand   = _entity_meta.get("demand", [""] * len(e_ids))
                e_presence = _entity_meta.get("presence", [""] * len(e_ids))
                e_websites = _entity_meta.get("websites", [""] * len(e_ids))

                e_raw: list[dict] = []
                for i, eid in enumerate(e_ids):
                    # Apply country filter to entities too
                    if filt.get("country") and filt["country"].upper() != e_countries[i].upper():
                        continue
                    e_raw.append({
                        "rank":        0,
                        "score":       float(e_scores[i]),
                        "score_raw":   float(e_scores[i]),
                        "id":          eid,
                        "name":        e_names[i],
                        "entity_type": e_types[i],
                        "country":     e_countries[i].upper(),
                        "theme":       e_themes[i],
                        "one_liner":   e_demand[i].replace(";", " | ").replace("_", " "),
                        "quality":     8.0,   # entities always high-quality
                        "stage":       "",
                        "funded":      True,
                        "website":     e_websites[i],
                        "latam_presence": e_presence[i],
                    })

                e_raw.sort(key=lambda x: -x["score"])
                # Rescale entity scores independently
                entity_results = _rescale(e_raw[:top_k])
                for i, r in enumerate(entity_results):
                    r["rank"] = i + 1

            ms = round((time.time() - t1) * 1000)
            self._json(200, {
                "results":  results,
                "entities": entity_results,
                "ms":       ms,
                "query":    query,
            })

        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def _json(self, status: int, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # suppress per-request logs


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), _Handler)
    server.serve_forever()
