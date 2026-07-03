"""
src/bump_cache.py — cache-busting automático de los bundles JS referenciados
desde pilot/*.html.

Reemplaza el valor de `?v=...` de cada `<script src="./archivo.js?v=...">`
por un hash corto (8 chars sha1) del contenido ACTUAL de `pilot/archivo.js`.
Idempotente: si el hash no cambió, no toca el HTML.

Referencias sin `?v=` (ej. `src="./i18n.js"`) o hacia subcarpetas
(ej. `src="./data/embedded-data.js"`) se dejan intactas — solo se tocan
los `?v=` ya presentes de archivos directamente en pilot/.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PILOT = ROOT / "pilot"

_SRC_V_RE = re.compile(r'(src="\./(?P<name>[\w.-]+\.js))\?v=[\w.-]*(?P<quote>")')


def _hash_file(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:8]


def bump_cache(pilot_dir: Path = PILOT) -> dict[str, int]:
    """Actualiza los `?v=` de pilot/*.html al hash de contenido de cada .js.

    Retorna: {html_scanned, html_updated, refs_updated}
    """
    bundle_hashes: dict[str, str] = {
        js_path.name: _hash_file(js_path) for js_path in pilot_dir.glob("*.js")
    }

    stats = {"html_scanned": 0, "html_updated": 0, "refs_updated": 0}

    for html_path in pilot_dir.glob("*.html"):
        stats["html_scanned"] += 1
        text = html_path.read_text(encoding="utf-8")
        n_refs = 0

        def _sub(m: re.Match) -> str:
            nonlocal n_refs
            h = bundle_hashes.get(m.group("name"))
            if h is None:
                return m.group(0)
            new = f'{m.group(1)}?v={h}{m.group("quote")}'
            if new != m.group(0):
                n_refs += 1
            return new

        new_text = _SRC_V_RE.sub(_sub, text)
        if n_refs:
            html_path.write_text(new_text, encoding="utf-8")
            stats["html_updated"] += 1
            stats["refs_updated"] += n_refs

    return stats
