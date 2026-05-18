"""
scripts/intake_to_canonical.py

Convierte staging/capital_intake.csv → filas nuevas en
canonical/manual_canonical_investment_edges.csv

Para cada fila del intake:
  1. Resuelve investor_id: usa investor_id si está dado, si no busca investor_name
     contra entities + entity_aliases
  2. Resuelve startup_id: igual que investor_id
  3. Determina relation_type_raw y confidence según round_stage / source_url
  4. Genera raw_edge_id único
  5. Append al CSV canónico (evita duplicados por investor+startup)

Uso:
  python scripts/intake_to_canonical.py
  python scripts/intake_to_canonical.py --dry-run  # solo muestra, no escribe
  python scripts/intake_to_canonical.py --file staging/mi_lote.csv  # archivo custom

Después de correr, ejecutar:
  python pipeline.py rebuild --phase canonical
  python pipeline.py build-atlas
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sqlite3
import sys
import unicodedata
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT      = pathlib.Path(__file__).resolve().parent.parent
DB_PATH   = ROOT / "db" / "bio_latam.db"
INTAKE    = ROOT / "staging" / "capital_intake.csv"
CANONICAL = ROOT / "canonical" / "manual_canonical_investment_edges.csv"


def normalize(s: str) -> str:
    """Normaliza nombre para matching: lowercase, sin acentos, sin puntuación."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")  # quita acentos
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)  # puntuación → espacio
    s = re.sub(r"\s+", " ", s).strip()
    return s


def confidence_from_url(source_url: str, round_stage: str) -> float:
    """Estima confidence según tipo de URL y stage."""
    if not source_url:
        return 0.75
    url = source_url.lower()
    # Press release / announcement
    if any(k in url for k in ["techcrunch", "bloomberg", "reuters", "businesswire",
                                "prnewswire", "announces", "announcement", "news",
                                "press-release", "crunchbase.com/funding"]):
        return 0.98
    # Página específica del startup (no solo portfolio del fondo)
    if any(k in url for k in ["/portfolio/", "/investments/", "/participadas/",
                                "/folio/", "/companies/"]):
        return 0.96
    # Página oficial del fondo (genérica)
    if any(k in url for k in ["portfolio", "invest", "startup"]):
        return 0.92
    return 0.90


def relation_type_from_stage(round_stage: str, source_url: str = "") -> str:
    """Mapea round_stage a relation_type_raw canónico."""
    url = source_url.lower()
    if "accelerat" in url or "incubat" in url or "program" in url:
        return "official_program_investment"
    stage = (round_stage or "").lower()
    if stage in ("pre-seed", "seed", "series-a", "series-b", "series-c", "growth", "series_a"):
        return "official_direct_investment"
    return "official_portfolio_investment"


def build_entity_index(conn: sqlite3.Connection) -> dict[str, str]:
    """Construye índice normalized_name → entity_id desde entities + aliases."""
    idx: dict[str, str] = {}

    # Nombres canónicos
    for row in conn.execute("SELECT entity_id, canonical_name FROM entities").fetchall():
        key = normalize(row[0])  # entity_id también como llave (exacto)
        if key and key not in idx:
            idx[key] = row[0]
        key2 = normalize(row[1])
        if key2 and key2 not in idx:
            idx[key2] = row[0]

    # Aliases
    for row in conn.execute("SELECT entity_id, alias FROM entity_aliases").fetchall():
        key = normalize(row[1])
        if key and key not in idx:
            idx[key] = row[0]

    return idx


def resolve_entity(name_or_id: str, slug: str, idx: dict[str, str], label: str) -> Optional[str]:
    """Devuelve entity_id o None si no se puede resolver."""
    # 1. Slug exacto
    if slug and slug.strip():
        s = slug.strip()
        if normalize(s) in idx:
            return idx[normalize(s)]
        # Intentar directamente (puede ser ya el entity_id)
        if s in idx.values() or normalize(s) in {normalize(k) for k in idx}:
            return s
        print(f"    [WARN] {label} slug '{s}' no encontrado en entities — revisar")
        return None

    # 2. Nombre libre
    if name_or_id and name_or_id.strip():
        n = normalize(name_or_id.strip())
        if n in idx:
            return idx[n]
        # Búsqueda parcial (contiene)
        matches = [eid for key, eid in idx.items() if n in key or key in n]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            print(f"    [WARN] {label} '{name_or_id}' → múltiples matches: {matches[:5]}")
            return None
        print(f"    [WARN] {label} '{name_or_id}' no encontrado en entities")
        return None

    return None


def existing_edge_keys(canonical_path: pathlib.Path) -> set[tuple[str, str]]:
    """Devuelve set de (investor_id_candidate, startup_id_candidate) ya en el CSV."""
    keys: set[tuple[str, str]] = set()
    if not canonical_path.exists():
        return keys
    with canonical_path.open("r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            inv = (row.get("investor_id_candidate") or "").strip()
            sta = (row.get("startup_id_candidate") or "").strip()
            if inv and sta:
                keys.add((inv, sta))
    return keys


def existing_edge_ids(canonical_path: pathlib.Path) -> set[str]:
    """Devuelve set de raw_edge_id ya en el CSV."""
    ids: set[str] = set()
    if not canonical_path.exists():
        return ids
    with canonical_path.open("r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            eid = (row.get("raw_edge_id") or "").strip()
            if eid:
                ids.add(eid)
    return ids


def make_edge_id(investor_id: str, startup_id: str, existing_ids: set[str]) -> str:
    """Genera un raw_edge_id único para la nueva edge."""
    base = f"manual-{investor_id[:12]}-{startup_id[:12]}"
    base = re.sub(r"[^a-z0-9_-]", "-", base.lower())
    candidate = base
    suffix = 2
    while candidate in existing_ids:
        candidate = f"{base}-{suffix}"
        suffix += 1
    existing_ids.add(candidate)
    return candidate


def main(intake_path: pathlib.Path, dry_run: bool = False) -> None:
    if not intake_path.exists():
        print(f"  [ERROR] No se encontró {intake_path}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    entity_idx = build_entity_index(conn)
    conn.close()

    # Leer intake
    with intake_path.open("r", encoding="utf-8-sig") as f:
        intake_rows = list(csv.DictReader(f))

    # Filtrar filas vacías y la fila de ejemplo
    intake_rows = [
        r for r in intake_rows
        if any(v.strip() for v in r.values())
        and (r.get("investor_id") or "").strip() not in ("investor_id", "")
        or (r.get("investor_name") or "").strip() not in ("", "sp_ventures")
    ]
    # Filtrar genuinamente vacíos
    intake_rows = [
        r for r in intake_rows
        if (r.get("investor_id") or r.get("investor_name") or "").strip()
        and (r.get("startup_id") or r.get("startup_name") or "").strip()
        and (r.get("source_url") or "").strip()
    ]

    if not intake_rows:
        print("  No hay filas válidas en el intake (requieren investor, startup y source_url).")
        return

    existing_keys = existing_edge_keys(CANONICAL)
    existing_ids  = existing_edge_ids(CANONICAL)

    CANONICAL_COLS = [
        "raw_edge_id", "source_id", "target_id", "source_file",
        "relation_type_raw", "direction_status",
        "investor_id_candidate", "startup_id_candidate",
        "confidence_score", "notes",
    ]

    new_rows: list[dict] = []
    skipped = 0

    for i, row in enumerate(intake_rows, 1):
        inv_slug  = (row.get("investor_id") or "").strip()
        inv_name  = (row.get("investor_name") or "").strip()
        sta_slug  = (row.get("startup_id") or "").strip()
        sta_name  = (row.get("startup_name") or "").strip()
        src_url   = (row.get("source_url") or "").strip()
        stage     = (row.get("round_stage") or "").strip()
        rname     = (row.get("round_name") or "").strip()
        date_     = (row.get("announced_date") or "").strip()
        amount    = (row.get("amount_usd") or "").strip()
        currency  = (row.get("currency") or "USD").strip()
        is_lead   = (row.get("is_lead") or "").strip()
        conf_raw  = (row.get("confidence_score") or "").strip()
        notes_in  = (row.get("notes") or "").strip()

        print(f"\n  [{i}] {inv_name or inv_slug} → {sta_name or sta_slug}")

        investor_id = resolve_entity(inv_name, inv_slug, entity_idx, "Investor")
        startup_id  = resolve_entity(sta_name, sta_slug, entity_idx, "Startup")

        if not investor_id or not startup_id:
            print(f"    [SKIP] No se pudo resolver uno o ambos IDs")
            skipped += 1
            continue

        if (investor_id, startup_id) in existing_keys:
            print(f"    [SKIP] Edge {investor_id} → {startup_id} ya existe en canonical")
            skipped += 1
            continue

        # Calcular confidence
        if conf_raw:
            try:
                conf = float(conf_raw)
            except ValueError:
                conf = confidence_from_url(src_url, stage)
        else:
            conf = confidence_from_url(src_url, stage)

        # Construir notes enriquecidas
        notes_parts = []
        if notes_in:
            notes_parts.append(notes_in)
        if date_:
            notes_parts.append(f"announced: {date_}")
        if amount:
            notes_parts.append(f"amount: {amount} {currency}")
        if is_lead == "1":
            notes_parts.append("lead investor")
        notes_final = " | ".join(notes_parts) or f"{investor_id} → {startup_id} via portfolio page"

        edge_id = make_edge_id(investor_id, startup_id, existing_ids)
        relation_type = relation_type_from_stage(stage, src_url)

        new_row = {
            "raw_edge_id":          edge_id,
            "source_id":            inv_name or investor_id,
            "target_id":            sta_name or startup_id,
            "source_file":          src_url,
            "relation_type_raw":    relation_type,
            "direction_status":     "validated_investor_to_startup",
            "investor_id_candidate": investor_id,
            "startup_id_candidate":  startup_id,
            "confidence_score":     str(round(conf, 2)),
            "notes":                notes_final,
        }
        new_rows.append(new_row)
        existing_keys.add((investor_id, startup_id))
        print(f"    OK → {edge_id} (conf={conf:.2f}, type={relation_type})")

    print(f"\n  ─────────────────────────────────")
    print(f"  Filas procesadas: {len(intake_rows)}")
    print(f"  Nuevas edges:     {len(new_rows)}")
    print(f"  Saltadas:         {skipped}")

    if not new_rows:
        print("  Nada que escribir.\n")
        return

    if dry_run:
        print("\n  [dry-run] No se escribió nada. Correr sin --dry-run para aplicar.")
        return

    # Append al CSV canónico
    write_header = not CANONICAL.exists()
    with CANONICAL.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CANONICAL_COLS)
        if write_header:
            w.writeheader()
        w.writerows(new_rows)

    print(f"\n  Escritas {len(new_rows)} edges en canonical/manual_canonical_investment_edges.csv")
    print("\n  Siguiente paso:")
    print("    python pipeline.py rebuild --phase canonical")
    print("    python pipeline.py build-atlas\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo muestra resultados, no escribe")
    parser.add_argument("--file", type=pathlib.Path, default=INTAKE,
                        help=f"CSV de intake (default: {INTAKE})")
    args = parser.parse_args()
    main(intake_path=args.file, dry_run=args.dry_run)
