"""
src/audit.py — Audit log obligatorio para todo UPDATE a la DB.

Patrón: NUNCA hacer UPDATE directo. Usar diff_and_log_update().
El audit_log registra actor, entidad, campo, valor_antes, valor_después, razón, timestamp.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_change(
    conn: sqlite3.Connection,
    actor: str,
    entity_id: str | None,
    field: str,
    old_value: Any,
    new_value: Any,
    reason: str,
    evidence_url: str | None = None,
    confidence: float | None = None,
) -> None:
    """Inserta una entrada en audit_log. Llamar por cada campo cambiado."""
    conn.execute(
        """
        INSERT INTO audit_log
            (timestamp, actor, entity_id, field, old_value, new_value, reason, evidence_url, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _now(),
            actor,
            entity_id,
            field,
            str(old_value) if old_value is not None else None,
            str(new_value) if new_value is not None else None,
            reason,
            evidence_url,
            confidence,
        ),
    )


def diff_and_log_update(
    conn: sqlite3.Connection,
    table: str,
    row_id_col: str,
    row_id: Any,
    new_values: dict[str, Any],
    actor: str,
    reason: str,
    evidence_url: str | None = None,
) -> int:
    """Lee el row actual, compara con new_values, loguea y aplica solo los campos cambiados.

    Retorna el número de campos efectivamente actualizados.
    Es la única forma correcta de tocar startup_extended / entities / investors
    desde el pipeline.

    Ejemplo:
        diff_and_log_update(
            conn, "entities", "entity_id", "beeflow",
            {"founded_year": 2017, "website": "https://beeflow.com"},
            actor="pipeline:ingest_founding_years",
            reason="staging/founding_years.csv — fuente: crunchbase"
        )
    """
    # Leer row actual
    cols_str = ", ".join(new_values.keys())
    row = conn.execute(
        f"SELECT {cols_str} FROM {table} WHERE {row_id_col} = ?", (row_id,)
    ).fetchone()

    if row is None:
        return 0  # entidad no existe, saltar silenciosamente

    old_row = dict(zip(new_values.keys(), row))
    changes: dict[str, Any] = {}

    for field, new_val in new_values.items():
        old_val = old_row.get(field)
        # Normalizar: None y "" se tratan igual para comparación
        old_str = str(old_val).strip() if old_val is not None else ""
        new_str = str(new_val).strip() if new_val is not None else ""
        if old_str == new_str:
            continue  # sin cambio
        changes[field] = (old_val, new_val)

    if not changes:
        return 0

    # Aplicar UPDATE solo con los campos que cambiaron
    set_clause = ", ".join(f"{f} = ?" for f in changes)
    values = [v for _, v in changes.values()]
    conn.execute(
        f"UPDATE {table} SET {set_clause} WHERE {row_id_col} = ?",
        values + [row_id],
    )

    # Loguear cada cambio
    for field, (old_val, new_val) in changes.items():
        log_change(
            conn,
            actor=actor,
            entity_id=str(row_id),
            field=f"{table}.{field}",
            old_value=old_val,
            new_value=new_val,
            reason=reason,
            evidence_url=evidence_url,
        )

    return len(changes)
