"""
src/orphan_triage.py — Frente B: tipificar las entidades startup huérfanas.

Una entidad huérfana = entity_type='startup' con aristas de inversión pero SIN
fila en startup_extended. Entraron por barridos de portfolio y nunca se
procesaron (scope, tema, summary). Son 62 y contaminan los counts: cada una es
indistinguible entre "duplicado contando doble", "fuera de scope" y "bio
legítima sin procesar".

Este módulo NO decide scope (eso es editorial, del curador). Tipifica con
evidencia para que la decisión sea barata:

- probable_duplicate : normalize_key colisiona con una startup ya procesada
                       (p.ej. syocin_bio ↔ syocin-biotech). Candidato a merge.
- likely_out_of_scope: el nombre matchea señales no-bio conocidas (exchanges,
                       hardware genérico, fintech). Candidato a exclude.
- needs_processing   : bio aparentemente legítima sin procesar — entra a la cola
                       de enriquecimiento (scope + tema + summary).

Salida: quality/orphan_entities_triage.csv
No modifica la DB: el merge seguro se hace con `merge-duplicate-entities`, el
scope lo decide el curador sobre este CSV.

Uso:
    python pipeline.py orphan-triage
"""
from __future__ import annotations

import pathlib
import re
import sqlite3
from collections import Counter

from src.utils import normalize_key, write_csv

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Señales de nombre que sugieren fuera del universo BIO LATAM. Solo heurística
# para priorizar revisión — NO excluye automáticamente.
OUT_OF_SCOPE_HINTS = {
    "bitmex": "exchange de criptomonedas",
    "formlabs": "impresoras 3D (hardware genérico, US)",
    "opentrons": "robótica de laboratorio (hardware, US)",
    "ngc partners": "vehículo de inversión, no startup",
    "peek": "posible app de viajes/genérica — verificar",
}


def _best_duplicate(conn: sqlite3.Connection, orphan_id: str, name: str,
                    extended_keys: dict[str, str]) -> str | None:
    """Busca una startup ya procesada cuyo normalize_key colisione."""
    for cand in {normalize_key(orphan_id), normalize_key(name)}:
        if not cand:
            continue
        hit = extended_keys.get(cand)
        if hit and hit != orphan_id:
            return hit
    return None


def run(db_path: pathlib.Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Índice de claves normalizadas → startup_id ya procesado.
    extended_keys: dict[str, str] = {}
    for r in conn.execute(
        "SELECT sx.startup_id, e.canonical_name FROM startup_extended sx "
        "JOIN entities e ON e.entity_id = sx.startup_id"
    ):
        extended_keys[normalize_key(r["startup_id"])] = r["startup_id"]
        if r["canonical_name"]:
            extended_keys.setdefault(normalize_key(r["canonical_name"]), r["startup_id"])

    orphans = conn.execute(
        """
        SELECT e.entity_id, e.canonical_name, e.country_code, e.status
        FROM entities e
        WHERE e.entity_type = 'startup'
          AND NOT EXISTS (SELECT 1 FROM startup_extended sx WHERE sx.startup_id = e.entity_id)
        ORDER BY e.canonical_name
        """
    ).fetchall()

    triage: list[dict] = []
    for o in orphans:
        eid, name = o["entity_id"], o["canonical_name"] or ""
        n_edges = conn.execute(
            "SELECT count(*) FROM investment_edges WHERE startup_id=?", (eid,)
        ).fetchone()[0]
        investors = [r[0] for r in conn.execute(
            "SELECT DISTINCT investor_id FROM investment_edges WHERE startup_id=? LIMIT 4", (eid,)
        ).fetchall()]

        dup = _best_duplicate(conn, eid, name, extended_keys)
        name_l = name.lower().strip()
        scope_hint = next((reason for k, reason in OUT_OF_SCOPE_HINTS.items()
                           if k in name_l or k in eid.lower()), None)

        if dup:
            disposition = "probable_duplicate"
            action = f"Verificar y mergear edges hacia '{dup}' (mismo normalize_key)."
        elif scope_hint:
            disposition = "likely_out_of_scope"
            action = f"Revisar exclude: {scope_hint}."
        else:
            disposition = "needs_processing"
            action = "Procesar: scope_decision + bio_theme + summary (cola de enriquecimiento)."

        triage.append({
            "entity_id": eid,
            "name": name,
            "country_code": o["country_code"] or "",
            "n_investment_edges": n_edges,
            "sample_investors": "; ".join(investors),
            "duplicate_of": dup or "",
            "disposition": disposition,
            "suggested_action": action,
        })

    triage.sort(key=lambda t: (t["disposition"], -t["n_investment_edges"]))
    write_csv(ROOT / "quality" / "orphan_entities_triage.csv", triage,
              ["entity_id", "name", "country_code", "n_investment_edges",
               "sample_investors", "duplicate_of", "disposition", "suggested_action"])

    conn.close()
    counts = Counter(t["disposition"] for t in triage)
    return {
        "total_orphans": len(triage),
        "by_disposition": dict(counts),
        "probable_duplicates": [t for t in triage if t["disposition"] == "probable_duplicate"],
    }
