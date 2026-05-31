"""
src/enrich_periphery.py — enriquece campos semánticos de startups con señal débil.

Para cada startup sin business_one_liner (y/o emergent_theme/technology_tags),
usa Claude haiku para generar los campos faltantes desde el summary existente.
Luego actualiza startup_extended con audit_log e invalida el embedding cache
para que el próximo run de embeddings re-vectorice solo esas N startups.

Uso:
    python -m src.enrich_periphery               # dry-run (imprime propuestas)
    python -m src.enrich_periphery --apply       # aplica a DB
    python -m src.enrich_periphery --apply --id rnatech-ar  # solo una
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "db" / "bio_latam.db"

PROMPT_TEMPLATE = """You are a biotech/agtech analyst. Given a startup description, generate three concise fields:

Startup: {name} ({country})
Summary: {summary}
Macro theme: {macro}

Generate exactly this JSON (no markdown, no explanation):
{{
  "business_one_liner": "<one sentence, max 120 chars, what they do and for whom>",
  "emergent_theme": "<2-4 words: the specific niche/sub-trend, e.g. 'precision fermentation' or 'nature-based MRV'>",
  "technology_tags": "<comma-separated, 3-5 core technologies, e.g. 'machine learning, IoT sensors, remote sensing'>"
}}"""


def fetch_weak_startups(conn: sqlite3.Connection, startup_id: str | None = None) -> list[dict]:
    cur = conn.cursor()
    where = "sx.scope_decision = 'include' AND (sx.business_one_liner IS NULL OR length(sx.business_one_liner) < 10)"
    params: list = []
    if startup_id:
        where += " AND sx.startup_id = ?"
        params.append(startup_id)
    cur.execute(f"""
        SELECT sx.startup_id, e.canonical_name, e.country_code,
               coalesce(sx.startup_summary_en, sx.startup_summary_v1, '') as summary,
               sx.business_one_liner, sx.emergent_theme, sx.technology_tags,
               sx.macro_theme, sx.cluster_id, sx.cluster_confidence
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE {where}
        ORDER BY sx.cluster_confidence
    """, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def enrich_with_claude(startup: dict) -> dict:
    """Call Claude haiku to generate missing semantic fields."""
    import anthropic
    client = anthropic.Anthropic()
    prompt = PROMPT_TEMPLATE.format(
        name=startup["canonical_name"],
        country=startup["country_code"] or "?",
        summary=startup["summary"][:400],
        macro=startup["macro_theme"] or "biotech",
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
        text = text.rstrip("`").strip()
    return json.loads(text)


def apply_enrichment(
    conn: sqlite3.Connection,
    startup_id: str,
    fields: dict,
    reason: str = "LLM enrichment: generated missing semantic fields from summary",
) -> None:
    cur = conn.cursor()
    now = datetime.datetime.now(datetime.UTC).isoformat()
    updatable = {k: v for k, v in fields.items() if v and k in
                 ("business_one_liner", "emergent_theme", "technology_tags")}
    if not updatable:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updatable)
    values = list(updatable.values()) + [startup_id]
    cur.execute(f"UPDATE startup_extended SET {set_clause} WHERE startup_id = ?", values)

    for field, new_val in updatable.items():
        cur.execute("""
            INSERT INTO audit_log (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, "llm:haiku", startup_id, "startup_extended", field, None, new_val, reason))

    conn.commit()


def invalidate_embedding_cache(startup_ids: list[str]) -> None:
    """
    The embedding cache uses a hash of the embed text per startup.
    Since we changed fields, the hash will differ → automatic cache miss.
    No manual action needed; just informing the user.
    """
    print(f"\n  Cache note: {len(startup_ids)} startup(s) will be re-embedded on next run")
    print("  Run: python pipeline.py rebuild --phase embeddings")


def run(apply: bool = False, startup_id: str | None = None) -> None:
    conn = sqlite3.connect(DB_PATH)
    startups = fetch_weak_startups(conn, startup_id)

    if not startups:
        print("No startups with weak signal found.")
        conn.close()
        return

    print(f"\n=== Enriquecimiento semántico — {len(startups)} startups ===")
    if not apply:
        print("  (dry-run — pasar --apply para escribir a DB)\n")

    enriched_ids = []
    errors = []

    for s in startups:
        sid = s["startup_id"]
        name = s["canonical_name"]
        print(f"\n[CL{s['cluster_id']} conf={s['cluster_confidence']:.2f}] {name} ({s['country_code']})")
        print(f"  summary: {s['summary'][:100]}...")

        try:
            fields = enrich_with_claude(s)
            print(f"  one_liner  : {fields.get('business_one_liner', '')}")
            print(f"  emergent   : {fields.get('emergent_theme', '')}")
            print(f"  tech_tags  : {fields.get('technology_tags', '')}")

            if apply:
                apply_enrichment(conn, sid, fields)
                print(f"  -> APPLIED to DB")
                enriched_ids.append(sid)
            else:
                enriched_ids.append(sid)

        except Exception as e:
            print(f"  ERROR: {e}")
            errors.append(sid)

    print(f"\n=== Resumen ===")
    print(f"  Procesados: {len(startups)}")
    print(f"  OK: {len(enriched_ids) - len(errors)}")
    print(f"  Errors: {len(errors)}")
    if errors:
        print(f"  Failed: {errors}")

    if enriched_ids:
        invalidate_embedding_cache(enriched_ids)

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Escribir cambios a DB (sin esto es dry-run)")
    parser.add_argument("--id", dest="startup_id", default=None, help="Enriquecer solo este startup_id")
    args = parser.parse_args()
    run(apply=args.apply, startup_id=args.startup_id)
