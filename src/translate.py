"""
src/translate.py — Normalize startup summaries to English.

Detects non-English summaries and translates them via Claude claude-haiku-4-5.
Stores the result in startup_summary_en (new column).
English summaries are copied as-is.

The embeddings pipeline uses startup_summary_en as primary text so that UMAP
clusters by semantic content, not by language.

Usage:
    python pipeline.py translate            # translate only missing/new
    python pipeline.py translate --force    # retranslate everything
"""
from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"

# ──────────────────────────────────────────────────────────────────────────────
# Language detection — simple heuristic, good enough for ES/PT vs EN
# ──────────────────────────────────────────────────────────────────────────────

_ES_PT = re.compile(
    r"\b(que|desarrolla|para\b|empresa|startup de|del\b|los\b|las\b|sus\b|"
    r"produce|utiliza|combina|ofrece|busca|permite|mediante|través|"
    r"desenvolve|empresa brasileira|focada|soluções|tecnologia|"
    r"producción|produccion|diagnóstico|diagnostico|herramientas|"
    r"plataforma de|soluciones de|aplicaciones|compañía|compania)\b",
    re.I,
)
_EN = re.compile(
    r"\b(develops?|developing|company|platform|solutions|technology|"
    r"based|using|focused|provides?|enables?|startup that|leverages?|"
    r"builds?|offers?|creates?)\b",
    re.I,
)


def _is_english(text: str) -> bool:
    if not text:
        return True
    es_hits = len(_ES_PT.findall(text))
    en_hits = len(_EN.findall(text))
    return en_hits >= es_hits


# ──────────────────────────────────────────────────────────────────────────────
# DB helpers
# ──────────────────────────────────────────────────────────────────────────────

def _ensure_column(conn: sqlite3.Connection) -> None:
    """Add startup_summary_en column if it doesn't exist yet."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(startup_extended)").fetchall()}
    if "startup_summary_en" not in cols:
        conn.execute("ALTER TABLE startup_extended ADD COLUMN startup_summary_en TEXT")
        conn.commit()
        print("  [translate] Added column startup_summary_en")


def _load_rows(conn: sqlite3.Connection, force: bool) -> list[dict]:
    """Load startups that need translation."""
    if force:
        where = "WHERE sx.scope_decision='include' AND sx.startup_summary_v1 IS NOT NULL AND sx.startup_summary_v1 != ''"
    else:
        where = ("WHERE sx.scope_decision='include' "
                 "AND sx.startup_summary_v1 IS NOT NULL AND sx.startup_summary_v1 != '' "
                 "AND (sx.startup_summary_en IS NULL OR sx.startup_summary_en = '')")

    rows = conn.execute(f"""
        SELECT sx.startup_id, e.canonical_name, sx.startup_summary_v1
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        {where}
        ORDER BY e.canonical_name
    """).fetchall()
    return [{"startup_id": r[0], "name": r[1], "summary": r[2]} for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# Translation via deep_translator (Google Translate, free, no API key needed)
# Falls back to Anthropic Claude if ANTHROPIC_API_KEY is set (higher quality)
# ──────────────────────────────────────────────────────────────────────────────

def _translate_one_google(text: str) -> str:
    """Translate a single text to English using Google Translate (free)."""
    from deep_translator import GoogleTranslator
    try:
        result = GoogleTranslator(source="auto", target="en").translate(text)
        return result or text
    except Exception:
        return text


def _translate_batch_google(items: list[dict]) -> list[str]:
    """Translate a batch via Google Translate. One request per item (free tier)."""
    results = []
    for item in items:
        results.append(_translate_one_google(item["summary"]))
        time.sleep(0.05)  # gentle rate limiting
    return results


def _translate_batch_claude(client, items: list[dict]) -> list[str]:
    """Translate a batch using Claude claude-haiku-4-5 (higher quality, needs API key)."""
    system = (
        "You are a precise scientific translator specializing in biotech. "
        "Translate startup descriptions from Spanish or Portuguese to English. "
        "Preserve all technical terms. Output ONLY the translated text."
    )
    numbered = "\n".join(f"{i+1}. {item['summary']}" for i, item in enumerate(items))
    prompt = (
        "Translate each numbered description to English. "
        "Output ONLY the translations, one per line, numbered to match.\n\n"
        + numbered
    )
    msg = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()

    results: list[str] = []
    current: list[str] = []
    for line in raw.split("\n"):
        m = re.match(r"^(\d+)\.\s*(.*)", line)
        if m:
            if current:
                results.append(" ".join(current).strip())
            current = [m.group(2)] if m.group(2) else []
        elif line.strip() and current is not None:
            current.append(line.strip())
    if current:
        results.append(" ".join(current).strip())

    while len(results) < len(items):
        results.append(items[len(results)]["summary"])
    return results[: len(items)]


# ──────────────────────────────────────────────────────────────────────────────
# Main run()
# ──────────────────────────────────────────────────────────────────────────────

def run(db_path: Path = DB_PATH, force: bool = False, batch_size: int = 20) -> dict:
    import os

    conn = sqlite3.connect(db_path)
    _ensure_column(conn)

    all_rows = _load_rows(conn, force=force)
    if not all_rows:
        print("  [translate] Nothing to translate — all summaries already have EN version.")
        conn.close()
        return {"copied": 0, "translated": 0, "total": 0}

    print(f"  [translate] {len(all_rows)} summaries to process...")

    # Choose backend
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        import anthropic
        claude_client = anthropic.Anthropic(api_key=api_key)
        backend = "claude-haiku-4-5"
    else:
        claude_client = None
        backend = "google-translate (free)"
    print(f"  [translate] Backend: {backend}")

    # Split into: already English (copy) vs needs translation
    english_rows = [r for r in all_rows if _is_english(r["summary"])]
    foreign_rows = [r for r in all_rows if not _is_english(r["summary"])]

    print(f"  [translate] English (copy): {len(english_rows)}  |  Translate: {len(foreign_rows)}")

    # ── Copy English summaries ────────────────────────────────────────────────
    copied = 0
    for r in english_rows:
        conn.execute(
            "UPDATE startup_extended SET startup_summary_en=? WHERE startup_id=?",
            (r["summary"], r["startup_id"]),
        )
        copied += 1
    conn.commit()
    print(f"  [translate] {copied} English summaries copied.")

    # ── Translate foreign summaries in batches ────────────────────────────────
    translated = 0
    errors = 0
    batches = [foreign_rows[i : i + batch_size] for i in range(0, len(foreign_rows), batch_size)]

    for b_idx, batch in enumerate(batches):
        print(f"  [translate] Batch {b_idx+1}/{len(batches)}  ({len(batch)} items)...", end=" ", flush=True)
        try:
            if claude_client:
                results = _translate_batch_claude(claude_client, batch)
                time.sleep(0.3)
            else:
                results = _translate_batch_google(batch)

            for item, en_text in zip(batch, results):
                conn.execute(
                    "UPDATE startup_extended SET startup_summary_en=? WHERE startup_id=?",
                    (en_text, item["startup_id"]),
                )
                translated += 1
            conn.commit()
            print(f"OK ({translated} done)")
        except Exception as e:
            print(f"ERROR: {e}")
            # Fallback: store original text so embeddings still work
            for item in batch:
                conn.execute(
                    "UPDATE startup_extended SET startup_summary_en=? WHERE startup_id=?",
                    (item["summary"], item["startup_id"]),
                )
            conn.commit()
            errors += len(batch)

    conn.close()

    print(f"\n  [translate] Done: {copied} copied, {translated} translated, {errors} errors")
    return {"copied": copied, "translated": translated, "errors": errors,
            "total": copied + translated + errors}
