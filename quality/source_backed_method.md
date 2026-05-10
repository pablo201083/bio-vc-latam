**Source-Backed Standard**
La base debería considerar como estándar mínimo que cada startup tenga al menos una fuente externa auditable.

**Orden correcto**
- fuente externa
- resumen mínimo
- decisión de scope
- taxonomía

**Estados propuestos**
- `source_backed_reviewed`
  Hay `source_url` y el perfil fue curado manualmente.
- `source_backed_seeded`
  Hay `source_url` y ya existe una buena semilla de información, pero todavía no hubo curaduría completa.
- `source_backed_minimum`
  Hay `source_url`, pero el perfil todavía no está editorialmente trabajado.
- `missing_external_source`
  No hay URL fuente; la startup sigue sostenida por análisis endógeno o estructura heredada.

**Implicancias**
- `taxonomy_stub` puede seguir existiendo como estado interno de cobertura, pero no debería ser la base pública de la taxonomía.
- El objetivo inmediato es vaciar `include + missing_external_source`.
- La taxonomía v2 debería reconstruirse principalmente a partir de startups `source_backed_reviewed` y `source_backed_seeded`.

**Artefactos**
- [source_backed_coverage.csv](C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_backed_coverage.csv)
- [source_backed_coverage.md](C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_backed_coverage.md)
- [source_backed_priority_queue.csv](C:\Users\Pablo A\Documents\Codex\2026-04-18-summarize-what-s-happening-on-slack\quality\source_backed_priority_queue.csv)
