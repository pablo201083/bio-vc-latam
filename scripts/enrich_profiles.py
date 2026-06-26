"""
scripts/enrich_profiles.py — Fase 2+3: scraping de webs oficiales de startups.

Qué hace:
  - Scraping del sitio oficial de cada startup incluida en el ecosistema
  - Guarda el texto extraído en data/website_scrapes/<startup_id>.txt (referencia futura)
  - Extrae el tagline/hero (H1 + primer párrafo) como candidato a business_one_liner
  - Marca profile_source en la DB según resultado del scrape
  - NO reemplaza startup_summary_v1 ni startup_summary_en (ya son de buena calidad)

Uso:
  python scripts/enrich_profiles.py                         # todos los pendientes
  python scripts/enrich_profiles.py --limit 20             # primeros N
  python scripts/enrich_profiles.py --startup-id puna_bio  # uno solo
  python scripts/enrich_profiles.py --dry-run              # sin escribir a DB
  python scripts/enrich_profiles.py --force                # re-procesar ya scrapeados
  python scripts/enrich_profiles.py --show-taglines        # imprime taglines extraídos
"""

import argparse
import csv
import os
import pathlib
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "bio_latam.db"
SCRAPES_DIR = ROOT / "data" / "website_scrapes"
LOG_PATH = ROOT / "data" / "enrich_profiles_log.csv"

SCRAPES_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

SCRAPE_TIMEOUT = 12
SCRAPE_DELAY = 1.2
MAX_TEXT_CHARS = 8000
MIN_TEXT_CHARS = 80

NOISE = re.compile(
    r"(cookie|subscribe|newsletter|sign up|log in|login|privacy policy|terms of service|"
    r"all rights reserved|instagram|facebook|twitter|linkedin|©|\bjs\b|javascript|"
    r"skip to|menu|search|shopping cart|\d{1,2}/\d{1,2}/\d{4})",
    re.IGNORECASE,
)
ACCENT_RE = re.compile(r"[áéíóúñüÁÉÍÓÚÑÜ¡¿ãõçÃÕÇàèìòùÀÈÌÒÙ]")

SUBPAGES = [
    "/about", "/about-us", "/about-us/", "/nosotros", "/quienes-somos",
    "/technology", "/tecnologia", "/platform", "/solution", "/science",
    "/product", "/products", "/en", "/en/about", "/en/technology",
]

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en,es;q=0.8",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}


def ensure_db_columns(conn):
    cols = {c[1] for c in conn.execute("PRAGMA table_info(startup_extended)").fetchall()}
    needed = {"profile_source": "TEXT", "profile_scraped_at": "TEXT"}
    for col, typ in needed.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE startup_extended ADD COLUMN {col} {typ}")
    conn.commit()


def get_targets(conn, startup_id=None, force=False):
    where_extra = ""
    params = []
    if startup_id:
        where_extra = "AND e.entity_id = ?"
        params.append(startup_id)
    elif not force:
        where_extra = "AND (sx.profile_source IS NULL OR sx.profile_source = '')"

    return conn.execute(f"""
        SELECT e.entity_id, e.canonical_name, e.website,
               sx.startup_summary_v1, sx.business_one_liner, sx.macro_theme
        FROM entities e
        JOIN startup_extended sx ON sx.startup_id = e.entity_id
        WHERE sx.scope_decision = 'include'
        {where_extra}
        ORDER BY sx.computed_quality_score DESC NULLS LAST
    """, params).fetchall()


def _fetch(url: str, client: httpx.Client) -> str | None:
    try:
        r = client.get(url, timeout=SCRAPE_TIMEOUT, follow_redirects=True)
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        if "text/html" not in ct and "text/plain" not in ct:
            return None
        return r.text
    except Exception:
        return None


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript",
                     "iframe", "form", "button", "svg", "img", "aside"]):
        tag.decompose()

    # Priority content zones
    chunks = []
    for sel in ["main", "article", "[class*='about']", "[class*='hero']",
                "[class*='mission']", "[class*='product']", "[class*='technology']",
                "[class*='solution']", "section", "h1", "h2", "h3", "p"]:
        for el in soup.select(sel)[:6]:
            t = el.get_text(" ", strip=True)
            if len(t) > 25:
                chunks.append(t)
    if not chunks:
        chunks.append(soup.get_text(" ", strip=True))

    text = "\n\n".join(chunks)
    text = re.sub(r"\s{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()[:MAX_TEXT_CHARS]


def _extract_tagline(html: str, company_name: str) -> str:
    """Extract the company's hero tagline: H1 or first short strong paragraph."""
    soup = BeautifulSoup(html, "html.parser")
    # Collect H1/H2 BEFORE removing structural tags (they may live inside header/nav)
    all_h1 = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    all_h2 = [h.get_text(" ", strip=True) for h in soup.find_all("h2")]

    for tag in soup(["script", "style", "footer", "noscript", "iframe"]):
        tag.decompose()

    candidates = []

    # H1 tags (from pre-extraction list — avoids nav/header removal issue)
    seen_h1 = set()
    for h1_text in all_h1:
        if h1_text in seen_h1:
            continue
        seen_h1.add(h1_text)
        if 15 < len(h1_text) < 200 and not NOISE.search(h1_text):
            candidates.append(("h1", h1_text))

    # Hero/banner short paragraphs
    for sel in ["[class*='hero'] p", "[class*='banner'] p",
                "[class*='headline']", "[class*='tagline']", "[class*='pitch']"]:
        for el in soup.select(sel)[:3]:
            t = el.get_text(" ", strip=True)
            if 20 < len(t) < 200 and not NOISE.search(t):
                candidates.append(("hero", t))

    # First short paragraph in main content
    for p in soup.select("main p, article p")[:10]:
        t = p.get_text(" ", strip=True)
        if 30 < len(t) < 180 and not NOISE.search(t):
            candidates.append(("p", t))
            if len(candidates) >= 5:
                break

    if not candidates:
        return ""

    # Prefer English candidates (low accent ratio)
    def en_score(c):
        _, text = c
        ratio = len(ACCENT_RE.findall(text)) / max(len(text), 1)
        return ratio

    candidates_en = [(tag, t) for tag, t in candidates if en_score((tag, t)) < 0.03]
    pool = candidates_en if candidates_en else candidates

    # Rank: h1 > hero > p; shorter is better for tagline
    priority = {"h1": 0, "hero": 1, "p": 2}
    pool.sort(key=lambda c: (priority.get(c[0], 3), len(c[1])))

    tagline = pool[0][1] if pool else ""

    # Skip if tagline is just the company name or navigation text
    if tagline.strip().lower() == company_name.lower():
        tagline = pool[1][1] if len(pool) > 1 else ""

    return tagline


def _normalize_pov(text: str, company_name: str) -> str:
    """Convert first-person we/our → company name."""
    name = company_name.strip()
    _v3 = {"develop": "develops", "create": "creates", "build": "builds",
            "offer": "offers", "provide": "provides", "design": "designs",
            "produce": "produces", "use": "uses", "enable": "enables",
            "help": "helps", "connect": "connects", "focus": "focuses",
            "work": "works", "specialize": "specializes", "leverage": "leverages",
            "combine": "combines", "apply": "applies", "transform": "transforms"}

    text = re.sub(
        r"\bWe (develop|create|build|offer|provide|design|produce|use|enable|help|"
        r"connect|focus|work|specialize|leverage|combine|apply|transform)\b",
        lambda m: f"{name} {_v3.get(m.group(1).lower(), m.group(1)+'s')}",
        text, flags=re.I,
    )
    text = re.sub(r"\bWe are\b", f"{name} is", text, flags=re.I)
    text = re.sub(r"\bOur\b", f"{name}'s", text, flags=re.I)
    text = re.sub(r"\bwe\b", name, text, flags=re.I)
    return text


def scrape_startup(base_url: str) -> tuple[str, str, str]:
    """
    Scrape website. Returns (full_text, tagline_html, status).
    status: 'ok' | 'partial' | 'empty' | 'timeout' | 'error:<type>'
    """
    if not base_url:
        return "", "", "no_url"
    if not base_url.startswith("http"):
        base_url = "https://" + base_url.lstrip("/")

    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    urls_to_try = [base_url]
    for sub in SUBPAGES:
        cand = origin + sub
        if cand != base_url:
            urls_to_try.append(cand)

    full_text_chunks = []
    tagline_html = ""
    seen = set()
    got_error = None

    with httpx.Client(headers=HTTP_HEADERS, follow_redirects=True) as client:
        for url in urls_to_try:
            if url in seen:
                continue
            seen.add(url)

            html = _fetch(url, client)
            if not html:
                got_error = "fetch_fail"
                time.sleep(0.3)
                continue

            text = _html_to_text(html)
            if len(text.strip()) > MIN_TEXT_CHARS:
                full_text_chunks.append(text)

            if not tagline_html and url in (base_url, origin, origin + "/en"):
                tagline_html = html  # Save homepage HTML for tagline extraction

            total_chars = sum(len(c) for c in full_text_chunks)
            if total_chars >= MAX_TEXT_CHARS:
                break

            time.sleep(0.35)

    full_text = "\n\n---\n\n".join(full_text_chunks)[:MAX_TEXT_CHARS]

    if not full_text.strip():
        return "", "", f"empty:{got_error or 'no_content'}"

    status = "ok" if len(full_text.strip()) >= 500 else "partial"
    return full_text, tagline_html, status


def write_log(row: dict):
    exists = LOG_PATH.exists()
    with open(LOG_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["startup_id", "name", "url",
                                                "scrape_status", "tagline", "timestamp"])
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Scrape startup websites and enrich profiles")
    parser.add_argument("--startup-id", help="Process single startup by entity_id")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="No DB writes")
    parser.add_argument("--force", action="store_true", help="Re-process already scraped")
    parser.add_argument("--show-taglines", action="store_true", help="Print extracted taglines")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    ensure_db_columns(conn)

    targets = get_targets(conn, startup_id=args.startup_id, force=args.force)
    if args.limit:
        targets = targets[:args.limit]

    print(f"BIO LATAM Profile Enrichment")
    print(f"Targets : {len(targets)} startups")
    print(f"Mode    : {'dry-run' if args.dry_run else 'live'}")
    print(f"Scrapes : {SCRAPES_DIR}")
    print()

    stats = {"ok": 0, "partial": 0, "empty": 0, "no_url": 0, "error": 0}

    for idx, (startup_id, name, website, summary_v1, existing_liner, macro_theme) in enumerate(targets):
        print(f"[{idx+1:3d}/{len(targets)}] {name}", end="")

        if not website:
            print(f"  — no URL")
            stats["no_url"] += 1
            write_log({"startup_id": startup_id, "name": name, "url": "",
                       "scrape_status": "no_url", "tagline": "",
                       "timestamp": datetime.now(timezone.utc).isoformat()})
            continue

        url = website if website.startswith("http") else f"https://{website}"
        print(f"  {url[:60]}", end="", flush=True)

        full_text, tagline_html, scrape_status = scrape_startup(url)
        status_key = scrape_status.split(":")[0]
        print(f"  [{scrape_status}] {len(full_text)} chars")

        # Extract tagline from homepage HTML
        tagline = ""
        if tagline_html:
            tagline = _extract_tagline(tagline_html, name)
            tagline = _normalize_pov(tagline, name)

        if args.show_taglines and tagline:
            print(f"         tagline: {tagline}")

        # Write scrape to disk
        scrape_path = SCRAPES_DIR / f"{startup_id}.txt"
        if not args.dry_run and full_text:
            scrape_path.write_text(full_text, encoding="utf-8")

        # Update DB: profile_source, profile_scraped_at, business_one_liner (only if empty)
        if not args.dry_run and status_key in ("ok", "partial"):
            updates = [datetime.now(timezone.utc).isoformat(), scrape_status, startup_id]
            # Update one_liner only if currently empty and we extracted a tagline
            if tagline and not existing_liner:
                conn.execute("""
                    UPDATE startup_extended
                    SET profile_scraped_at=?, profile_source=?, business_one_liner=?
                    WHERE startup_id=?
                """, [updates[0], updates[1], tagline, startup_id])
            else:
                conn.execute("""
                    UPDATE startup_extended
                    SET profile_scraped_at=?, profile_source=?
                    WHERE startup_id=?
                """, updates)
            conn.commit()
        elif not args.dry_run and status_key in ("empty", "error", "no_url"):
            conn.execute("""
                UPDATE startup_extended
                SET profile_scraped_at=?, profile_source=?
                WHERE startup_id=?
            """, [datetime.now(timezone.utc).isoformat(), scrape_status, startup_id])
            conn.commit()

        stats[status_key if status_key in stats else "error"] += 1

        write_log({
            "startup_id": startup_id, "name": name, "url": url,
            "scrape_status": scrape_status,
            "tagline": tagline[:120] if tagline else "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        time.sleep(SCRAPE_DELAY)

    conn.close()

    print()
    print("=" * 40)
    print(f"Results:")
    for k, v in stats.items():
        print(f"  {k:10s}: {v}")
    print(f"Log     : {LOG_PATH}")
    print(f"Scrapes : {SCRAPES_DIR}")


if __name__ == "__main__":
    main()
