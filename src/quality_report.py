"""
src/quality_report.py — Genera pilot/quality-tracker.html

Uso:
    python pipeline.py quality-report
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path


# ──────────────────────────────────────────────
# Data collection
# ──────────────────────────────────────────────

DISCOVERY_TARGETS = {"BR": 200, "AR": 150, "CL": 70, "MX": 50, "CO": 20, "UY": 10}

COMPLETENESS_FIELDS = [
    ("website",            "Website"),
    ("founded_year",       "Founded yr"),
    ("bio_theme_primary",  "Bio theme"),
    ("startup_summary_v1", "Summary"),
    ("tech_codes",         "Tech codes"),
]

VALIDATION_CHECKS = [
    ("Includes missing bio_theme_primary",
     "SELECT count(*) FROM startup_extended WHERE scope_decision='include' AND (bio_theme_primary IS NULL OR bio_theme_primary='')",
     "error"),
    ("Includes missing summary",
     "SELECT count(*) FROM startup_extended WHERE scope_decision='include' AND (startup_summary_v1 IS NULL OR startup_summary_v1='')",
     "warn"),
    ("Includes missing country_code",
     "SELECT count(*) FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id WHERE sx.scope_decision='include' AND (e.country_code IS NULL OR e.country_code='')",
     "warn"),
    ("Investment edges — investor not found",
     "SELECT count(*) FROM investment_edges ie WHERE NOT EXISTS (SELECT 1 FROM entities e WHERE e.entity_id=ie.investor_id)",
     "error"),
    ("Investment edges — startup not found",
     "SELECT count(*) FROM investment_edges ie WHERE NOT EXISTS (SELECT 1 FROM entities e WHERE e.entity_id=ie.startup_id)",
     "error"),
    ("Outcomes missing source_url",
     "SELECT count(*) FROM outcomes WHERE source_url IS NULL OR source_url=''",
     "error"),
    ("Includes missing tech_codes and industry_codes",
     "SELECT count(*) FROM startup_extended WHERE scope_decision='include' AND (tech_codes IS NULL OR tech_codes='[]' OR tech_codes='') AND (industry_codes IS NULL OR industry_codes='[]' OR industry_codes='')",
     "warn"),
    ("Orphan entities (no startup_extended row)",
     "SELECT count(*) FROM entities WHERE entity_type='startup' AND NOT EXISTS (SELECT 1 FROM startup_extended sx WHERE sx.startup_id=entity_id)",
     "info"),
]


def _pct(n: int, total: int) -> int:
    return round(100 * n / total) if total else 0


def collect_metrics(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)
    m: dict = {}

    # ── Census ──────────────────────────────────
    m["entity_types"] = dict(
        conn.execute("SELECT entity_type, count(*) FROM entities GROUP BY entity_type").fetchall()
    )
    m["scope_dist"] = dict(
        conn.execute("SELECT scope_decision, count(*) FROM startup_extended GROUP BY scope_decision").fetchall()
    )
    m["basis_dist"] = dict(
        conn.execute(
            "SELECT scope_basis, count(*) FROM startup_extended WHERE scope_decision='include' GROUP BY scope_basis"
        ).fetchall()
    )
    m["edges_total"]       = conn.execute("SELECT count(*) FROM investment_edges").fetchone()[0]
    m["edges_with_stage"]  = conn.execute("SELECT count(*) FROM investment_edges WHERE round_stage IS NOT NULL").fetchone()[0]
    m["edges_with_amount"] = conn.execute("SELECT count(*) FROM investment_edges WHERE amount IS NOT NULL").fetchone()[0]
    m["outcomes_total"]    = conn.execute("SELECT count(*) FROM outcomes").fetchone()[0]
    m["audit_total"]       = conn.execute("SELECT count(*) FROM audit_log").fetchone()[0]
    m["orphans"]           = conn.execute(
        "SELECT count(*) FROM entities WHERE entity_type='startup' AND NOT EXISTS "
        "(SELECT 1 FROM startup_extended sx WHERE sx.startup_id=entity_id)"
    ).fetchone()[0]

    total_includes = m["scope_dist"].get("include", 0)
    m["total_includes"] = total_includes

    # ── Startups by country (includes) ──────────
    m["by_country"] = dict(
        conn.execute(
            "SELECT e.country_code, count(*) FROM entities e "
            "JOIN startup_extended sx ON e.entity_id=sx.startup_id "
            "WHERE sx.scope_decision='include' AND e.country_code IS NOT NULL "
            "GROUP BY e.country_code ORDER BY count(*) DESC"
        ).fetchall()
    )

    # ── Auto-discovery by country ────────────────
    rows = conn.execute(
        "SELECT e.country_code, sx.scope_decision, count(*) "
        "FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id "
        "WHERE sx.scope_basis='auto_discovery' "
        "GROUP BY e.country_code, sx.scope_decision"
    ).fetchall()
    disc: dict = {}
    for cc, dec, n in rows:
        if cc not in disc:
            disc[cc] = {"include": 0, "review": 0}
        disc[cc][dec] = disc[cc].get(dec, 0) + n
    m["discovery"] = disc

    # ── Completeness matrix ──────────────────────
    countries = [cc for cc, n in m["by_country"].items() if n >= 3]
    completeness: dict = {}
    for cc in countries:
        total = m["by_country"].get(cc, 0)
        if not total:
            continue
        row: dict = {"total": total}
        for field_key, _ in COMPLETENESS_FIELDS:
            if field_key == "website":
                n = conn.execute(
                    "SELECT count(*) FROM startup_extended sx "
                    "JOIN entities e ON e.entity_id=sx.startup_id "
                    "WHERE sx.scope_decision='include' AND e.country_code=? "
                    "AND e.website IS NOT NULL AND e.website!=''", (cc,)
                ).fetchone()[0]
            elif field_key == "founded_year":
                n = conn.execute(
                    "SELECT count(*) FROM startup_extended sx "
                    "JOIN entities e ON e.entity_id=sx.startup_id "
                    "WHERE sx.scope_decision='include' AND e.country_code=? "
                    "AND e.founded_year IS NOT NULL", (cc,)
                ).fetchone()[0]
            elif field_key == "tech_codes":
                n = conn.execute(
                    "SELECT count(*) FROM startup_extended sx "
                    "JOIN entities e ON e.entity_id=sx.startup_id "
                    "WHERE sx.scope_decision='include' AND e.country_code=? "
                    "AND sx.tech_codes IS NOT NULL AND sx.tech_codes!='' AND sx.tech_codes!='[]'", (cc,)
                ).fetchone()[0]
            else:
                n = conn.execute(
                    f"SELECT count(*) FROM startup_extended sx "
                    f"JOIN entities e ON e.entity_id=sx.startup_id "
                    f"WHERE sx.scope_decision='include' AND e.country_code=? "
                    f"AND sx.{field_key} IS NOT NULL AND sx.{field_key}!=''", (cc,)
                ).fetchone()[0]
            row[field_key] = _pct(n, total)
        completeness[cc] = row
    m["completeness"] = completeness

    # ── Overall completeness score ───────────────
    if total_includes:
        scores = []
        for field_key, _ in COMPLETENESS_FIELDS:
            if field_key == "website":
                n = conn.execute(
                    "SELECT count(*) FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id "
                    "WHERE sx.scope_decision='include' AND e.website IS NOT NULL AND e.website!=''"
                ).fetchone()[0]
            elif field_key == "founded_year":
                n = conn.execute(
                    "SELECT count(*) FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id "
                    "WHERE sx.scope_decision='include' AND e.founded_year IS NOT NULL"
                ).fetchone()[0]
            elif field_key == "tech_codes":
                n = conn.execute(
                    "SELECT count(*) FROM startup_extended WHERE scope_decision='include' "
                    "AND tech_codes IS NOT NULL AND tech_codes!='' AND tech_codes!='[]'"
                ).fetchone()[0]
            else:
                n = conn.execute(
                    f"SELECT count(*) FROM startup_extended WHERE scope_decision='include' "
                    f"AND {field_key} IS NOT NULL AND {field_key}!=''"
                ).fetchone()[0]
            scores.append(_pct(n, total_includes))
        m["overall_completeness"] = round(sum(scores) / len(scores))
    else:
        m["overall_completeness"] = 0

    # ── Bio theme distribution ───────────────────
    m["themes"] = [
        {"label": t, "n": n}
        for t, n in conn.execute(
            "SELECT bio_theme_primary, count(*) FROM startup_extended "
            "WHERE scope_decision='include' AND bio_theme_primary IS NOT NULL AND bio_theme_primary!='' "
            "GROUP BY bio_theme_primary ORDER BY count(*) DESC"
        ).fetchall()
    ]

    # ── Bio universe stats ────────────────────────
    m["bio_core"]     = conn.execute(
        "SELECT count(*) FROM startup_extended WHERE scope_decision='include' AND is_bio_universe=1"
    ).fetchone()[0]
    m["eco_adjacent"] = conn.execute(
        "SELECT count(*) FROM startup_extended WHERE scope_decision='include' AND is_bio_universe=0"
    ).fetchone()[0]
    m["bio_unclassified"] = conn.execute(
        "SELECT count(*) FROM startup_extended WHERE scope_decision='include' AND is_bio_universe IS NULL"
    ).fetchone()[0]

    # ── Secondary theme coverage ──────────────────
    m["has_secondary"] = conn.execute(
        "SELECT count(*) FROM startup_extended WHERE scope_decision='include' "
        "AND bio_theme_secondary IS NOT NULL AND bio_theme_secondary!=''"
    ).fetchone()[0]

    # ── Founded year distribution ────────────────
    m["year_dist"] = [
        {"year": y, "n": n}
        for y, n in conn.execute(
            "SELECT e.founded_year, count(*) FROM entities e "
            "JOIN startup_extended sx ON e.entity_id=sx.startup_id "
            "WHERE sx.scope_decision='include' AND e.founded_year BETWEEN 2000 AND 2025 "
            "GROUP BY e.founded_year ORDER BY e.founded_year"
        ).fetchall()
    ]

    # ── Validation checks ────────────────────────
    validation = []
    errors = warnings = 0
    for desc, query, level in VALIDATION_CHECKS:
        try:
            n = conn.execute(query).fetchone()[0]
        except Exception as e:
            n = -1
        ok = n == 0
        validation.append({"desc": desc, "n": n, "level": level, "ok": ok})
        if not ok:
            if level == "error":
                errors += 1
            elif level == "warn":
                warnings += 1
    m["validation"] = validation
    m["val_errors"] = errors
    m["val_warnings"] = warnings

    # ── Recent audit feed ────────────────────────
    m["recent_audit"] = [
        {
            "ts": row[0],
            "actor": row[1],
            "entity_id": row[2],
            "table": row[3],
            "field": row[4],
            "old": row[5],
            "new": row[6],
            "reason": row[7],
        }
        for row in conn.execute(
            "SELECT timestamp, actor, entity_id, table_name, field, old_value, new_value, reason "
            "FROM audit_log ORDER BY timestamp DESC LIMIT 30"
        ).fetchall()
    ]

    # ── Scope basis labels ────────────────────────
    m["basis_labels"] = {
        "external_auditable_source": "External auditable source",
        "internal_structured_inference": "Structured inference",
        "auto_discovery": "Auto-discovery",
        "manual_curator": "Manual curator",
    }

    # ── Discovery targets ─────────────────────────
    m["discovery_targets"] = DISCOVERY_TARGETS

    # ── Generated at ─────────────────────────────
    m["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn.close()
    return m


# ──────────────────────────────────────────────
# HTML generation
# ──────────────────────────────────────────────

def _color_for_pct(p: int) -> str:
    if p >= 80:
        return "#16a34a"   # green
    if p >= 50:
        return "#d97706"   # amber
    return "#dc2626"        # red


def _bg_for_pct(p: int) -> str:
    if p >= 80:
        return "#f0fdf4"
    if p >= 50:
        return "#fffbeb"
    return "#fef2f2"


def generate_html(m: dict) -> str:
    # ── Helper for completeness cell ─────────────
    def cell(p: int) -> str:
        color = _color_for_pct(p)
        bg = _bg_for_pct(p)
        bar = round(p * 0.38)  # max 38px wide
        return (
            f'<td style="background:{bg};color:{color};font-weight:700;'
            f'font-size:0.85rem;text-align:center;padding:8px 4px;">'
            f'{p}%</td>'
        )

    # ── Completeness matrix HTML ──────────────────
    field_labels = [lbl for _, lbl in COMPLETENESS_FIELDS]
    field_keys   = [k   for k, _ in COMPLETENESS_FIELDS]
    countries_sorted = sorted(m["completeness"].keys(),
                              key=lambda cc: m["completeness"][cc]["total"], reverse=True)

    matrix_rows = ""
    for cc in countries_sorted:
        row = m["completeness"][cc]
        total = row["total"]
        cells = "".join(cell(row.get(k, 0)) for k in field_keys)
        matrix_rows += (
            f"<tr>"
            f'<td style="font-weight:700;padding:8px 12px;">{cc}</td>'
            f'<td style="color:#64748b;font-size:0.85rem;padding:8px 6px;text-align:right;">{total}</td>'
            f"{cells}"
            f"</tr>\n"
        )

    header_cells = "".join(
        f'<th style="padding:8px 4px;font-size:0.8rem;color:#64748b;font-weight:600;">{lbl}</th>'
        for lbl in field_labels
    )
    completeness_table = f"""
    <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
      <thead>
        <tr>
          <th style="text-align:left;padding:8px 12px;font-size:0.8rem;color:#64748b;">Country</th>
          <th style="text-align:right;padding:8px 6px;font-size:0.8rem;color:#64748b;">N</th>
          {header_cells}
        </tr>
      </thead>
      <tbody>{matrix_rows}</tbody>
    </table>
    """

    # ── Validation checks HTML ────────────────────
    def val_icon(item: dict) -> str:
        if item["ok"]:
            return '<span style="color:#16a34a;font-size:1.1rem;">✓</span>'
        icons = {"error": '<span style="color:#dc2626;font-size:1.1rem;">✗</span>',
                 "warn":  '<span style="color:#d97706;font-size:1.1rem;">⚠</span>',
                 "info":  '<span style="color:#3b82f6;font-size:1.1rem;">ℹ</span>'}
        return icons.get(item["level"], "?")

    val_rows = ""
    for v in m["validation"]:
        icon = val_icon(v)
        count_txt = "OK" if v["ok"] else str(v["n"])
        count_color = "#16a34a" if v["ok"] else (
            "#dc2626" if v["level"] == "error" else
            "#d97706" if v["level"] == "warn" else "#3b82f6"
        )
        val_rows += f"""
        <div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f1e9de;">
          {icon}
          <span style="flex:1;font-size:0.9rem;">{v['desc']}</span>
          <span style="font-weight:700;color:{count_color};font-size:0.9rem;">{count_txt}</span>
        </div>"""

    # ── Discovery progress HTML ───────────────────
    disc_rows = ""
    for cc, target in sorted(DISCOVERY_TARGETS.items()):
        actual = m["by_country"].get(cc, 0)
        pct = min(round(100 * actual / target), 100) if target else 0
        color = _color_for_pct(pct)
        disc_rows += f"""
        <div class="bar-row">
          <div class="bar-head">
            <span style="font-weight:700;">{cc}</span>
            <span>{actual} / {target} <span style="color:{color};font-weight:700;">{pct}%</span></span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct}%;background:{color};"></div>
          </div>
        </div>"""

    # ── Recent audit HTML ─────────────────────────
    def short(s, n=40):
        if not s:
            return "—"
        return s[:n] + "…" if len(str(s)) > n else str(s)

    audit_rows = ""
    for a in m["recent_audit"][:20]:
        ts = a["ts"][:16] if a["ts"] else "—"
        actor = a["actor"] or "—"
        actor_short = actor.replace("pipeline:", "").replace("curator:", "")
        audit_rows += f"""
        <div style="display:grid;grid-template-columns:90px 1fr auto;gap:8px;align-items:start;
                    padding:9px 0;border-bottom:1px solid #f1e9de;font-size:0.84rem;">
          <span style="color:#94a3b8;">{ts}</span>
          <span>
            <strong style="font-size:0.82rem;color:#475569;">{short(a['entity_id'],24)}</strong>
            <span style="color:#64748b;"> · {a['field'] or '—'}</span>
            <span style="display:block;color:#94a3b8;font-size:0.79rem;">{short(a['reason'],55)}</span>
          </span>
          <span style="background:#f1e9de;border-radius:6px;padding:2px 7px;
                       font-size:0.76rem;white-space:nowrap;">{actor_short}</span>
        </div>"""

    # ── Scope distribution bars ───────────────────
    scope_bars = ""
    scope_colors = {"include": "#16a34a", "review": "#d97706", "exclude": "#dc2626", "triage": "#3b82f6"}
    total_scope = sum(m["scope_dist"].values())
    for dec, n in sorted(m["scope_dist"].items(), key=lambda x: -x[1]):
        pct = _pct(n, total_scope)
        color = scope_colors.get(dec, "#94a3b8")
        scope_bars += f"""
        <div class="bar-row">
          <div class="bar-head">
            <span style="font-weight:600;text-transform:capitalize;">{dec}</span>
            <span>{n} <span style="color:#94a3b8;">({pct}%)</span></span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct}%;background:{color};"></div>
          </div>
        </div>"""

    # ── Basis distribution bars ───────────────────
    basis_bars = ""
    total_basis = sum(m["basis_dist"].values()) or 1
    basis_colors = {
        "external_auditable_source": "#14b8a6",
        "auto_discovery": "#8b5cf6",
        "internal_structured_inference": "#f97316",
        "manual_curator": "#3b82f6",
    }
    for basis, n in sorted(m["basis_dist"].items(), key=lambda x: -x[1]):
        pct = _pct(n, total_basis)
        label = m["basis_labels"].get(basis, basis)
        color = basis_colors.get(basis, "#94a3b8")
        basis_bars += f"""
        <div class="bar-row">
          <div class="bar-head">
            <span style="font-size:0.87rem;">{label}</span>
            <span>{n} <span style="color:#94a3b8;">({pct}%)</span></span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct}%;background:{color};"></div>
          </div>
        </div>"""

    # ── Chart.js data for themes ──────────────────
    theme_labels = json.dumps([t["label"] for t in m["themes"][:12]])
    theme_data   = json.dumps([t["n"]     for t in m["themes"][:12]])

    year_labels  = json.dumps([str(y["year"]) for y in m["year_dist"]])
    year_data    = json.dumps([y["n"] for y in m["year_dist"]])

    # ── Census numbers ────────────────────────────
    total_entities    = sum(m["entity_types"].values())
    total_startups    = m["entity_types"].get("startup", 0)
    total_investors   = m["entity_types"].get("investor", 0)
    total_includes    = m["total_includes"]
    total_auto        = sum(
        v.get("include", 0) for v in m["discovery"].values()
    )
    completeness_pct  = m["overall_completeness"]
    val_status        = "No errors" if m["val_errors"] == 0 else f"{m['val_errors']} errors"
    val_color         = "#16a34a" if m["val_errors"] == 0 else "#dc2626"
    bio_core_pct      = _pct(m["bio_core"], total_includes) if total_includes else 0

    # ── Final HTML ────────────────────────────────
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ecosystem Quality Tracker — BIO LATAM</title>
  <link rel="stylesheet" href="./styles.css?v=20260513">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
  <style>
    /* ── Layout ── */
    .tracker-grid {{
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      gap: 20px;
    }}
    .tracker-sidebar, .tracker-main {{
      display: grid;
      gap: 20px;
      align-content: start;
    }}
    .census-strip {{
      display: grid;
      grid-template-columns: repeat(6, minmax(0,1fr));
      gap: 12px;
    }}
    .census-card {{
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 14px 16px;
      background: rgba(255,255,255,0.82);
      display: grid;
      gap: 4px;
    }}
    .census-card .c-num {{
      font-size: 2rem;
      font-weight: 800;
      letter-spacing: -0.05em;
      line-height: 1;
    }}
    .census-card .c-lbl {{
      color: var(--muted);
      font-size: 0.8rem;
      line-height: 1.3;
    }}
    .census-card .c-delta {{
      font-size: 0.78rem;
      color: #16a34a;
      font-weight: 600;
    }}
    /* ── Completeness matrix ── */
    .completeness-wrap {{
      overflow-x: auto;
    }}
    .completeness-wrap table tr:hover td {{
      filter: brightness(0.95);
    }}
    /* ── Discovery progress ── */
    .disc-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0,1fr));
      gap: 14px;
    }}
    .disc-card {{
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      background: rgba(255,255,255,0.78);
    }}
    /* ── Charts ── */
    .chart-twin {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0,1fr));
      gap: 20px;
    }}
    .chart-box {{
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
      background: rgba(255,255,255,0.78);
    }}
    .chart-box h3 {{
      font-size: 0.95rem;
      font-weight: 700;
      margin-bottom: 14px;
      color: #334155;
    }}
    /* ── Audit feed ── */
    .audit-feed {{
      max-height: 480px;
      overflow-y: auto;
    }}
    /* ── Readiness score card ── */
    .readiness-hero {{
      display: grid;
      grid-template-columns: 220px minmax(0,1fr);
      gap: 20px;
      align-items: stretch;
    }}
    .readiness-score {{
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 22px;
      background:
        radial-gradient(circle at 80% 10%, rgba(20,184,166,0.2), transparent 38%),
        linear-gradient(145deg, #fffaf2, #f4efe5);
      display: grid;
      align-content: center;
      gap: 8px;
    }}
    .score-num {{
      font-size: 4rem;
      font-weight: 800;
      letter-spacing: -0.07em;
      line-height: 0.95;
    }}
    /* ── Bar rows ── */
    .bar-row {{ display: grid; gap: 5px; }}
    .bar-head {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      font-size: 0.88rem;
    }}
    .bar-track {{
      width: 100%;
      height: 8px;
      border-radius: 999px;
      background: #eadfce;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 999px;
    }}
    .stack-list {{ display: grid; gap: 10px; }}
    @media (max-width: 1100px) {{
      .tracker-grid {{ grid-template-columns: 1fr; }}
      .census-strip {{ grid-template-columns: repeat(3, minmax(0,1fr)); }}
      .chart-twin {{ grid-template-columns: 1fr; }}
      .readiness-hero {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 640px) {{
      .census-strip {{ grid-template-columns: repeat(2, minmax(0,1fr)); }}
    }}
  </style>
</head>
<body>
<div class="page-shell">

  <!-- ── HEADER ── -->
  <header class="hero">
    <div class="hero-copy">
      <p class="eyebrow">Quality</p>
      <h1>Ecosystem Quality Tracker</h1>
      <p class="lede">DB health for BIO LATAM: completeness, validation, country coverage, discovery progress, and bio theme classification.</p>
    </div>
    <div class="hero-meta">
      <div class="meta-card">
        <span class="meta-label">Generated</span>
        <strong>{m["generated_at"]}</strong>
      </div>
      <div class="meta-card">
        <span class="meta-label">Includes</span>
        <strong>{total_includes} startups</strong>
      </div>
      <div class="meta-card">
        <span class="meta-label">Validation</span>
        <strong style="color:{val_color};">{val_status}</strong>
      </div>
      <div class="meta-card">
        <span class="meta-label">Navigation</span>
        <strong><a href="./index.html" style="color:inherit;">&#8592; Pilot</a></strong>
      </div>
    </div>
  </header>

  <!-- ── CENSUS STRIP ── -->
  <section class="census-strip">
    <div class="census-card">
      <span class="c-num">{total_includes}</span>
      <span class="c-lbl">Startups<br>Include</span>
    </div>
    <div class="census-card">
      <span class="c-num" style="color:#16a34a;">{m["bio_core"]}</span>
      <span class="c-lbl">Bio-core<br><span style="font-size:0.72rem;color:#94a3b8;">{bio_core_pct}% of includes</span></span>
    </div>
    <div class="census-card">
      <span class="c-num">{total_auto}</span>
      <span class="c-lbl">Auto-<br>discovery</span>
    </div>
    <div class="census-card">
      <span class="c-num">{m["scope_dist"].get("review", 0)}</span>
      <span class="c-lbl">In<br>review</span>
    </div>
    <div class="census-card">
      <span class="c-num">{m["edges_total"]}</span>
      <span class="c-lbl">Investment<br>edges</span>
    </div>
    <div class="census-card">
      <span class="c-num">{total_investors}</span>
      <span class="c-lbl">Capital<br>actors</span>
    </div>
  </section>

  <!-- ── READINESS + DISCOVERY ── -->
  <section class="readiness-hero">
    <div class="readiness-score">
      <span class="eyebrow">Completeness</span>
      <strong class="score-num">{completeness_pct}%</strong>
      <span style="color:var(--muted);font-size:0.86rem;line-height:1.45;">
        Average completeness across key fields (website, founding year, bio theme, summary, tech codes) for all includes.
      </span>
    </div>
    <section class="panel">
      <div class="panel-head">
        <h2>Discovery Progress</h2>
        <span class="pill">vs. target</span>
      </div>
      <div class="stack-list">
        {disc_rows}
      </div>
    </section>
  </section>

  <!-- ── COMPLETENESS MATRIX ── -->
  <section class="panel">
    <div class="panel-head">
      <h2>Completeness matrix by country</h2>
      <span class="pill">Startups include</span>
    </div>
    <p style="color:var(--muted);font-size:0.88rem;margin-bottom:12px;">
      Green ≥80% &nbsp; Amber 50–79% &nbsp; Red &lt;50%
    </p>
    <div class="completeness-wrap">
      {completeness_table}
    </div>
  </section>

  <!-- ── CHARTS ── -->
  <div class="chart-twin">
    <div class="chart-box">
      <h3>Bio Theme Distribution (primary)</h3>
      <canvas id="themeChart" height="220"></canvas>
    </div>
    <div class="chart-box">
      <h3>Vintage — Founding year</h3>
      <canvas id="yearChart" height="220"></canvas>
    </div>
  </div>

  <!-- ── MAIN GRID ── -->
  <div class="tracker-grid">

    <!-- ── SIDEBAR ── -->
    <aside class="tracker-sidebar">

      <section class="panel">
        <div class="panel-head">
          <h2>Scope</h2>
          <span class="pill">Full universe</span>
        </div>
        <div class="stack-list">{scope_bars}</div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>Source basis (includes)</h2>
          <span class="pill muted">Basis</span>
        </div>
        <div class="stack-list">{basis_bars}</div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>Investment graph</h2>
          <span class="pill muted">Edges</span>
        </div>
        <div class="stack-list">
          <div class="bar-row">
            <div class="bar-head">
              <span>With round_stage</span>
              <span>{m["edges_with_stage"]} / {m["edges_total"]}</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width:{_pct(m["edges_with_stage"], m["edges_total"] or 1)}%;background:#14b8a6;"></div>
            </div>
          </div>
          <div class="bar-row">
            <div class="bar-head">
              <span>With amount</span>
              <span>{m["edges_with_amount"]} / {m["edges_total"]}</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width:{_pct(m["edges_with_amount"], m["edges_total"] or 1)}%;background:#8b5cf6;"></div>
            </div>
          </div>
          <div style="padding-top:6px;color:var(--muted);font-size:0.86rem;">
            Outcomes logged: <strong style="color:#334155;">{m["outcomes_total"]}</strong><br>
            Audit log entries: <strong style="color:#334155;">{m["audit_total"]}</strong>
          </div>
        </div>
      </section>

      <!-- Bio universe breakdown -->
      <section class="panel">
        <div class="panel-head">
          <h2>Bio Universe</h2>
          <span class="pill muted">is_bio_universe</span>
        </div>
        <div class="stack-list">
          <div class="bar-row">
            <div class="bar-head">
              <span style="color:#16a34a;font-weight:600;">Bio-core</span>
              <span>{m["bio_core"]} <span style="color:#94a3b8;">({bio_core_pct}%)</span></span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width:{bio_core_pct}%;background:#16a34a;"></div>
            </div>
          </div>
          <div class="bar-row">
            <div class="bar-head">
              <span style="color:#d97706;font-weight:600;">Eco-adjacent</span>
              <span>{m["eco_adjacent"]} <span style="color:#94a3b8;">({_pct(m["eco_adjacent"], total_includes)}%)</span></span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width:{_pct(m["eco_adjacent"], total_includes)}%;background:#d97706;"></div>
            </div>
          </div>
          <div style="padding-top:6px;color:var(--muted);font-size:0.86rem;">
            With secondary theme: <strong style="color:#334155;">{m["has_secondary"]}</strong>
            ({_pct(m["has_secondary"], total_includes)}% of includes)
          </div>
        </div>
      </section>

    </aside>

    <!-- ── MAIN COLUMN ── -->
    <main class="tracker-sidebar">

      <!-- Validation -->
      <section class="panel">
        <div class="panel-head">
          <h2>Pipeline validation</h2>
          <span class="pill {'warning' if m["val_errors"] > 0 else ''}">
            {'✗ ' + str(m["val_errors"]) + ' errors' if m["val_errors"] else '✓ OK'}
          </span>
        </div>
        <div>{val_rows}</div>
      </section>

      <!-- Audit feed -->
      <section class="panel">
        <div class="panel-head">
          <h2>Recent activity</h2>
          <span class="pill muted">Audit log</span>
        </div>
        <div class="audit-feed">{audit_rows}</div>
      </section>

    </main>
  </div>

</div><!-- /page-shell -->

<script>
// ── Theme chart ──────────────────────────────
const themeCtx = document.getElementById('themeChart').getContext('2d');
new Chart(themeCtx, {{
  type: 'bar',
  data: {{
    labels: {theme_labels},
    datasets: [{{
      label: 'Startups include',
      data: {theme_data},
      backgroundColor: [
        '#14b8a6','#8b5cf6','#f97316','#3b82f6','#16a34a',
        '#d97706','#dc2626','#06b6d4','#84cc16','#f43f5e',
        '#a855f7','#0ea5e9'
      ],
      borderRadius: 6,
      borderSkipped: false,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: '#f1e9de' }}, ticks: {{ font: {{ size: 11 }} }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}
    }}
  }}
}});

// ── Year chart ───────────────────────────────
const yearCtx = document.getElementById('yearChart').getContext('2d');
new Chart(yearCtx, {{
  type: 'bar',
  data: {{
    labels: {year_labels},
    datasets: [{{
      label: 'Fundadas',
      data: {year_data},
      backgroundColor: 'rgba(139,92,246,0.75)',
      borderRadius: 4,
      borderSkipped: false,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxRotation: 45 }} }},
      y: {{ grid: {{ color: '#f1e9de' }}, ticks: {{ font: {{ size: 11 }} }} }}
    }}
  }}
}});
</script>
</body>
</html>
"""


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def run(db_path: Path, output_path: Path) -> None:
    print("  [quality-report] Collecting metrics...")
    m = collect_metrics(db_path)
    print(f"  [quality-report] {m['total_includes']} includes, "
          f"{m['overall_completeness']}% completeness, "
          f"{m['val_errors']} validation errors, "
          f"{m['bio_core']} bio-core")
    html = generate_html(m)
    output_path.write_text(html, encoding="utf-8")
    print(f"  [quality-report] => {output_path}")
