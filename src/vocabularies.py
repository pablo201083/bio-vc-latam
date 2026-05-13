"""
src/vocabularies.py — normalización léxica de tech_codes e industry_codes.

Carga vocabularios controlados desde:
  - quality/vocab_technologies.csv (code, canonical_label, aliases, group)
  - quality/vocab_industries.csv

Cada vocabulario tiene:
  - code: identificador estable (ej: 'ai_ml')
  - canonical_label: cómo se muestra en UI (ej: 'AI / Machine Learning')
  - aliases: lista separada por ';' de variantes léxicas que matchean este código
  - group: agrupación temática (digital, bio, materials, climate, etc.)

extract_codes() toma un blob de texto (technical_stack + tags) y devuelve
la lista de codes únicos que matchean. El matching es por substring case-insensitive
sobre tokens separados por ';'/','.

El curador edita los CSVs cuando aparecen tokens nuevos que no caen en ningún
código existente — se reportan en la salida del pipeline para revisión.
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass
from typing import Iterable

from src.utils import load_csv, clean

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOCAB_TECH = ROOT / "quality" / "vocab_technologies.csv"
VOCAB_INDUSTRY = ROOT / "quality" / "vocab_industries.csv"


@dataclass(frozen=True)
class VocabEntry:
    code: str
    canonical_label: str
    aliases: tuple[str, ...]
    group: str


def _normalize_alias(alias: str) -> str:
    """Normaliza un alias para matching: lowercase, trim, colapsar guiones/espacios."""
    s = alias.strip().lower()
    s = re.sub(r"[-_]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def load_vocab(path: pathlib.Path) -> list[VocabEntry]:
    """Carga un vocabulario desde CSV."""
    entries = []
    for row in load_csv(path):
        code = clean(row.get("code"))
        if not code:
            continue
        aliases_raw = clean(row.get("aliases")) or ""
        aliases = tuple(
            _normalize_alias(a) for a in aliases_raw.split(";") if a.strip()
        )
        # El propio code también es alias implícito
        aliases = tuple(set(aliases + (_normalize_alias(code), _normalize_alias(row.get("canonical_label") or ""))))
        entries.append(VocabEntry(
            code=code,
            canonical_label=clean(row.get("canonical_label")) or code,
            aliases=tuple(a for a in aliases if a),
            group=clean(row.get("group")) or "other",
        ))
    return entries


def build_alias_lookup(vocab: list[VocabEntry]) -> dict[str, str]:
    """Construye un diccionario alias_normalizado → code."""
    lookup: dict[str, str] = {}
    for entry in vocab:
        for alias in entry.aliases:
            if alias and alias not in lookup:
                lookup[alias] = entry.code
    return lookup


def tokenize_blob(blob: str) -> list[str]:
    """Separa un blob en tokens normalizados.

    Acepta separadores ';' y ',' (los más usados en los campos del CSV).
    """
    if not blob:
        return []
    raw_tokens = re.split(r"[;,]", blob)
    return [_normalize_alias(t) for t in raw_tokens if t.strip()]


def extract_codes(
    blob: str,
    alias_lookup: dict[str, str],
    *,
    capture_unknown: set[str] | None = None,
) -> list[str]:
    """Extrae codes únicos desde un blob de texto.

    Estrategia:
      1. Tokenizar por ; o ,
      2. Para cada token, buscar match exacto en alias_lookup
      3. Si no hay match exacto, buscar match parcial (substring) sobre las claves
      4. Si no matchea nada, opcionalmente registrar en capture_unknown para reporte

    Retorna lista de codes únicos (preservando orden de primera aparición).
    """
    if not blob:
        return []
    tokens = tokenize_blob(blob)
    found: list[str] = []
    seen: set[str] = set()
    sorted_aliases = sorted(alias_lookup.keys(), key=len, reverse=True)

    for tok in tokens:
        match: str | None = alias_lookup.get(tok)
        if match is None:
            # Buscar como substring: el alias está contenido en el token o viceversa
            for alias in sorted_aliases:
                if len(alias) < 3:
                    continue
                if alias in tok or tok in alias:
                    match = alias_lookup[alias]
                    break
        if match is None:
            if capture_unknown is not None and len(tok) > 2:
                capture_unknown.add(tok)
            continue
        if match not in seen:
            seen.add(match)
            found.append(match)
    return found


# ---------------------------------------------------------------------------
# API de alto nivel
# ---------------------------------------------------------------------------

def load_tech_vocab() -> tuple[list[VocabEntry], dict[str, str]]:
    vocab = load_vocab(VOCAB_TECH)
    return vocab, build_alias_lookup(vocab)


def load_industry_vocab() -> tuple[list[VocabEntry], dict[str, str]]:
    vocab = load_vocab(VOCAB_INDUSTRY)
    return vocab, build_alias_lookup(vocab)


def vocab_to_dict(vocab: list[VocabEntry]) -> dict[str, dict]:
    """Serializa un vocab para consumo del frontend."""
    return {
        entry.code: {
            "label": entry.canonical_label,
            "group": entry.group,
        }
        for entry in vocab
    }


# ---------------------------------------------------------------------------
# CLI: reporte de tokens desconocidos
# ---------------------------------------------------------------------------

def report_unknown_tokens(db_path: pathlib.Path | None = None) -> None:
    """Recorre el dataset y reporta tokens que ningún vocab cubre.

    El curador usa este reporte para decidir si extender los vocabularios
    o ignorar tokens marginales.
    """
    import sqlite3
    if db_path is None:
        db_path = ROOT / "db" / "bio_latam.db"
    conn = sqlite3.connect(db_path)

    _, tech_lookup = load_tech_vocab()
    _, ind_lookup = load_industry_vocab()

    rows = conn.execute(
        """SELECT technical_stack, technology_tags, industry_destination, domain_tags
           FROM startup_extended WHERE scope_decision='include'"""
    ).fetchall()

    unknown_tech: set[str] = set()
    unknown_ind: set[str] = set()

    for ts, tt, ind, dt in rows:
        tech_blob = (ts or "") + ";" + (tt or "")
        ind_blob = (ind or "") + ";" + (dt or "")
        extract_codes(tech_blob, tech_lookup, capture_unknown=unknown_tech)
        extract_codes(ind_blob, ind_lookup, capture_unknown=unknown_ind)

    print(f"\n=== Tokens TECH desconocidos: {len(unknown_tech)} ===")
    for tok in sorted(unknown_tech):
        print(f"  - {tok}")
    print(f"\n=== Tokens INDUSTRY desconocidos: {len(unknown_ind)} ===")
    for tok in sorted(unknown_ind):
        print(f"  - {tok}")


if __name__ == "__main__":
    report_unknown_tokens()
