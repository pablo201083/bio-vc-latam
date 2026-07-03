# Plan de ejecución — Fixes post-evaluación (julio 2026)

> **Para el agente ejecutor:** este plan es autocontenido. Sale de una evaluación completa
> del proyecto hecha el 2026-07-02 (dashboards en vivo + generadores Python + DB).
> Ejecutar las fases EN ORDEN — la Fase 1 cambia los datos de los que dependen las demás.
> Cada fase termina con verificación y un commit propio.

---

## Contexto mínimo del repo

- Proyecto: BIO LATAM Ecosystem Tracker. SQLite (`db/bio_latam.db`) es la fuente de verdad
  operativa; el pipeline Python (`src/`, orquestado por `pipeline.py`) genera bundles JS
  (`pilot/*-data.js`) que consumen dashboards HTML estáticos (`pilot/*.html`).
- Entorno: Windows / PowerShell. Activar venv antes de todo:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  o invocar directo: `.\.venv\Scripts\python.exe pipeline.py <cmd>`.
- Server local para verificar dashboards: `python -m http.server 4174` desde la raíz
  (las páginas viven en `http://localhost:4174/pilot/<page>.html`).

### Reglas intocables (leer antes de tocar nada)

1. **NO editar**: `startup_master_dataset.csv`, `canonical/manual_*.csv`,
   `schema_observatorio_biotech_v2.sql` (contrato sellado; extensiones → `db/migrations/`).
2. Todo UPDATE/DELETE a SQLite fuera de comandos existentes del pipeline debe registrarse
   vía `src/audit.py:diff_and_log_update()` (o al menos dejar rastro equivalente en `audit_log`).
3. Los 68 scripts PowerShell legacy en `scripts/` NO se borran.
4. La taxonomía de 8 temas está sellada. Este plan **corrige el nombre inconsistente de un
   tema en el código**, no cambia la taxonomía.
5. `quality/bio_definition_operativa.md` y `quality/data_contract.md` son governance — solo lectura.

### Estado de partida verificado (2026-07-02)

| Hecho | Valor |
|---|---|
| `pipeline.py validate` | **FALLA** — 13 investment edges con `investor_id` inexistente |
| `investment_edges` | 1.619 filas, pero solo **805 pares (investor, startup) únicos** |
| Pares con >1 edge y MISMO `round_stage` | **345** (duplicados genuinos, ej. `AIR Capital→aplife_biotech` ×3 con round_name `funding`) |
| Edges cuyo startup está excluded/missing | 156 (esperado: el atlas los poda; no tocar) |
| Nombre del tema en DB | `Biomanufacturing & Platform Technologies` (37 includes) |
| Nombre del tema en parte del código | `Biomanufacturing & Fermentation Economy` (¡no existe en la DB!) |
| `pilot/matchmaking-data.js` | Generado **2026-05-09**, taxonomía vieja pre-sellado, 283 startups (hoy 573), 23 fondos (hoy 129) |
| `pilot/startup-themes.js` | **Código muerto** — ningún HTML lo referencia (la lógica vive inline en `startup-themes.html`) |
| Bundles stale (>7d vs DB) | `capital-atlas-data.js`, `ecosystem-graph-data.js`, `ecosystem-health-data.js` |
| Outcomes en DB | 4 (meta ≥60) — no hay ground truth para calibrar el matchmaker |
| precision@5 matchmaker | 0.164 (meta ≥0.30) — ver `quality/score_calibration.json` |

---

## Fase 0 — Preparación

1. Crear branch: `git checkout -b fixes/evaluacion-julio`
2. Backup de la DB (fuera del repo o gitignored):
   ```powershell
   Copy-Item db\bio_latam.db db\bio_latam.backup-2026-07.db
   ```
   Verificar que `db/*.backup*` esté cubierto por `.gitignore`; si no, agregarlo.
3. Guardar baseline para comparar al final:
   ```powershell
   .\.venv\Scripts\python.exe pipeline.py validate > tmp\baseline_validate.txt 2>&1
   .\.venv\Scripts\python.exe pipeline.py health   > tmp\baseline_health.txt 2>&1
   ```
   (El `validate` baseline sale con exit code 1 — es el estado esperado de partida.)

---

## Fase 1 — Higiene de investment_edges

**Objetivo:** `pipeline.py validate` en verde y grafo de capital sin duplicados.
Es la fase con más impacto: degree, deal counts, sindicación, HHI y el Sankey del
Capital Atlas hoy cuentan filas infladas ~2×.

### 1.1 Triage de los 13 edges con investor_id roto

```sql
-- Identificarlos:
SELECT ie.investment_id, ie.investor_id, ie.startup_id, ie.round_name, ie.source_id
FROM investment_edges ie
LEFT JOIN entities e ON e.entity_id = ie.investor_id
WHERE e.entity_id IS NULL;
```

Para cada `investor_id` roto, decidir en este orden:
1. **¿Es un rename/merge?** Buscar en `entity_aliases` y en `entities` por nombre similar
   (ej. case distinto, guiones vs underscores). Si hay match claro → UPDATE del
   `investor_id` al canonical, registrando en audit_log. Existe precedente: el comando
   `merge-duplicate-entities` migra edges de ids PascalCase al slug canónico — revisar si
   correrlo resuelve varios de una vez (`python pipeline.py merge-duplicate-entities --dry-run`
   si soporta dry-run; si no, inspeccionar su código en `pipeline.py:344` antes).
2. **¿Es un inversor real que falta como entidad?** → crear entidad vía el flujo existente
   (`staging/new_investors.csv` + `python pipeline.py ingest-new-investors`), NO inserts a mano.
3. **¿Es basura sin recuperación?** → DELETE del edge con nota en audit_log.

### 1.2 Dedup de edges — CON ANÁLISIS PREVIO, NO A CIEGAS

Existe `python pipeline.py dedup-investment-edges` ("mismo investor+startup — mantiene la
de mayor prioridad"). **PRECAUCIÓN:** un mismo par investor→startup con `round_stage`
DISTINTO (seed y luego series-a) es legítimo y NO debe colapsarse.

1. Leer la implementación del comando (definida en `pipeline.py:337` →
   función en `src/`). Determinar si dedupea por par (investor, startup) a secas o por
   (investor, startup, round_stage).
2. **Si dedupea por par a secas:** modificarla (o crear variante) para que la clave sea
   `(investor_id, startup_id, COALESCE(round_stage,''))`. Mantener el criterio de prioridad
   existente para elegir la fila superviviente (mayor confidence / mejor source).
3. Ejecutar y registrar cuántas filas se eliminaron. Esperado: ~800 filas eliminadas
   (de 1.619 a un número cercano a 805 + pares multi-round legítimos).
4. Sanity check post-dedup:
   ```sql
   SELECT COUNT(*) FROM (
     SELECT investor_id, startup_id, COALESCE(round_stage,'') rs, COUNT(*) n
     FROM investment_edges GROUP BY 1,2,3 HAVING n>1);
   -- debe dar 0
   ```

### 1.3 Regenerar todo lo derivado de edges

```powershell
.\.venv\Scripts\python.exe pipeline.py build-atlas
.\.venv\Scripts\python.exe pipeline.py build-ecosystem-graph
.\.venv\Scripts\python.exe pipeline.py graph --refresh
.\.venv\Scripts\python.exe pipeline.py capital-structure
.\.venv\Scripts\python.exe pipeline.py ecosystem-health-data
.\.venv\Scripts\python.exe pipeline.py intelligence-data
```

### 1.4 Verificación de fase

- `python pipeline.py validate` → exit 0, "Investment edges con investor_id inexistente: OK".
- Abrir `http://localhost:4174/pilot/capital-atlas.html`: el KPI de edges baja de 1.418 a ~la
  cifra dedupeada; sin errores de consola; GridX sigue ~104 startups (la UI ya dedupeaba
  por startup, así que su count NO debería cambiar mucho — si cambia drásticamente,
  investigar antes de seguir).
- Commit: `fix(data): dedup investment_edges + repair 13 broken investor_ids`

---

## Fase 2 — Unificar el nombre del tema Biomanufacturing

**Objetivo:** un solo nombre canónico — el de la DB: **`Biomanufacturing & Platform
Technologies`** — en todo `src/` y en las listas hardcodeadas de los HTML.

**Bug actual:** la matriz de adyacencia temática del matchmaker
(`src/intelligence.py:74`) y otros módulos usan `Biomanufacturing & Fermentation Economy`,
que no existe en la DB. Resultado: las 5 adyacencias de biomanuf (0.45 con Food, 0.38 con
Biomaterials, 0.35 con Therapeutics, 0.25 con Diagnostics, 0.28 con Nature) devuelven
silenciosamente 0.0, degradando el scoring de `latent_potential()` para 37 startups y el
tema transversal del ecosistema.

### 2.1 Crear la constante compartida

En `src/vocabularies.py` (ya existe como módulo de vocabularios), agregar:

```python
# Los 8 temas sellados — nombre EXACTO como vive en startup_extended.bio_theme_primary.
BIO_THEMES = (
    "Bioinputs & Crop Resilience",
    "Precision Agriculture",
    "Nature & Ecosystem Tech",
    "Food Systems & Alt Proteins",
    "Biomanufacturing & Platform Technologies",
    "Biomaterials & Green Chemistry",
    "Therapeutics",
    "Diagnostics & Devices",
)
# Alias legacy → canónico (para ingestas viejas / código que aún lo emita)
BIO_THEME_ALIASES = {
    "Biomanufacturing & Fermentation Economy": "Biomanufacturing & Platform Technologies",
}
```

### 2.2 Corregir cada módulo que usa el nombre viejo

Ocurrencias verificadas de `Fermentation Economy` en `src/` (buscar con grep para
confirmar que no aparecieron más):

| Archivo | Línea aprox. | Qué corregir |
|---|---|---|
| `src/intelligence.py` | 74 | Clave del dict `_T` (adyacencia) → nombre canónico |
| `src/intelligence.py` | 340 | Clave del dict de keywords para org-matching → nombre canónico |
| `src/intro_builder.py` | 269 y 364 | Claves de dicts de keywords → nombre canónico |
| `src/clustering.py` | 98 | Tupla `("Biomanufacturing & Fermentation Economy", "precis")` → canónico |
| `src/clustering.py` | 1291 | Clave de dict → canónico |
| `src/reclassify_v2.py` | 49 | Entrada en lista de temas → canónico |

Donde sea razonable, importar `BIO_THEMES` / `BIO_THEME_ALIASES` desde `vocabularies`
en vez de re-declarar strings. Mínimo indispensable: que ningún dict tenga claves que no
existan en la DB.

### 2.3 Corregir las listas hardcodeadas en los dashboards

Síntoma visible hoy en `pilot/ecosystem-intelligence.html`: la sección "VERTICALES DEL
ECOSISTEMA" lista `Biomanufacturing & Fermentation Economy 0` y
`Digital AgTech & Agrifintech 0` junto a `Biomanufacturing 37` — la lista de labels está
hardcodeada y desincronizada de los datos.

1. Grep en `pilot/*.html` por `Fermentation Economy`: hay ocurrencias en
   `capital-atlas.html` (que ya lo trata como alias legacy y lo filtra — patrón correcto,
   dejarlo), `ecosystem-intelligence.html`, `startup-themes.html`, `biolatam-map.html`,
   `cluster-quality.html`, `ecosystem-graph.html`, `quality-tracker.html`.
2. En cada uno, decidir: si es un **alias-map** (traduce el nombre viejo por si aparece en
   datos) → conservar. Si es una **lista de temas para render** → debe salir de los datos o
   usar el nombre canónico; eliminar entradas fantasma que rendericen con count 0.
3. `Digital AgTech & Agrifintech` es un tema eco-adjacent (fuera del universo include, del
   split de Farm Intelligence de junio) — no debe aparecer en listas de verticales del
   universo include con count 0. Quitarlo de esas listas (mantenerlo donde se muestren
   eco-adjacent explícitamente).

### 2.4 Verificación de fase

- `grep -r "Fermentation Economy" src/` → solo debe quedar (a) el alias en
  `vocabularies.py` y (b) comentarios/documentación si los hubiera.
- Smoke test del scoring — la adyacencia debe ser ≠ 0 ahora:
  ```powershell
  .\.venv\Scripts\python.exe -c "from src.intelligence import _theme_overlap; print(_theme_overlap('Biomanufacturing & Platform Technologies','Food Systems & Alt Proteins'))"
  # esperado: 0.45 (antes: 0.0)
  ```
- Regenerar y recalibrar:
  ```powershell
  .\.venv\Scripts\python.exe pipeline.py intelligence-data
  .\.venv\Scripts\python.exe pipeline.py calibrate-scores
  ```
  Anotar el nuevo precision@5 en el mensaje de commit (baseline: 0.164). No se espera un
  salto a 0.30 — este fix quita un handicap, no reentrena nada.
- Abrir `ecosystem-intelligence.html`: la lista de verticales sin entradas con 0.
- Commit: `fix(themes): unify Biomanufacturing canonical name across src/ + dashboards`

---

## Fase 3 — Retirar matchmaking.html de circulación

**Objetivo:** que nadie llegue a recomendaciones de mayo con taxonomía muerta creyendo
que son actuales.

**Decisión tomada (no re-litigar):** NO regenerar `matchmaking-data.js`. El generador es un
script PowerShell legacy (`scripts/build_matchmaking_recommendations.ps1`) con un método
superado por `intelligence.py`. La herramienta de matching vigente es
`ecosystem-intelligence.html`.

1. En `pilot/index.html` (~línea 330): la card primaria "3. Relevancia accionable" que
   apunta a `matchmaking.html` debe pasar a apuntar a `ecosystem-intelligence.html`
   (ajustar título/descripción de la card a lo que realmente ofrece esa página).
2. Mover el link a `matchmaking.html` a la sección de tool-cards secundarias con
   `<span class="pill muted">Legacy</span>` — mismo patrón que ya usa `ecosystem.html`
   (ver `pilot/index.html:380`).
3. Dentro de `pilot/matchmaking.html`, agregar un banner fijo visible arriba:
   "⚠ Vista legacy congelada (datos 2026-05-09, taxonomía anterior). La herramienta
   vigente es Ecosystem Intelligence." con link. No hace falta tocar `matchmaking.js`.
4. NO borrar `matchmaking-data.js` ni `matchmaking.html` (referencia histórica, patrón del
   repo con legacy).

**Verificación:** abrir `index.html` → la card primaria 3 lleva a ecosystem-intelligence;
`matchmaking.html` muestra el banner. Commit:
`chore(pilot): freeze matchmaking.html as legacy, promote ecosystem-intelligence`

---

## Fase 4 — Frescura automática de bundles

**Objetivo:** que `pipeline.py rebuild` deje los bundles Y el cache-busting al día, sin
pasos manuales que se olvidan (hoy: `?v=20260623latam` editado a mano).

1. En `pipeline.py`, revisar `cmd_rebuild` (línea ~400): confirmar qué fases regeneran
   bundles JS. Asegurar que el rebuild completo incluya (o encadenar al final):
   `build-atlas`, `build-ecosystem-graph`, `ecosystem-health-data`, `intelligence-data`,
   `capital-structure`, `phylo-tree`.
2. Crear `src/bump_cache.py` con una función que:
   - Escanee `pilot/*.html` buscando `src="./<bundle>.js?v=..."` para los bundles generados.
   - Reemplace el valor de `?v=` por un hash corto (8 chars de sha1) del contenido actual
     del bundle. Idempotente: si el hash no cambió, no toca el HTML.
   - Se invoque automáticamente al final de cada comando que genera bundles (o al menos
     al final de `rebuild`), y también como comando suelto `python pipeline.py bump-cache`.
3. Correr `python pipeline.py rebuild` completo una vez y verificar:
   - `python pipeline.py health` → sección Frescura sin "Bundles JS desactualizados".
   - Los `?v=` de los HTML cambiaron a hashes.
   - Los 4 dashboards principales cargan sin errores de consola
     (`startup-themes.html`, `capital-atlas.html`, `ecosystem-intelligence.html`, `index.html`).

Commit: `feat(pipeline): auto cache-busting + bundles frescos en rebuild`

---

## Fase 5 — Limpieza

1. **Borrar `pilot/startup-themes.js`** (91KB, mayo): código muerto — `startup-themes.html`
   ya no lo referencia (verificar con grep antes de borrar; si algún HTML viejo lo
   referencia, evaluar ese HTML también).
2. **Triage SOSV**: en el atlas conviven `SOSV` (allocator, degree 6) y `SOSV_IndieBio`
   (fund, degree 14). Investigar en `entities` / `investment_edges` / `capital_relations`
   si son la misma entidad con doble identidad. Si IndieBio es el programa/fondo y SOSV el
   LP paraguas, puede ser legítimo — en ese caso documentar la relación con un edge en
   `capital_relations` (SOSV → SOSV_IndieBio) en lugar de merge. Si es duplicado puro →
   `merge-duplicate-entities` o merge manual auditado.
3. **Archivos sin commitear** (estado git al 2026-07-02): `data/`, `logs/`,
   `scripts/oneoff/fix_cluster_labels*.py`, `scripts/swarm_descriptions.py`,
   `scripts/write_descriptions.py`, `startup_master_dataset_pre_clean.csv`,
   `tmp_design_handoff/`. Regla:
   - `logs/` y `tmp_design_handoff/` → `.gitignore`.
   - `data/website_scrapes/` → es corpus regenerable por `scripts/enrich_profiles.py`;
     gitignorar salvo que el usuario haya dicho lo contrario.
   - Scripts oneoff y de swarm → commitearlos (son referencia del proceso, patrón del repo).
   - `startup_master_dataset_pre_clean.csv` → **PREGUNTAR AL USUARIO** antes de borrar o
     commitear (es un snapshot pre-limpieza de la fuente de verdad; no decidir solo).

Commit: `chore: remove dead startup-themes.js + repo hygiene`

---

## Fase 6 — Outcomes (preparación; el fill es humano)

Con 4 outcomes no hay ground truth: la calibración del matchmaker mide contra portfolios
existentes y premia fondos chicos (los top de `quality/score_calibration.json` tienen
portfolio 3-4; GridX con 104 da precision@5 = 0.029). **No invertir más en tuning del
algoritmo hasta tener ≥60 outcomes.**

Lo que SÍ puede hacer el agente:
1. Generar una cola de captura priorizada: las ~50 startups include con mayor
   degree/pagerank y `funding_stage` ≥ seed que NO tengan outcome registrado, con columnas
   (startup, país, tema, inversores actuales, última señal, URL fuente sugerida) →
   `quality/outcomes_capture_queue.csv`.
2. Documentar en ese CSV el formato esperado por `staging/outcomes_incoming.csv` para que
   el curador solo tenga que llenar y correr `python pipeline.py ingest-outcomes`.
3. NO usar agentes/LLM para inventar outcomes — regla del repo: outcomes se cargan
   manualmente con fuente.

Commit: `feat(quality): outcomes capture queue`

---

## Cierre — Verificación global

1. `python pipeline.py validate` → exit 0, sin errores (warnings de conflictos 21 y
   clusters metodológicos 71 son conocidos y quedan fuera de este plan).
2. `python pipeline.py health` → comparar contra `tmp/baseline_health.txt`. Deben mejorar:
   edges rotos (0), bundles stale (0). Deben quedar iguales o mejor: el resto.
3. Los 4 dashboards cargan sin errores de consola y con datos consistentes entre sí
   (mismo total de startups include en startup-themes, capital-atlas y
   ecosystem-intelligence).
4. `git log --oneline` → un commit por fase, mensajes según lo indicado.
5. Reportar al usuario: filas dedupeadas, resolución de los 13 edges, nuevo precision@5,
   y cualquier decisión que haya quedado pendiente de su input (ej. el CSV pre_clean).

### Fuera de alcance (NO hacer en esta pasada)

- Resolver los 21 conflictos theme↔cluster ni los 71 startups en clusters quality=0
  (requieren criterio del curador; ya tienen triage CSV propio).
- Extraer el JS inline de `startup-themes.html` / `capital-atlas.html` a módulos
  (refactor grande, sesión aparte).
- Rediseñar el scoring del matchmaker o tocar `_rescale_scores` (primero outcomes).
- El gap de schema startups vs startup_extended (315 filas) — decisión de arquitectura
  pendiente del usuario.
