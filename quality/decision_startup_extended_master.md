# Decisión: `startup_extended` es la tabla maestra del universo

**Fecha:** 2026-07-04
**Estado:** Decidida (no re-litigar sin nueva evidencia)

## Contexto

El schema sellado (`schema_observatorio_biotech_v2.sql`) define dos tablas de
startup:

- `startups` — tabla original del schema v2, con campos de una taxonomía
  anterior (`biotech_vertical`, `biotech_subvertical`, `trl_level`,
  `validation_status`, etc.).
- `startup_extended` — tabla que en la práctica acumula todo el trabajo
  editorial y de clasificación vigente: `scope_decision`, `bio_theme_primary`,
  `macro_theme`, `cluster_label`, `data_quality_score`, `umap_x/y`, y el resto
  de los campos que alimentan dashboards, matchmaker y health.

Desde hace meses, `health` reporta en rojo permanente: **315 filas de
`startup_extended` con `scope_decision='include'` que no tienen fila
correspondiente en `startups`**. Ninguna herramienta del pipeline actual
(`src/`) escribe en `startups`; toda la ingesta, clasificación y enriquecimiento
de los últimos meses fue directamente a `startup_extended`.

## Decisión

**`startup_extended` es la tabla maestra del universo de startups.** La tabla
`startups` queda como remanente del schema original — no se retro-llena, no se
sincroniza, no se deprecha formalmente (el schema está sellado), pero deja de
tratarse como la fuente de verdad del universo.

Toda query o herramienta que necesite "el universo de startups BIO LATAM"
debe partir de:

```sql
SELECT * FROM startup_extended WHERE scope_decision = 'include'
```

y hacer `JOIN` con `entities` para nombre/país/website, no con `startups`.

## Alternativa descartada

**Backfill de `startups`** con las 315 filas faltantes, para que ambas tablas
queden sincronizadas. Descartada porque:

- No hay ningún consumidor (dashboard, script, query) que lea de `startups`
  hoy — el backfill no cambiaría ningún comportamiento observable.
- Los campos de `startups` (`biotech_vertical`, `trl_level`, etc.) pertenecen
  a una taxonomía que ya no se usa; poblarlos con datos inventados o
  placeholder sería peor que dejarlos vacíos.
- El "gap" no es un error de datos: es un desajuste entre el schema sellado
  original y cómo evolucionó operativamente el proyecto. Backfillear para
  cerrar un número en el semáforo, sin que nadie use esos datos, es teatro de
  calidad — no calidad real.

## Razón

- Es la realidad operativa desde hace meses: el pipeline entero (clustering,
  reclassify, intelligence, health, coverage) ya trata `startup_extended`
  como maestra.
- Un rojo permanente en el semáforo de salud erosiona la confianza en el
  semáforo mismo — cuando una señal nunca puede ponerse en verde pase lo que
  pase, deja de leerse.

## Implicaciones

1. Cualquier función o query nueva que necesite el universo de startups debe
   usar `startup_extended WHERE scope_decision='include'` como punto de
   partida, no `startups`.
2. `startups` queda como tabla legacy del schema sellado — no se borra (el
   schema está sellado), no se le agregan filas nuevas.
3. El check de health "Includes sin fila en tabla startups" deja de ser
   `[BAD]` y pasa a línea informativa `[i]` (ver `src/health.py`), señalando
   la decisión y apuntando a este documento.
4. Los **orphan entities** (57 — entidades `entity_type='startup'` sin fila en
   `startup_extended`, la tabla maestra real) siguen siendo un problema
   genuino y NO se tocan por esta decisión. Ese check sigue en rojo/warn
   hasta que el curador resuelva el triage (`quality/orphan_entities_triage.csv`,
   generado por `python pipeline.py orphan-triage`).
