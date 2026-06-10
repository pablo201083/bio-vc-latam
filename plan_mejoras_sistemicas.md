# Plan de Mejoras Sistémicas — BIO VC LATAM Ecosystem Tracker

**Fecha:** 2026-06-10 · **Ejecutor previsto:** Claude Opus 4.6 · **Horizonte:** 8–12 sesiones

## El espíritu del proyecto (de dónde sale este plan)

El proyecto no es una base de startups: es infraestructura de inteligencia ecosistémica para
hacer que el universo BIO de América Latina sea **reconocible, buscable, analizable, invertible
y accionable** (`quality/project_context_from_pitch.md`). El flywheel es Map → Understand →
Connect → Amplify. Las cuatro preguntas que el sistema tiene que responder bien:

1. **¿Quién existe y qué es?** — taxonomizar y clasificar el ecosistema bio.
2. **¿Cómo se financia?** — entender la estructura de inversión real.
3. **¿Quiénes son los actores clave?** — fondos, builders, instituciones, puentes.
4. **¿Cómo se muestra?** — visualizaciones que respondan preguntas, no que decoren.

Y una condición de honestidad que atraviesa todo: **los datos se recolectaron por parches**
(barridos de portfolios accesibles, batches de curación, oleadas por país). El mapa hoy refleja
en parte *dónde se buscó*, no solo *qué existe*. Un observatorio que no distingue "no hay" de
"no miramos" pierde credibilidad. Hacer visible y corregible ese sesgo es mejora sistémica
número uno.

## Diagnóstico medido (2026-06-10, contra la DB en vivo)

**Pregunta 1 — Clasificación.** Sólida pero con deuda: 496 includes, 8 temas, 100% con tema
asignado. Pero `validate` reporta 92 startups cuyo `bio_theme` contradice su cluster semántico
(19% del universo) y 80 en clusters metodológicos con quality=0. El mapa principal se
contradice a sí mismo en ~1 de cada 5 puntos.

**Pregunta 2 — Estructura de inversión.** El grafo es topológico, no estructural:
- 680 aristas de inversión, 538 con fuente (79%, bien) — pero solo **142 con fecha (21%)** y
  **66 con monto (10%)**. Se sabe *quién* invirtió en *quién*; casi nunca *cuándo* ni *cuánto*.
  Sin eso no hay cohortes, ni velocidad de deploy, ni tamaño relativo de actores, ni tendencia.
- 143 includes (29%) tienen **cero** aristas de capital: indistinguible "no levantó" de
  "no lo mapeamos".
- Capa institucional casi vacía: 26 capital_relations (LP→fondo), outcomes=4.

**Pregunta 3 — Actores clave.** 143 inversores, 143 tipados, 95 con tesis (66%). Pero la
centralidad medida está contaminada por el método de recolección: GridX concentra 116/680
aristas (17%) porque su portfolio se barrió exhaustivamente; fondos brasileños y mexicanos
pesan poco porque se barrieron menos. PageRank sobre este grafo rankea esfuerzo de curación,
no influencia real.

**Pregunta 4 — Mostrar.** 9+ vistas funcionando (themes, atlas, matchmaker, graph, profiles,
quality). Lo que falta no son más vistas: es que las vistas declaren cobertura y que exista
una capa de **lectura** (qué significa lo que se ve) además de la capa de exploración.

**El parche-sesgo, cuantificado:** AR=149 includes vs BR=68, MX=11, CO=9, PE=1. Brasil es la
mayor bioeconomía de la región y acá pesa menos de la mitad que Argentina. Las fuentes son 60%
official_website + portfolio profiles — es decir, la base creció siguiendo portfolios de fondos
accesibles (sesgo: solo startups ya financiadas por fondos conocidos entran fácil).

---

## Principios de ejecución (no negociables)

1. Todo UPDATE a SQLite pasa por `src/audit.py:diff_and_log_update()`.
2. Intocables: `startup_master_dataset.csv`, `canonical/manual_*.csv`,
   `quality/data_contract.md`, `schema_observatorio_biotech_v2.sql`. Extensiones de schema →
   `db/migrations/`.
3. Los emisores de JS viven en `src/`; nunca editar `pilot/*-data.js` a mano.
4. Nada de inferencia endógena disfrazada de fuente: dato nuevo = `source_id` con URL y tipo.
5. Cada sesión cierra con `python pipeline.py validate` limpio y el dashboard afectado
   **abierto y mirado**.
6. Mínima entidad canónica: nunca duplicar GridX, SF500, Puna Bio, etc.; usar aliases.

---

## Frente A — Honestidad de cobertura: convertir "parches" en mapa de cobertura (1–2 sesiones)

*El cimiento. Sin esto, todo análisis hereda el sesgo de recolección sin declararlo.*

1. **Registro de barridos.** Crear `quality/coverage_ledger.csv`: una fila por parche de
   recolección histórico (portfolio sweep de GridX, batch Brasil, oleada Gemini, etc.) con
   método, fecha, alcance y qué porción de la base produjo. Reconstruible desde `audit_log`
   (13.670 entradas fechadas) + los CSVs de `quality/` que documentan cada batch.
2. **Score de cobertura por celda tema×país.** Nuevo comando `pipeline.py coverage`
   (módulo `src/coverage.py`): para cada celda, # startups, # con fuente confirmada, # fondos
   locales barridos vs. conocidos, y una etiqueta honesta: `bien_mapeado` / `parcial` /
   `no_explorado`. Salida: `pilot/coverage-data.js` + tabla en quality/.
3. **Cobertura visible en producto.** En startup-themes y capital-atlas, las celdas/regiones
   `no_explorado` se muestran distinto (trama, nota al pie, tooltip "zona poco barrida").
   La ausencia deja de leerse como inexistencia.
4. **Cola de des-sesgo dirigida.** El score de cobertura genera automáticamente la cola de
   curación: hoy saldría "Brasil: barrer Fundo Vale, Antera, Baraúna, KPTL completo, Bossanova
   bio-subset; México: barrer DUX, Angel Ventures bio-subset". Cada sesión de curación futura
   ataca la celda más sesgada, no la más cómoda. Meta direccional: BR ≥ 120 includes antes de
   declarar el mapa "regional".

**Aceptación:** coverage ledger poblado; toda vista de producto declara cobertura; existe una
cola priorizada de des-sesgo con ≥20 objetivos concretos por fuente.

## Frente B — Clasificación que no se contradiga (1–2 sesiones)

*La taxonomía es el producto intelectual central: tiene que aguantar el escrutinio de un
inversor que conoce el sector.*

1. **Triage de los 92 conflictos theme↔cluster.** CSV de triage con decisión por caso:
   el cluster está mal (→ override auditable en `quality/manual_semantic_theme_overrides.csv`),
   el tema está mal (→ `reclassify-themes`), o el summary es ambiguo (→ reescritura con señales
   temáticas + `rebuild --phase embeddings`). Heurística: con fuente externa confirmada y
   distancia < 3.0 al centroide, sospechar del label; si es taxonomy_stub, del summary.
2. **Resolver los 62 orphan entities** (`merge-duplicate-entities --dry-run` → clasificar →
   ejecutar). Cada huérfano es un posible duplicado contando doble en el mapa.
3. **Decisión por cluster para los 80 quality=0**: clusters con ≥3 temas mezclados son problema
   de parámetros, no de 80 curaciones manuales. Evaluar splits solo si la confianza media del
   cluster mejora >10%.
4. **Ficha de taxonomía para afuera.** Un `taxonomy_card.md` por tema (8 en total): definición,
   fronteras con temas vecinos, 5 startups arquetípicas, qué queda explícitamente afuera.
   Es el artefacto que hace la taxonomía *legible para terceros* (objetivo del pitch) y a la
   vez el estándar contra el que se valida cada clasificación futura.

**Aceptación:** conflictos < 25 con los restantes documentados como excepciones; orphans < 15;
8 fichas de tema publicadas y linkeadas desde startup-themes.html.

## Frente C — Estructura de inversión real: agregar tiempo y magnitud (2–3 sesiones)

*De "quién conoce a quién" a "cómo fluye el capital".*

1. **Campaña dirigida de fechas y montos.** No intentar el 100%: enriquecer `announced_date` +
   `amount` para las aristas de los **top 15 inversores por grado** (≈ 450 de las 680 aristas)
   desde fuentes públicas (notas de prensa, LAVCA, Crunchbase público, anuncios de los fondos).
   Flujo existente: `staging/` + `ingest-rounds` / `enrich-rounds-valuation`. Meta: fecha ≥ 60%
   (hoy 21%), monto ≥ 30% (hoy 10%).
2. **Resolver el limbo de las 143 sin capital.** Para cada include sin aristas, una pasada
   binaria barata: `bootstrapped/grant-funded` (con fuente), `funded_but_unmapped` (se encontró
   ronda → ingestar la arista), o `unknown` (queda marcada). Convierte un agujero en dato.
3. **Outcomes como capa de realidad.** outcomes=4 es la tabla más pobre del sistema. Poblar
   `staging/outcomes_incoming.csv` con rondas/exits/cierres públicos verificables (meta ≥60),
   priorizando los actores del top 15. Sin outcomes no hay manera de saber si el mapa describe
   un ecosistema vivo o un catálogo.
4. **Análisis que esto desbloquea** (emitir como `src/capital_structure.py` →
   `pilot/capital-structure-data.js`):
   - **Cohortes**: startups por año de primera ronda; tiempo seed→serie A por tema.
   - **Pirámide de stages por tema**: dónde hay base sin cúspide (señal del "valle" que el
     pitch identifica como cuello de botella central: capital insuficiente para madurar).
   - **Dependencia del capital extranjero** por tema (% aristas de inversores no-LATAM).
   - **Sindicación**: con quién co-invierte cada fondo; pares de tesis solapada que nunca
     co-invirtieron.
5. **Capa LP/institucional.** Expandir `capital_relations` (26 hoy) con allocators públicos:
   BNDES, IDB Lab, CAF, Bancóldex, CORFO, family offices documentados. Vía
   `ingest-capital-allocators`. Es la parte de la estructura de inversión que decide si el
   ecosistema escala, y hoy es invisible.

**Aceptación:** fecha ≥60% / monto ≥30% en aristas del top 15; las 143 huérfanas clasificadas;
≥60 outcomes; ≥60 relaciones LP→fondo; el análisis de cohortes y pirámide corre end-to-end.

## Frente D — Actores clave, medidos sin el sesgo de recolección (1–2 sesiones)

1. **Centralidad ajustada por cobertura.** Recalcular PageRank/grado ponderando por el
   coverage score del Frente A (o reportando junto a cada ranking la nota "X% del portfolio de
   este actor está barrido"). GridX no debe rankear 3× por haber sido 3× mejor barrido.
2. **Tipología funcional de actores.** Con fecha+monto (Frente C) se puede clasificar por
   *comportamiento observado*, no por autodescripción: venture builder / fondo temático /
   generalista con apetito bio / aceleradora / institucional. Persistir en `investors` y usarla
   en atlas y matchmaker.
3. **Actores estructurales:** explotar lo ya computado (134 bridges, 27 bottlenecks, 73
   whitespace) como capa narrada: ¿qué fondos son el único puente entre dos comunidades?
   ¿qué institución sostiene un tema entero? Emitir como sección "Key Actors" con evidencia.
4. **Completar tesis** de los 48 inversores sin ella (95/143 hoy), priorizando por grado.

**Aceptación:** ranking de actores con nota de cobertura; tipología funcional asignada a los
top 30; tesis ≥ 85%; sección Key Actors visible en producto.

## Frente E — Mostrar: capa de lectura sobre la capa de exploración (2 sesiones)

*Las vistas actuales exploran bien. Falta la capa que cuenta qué significa.*

1. **`pilot/state-of-bio.html` — la vista síntesis.** Una sola página que responde las cuatro
   preguntas con los datos de los frentes A–D: el universo por tema (con cobertura declarada),
   la pirámide de capital, los actores clave tipificados, y los 5–10 hallazgos vigentes. Es la
   página que se le muestra a un inversor o policymaker en 5 minutos; hoy esa página no existe.
2. **Hallazgos generados, no manuales.** `pipeline.py insights` (módulo `src/insights.py`):
   reglas tipadas sobre lo ya computado — whitespace tema×país con cobertura alta (¡vacío real,
   no parche!), startups de calidad alta sin capital mapeado, temas con base ancha y cúspide
   vacía, dependencia extranjera extrema, puentes frágiles. Cada hallazgo: qué / por qué
   importa / acción / evidencia (IDs + fuentes). El cruce con coverage es lo que distingue este
   motor de una lista de queries: solo afirma "falta X" donde el mapa está bien barrido.
3. **Flujo de capital (Sankey):** LP → fondo → tema → país, cuando el Frente C.5 tenga masa.
4. **Performance:** partir `matchmaking-data.js` (3.8 MB) e `intelligence-data.js` (2.2 MB) —
   vectores a fetch lazy, metadatos en bundle chico (< 1 MB inicial). Cambios en los emisores
   de `src/`.

**Aceptación:** state-of-bio.html responde las 4 preguntas en una pantalla con datos vivos;
≥20 hallazgos con evidencia y filtro de cobertura; bundles iniciales < 1 MB.

## Frente F — Gobernanza del crecimiento (transversal, barato)

1. **`pipeline.py health`:** semáforo de una pantalla — counts, % fuentes, % fecha/monto,
   conflictos abiertos, edad de embeddings vs. summaries, celdas no_explorado. "¿Puedo confiar
   en el sistema hoy?" en 5 segundos.
2. **Drift de clusters:** tras cada `rebuild --phase clustering`, diff contra la corrida
   anterior (`quality/cluster_drift_report.csv`); >10% de reasignaciones bloquea la
   regeneración de JS de producto hasta revisión.
3. **CLAUDE.md actualizado** con cada comando nuevo (coverage, insights, health).

---

## Secuencia recomendada

| Sesión | Frente | Por qué este orden |
|--------|--------|--------------------|
| 1–2 | A (cobertura) + F.1 (health) | Sin mapa de cobertura, todo análisis posterior miente por omisión |
| 3 | B (clasificación) | La taxonomía es la cara del producto; deuda acotada y medible |
| 4–6 | C (estructura de inversión) | El frente más caro y el de mayor retorno estratégico: tiempo + magnitud |
| 7 | D (actores clave) | Necesita C (comportamiento) y A (ajuste por cobertura) |
| 8–9 | E (state-of-bio + insights) | Cosecha todo lo anterior en la capa de lectura |
| 10+ | E.3–E.4 + F.2 | Sankey cuando haya masa LP; performance y drift como cierre |

**Regla de corte:** cada sesión termina un entregable con su criterio de aceptación verificado
antes de abrir el siguiente. Cierre estándar: `validate` limpio, dashboard mirado, commit
convencional (feat/fix/chore + scope).
