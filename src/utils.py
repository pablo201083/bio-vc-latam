"""
src/utils.py — utilidades canónicas para todo el pipeline.

Esta es la única implementación válida de normalize_key, clean, repair_mojibake,
etc. Todos los módulos del pipeline importan desde acá. Los scripts PowerShell
legacy tienen ~8 implementaciones distintas de normalize_key con bugs sutiles
(algunas mantienen espacios, otras no, algunas usan FormD, otras no). La canónica
es la de scripts/build_canonical_layer.ps1.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import unicodedata
from typing import Any, Iterable


# ---------- normalización ----------

def normalize_key(value: str | None) -> str:
    """Port canónico de Normalize-Key de build_canonical_layer.ps1.

    Pasos:
    1. Lowercase + strip
    2. Unicode FormD decomposition (separa caracteres base de marcas)
    3. Elimina caracteres con categoría 'Mn' (NonSpacingMark — acentos, ñ→n)
    4. Elimina todo lo no alfanumérico (incluye espacios)

    Resultado: una clave compacta sin espacios, sin acentos, alfanumérica.
    Útil para deduplicación tolerante a tipeo.
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    s = s.lower()
    decomposed = unicodedata.normalize("NFD", s)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", stripped)


def normalize_text(value: str | None) -> str:
    """Normalización suave: lowercase + sin acentos + non-alphanumeric → espacio.

    Mantiene espacios (a diferencia de normalize_key). Útil para tokenización
    en taxonomy matching, no para deduplicación de nombres propios.
    """
    if value is None:
        return ""
    s = str(value).strip().lower()
    if not s:
        return ""
    decomposed = unicodedata.normalize("NFD", s)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    stripped = stripped.replace("·", " ")
    return re.sub(r"[^a-z0-9]+", " ", stripped).strip()


def slugify(value: str | None) -> str:
    """Convierte a slug URL-safe. Más legible que normalize_key (mantiene guiones)."""
    if value is None:
        return ""
    s = str(value).strip().lower()
    decomposed = unicodedata.normalize("NFD", s)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    slug = re.sub(r"[^a-z0-9]+", "-", stripped).strip("-")
    return slug or "entity"


# ---------- limpieza de valores ----------

NAN_MARKERS = {"", "nan", "none", "null", "n/a", "na", "#n/a", "tbd"}


def clean(value: Any) -> str:
    """Limpia un valor para CSV/SQL: None, NaN, strings vacíos → ''. Strip whitespace."""
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in NAN_MARKERS:
        return ""
    return s


def to_float(value: Any, default: float | None = None) -> float | None:
    """Convierte a float, retornando default si no se puede."""
    s = clean(value)
    if not s:
        return default
    try:
        return float(s.replace(",", "."))
    except (ValueError, TypeError):
        return default


def to_int(value: Any, default: int | None = None) -> int | None:
    """Convierte a int. Soporta '7', '7.0', '7.5'→7. Retorna default si no se puede."""
    s = clean(value)
    if not s:
        return default
    try:
        return int(float(s.replace(",", ".")))
    except (ValueError, TypeError):
        return default


def repair_mojibake(value: Any) -> str:
    """Repara mojibake típico de LATAM (Ã©→é, Ã±→ñ, etc.) usando ftfy.

    Mucho más robusto que el roll-out manual de Repair-Mojibake en PowerShell.
    Si ftfy no está disponible, retorna el string sin cambios.
    """
    s = clean(value)
    if not s:
        return ""
    try:
        import ftfy
        return ftfy.fix_text(s)
    except ImportError:
        return s


def split_tags(value: Any, separator: str = ";") -> list[str]:
    """Parsea un campo de tags separados por ';'. Retorna lista limpia y dedupada.

    Ejemplo: 'ai-data; iot ; ai-data' → ['ai-data', 'iot']
    """
    s = clean(value)
    if not s:
        return []
    seen = set()
    out: list[str] = []
    for raw in s.split(separator):
        tag = raw.strip()
        if not tag:
            continue
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(tag)
    return out


# ---------- I/O CSV ----------

def load_csv(path: pathlib.Path) -> list[dict[str, str]]:
    """Carga CSV con manejo de BOM UTF-8. Retorna lista de dicts."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def write_csv(path: pathlib.Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    """Escribe CSV con UTF-8 BOM (para compatibilidad con Excel y PowerShell Export-Csv -Encoding UTF8)."""
    if not rows and not fieldnames:
        path.write_text("﻿", encoding="utf-8")
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (clean(row.get(k))) for k in fieldnames})


def write_js_global(path: pathlib.Path, varname: str, data: Any) -> None:
    """Escribe un archivo JS con `window.VARNAME = <json>;` para los dashboards pilot/."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, default=_json_default)
    js = f"window.{varname} = {payload};\n"
    path.write_text(js, encoding="utf-8")


def _json_default(obj: Any) -> Any:
    """Default JSON encoder para tipos no serializables (Path, set, etc.)."""
    if isinstance(obj, pathlib.Path):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"No JSON serializer for {type(obj)}")


# ---------- mapeos auxiliares ----------

# Centroides geográficos por país para datasette-cluster-map (T6)
COUNTRY_CENTROIDS: dict[str, tuple[float, float]] = {
    "AR": (-38.416, -63.617),
    "BR": (-14.235, -51.925),
    "BO": (-16.290, -63.589),
    "CL": (-35.675, -71.543),
    "CO": (4.571, -74.297),
    "CR": (9.748, -83.754),
    "DO": (18.735, -70.162),
    "EC": (-1.831, -78.183),
    "GT": (15.784, -90.230),
    "HN": (15.200, -86.242),
    "JM": (18.110, -77.298),
    "MX": (23.635, -102.553),
    "NI": (12.865, -85.207),
    "PA": (8.538, -80.782),
    "PE": (-9.190, -75.015),
    "PR": (18.221, -66.591),
    "PY": (-23.443, -58.444),
    "SV": (13.794, -88.897),
    "UY": (-32.523, -55.765),
    "VE": (6.423, -66.590),
    # Resto del mundo (para entidades no-LATAM en el dataset)
    "US": (37.090, -95.713),
    "CA": (56.130, -106.347),
    "ES": (40.464, -3.749),
    "PT": (39.400, -8.224),
    "GB": (55.378, -3.436),
    "FR": (46.227, 2.213),
    "DE": (51.166, 10.452),
    "NL": (52.133, 5.291),
    "CH": (46.818, 8.228),
}


def country_centroid(country_code: str | None) -> tuple[float, float] | None:
    """Devuelve (lat, lng) para un código de país ISO-2, o None si desconocido."""
    if not country_code:
        return None
    return COUNTRY_CENTROIDS.get(country_code.strip().upper())


# ---------- mapeo de status / scope ----------

def scope_to_entity_status(scope_decision: str | None) -> str:
    """Mapea scope_decision (editorial) a entities.status (técnico).

    include → 'active', exclude → 'excluded', review → 'review',
    cualquier otro → 'unknown'.
    """
    s = clean(scope_decision).lower()
    if s == "include":
        return "active"
    if s == "exclude":
        return "excluded"
    if s == "review":
        return "review"
    return "unknown"
