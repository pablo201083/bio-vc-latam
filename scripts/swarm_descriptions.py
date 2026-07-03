"""
scripts/swarm_descriptions.py — Genera descripciones funcionales para themes y clusters.

Para cada bio_theme (8) y cada cluster semántico (25), construye un prompt con las
top-N startups de mayor calidad y llama a Claude Sonnet para producir:
  - tagline: 1 oración de badge (≤15 palabras)
  - description: 2-3 oraciones funcionales (qué hace el grupo, qué los une)
  - boundary: frontera con el cluster/theme más confundible (1 oración)

Output: pilot/theme-cluster-descriptions.js (consumido por startup-themes.html)

Uso:
    python scripts/swarm_descriptions.py              # genera todo
    python scripts/swarm_descriptions.py --dry-run    # imprime prompts sin llamar API
    python scripts/swarm_descriptions.py --only themes   # solo los 8 themes
    python scripts/swarm_descriptions.py --only clusters # solo los 25 clusters
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import pathlib
import re
import sqlite3
import sys
from textwrap import dedent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

DB_PATH = ROOT / "db" / "bio_latam.db"
OUT_JS   = ROOT / "pilot" / "theme-cluster-descriptions.js"

WORKERS = 8

# ── Adjacency map for boundary hints ─────────────────────────────────────────
THEME_ADJACENCY = {
    "Diagnostics & Devices":               "Therapeutics",
    "Therapeutics":                        "Diagnostics & Devices",
    "Food Systems & Alt Proteins":         "Biomaterials & Green Chemistry",
    "Bioinputs & Crop Resilience":         "Precision Agriculture",
    "Biomaterials & Green Chemistry":      "Food Systems & Alt Proteins",
    "Precision Agriculture":               "Bioinputs & Crop Resilience",
    "Nature & Ecosystem Tech":             "Precision Agriculture",
    "Biomanufacturing & Platform Technologies": "Biomaterials & Green Chemistry",
}

# ── Prompts ───────────────────────────────────────────────────────────────────
THEME_PROMPT = dedent("""\
    You are writing investor-facing taxonomy copy for BIO VC LATAM, a venture fund \
    covering the bioeconomy of Latin America. You have deep expertise in biotech, \
    agtech, and climate tech.

    Below are the {n} highest-quality startups in the bio theme "{theme}".
    Each line: startup name (country) — one-liner.

    {startup_list}

    Write a JSON object with exactly these three keys (no markdown, no extra keys):
    {{
      "tagline": "<one punchy sentence, ≤15 words, what this theme DOES — not a label>",
      "description": "<2–3 sentences. What functional output do these companies share? What biological or technical mechanism unites them? Who is the end customer or market?>",
      "boundary": "<1 sentence starting with 'Not to be confused with {adjacent}:' explaining the key differentiator>"
    }}

    Rules:
    - Write in English.
    - Be concrete about biology/technology — avoid "innovative", "solutions", "platform" without context.
    - The tagline should work as a standalone badge (e.g. "Biological inputs that replace synthetic agrochemicals in crop systems").
    - Do NOT mention the theme name itself in the tagline or description.
    - Output only valid JSON, nothing else.
""")

CLUSTER_PROMPT = dedent("""\
    You are writing investor-facing taxonomy copy for BIO VC LATAM, a venture fund \
    covering the bioeconomy of Latin America. You have deep expertise in biotech, \
    agtech, and climate tech.

    Below are the {n} highest-quality startups in the sub-cluster "{cluster}" \
    (which belongs to the broader theme "{theme}").
    Each line: startup name (country) — one-liner.

    {startup_list}

    Write a JSON object with exactly these three keys (no markdown, no extra keys):
    {{
      "tagline": "<one punchy sentence, ≤15 words, what this cluster DOES>",
      "description": "<2–3 sentences. What specific technology, mechanism or market niche unites these startups within the theme? What makes this a coherent sub-group?>",
      "boundary": "<1 sentence explaining what you would NOT put in this cluster vs the rest of {theme}>"
    }}

    Rules:
    - Write in English.
    - Be concrete about biology/technology — avoid "innovative", "solutions" without context.
    - Output only valid JSON, nothing else.
""")


# ── DB queries ────────────────────────────────────────────────────────────────
def load_themes(conn: sqlite3.Connection) -> list[dict]:
    """Returns list of {theme, startups: [{name, country, one_liner}]}."""
    cur = conn.execute("""
        SELECT e.canonical_name, e.country_code, sx.bio_theme_primary,
               COALESCE(sx.business_one_liner, sx.startup_summary_en, '') AS one_liner,
               COALESCE(sx.computed_quality_score, sx.data_quality_score, 0) AS qs
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
          AND sx.bio_theme_primary IS NOT NULL
          AND (sx.business_one_liner IS NOT NULL OR sx.startup_summary_en IS NOT NULL)
        ORDER BY sx.bio_theme_primary, qs DESC
    """)
    rows = cur.fetchall()

    from collections import defaultdict
    by_theme: dict[str, list] = defaultdict(list)
    for name, country, theme, one_liner, qs in rows:
        by_theme[theme].append({"name": name, "country": country, "one_liner": one_liner})

    result = []
    for theme, startups in sorted(by_theme.items()):
        result.append({"theme": theme, "startups": startups[:10]})
    return result


def load_clusters(conn: sqlite3.Connection) -> list[dict]:
    """Returns list of {cluster_label, theme, startups}."""
    cur = conn.execute("""
        SELECT e.canonical_name, e.country_code, sx.bio_theme_primary,
               sx.sub_cluster_label,
               COALESCE(sx.business_one_liner, sx.startup_summary_en, '') AS one_liner,
               COALESCE(sx.computed_quality_score, sx.data_quality_score, 0) AS qs
        FROM startup_extended sx
        JOIN entities e ON e.entity_id = sx.startup_id
        WHERE sx.scope_decision = 'include'
          AND sx.sub_cluster_label IS NOT NULL
          AND sx.sub_cluster_label != ''
          AND sx.sub_cluster_label != sx.bio_theme_primary
          AND (sx.business_one_liner IS NOT NULL OR sx.startup_summary_en IS NOT NULL)
        ORDER BY sx.sub_cluster_label, qs DESC
    """)
    rows = cur.fetchall()

    from collections import defaultdict
    by_cluster: dict[str, dict] = defaultdict(lambda: {"theme": "", "startups": []})
    for name, country, theme, cluster, one_liner, qs in rows:
        by_cluster[cluster]["theme"] = theme
        by_cluster[cluster]["startups"].append({"name": name, "country": country, "one_liner": one_liner})

    # Filter clusters with at least 3 startups (exclude singletons)
    result = []
    for cluster, data in sorted(by_cluster.items()):
        if len(data["startups"]) >= 3:
            result.append({
                "cluster": cluster,
                "theme": data["theme"],
                "startups": data["startups"][:8],
            })
    return result


# ── API call ──────────────────────────────────────────────────────────────────
def build_startup_list(startups: list[dict]) -> str:
    lines = []
    for s in startups:
        liner = (s["one_liner"] or "").strip()[:120]
        lines.append(f"- {s['name']} ({s['country']}) — {liner}")
    return "\n".join(lines)


def extract_json(text: str) -> dict | None:
    """Extract first JSON object from model output."""
    m = re.search(r'\{[\s\S]*\}', text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


async def call_model(client, prompt: str, label: str, dry_run: bool) -> dict | None:
    if dry_run:
        print(f"\n=== DRY RUN: {label} ===")
        print(prompt[:400], "\n...")
        return {"tagline": "[DRY]", "description": "[DRY]", "boundary": "[DRY]"}

    try:
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        parsed = extract_json(text)
        if parsed is None:
            print(f"  WARN: could not parse JSON for {label}", file=sys.stderr)
            print(f"  Raw: {text[:200]}", file=sys.stderr)
            return None
        return parsed
    except Exception as exc:
        print(f"  ERROR {label}: {exc}", file=sys.stderr)
        return None


# ── Async runners ─────────────────────────────────────────────────────────────
async def run_themes(client, themes: list[dict], dry_run: bool) -> dict[str, dict]:
    sem = asyncio.Semaphore(WORKERS)
    results: dict[str, dict] = {}

    async def process(t):
        prompt = THEME_PROMPT.format(
            n=len(t["startups"]),
            theme=t["theme"],
            startup_list=build_startup_list(t["startups"]),
            adjacent=THEME_ADJACENCY.get(t["theme"], "adjacent themes"),
        )
        async with sem:
            result = await call_model(client, prompt, f"THEME:{t['theme']}", dry_run)
        if result:
            results[t["theme"]] = result
            if not dry_run:
                print(f"  ✓ theme: {t['theme']}")

    await asyncio.gather(*[process(t) for t in themes])
    return results


async def run_clusters(client, clusters: list[dict], dry_run: bool) -> dict[str, dict]:
    sem = asyncio.Semaphore(WORKERS)
    results: dict[str, dict] = {}

    async def process(c):
        prompt = CLUSTER_PROMPT.format(
            n=len(c["startups"]),
            cluster=c["cluster"],
            theme=c["theme"],
            startup_list=build_startup_list(c["startups"]),
        )
        async with sem:
            result = await call_model(client, prompt, f"CLUSTER:{c['cluster']}", dry_run)
        if result:
            results[c["cluster"]] = result
            if not dry_run:
                print(f"  ✓ cluster: {c['cluster']}")

    await asyncio.gather(*[process(c) for c in clusters])
    return results


# ── Main ──────────────────────────────────────────────────────────────────────
async def main(only: str | None, dry_run: bool):
    import anthropic
    if not dry_run:
        from _swarm_auth import ensure_api_key
        ensure_api_key()

    conn = sqlite3.connect(DB_PATH)
    client = anthropic.AsyncAnthropic()

    theme_descs: dict[str, dict] = {}
    cluster_descs: dict[str, dict] = {}

    if only != "clusters":
        themes = load_themes(conn)
        print(f"Generando descripciones para {len(themes)} themes...")
        theme_descs = await run_themes(client, themes, dry_run)

    if only != "themes":
        clusters = load_clusters(conn)
        print(f"Generando descripciones para {len(clusters)} clusters (n≥3)...")
        cluster_descs = await run_clusters(client, clusters, dry_run)

    # ── Write output ──────────────────────────────────────────────────────────
    payload = {
        "generated_at": datetime.datetime.now().isoformat(),
        "model": "claude-haiku-4-5-20251001",
        "theme_descriptions": theme_descs,
        "cluster_descriptions": cluster_descs,
    }

    js = "window.THEME_CLUSTER_DESCRIPTIONS = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    OUT_JS.write_text(js, encoding="utf-8")

    print(f"\n✓ Escrito → {OUT_JS}")
    print(f"  {len(theme_descs)} themes, {len(cluster_descs)} clusters")

    if dry_run:
        print("\n[dry-run — no se llamó a la API]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Swarm de descripciones theme+cluster")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", choices=["themes", "clusters"], default=None)
    args = parser.parse_args()
    asyncio.run(main(args.only, args.dry_run))
