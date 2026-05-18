# Sistema de Clasificación y Representación Visual — Decisiones de Diseño

Documento vivo. Captura decisiones base, principios y aprendizajes experimentales
para el pipeline de clasificación semántica y visualización del ecosistema BIO LATAM.

Actualizado: 2026-05-17 | Estado corpus: 490 startups `include`, 24 clusters, 9% noise

---

## 1. Taxonomía bio_theme_primary

### Los 8 temas (contrato sellado)

| bio_theme_primary                      | macro_theme (embedding)                            |
|----------------------------------------|----------------------------------------------------|
| Therapeutics                           | therapeutics and regenerative medicine             |
| Diagnostics & Health Access            | diagnostics and medtech                            |
| Bioinputs & Crop Resilience            | ag biologicals and crop resilience                 |
| Food Systems & Alt Proteins            | food biotech and novel ingredients                 |
| Nature & Ecosystem Tech                | climate, energy and resource systems               |
| Farm Intelligence                      | precision agriculture and resource intelligence    |
| Biomaterials & Circular Economy        | biobased chemistry and advanced materials          |
| Biomanufacturing & Fermentation Economy| biomanufacturing and bioindustrial platforms        |

### Criterios de inclusión en el universo bio (`scope_decision = 'include'`)

Entra si tiene **al menos una** de estas señales materiales:
- Materialidad bio-based (bacteria, enzimas, tejidos, células, organismos)
- Enfoque biocéntrico (opera sobre sistemas vivos como unidad de análisis)
- Software acoplado materialmente a bio/agri/materiales/clima (no SaaS horizontal)
- Regeneración dentro de límites planetarios con impacto material claro

Sale (`exclude`) si es:
- SaaS generalista sin acople material (ERP, CRM, fintech, e-commerce)
- Logística, flete, frío comercial sin tecnología bio
- Drones, EVs, solar sin biology stack
- Plataformas de datos sin acople específico a bio o agri

Queda en `review` si:
- No hay evidencia suficiente en la descripción disponible
- Aparece en `Other / Unclassified` y requiere curaduría humana
- Podría tocar clima, materiales o regeneración pero no está bien descrita

### Regla de peso de evidencia

`reviewed + source_url` > `seeded + source_url` > `structured_sector` > `taxonomy_stub sin URL`

---

## 2. Pipeline de clasificación (flujo de datos)

```
Fuente externa (GRIDX, manual) 
    → scripts/enrich_gridx_import.py  [Claude Haiku 4.5 — clasifica is_bio + bio_theme + summary]
    → staging/entity_enrichments.csv  [CSV de staging, append]
    → python pipeline.py ingest-entity-enrichments
    → startup_extended (SQLite)
    → python pipeline.py rebuild --phase embeddings
    → python pipeline.py rebuild --phase clustering
    → pilot/startup-themes-data.js    [exportado para el dashboard]
```

### Regla de staging CSV

- Nunca editar `startup_extended` directamente — siempre pasar por `staging/entity_enrichments.csv`
- El ingest pasa por `src/audit.py:diff_and_log_update()` para garantizar audit_log
- `scope_reason` NO se actualiza durante ingest (solo `scope_decision`). Siempre usar `=` exacto en WHERE, no `LIKE`

---

## 3. Sistema de embeddings

### Modelo
`intfloat/multilingual-e5-large-instruct` — vectores de 1024 dims. Prefijo `passage:` para documentos.

### Composición del texto (`make_embed_text`)

```python
parts = [
    summary,          # campo principal
    summary,          # ×2 — doble peso, los modelos e5 son sensibles a frecuencia de tokens
    business_one_liner,
    macro_theme,
    emergent_theme,
    technical_stack,
    technology_tags,
    industry_destination,
    domain_tags,
    bio_lens_tags,
    scale_tags,
]
body = " | ".join(p for p in parts if p)
return f"passage: {body}"
```

### Regla de truncamiento de summary

El summary se trunca a `SUMMARY_MAX_CHARS` (aprox. 300 chars) para evitar que la
longitud de descripción domine el espacio de embedding. Sin truncamiento,
`r(len, umap_x)` alcanzó +0.73 en Cluster 3 (Ag Biologicals) — la longitud del texto
se convierte en una señal espuria que separa startups con buena vs. mala documentación.

### Cobertura de campos (baseline 2026-05-17)

| Campo              | Originales (373) | Nuevas GRIDX (117) |
|--------------------|:-----------------:|:------------------:|
| startup_summary_en | 100%              | 100%               |
| macro_theme        | 100%              | 100% (lookup)      |
| bio_lens_tags      | ~72%              | 100% (lookup)      |
| emergent_theme     | ~80%              | 0% ← deuda técnica |
| technical_stack    | ~76%              | 0% ← deuda técnica |
| domain_tags        | ~76%              | 0% ← deuda técnica |
| technology_tags    | ~76%              | 0% ← deuda técnica |
| business_one_liner | ~75%              | 0% ← deuda técnica |

**Las 117 nuevas tienen 194 chars promedio de summary vs. 307 de las originales.** Esta
asimetría de señal hace que UMAP las trate como ciudadanos de segunda clase en el
espacio vectorial. La solución correcta es `src/enrich_periphery.py` con API key.

---

## 4. UMAP 2D — visualización semi-supervisada por super-tema

### El problema que motivó este diseño

Farm Intelligence (agtech) y Diagnostics & Health Access (medtech) compartían vocabulario
genérico ("AI", "platform", "precision", "monitoring") sin señal de dominio específica.
El UMAP 2D puramente semántico los proyectaba como vecinos (dist≈7.0), aunque el
clustering 5D los separaba correctamente. La vecindad 2D era un artefacto de proyección.

### Solución: UMAP semi-supervisado por super-tema

El UMAP 2D toma `bio_theme_primary` como señal de guía, pero agrupando los 8 temas
en 3 **super-temas** en lugar de tratarlos como 8 categorías separadas:

```python
_SUPER_THEME = {
    "Therapeutics":                            "health",
    "Diagnostics & Health Access":             "health",
    "Bioinputs & Crop Resilience":             "agri",
    "Food Systems & Alt Proteins":             "agri",
    "Farm Intelligence":                       "agri",
    "Nature & Ecosystem Tech":                 "agri",
    "Biomaterials & Circular Economy":         "materials",
    "Biomanufacturing & Fermentation Economy": "materials",
}
VIZ_LABEL_WEIGHT = 0.35  # 35% label-guidance, 65% embedding semántico
```

El UMAP clustering (10D) **no cambia** — sigue siendo 100% semántico.
Solo el UMAP de visualización (2D) usa la guía.

### Por qué super-temas y no los 8 temas directos

Con los 8 temas como guía, UMAP separa TODO por igual y rompe vecindades correctas
(Farm se aleja de Nature, que DEBERÍA estar cerca). Con super-temas, UMAP separa los
macro-grupos (agri lejos de health) pero respeta vecindades dentro del grupo.

| Par                 | Antes | 8-temas | super-temas | Objetivo |
|---------------------|------:|--------:|------------:|----------|
| Farm ↔ Diagnostics  |   7.0 |    17.4 |        31.3 | separar  |
| Farm ↔ Nature       |   4.3 |    13.8 |         3.5 | juntar   |
| Bioinputs ↔ Food    |   2.4 |     8.6 |         3.6 | juntar   |
| Ther ↔ Diagnostics  |  12.1 |    16.7 |         9.6 | juntar   |

### Biomanufacturing como super-grupo libre (sin etiqueta)

Biomanufacturing es una tecnología de plataforma transversal: sirve a pharma, food y
materiales según la startup. Asignarla a "materials" la alejaba de Therapeutics
artificialmente. La solución: dejarla sin super-tema (`y=-1` en UMAP) para que su
posición emerja de la similitud semántica. Resultado: Biomanufacturing flota en el
centro del mapa, equidistante de health, agri y materials — que es donde pertenece.

**Caso Stämm**: diagnosticado como "lejos de Therapeutics". Root cause: dos entidades
duplicadas (`stamm` y `stamm-ar`), la segunda con datos vacíos y `scope_reason=None`.
Fix: `scripts/merge_duplicate_entities.py` excluyó el duplicado y migró sus
investment_edges. Stämm quedó a dist=10.2 de Therapeutics — correcto porque es una
plataforma de biorreactores transversal, no un therapeutic puro.

**Fingerprint de duplicados históricos**: `scope_reason=NULL` + `valuation_estimate_usd=4.0`
+ sufijo de país en entity_id (`-ar`, `-br`, `-mx`). Buscarlos con:
```sql
SELECT entity_id, canonical_name FROM entities e
JOIN startup_extended se ON se.startup_id=e.entity_id
WHERE se.scope_decision='include' AND se.scope_reason IS NULL
  AND (e.entity_id LIKE '%-ar' OR e.entity_id LIKE '%-br' OR e.entity_id LIKE '%-mx')
```

### Regla de ajuste futuro

Si un nuevo par de temas aparece visualmente cerca sin razón semántica:
1. Verificar si están en el mismo super-grupo (puede ser correcto)
2. Si son grupos distintos, aumentar `VIZ_LABEL_WEIGHT` hacia 0.5
3. Si son el mismo grupo pero deberían separarse, dividir el super-grupo
4. Antes de tocar UMAP, verificar que no haya duplicados ni datos vacíos en esas startups

---

## 5. HDBSCAN — Parámetros y reglas de ajuste

### Parámetros actuales

```python
HDBSCAN_PARAMS = {
    "min_cluster_size": 6,   # produce ~14-24 clusters con 490 startups
    "min_samples": 3,
    "metric": "euclidean",
    "cluster_selection_method": "eom",
}
```

### Regla de escala

`min_cluster_size` debe escalar aproximadamente con `sqrt(N/20)`, donde N es el corpus.

| N startups | min_cluster_size recomendado |
|:----------:|:----------------------------:|
| 373        | 6                            |
| 490        | 6–8                          |
| 700+       | 10                           |

Con 490 startups y `min_cluster_size=10` el resultado fue peor (super-cluster de 173
startups con todas las bio_themes mezcladas). Volver a 6 produce ~14 clusters bien
separados y ~9% noise.

### UMAP — dos configuraciones separadas

| Config              | n_neighbors | min_dist | Uso                              |
|---------------------|:-----------:|:--------:|----------------------------------|
| clustering (interno)| 12          | 0.05     | Reducción a 5D para HDBSCAN      |
| visualización (2D)  | 15          | 0.15     | SVG en el dashboard              |

Nunca usar la misma configuración para ambas. El 2D necesita más dispersión (min_dist
más alto) para que los clusters sean visualmente legibles. El clustering interno necesita
mayor compacidad (min_dist bajo) para que HDBSCAN encuentre bordes nítidos.

---

## 5. Representación visual (dashboard `pilot/startup-themes.html`)

### Tamaño de dot — escala lineal

```js
const VAL_R_MIN = 5;   // radio mínimo en px (startup sin valuation conocida)
const VAL_R_MAX = 30;  // radio máximo en px (startup con valuation >= $100M)
const VAL_CAP   = 100; // cap en $M — encima de esto no crece más

function nRadius(s) {
    const v = s.valuation_estimate_usd || 0.8;
    return VAL_R_MIN + (VAL_R_MAX - VAL_R_MIN) * Math.min(v, VAL_CAP) / VAL_CAP;
}
```

**Principio**: escala lineal sobre el rango $0–$100M. El cap en $100M evita que los
outliers de alto funding aplasten la señal visual del resto. El default `0.8` para
startups sin datos crea dots mínimos visibles sin inflar el tamaño.

### Estrategia de etiquetas

```js
// Siempre visible (independiente del toggle "Nombres")
function nFeatured(s) {
    return (s.valuation_tier != null && s.valuation_tier >= 2)
        || (s.valuation_estimate_usd || 0) >= 50;
}

// Visible cuando el toggle está activo
function nLabeled(s) {
    return s.quality_band === "high"
        || (s.valuation_estimate_usd || 0) >= 15;
}
```

**Principio**: 182/373 startups originales tenían `valuation_tier = NULL` — usar solo
ese campo como criterio excluía el 49% del corpus. El criterio combinado
(`quality_band` OR `valuation_estimate_usd`) es más robusto.

**Posición de etiqueta**: `y = n.cy`, `dominant-baseline: middle` — centrado vertical
dentro del dot. NO desplazar hacia abajo (confunde lectura visual).

### Colores por bio_theme

Constante en `pilot/startup-themes.html`. Cualquier cambio debe ser consistente con
los 8 temas del contrato sellado.

---

## 6. Reglas de no-hacer (aprendidas experimentalmente)

### ❌ No derivar `emergent_theme` de `cluster_label` del run anterior

Crea una **dependencia circular**: los embeddings del run anterior determinan los
clusters, cuyos labels se usan como `emergent_theme`, que cambia los embeddings del
próximo run. Resultado observado: outliers suben de 66 → 99. La señal de `emergent_theme`
debe venir de curaduría humana o de una fuente externa (enrich_periphery con API).

### ❌ No usar keyword matching amplio para `technology_tags`

El matching de keywords como "AI", "machine learning", "sensor" sobre el summary
spread "ai-data" a demasiadas startups de forma no discriminativa. Resultado observado:
outliers suben de 99 → 121. `technology_tags` debe venir de curaduría o de LLM
con control de calidad por startup.

### ❌ No usar la primera oración del summary como `business_one_liner`

Los summaries de las 117 nuevas (generados por LLM con prompt de 2-3 oraciones)
tienen primeras oraciones de 157 chars promedio vs. 45 chars de los curados a mano.
La asimetría de longitud crea un sesgo adicional en el embedding.
`business_one_liner` debe ser la versión editorial corta, no una extracción automática.

### ❌ No usar `scope_reason LIKE 'gridx_import%'` 

El campo `scope_reason` no se actualiza durante el ingest de enrichments — solo
`scope_decision`. Usar `LIKE` para matchear variantes que no existen produce 0 rows
silenciosamente. Siempre usar `= 'gridx_import'` (valor exacto asignado en el import).

### ❌ No aumentar `min_cluster_size` excesivamente para reducir noise

Con 490 startups, pasar de `min_cluster_size=6` a `10` no redujo noise — creó un
super-cluster de 173 startups que absorbió todos los bio_themes. El noise del 9%
con `min_cluster_size=6` es aceptable y refleja genuina ambigüedad semántica.

---

## 7. Marco de explicabilidad visual

### Principio

**Toda vecindad en el mapa 2D debe poder ser explicada.** Si dos clusters o grupos de
temas están cerca y no podemos articular por qué, es una señal de alerta — puede ser:

1. **Semántica real no obvia**: compartir vocabulario técnico legítimo (investigar antes de "corregir")
2. **Artefacto de proyección UMAP 2D**: dos grupos bien separados en 5D que UMAP comprime en el mismo lugar
3. **Problema de datos**: texto genérico sin señal específica de dominio que confunde el embedding

La fuente de verdad sobre similitud real es **el clustering en 5D** (HDBSCAN), no las posiciones 2D.
La visualización 2D es una aproximación útil pero con limitaciones inherentes.

### Topología esperada del mapa (qué debería estar cerca de qué)

| Tema                                    | Vecinos esperados                              | Razón                                |
|-----------------------------------------|------------------------------------------------|--------------------------------------|
| Therapeutics                            | Diagnostics (salud), Biomanufacturing          | plataformas terapéuticas + bio-tools |
| Diagnostics & Health Access             | Therapeutics, Biomanufacturing                 | medtech, life-science tools          |
| Bioinputs & Crop Resilience             | Food Systems, Farm Intelligence                | agri-bio, insumos para cultivos      |
| Food Systems & Alt Proteins             | Bioinputs, Biomanufacturing, Biomaterials      | ingredientes, proteínas alternativas |
| Farm Intelligence                       | Nature & Ecosystem Tech, Bioinputs             | agtech: datos + insumos              |
| Nature & Ecosystem Tech                 | Farm Intelligence, Biomaterials                | ecosistemas, recursos, circularidad  |
| Biomaterials & Circular Economy         | Biomanufacturing, Nature                       | materiales bio-basados               |
| Biomanufacturing & Fermentation Economy | Therapeutics, Biomaterials, Food              | plataformas de producción bio        |

Cualquier vecindad que **contradiga esta topología** debe investigarse antes de aceptarse.

### Checklist de calidad visual (aplicar cada vez que se reconstruye el clustering)

1. ¿Therapeutics y Diagnostics están en la misma región del mapa?
2. ¿Farm Intelligence está cerca de Nature & Ecosystem Tech?
3. ¿Bioinputs está cerca de Food Systems?
4. ¿Biomanufacturing está cerca de Therapeutics / Biomaterials?
5. ¿Hay algún bio_theme en una posición que contradice la tabla anterior?

Si alguna respuesta es "no", investigar si es artefacto 2D o problema de datos.

---

## 8. Fenómenos observados en el espacio vectorial

### Farm Intelligence aparece cerca de Diagnostics en 2D — artefacto de proyección

Farm (centroide cy≈11.9) y Diagnostics (centroide cy≈12.7) quedan al fondo del mapa 2D
siendo temas sin relación semántica obvia. La causa: ambos comparten vocabulario genérico
de software ("AI", "precision", "platform", "monitoring", "detection") y sin señal de
dominio específica (`technical_stack`, `emergent_theme`) el embedding e5 no distingue
"monitoreo agrícola" de "monitoreo clínico".

**El clustering HDBSCAN en 5D los separa correctamente.** La vecindad 2D es un artefacto
de proyección, no semántica real. La señal de alarma fue correcta — la explicación es
ausencia de vocabulario diferenciador, no clasificación errónea.

**Solución a largo plazo**: enrich_periphery en las 117 GRIDX + mejorar summaries de
Diagnostics puras (Oncoliq, Embryoxite, ZEV Biotech...) con vocabulario más específico.

### Bioinputs está semánticamente dividido en dos grupos

Hay dos tipos de startups de "Bioinputs & Crop Resilience" con lenguajes distintos:

1. **Crop Protection / Crop Resilience** (biopesticidas, biostimulantes) → cy≈-6 → cerca de Food Systems
2. **Biologicals** (gene editing, CRISPR, bioinformatics para cultivos) → cy≈7 → cerca de Farm Intelligence

Esta división es **semánticamente correcta** y refleja una diferencia real de tecnología,
no un bug de clustering. Los dos grupos hablan "idiomas" distintos en el embedding space.

### Farm Intelligence y Nature & Ecosystem Tech son semánticamente cercanos (esperado)

Sus clusters UMAP están a 1-4 unidades de distancia. Startups de gestión agrícola,
monitoreo de ecosistemas y plataformas de trazabilidad comparten vocabulario. El
solapamiento en la visualización es correcto — no intentar separarlos artificialmente.

### Startups de logística pura mal clasificadas como Nature & Ecosystem Tech

Identificadas startups que deberían ser `exclude` pero están en el corpus:
- **Sensify**: IoT para refrigeración comercial (no bio)
- **goFlux**: SaaS de flete por carretera (no bio)
- **LogShare**: plataforma de logistics (no bio)

Estas arrastran el cluster "Resource Efficiency" hacia un espacio semántico mixto.

---

## 8. Deuda técnica documentada

| Prioridad | Tarea                                                               | Bloqueado por     |
|:---------:|---------------------------------------------------------------------|:-----------------:|
| Alta      | `enrich_periphery.py` sobre las 117 nuevas → emergent_theme, technology_tags, technical_stack | API key |
| Alta      | Reclasificar Sensify/goFlux/LogShare como `exclude`                | —                 |
| Media     | Revisar Farm startups mal-etiquetadas como Nature & Ecosystem Tech  | curaduría humana  |
| Media     | Resolver encoding `brasil_ozônio` (3 rows fallaron en ingest)       | —                 |
| Baja      | Verificar si Levita Magnéticas pertenece al universo bio            | curaduría humana  |
| Baja      | Actualizar Stamm de Series A → Series B (tiene ronda reciente)      | verificar fuente  |

---

## 9. Estado baseline (2026-05-17)

```
Corpus include:     490 startups
Clusters:            24 (con min_cluster_size=6)
Noise:               48 startups (~9%)
Nuevas GRIDX bio:   117 startups (scope_reason='gridx_import')
Excluidas GRIDX:     66 startups (non-bio)

Mejor run hasta hoy: macro_theme + bio_lens_tags derivados, sin emergent_theme/tech_tags/business_one_liner
→ 14 clusters, 48 noise (9%), 1 super-cluster de 173 startups (Farm/Nature/Bioinputs biologicals)
```
