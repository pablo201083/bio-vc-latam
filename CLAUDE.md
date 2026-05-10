# BIO LATAM Ecosystem Tracker

Sistema de decisión sobre el ecosistema BIO LATAM. ~385 startups, ~57 capital actors, ~37 institutions.

## Fuentes de verdad (intocables)

- `startup_master_dataset.csv` — 58 campos, ~385 filas. NO editar a mano.
- `canonical/manual_*.csv` — inputs humanos del curador, intocables.
- `quality/data_contract.md` — reglas de governance, contrato sellado.
- `schema_observatorio_biotech_v2.sql` — schema SQL de 24 tablas, contrato sellado. Las extensiones van en `db/migrations/`.

## Arquitectura

```
CSVs (fuente humana) → db/bio_latam.db (SQLite, fuente de verdad operativa)
                     ↓
              Python pipeline (src/)
                     ↓
        pilot/*.js (legacy) + Datasette JSON API (en vivo)
                     ↓
              pilot/*.html (dashboards)
```

## Comandos principales

```powershell
python pipeline.py rebuild                    # rebuild completo
python pipeline.py rebuild --phase canonical  # solo una fase
python pipeline.py status                     # counts por tabla
python pipeline.py validate                   # validaciones de integridad
python pipeline.py graph --refresh            # PageRank/communities/bridges
python pipeline.py ingest-outcomes            # leer staging/outcomes_incoming.csv
python pipeline.py calibrate-matchmaker       # precision por bucket
datasette serve db/bio_latam.db --metadata datasette/metadata.json --port 8001
node pilot/server.js                          # dashboards custom en puerto 4173
```

## Setup inicial

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python db/import_csvs.py                      # primera vez: poblar SQLite
```

## Notas operativas

- Los 68 scripts PowerShell legacy viven en `scripts/`. Se mantienen como referencia hasta validar equivalencia con el pipeline Python. No borrar.
- Todo UPDATE a SQLite debe pasar por `src/audit.py:diff_and_log_update()` para garantizar audit_log.
- Los outcomes (funding rounds, exits, partnerships) se cargan manualmente vía `staging/outcomes_incoming.csv` o vía Datasette write form. Sin agentes IA.
- El embedding cache (`embeddings/`) es regenerable. No se commitea. Re-correr `python pipeline.py rebuild --phase embeddings` cuando cambien descripciones.

## Plan estratégico

Ver `.claude/plans/quiero-que-hagamos-un-snug-cook.md` (en el directorio user) para el plan completo de 30 días organizado en 6 transformaciones (T1 plomería → T2 grafo → T3 semántica → T4 memoria → T5 matchmaker → T6 UI por rol).
