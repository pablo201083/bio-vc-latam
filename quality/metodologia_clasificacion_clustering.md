# Metodología de Clasificación y Clustering Semántico
## BIO LATAM Ecosystem Tracker — Documento Técnico

**Versión:** 2.1  
**Fecha:** 2026-05-28  
**Autores:** Equipo BIO LATAM / CAB  
**Estado:** Vigente

---

## Resumen ejecutivo

Este documento describe el método sistemático utilizado para clasificar ~490 startups de biotecnología latinoamericana en 8 categorías temáticas editoriales (bio_themes) y organizar su representación espacial en un mapa semántico interactivo. El sistema combina embeddings de texto multilingüe, reducción dimensional UMAP, clustering HDBSCAN, y una capa de curación manual protegida por audit trail. El resultado es un mapa reproducible y explicable donde la posición de cada startup refleja su similitud semántica real, y su categoría temática se deriva de señales estructuradas y verificables.

---

## 1. Fundamentos del problema

### 1.1 El desafío de clasificación en biotech

Las startups de biotech son difíciles de clasificar con taxonomías predefinidas porque:

- Una misma tecnología (ej. fermentación microbiana) puede aplicarse a alimentos, fármacos, materiales o bioinsumos
- Las descripciones en inglés, español y portugués coexisten con terminología técnica específica
- Las categorías útiles para decisión de inversión/política son distintas a las categorías científicas convencionales
- Los tags estructurados asignados manualmente tienen cobertura incompleta y sesgos de curador

La solución adoptada parte de la semántica del texto como señal primaria, complementada con clustering no supervisado, y finaliza con una capa editorial controlada.

### 1.2 Las 8 categorías canónicas (bio_themes)

**Origen:** estas 8 categorías no son una taxonomía top-down impuesta a priori. Emergieron inductivamente del proceso de clustering semántico (24 clusters HDBSCAN) y fueron luego sintetizadas editorialmente para reflejar dimensiones relevantes para política, inversión y desarrollo de ecosistema. Son, en esencia, una lectura interpretativa de lo que el ecosistema latam produce — no una clasificación industrial estándar.

| # | Bio Theme | Naturaleza | Descripción operativa |
|---|---|---|---|
| 1 | **Diagnostics & Health Access** | Aplicación final | Diagnóstico in vitro, monitoreo de salud, acceso a servicios diagnósticos |
| 2 | **Therapeutics** | Aplicación final | Fármacos, biofármacos, terapia génica, medicina regenerativa, dispositivos terapéuticos |
| 3 | **Bioinputs & Crop Resilience** | Aplicación final | Biofertilizantes, biopesticidas, biocontrol, microbioma de suelo, biológicos para cultivo |
| 4 | **Food Systems & Alt Proteins** | Aplicación final | Proteínas alternativas, fermentación alimentaria, ingredientes funcionales, seguridad alimentaria |
| 5 | **Biomanufacturing & Platform Technologies** | **Plataforma habilitante** | Infraestructura de bioproducción, plataformas de fermentación industrial, enzimas, digital twins para bioprocessos, gene editing como servicio, synthetic biology tools |
| 6 | **Biomaterials & Circular Economy** | Aplicación final | Biomateriales, bioplásticos, economía circular, packaging bio-based |
| 7 | **Nature & Ecosystem Tech** | Aplicación final | Monitoreo ambiental, biodiversidad, créditos de carbono, restauración de ecosistemas, bioenergía |
| 8 | **Farm Intelligence** | Aplicación final | Sensores agrícolas, analítica de datos agro, decisión de cultivo, precision farming |

**Nota sobre Biomanufacturing & Platform Technologies:** es el único tema de naturaleza "plataforma habilitante" en lugar de "sector de aplicación final". Sus startups venden capacidades tecnológicas (infraestructura de fermentación, enzimas industriales, herramientas de diseño biológico) que sirven a múltiples sectores destino. Esta distinción es intencional: captura una categoría estratégicamente diferente — el substrato tecnológico que hace posible el resto del ecosistema — y tiene implicancias distintas para política de I+D e inversión en deep tech.

---

## 2. Datos de entrada

### 2.1 Fuente de texto primaria

El sistema usa **`startup_summary_en`** como señal textual principal: una descripción en inglés de 100–300 palabras que responde a "qué hace esta startup, qué problema resuelve, qué tecnología usa y para quién". Es la señal más densa disponible.

Campos adicionales que contribuyen al vector semántico (ver sección 3):
- `business_one_liner` — descripción de una línea (~15 palabras)
- `macro_theme` — categorización editorial de alto nivel (preservada como metadata)
- `emergent_theme` — señal de temática emergente si existe
- `technical_stack` — stack tecnológico declarado
- `technology_tags` — tags de tecnología (text libre)
- `industry_destination` — industria destino
- `domain_tags`, `bio_lens_tags`, `scale_tags` — tags estructurados heredados

**Nota de diseño:** Los tags estructurados (domain_tags, bio_lens_tags, industry_codes, etc.) son el resultado de clasificación manual anterior del curador. Tienen cobertura del 57–81% y valores demasiado amplios para discriminar entre temas. En el clasificador v2 (sección 5) **no se usan como input de clasificación** — se preservan como metadata pero no determinan el bio_theme.

### 2.2 Cobertura de datos

| Campo | Cobertura |
|---|---|
| startup_summary_en | ~97% |
| business_one_liner | ~95% |
| bio_theme_primary (post v2) | 100% |
| bio_theme_secondary (derivado) | 100% |
| funding_stage (derivado) | ~78% |
| cluster_id (mapa semántico) | ~100% (outliers = -1) |

---

## 3. Embeddings: representación vectorial del texto

### 3.1 Modelo

**Modelo:** `intfloat/multilingual-e5-small`  
**Dimensiones:** 384  
**Idiomas soportados:** 100+, optimizado para inglés y principales idiomas europeos/iberoamericanos  
**Ventana de contexto:** 512 tokens

Se eligió este modelo por su balance entre calidad semántica multilingüe, tamaño (~120 MB) y velocidad de inferencia local. Es un modelo de sentence-embedding contrastivo, entrenado para capturar similitud semántica entre textos.

### 3.2 Construcción del texto de embedding

La función `make_embed_text()` en `src/embeddings.py` construye el texto de entrada:

```python
def make_embed_text(row):
    parts = []
    if row.get("startup_summary_en"):
        # Summary duplicado para darle peso 2x
        parts.append(row["startup_summary_en"])
        parts.append(row["startup_summary_en"])
    if row.get("business_one_liner"):
        parts.append(row["business_one_liner"])
    for field in ["macro_theme", "emergent_theme", "technical_stack",
                  "technology_tags", "industry_destination",
                  "domain_tags", "bio_lens_tags", "scale_tags"]:
        if row.get(field):
            parts.append(str(row[field]))
    return " | ".join(parts)
```

El **peso doble del summary** refleja la decisión de que la descripción completa de la startup es la señal semántica dominante. El resto de campos contextualiza pero no domina.

### 3.3 Normalización y almacenamiento

Los vectores se normalizan a norma unitaria (L2) antes de almacenar, lo que permite usar **cosine similarity = dot product** directamente. Se guardan en `embeddings/startup_vectors.npy` (shape: N×384) con el índice correspondiente `embeddings/startup_ids.json`.

El cache es regenerable. Para regenerar:
```powershell
python pipeline.py rebuild --phase embeddings
```
O bien con forzado:
```powershell
python pipeline.py rebuild --phase embeddings --force
```

---

## 4. Mapa semántico: UMAP + HDBSCAN

### 4.1 Arquitectura de dos etapas

La reducción dimensional se realiza en **dos etapas consecutivas**:

```
Vectores 384D
    ↓  UMAP 10D  (para clustering — cosine, min_dist=0.0, n_neighbors=15)
Representación 10D (captura estructura topológica)
    ↓  HDBSCAN  (clustering no supervisado)
24 clusters + outliers
    ↓  UMAP 2D  (para visualización — euclidean sobre los 10D)
Posiciones 2D crudas (raw)
    ↓  Posicionamiento editorial
Posiciones finales (umap_x, umap_y) con layout por bio_theme
```

### 4.2 Parámetros UMAP

**Etapa 1 — Clustering (10D):**
```python
UMAP_CLUSTER_PARAMS = {
    "n_components": 10,
    "n_neighbors": 15,
    "min_dist": 0.0,
    "metric": "cosine",
    "random_state": 42,
}
```

**Etapa 2 — Visualización (2D):**
```python
UMAP_VIZ_PARAMS = {
    "n_components": 2,
    "n_neighbors": 15,
    "min_dist": 0.1,
    "metric": "euclidean",
    "random_state": 42,
}
```

El `random_state=42` garantiza **determinismo**: dada la misma base de datos y el mismo modelo de embedding, el mapa es reproducible bit a bit.

### 4.3 HDBSCAN: clustering semántico

**Parámetros operativos:**
```python
HDBSCAN_PARAMS = {
    "min_cluster_size": 8,
    "min_samples": 3,
    "metric": "euclidean",
    "cluster_selection_method": "eom",
}
```

HDBSCAN es un algoritmo de clustering jerárquico basado en densidad. Sus ventajas para este problema son:
- No requiere especificar el número de clusters a priori
- Detecta clusters de formas arbitrarias
- Asigna puntos ruidosos como outliers (cluster_id = -1) en lugar de forzar una asignación
- Calcula `cluster_confidence` por punto (0–1), indicando la certeza de pertenencia

El proceso generó **24 clusters** (IDs 0–23) con una distribución que refleja sub-especialidades dentro de los 8 temas. Por ejemplo, dentro de "Therapeutics" existen clusters separados para oncología (CL16), biofármacos (CL7), medicina regenerativa (CL17), etc.

### 4.4 REGLA FUNDAMENTAL: el clustering es sagrado

**El clustering HDBSCAN se ejecutó una sola vez sobre los 489 embeddings originales y sus resultados NO se vuelven a correr de forma automática.** Razón: el algoritmo es no determinista en cuanto a la interpretación semántica de los clusters — una re-corrida con datos ligeramente diferentes puede reorganizar clusters completos, invalidando semanas de curación manual.

Las correcciones al clustering se realizan **exclusivamente mediante scripts de reasignación manual** (ver sección 6.2) que quedan registrados en el audit_log con `actor = 'human:curador'`.

### 4.5 Labels de clusters

Cada cluster tiene un `cluster_label` con el formato:
```
"Bio Theme — Sub-label||keyword1 · keyword2 · keyword3"
```
Ejemplo: `"Therapeutics — Biopharmaceutical||biopharmaceutical · organ · therapeutic · medicine"`

El prefijo antes del `||` es legible para humanos. El sufijo (keywords) se usa como descriptores de búsqueda y display. El tema canónico al inicio del label es la fuente de verdad para la asignación de `bio_theme_primary` en el clasificador v2 (sección 5).

### 4.6 Posicionamiento editorial

Las posiciones finales en el mapa no son las coordenadas crudas de UMAP 2D. Se aplica un **posicionamiento editorial** en dos capas:

1. **Macro-posición:** Cada bio_theme tiene un centroide fijo en el espacio 2D, definido editorialmente para organizar el mapa de forma legible (clusters del mismo tema quedan próximos).

2. **Micro-posición (intra-tema):** Dentro de la región de cada bio_theme, las startups se ubican según sus coordenadas UMAP 2D relativas, preservando las distancias semánticas internas.

La función `editorial_positions()` en `src/clustering.py` implementa esta lógica:
```
umap_x_final = centroide_bio_theme_x + offset_umap_2d_x × escala
umap_y_final = centroide_bio_theme_y + offset_umap_2d_y × escala
```

**Consecuencia importante:** cambiar el `bio_theme_primary` de una startup cambia su región macro en el mapa (puede cruzar de un cuadrante a otro). Cambiar los embeddings o agregar startups cambia solo las posiciones relativas dentro de cada región. Ambos son operaciones seguras que no invalidan el clustering.

---

## 5. Clasificación temática v2 (bio_theme_primary)

### 5.1 Arquitectura del clasificador

El clasificador v2 (`src/reclassify_v2.py`) opera con tres fuentes en orden de prioridad:

```
PRIORIDAD 1: Correcciones manuales (LOCKED)
    ↓ Si startup_id está en audit_log con actor='human:curador' y field='bio_theme_primary'
    → Mantener el valor exactamente. Intocable.

PRIORIDAD 2: Cluster (para startups en el mapa)
    ↓ Si cluster_id >= 0 (startup clasificada por HDBSCAN)
    → Extraer bio_theme del prefijo del cluster_label
    → Validar con keyword scorer (solo como señal de confianza)
    → Asignar tema del cluster, confidence=0.90 (acuerdo) o 0.70 (conflicto)

PRIORIDAD 3: Keyword scorer (fallback para outliers)
    ↓ Si cluster_id == -1 (outlier semántico)
    → Aplicar keyword scoring sobre startup_summary_en ÚNICAMENTE
    → Usar reglas regex sobre 8 categorías de vocabulario
    → Confidence según intensidad del scoring
```

### 5.2 Por qué el cluster es mejor señal que los keywords

Para las startups con cluster asignado, el cluster proviene del embedding completo de la startup (384 dimensiones, 1536 palabras efectivas de contexto). El keyword scorer trabaja sobre patrones de palabras clave en texto libre. Cuando ambos discrepan:

- El cluster captura el **espacio semántico completo**: si una startup tiene tecnología de fermentación pero la aplica a producción de biofármacos, quedará en el cluster de Therapeutics (donde están otras startups similares), no en Biomanufacturing.
- El keyword scorer podría asignar Biomanufacturing por la presencia de "fermentación" en el texto.

En el mapa actual, hay 51 casos de conflicto donde el cluster asigna un tema distinto al que daría el keyword scorer. El clasificador v2 los registra como `source='cluster_conflict'` con confidence=0.70, dejando trazabilidad para revisión posterior.

### 5.3 Inputs explícitamente excluidos del clasificador

Los siguientes campos **NO** se usan para determinar bio_theme_primary en v2, aunque están disponibles en la base de datos:

| Campo | Razón de exclusión |
|---|---|
| `domain_tags` | Categorías demasiado amplias, cobertura parcial, sesgo de curador anterior |
| `bio_lens_tags` | Igual que domain_tags |
| `industry_codes` | Códigos NAICS/ISIC genéricos, no resuelven ambigüedad intra-bio |
| `tech_codes` | Cobertura ~57%, demasiado técnicos para temas de aplicación |
| `macro_theme` | Categorización manual anterior (10 categorías) — metadata, no input |
| `bio_theme_secondary` | Derivado del primario — sería circular usarlo como input |

### 5.4 Estado post v2 (ejecutado 2026-05-27)

| Fuente | Startups | Porcentaje |
|---|---|---|
| Locked (corrección manual) | 84 | 17.2% |
| Cluster (acuerdo con keyword) | 278 | 56.9% |
| Cluster (conflicto con keyword) | 51 | 10.4% |
| Keyword fallback (outliers) | 64 | 13.1% |
| Sin tema posible | 8 | 1.6% |
| Sin cambio necesario | ~220 | — |
| **Cambios aplicados en corrida** | 64 | — |

### 5.5 bio_theme_secondary

Se deriva automáticamente como la segunda temática más relevante para cada startup, basada en la combinación de (cluster_id, bio_theme_primary) y reglas de dominio para casos sin datos históricos. No requiere clasificador separado — usa la proximidad temática del clustering.

---

## 6. Curación manual y garantías de integridad

### 6.1 El audit_log como contrato de datos

**Toda modificación** a `startup_extended` que afecte campos clasificatorios pasa por el `audit_log`:

```sql
CREATE TABLE audit_log (
    id          INTEGER PRIMARY KEY,
    timestamp   TEXT,           -- ISO 8601 UTC
    actor       TEXT,           -- 'human:curador' | 'auto:reclassify_v2' | 'auto:pipeline'
    entity_id   TEXT,
    table_name  TEXT,
    field       TEXT,
    old_value   TEXT,
    new_value   TEXT,
    reason      TEXT            -- justificación explícita
);
```

El campo `actor` es la distinción crítica:
- `actor = 'human:curador'` → corrección manual explícita; el clasificador automático **nunca** la sobreescribe
- `actor = 'auto:reclassify_v2'` → asignación automática del clasificador; puede revisarse
- `actor = 'auto:pipeline'` → actualización de derivados (funding_stage, secondary theme, etc.)

### 6.2 Correcciones manuales de clustering (rondas)

Las reasignaciones de clusters incorrectos se ejecutan como scripts Python con nombre descriptivo:

```
fix_cl17_outliers.py     — Round CL17: 6 startups mal clasificadas en Therapeutics Regenerative
fix_round7_outliers.py   — Round 7: 6 reasignaciones cross-cluster
fix_cl9_outliers.py      — Round 9: ...
```

Cada script:
1. Lee el estado actual de la DB
2. Aplica UPDATE a `cluster_id`, `cluster_label`, `is_outlier`, y opcionalmente `bio_theme_primary`
3. Escribe una fila en `audit_log` por cada campo modificado con `actor='human:curador'`
4. Hace commit y cierra conexión

**REGLA:** estos scripts son idempotentes (correrlos dos veces no daña, solo genera logs duplicados). Nunca borran registros.

### 6.3 Criterios para reasignación manual de clusters

Una startup se reasigna de cluster cuando:
- Su `cluster_confidence` < 0.40 (baja confianza de pertenencia)
- Su descripción técnica es semánticamente incompatible con el cluster_label (ej. dispositivo médico de ondas electromagnéticas en cluster de oncología molecular)
- El curador tiene conocimiento de dominio que invalida la asignación automática

Reasignar implica evaluar cuál cluster existente es semánticamente más apropiado, no crear nuevos clusters.

---

## 7. Reproducibilidad y operaciones seguras

### 7.1 Invariantes del sistema

Las siguientes propiedades se mantienen siempre que el pipeline se ejecute correctamente:

1. **Determinismo de embeddings:** mismo texto → mismo vector (modelo fijo, no API)
2. **Determinismo de UMAP:** `random_state=42` en ambas etapas → mismas coordenadas para mismo input
3. **Inmutabilidad del clustering:** los 24 clusters son históricos; solo se modifican via scripts de corrección manual
4. **Inmutabilidad de correcciones humanas:** `audit_log` con `actor='human:curador'` protege 84 asignaciones

### 7.2 Operaciones seguras (no rompen integridad)

```powershell
# Regenerar embeddings (después de actualizar summaries)
python pipeline.py rebuild --phase embeddings

# Reclasificar bio_themes con nuevos embeddings
python pipeline.py reclassify-themes

# Actualizar posiciones UMAP (sin tocar clusters)
.venv/Scripts/python.exe update_umap_positions.py

# Regenerar dashboard data
python -c "import sqlite3,sys; sys.path.insert(0,'.'); from src.clustering import write_dashboard_data; conn=sqlite3.connect('db/bio_latam.db'); write_dashboard_data(conn); conn.close()"

# Validar integridad
python pipeline.py validate
```

### 7.3 Operaciones que requieren aprobación del curador

- **Re-correr HDBSCAN:** invalida todos los cluster_ids manuales. Requiere aprobación explícita y nueva ronda de curación.
- **Cambiar parámetros de UMAP cluster:** cambia los 10D sobre los que corre HDBSCAN. Equivalente al punto anterior.
- **Modificar `make_embed_text()`:** cambia los vectores base, invalida todo el mapa.
- **Agregar startups masivamente (>50):** puede desplazar centroides temáticos significativamente.

---

## 8. Diagrama de flujo completo

```
┌─────────────────────────────────────────────────────────────────┐
│  DATOS DE ENTRADA                                               │
│  startup_master_dataset.csv  →  startup_extended (SQLite)       │
│  canonical/manual_*.csv      →  investment_edges, entities...   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  EMBEDDINGS  (src/embeddings.py)                                │
│  make_embed_text() → intfloat/multilingual-e5-small → 384D     │
│  Cache: embeddings/startup_vectors.npy                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  UMAP 10D  (src/clustering.py)                                  │
│  cosine, n_neighbors=15, min_dist=0.0, random_state=42          │
│  384D → 10D (estructura topológica preservada)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  HDBSCAN  (src/clustering.py)  [EJECUTADO UNA VEZ — SAGRADO]   │
│  min_cluster_size=8, min_samples=3, eom                         │
│  → 24 clusters + outliers  →  cluster_id, cluster_confidence   │
│  → cluster_label: "Bio Theme — Sub||keywords"                   │
│                                                                  │
│  + Correcciones manuales (fix_*.py) via audit_log               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  CLASIFICADOR v2  (src/reclassify_v2.py)                        │
│                                                                  │
│  [LOCKED] human:curador entries  →  sin cambio (84 startups)   │
│  [CLUSTER] cluster_label prefix  →  bio_theme_primary           │
│  [KEYWORD] summary_en regex      →  bio_theme_primary (outlier)│
│                                                                  │
│  → bio_theme_primary, bio_theme_confidence, bio_theme_source    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  UMAP 2D  (src/clustering.py)                                   │
│  euclidean (sobre 10D), n_neighbors=15, min_dist=0.1            │
│  → coordenadas raw 2D                                           │
│                                                                  │
│  editorial_positions()                                           │
│  → umap_x, umap_y finales con layout bio_theme                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  DASHBOARD  (pilot/startup-themes-data.js)                      │
│  write_dashboard_data()  →  1.15 MB JSON para visualización     │
│  pilot/startup-themes.html  →  Mapa interactivo                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Limitaciones conocidas y trabajo futuro

### 9.1 Limitaciones actuales

**Cobertura de outliers (~13%):** Las 64 startups clasificadas por keyword scorer no tienen la calidad semántica del cluster-first. Son candidatas a revisión manual o enriquecimiento de sus summaries para que el siguiente rebuild las ubique en un cluster.

**Conflictos cluster/keyword (51 casos):** El clasificador asigna el tema del cluster por defecto (confidence=0.70), pero algunos casos donde el keyword scorer tiene razón (ej. startup de Farm Intelligence en cluster de Nature & Ecosystem) son candidatos a corrección manual.

**Embeddings de una sola corrida:** Los embeddings se calcularon con los summaries disponibles al momento. Startups con summaries cortos (<60 palabras) tienen vectores menos representativos. Hay ~173 startups en esta condición.

**Tema secundario derivado, no clasificado:** El `bio_theme_secondary` se deriva de patrones de dominio, no de un clasificador independiente. Para startups en la intersección de tres o más temas, el secundario puede ser subóptimo.

### 9.2 Trabajo futuro planificado

- **Enriquecimiento de summaries:** Completar los 173 summaries cortos para mejorar la calidad del embedding
- **Revisión de conflictos:** Audit manual de los 51 casos cluster/keyword conflict
- **Calibración del scoring de matching:** Ajuste de pesos para portfolios grandes (ver plan Fase 1)
- **Introduction Builder:** Generador de briefs de presentación startup ↔ inversor (ver plan Fase 2)
- **Ecosystem Health Monitor:** Vista de salud por tema × país (ver plan Fase 4b)

---

## 10. Referencias técnicas

| Componente | Referencia |
|---|---|
| Modelo de embedding | [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) — Wang et al. 2024 |
| UMAP | McInnes, L., Healy, J., Melville, J. (2018). UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction. |
| HDBSCAN | Campello, R.J.G.B., Moulavi, D., Sander, J. (2013). Density-Based Clustering Based on Hierarchical Density Estimates. |
| Implementación Python | `umap-learn 0.5.x`, `hdbscan 0.8.x`, `sentence-transformers 2.x` |

---

## Apéndice A: Archivos del sistema

```
src/
  embeddings.py          — make_embed_text(), run(), cache management
  clustering.py          — run_umap(), HDBSCAN runner, editorial_positions(), write_dashboard_data()
  reclassify_v2.py       — Clasificador temático v2 (vigente)
  reclassify_v1_backup.py — Keyword scorer heredado (fallback)
  audit.py               — diff_and_log_update()

db/
  bio_latam.db           — SQLite, fuente de verdad operativa
  migrations/            — DDL incremental

embeddings/
  startup_vectors.npy    — Cache de vectores 384D (regenerable)
  startup_ids.json       — Orden de IDs correspondiente

quality/
  data_contract.md       — Reglas de governance selladas
  sistema_clasificacion_visual.md — Decisiones de display (paleta, tipografía)
  metodologia_clasificacion_clustering.md — Este documento

fix_*.py                 — Scripts de corrección manual de clusters (historial)
update_umap_positions.py — Actualización selectiva de umap_x/umap_y

pilot/
  startup-themes.html    — Dashboard principal (mapa interactivo)
  startup-themes-data.js — Datos pre-computados para el dashboard
  cluster-quality.html   — Dashboard de calidad de clustering
```

---

## Apéndice B: Comandos de diagnóstico rápido

```powershell
# Ver distribución actual de bio_themes
.venv/Scripts/python.exe -c "
import sqlite3
conn = sqlite3.connect('db/bio_latam.db')
for row in conn.execute(\"SELECT bio_theme_primary, COUNT(*) as n FROM startup_extended WHERE scope_decision='include' GROUP BY 1 ORDER BY 2 DESC\"):
    print(f'{row[1]:>4}  {row[0]}')
"

# Ver startups outliers (cluster_id = -1)
.venv/Scripts/python.exe -c "
import sqlite3; conn = sqlite3.connect('db/bio_latam.db')
rows = conn.execute(\"SELECT e.canonical_name, sx.bio_theme_primary FROM startup_extended sx JOIN entities e ON e.entity_id=sx.startup_id WHERE sx.cluster_id=-1 ORDER BY 1\").fetchall()
print(f'{len(rows)} outliers:')
for r in rows: print(f'  {r[0][:40]:<40} {r[1]}')
"

# Ver conflictos cluster/keyword en audit_log
.venv/Scripts/python.exe -c "
import sqlite3; conn = sqlite3.connect('db/bio_latam.db')
rows = conn.execute(\"SELECT entity_id, old_value, new_value FROM audit_log WHERE reason LIKE '%cluster_conflict%' ORDER BY timestamp DESC LIMIT 20\").fetchall()
for r in rows: print(r)
"

# Verificar integridad completa
python pipeline.py validate
```

---

*Documento mantenido por el equipo BIO LATAM. Actualizar en cada cambio estructural al pipeline de clasificación.*
