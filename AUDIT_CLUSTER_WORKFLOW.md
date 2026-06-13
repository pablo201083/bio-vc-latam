# Audit & Cluster Workflow

**Proceso end-to-end para auditar startups y mejorar calidad de clustering.**

Cada vez que agregues startups nuevas a la base, debería ejecutarse este flujo para garantizar que el clustering semántico tenga datos de calidad.

## Paso 1: Auditoría de Data Gaps

```bash
python pipeline.py audit-cluster
```

**Qué hace:**
- Identifica startups con campos críticos VACÍOS:
  - `funding_stage` (etapa de financiamiento)
  - `computed_quality_score` (puntuación 0-10)
  - `tech_depth` (deep/medium/shallow/unclassified)
  - `short_description` (descripción en entities)

- Genera `quality/audit_cluster_triage.csv` con:
  - Severity: high (>=3 campos faltantes) | medium (1-2 campos)
  - Lista de campos faltantes por startup
  - Columna `curation_status` para tracking manual

**Salida típica:**
```
Total gaps detectados: 145
  High severity: 47
  Medium severity: 98

Triage CSV: quality/audit_cluster_triage.csv
```

---

## Paso 2: Curation Manual de Datos

### 2A. Priorizar por severidad

Edita `quality/audit_cluster_triage.csv`:

```csv
startup_id,name,severity,missing_critical,missing_recommended,curation_status,notes
startup-1,Name,high,funding_stage | quality_score,website,pending,Buscar en Crunchbase
startup-2,Name,medium,tech_depth,,in_progress,Auditar bio_theme
...
```

**Columnas a completar:**
- `curation_status`: `pending` → `in_progress` → `completed` → `verified`
- `notes`: fuente de dato, confianza, incertidumbres

### 2B. Completar datos en la BD

Para cada startup con status "in_progress":

**Opción 1: Update directo (vía Python script)**
```python
import sqlite3
conn = sqlite3.connect('db/bio_latam.db')
cursor = conn.cursor()

# Actualizar funding_stage
cursor.execute(
    "UPDATE startup_extended SET funding_stage = ? WHERE startup_id = ?",
    ('seed', 'startup-id')
)

# Actualizar quality_score
cursor.execute(
    "UPDATE startup_extended SET computed_quality_score = ? WHERE startup_id = ?",
    (7.5, 'startup-id')
)

# Actualizar description (en entities)
cursor.execute(
    "UPDATE entities SET short_description = ? WHERE entity_id = ?",
    ('Descripción corta', 'startup-id')
)

conn.commit()
conn.close()
```

**Opción 2: CSV masivo via `ingest-entity-enrichments`**

Crear `staging/entity_enrichments_audit.csv`:
```csv
entity_id,field,value,source,confidence
startup-1,short_description,Desc,manual,0.9
startup-1,funding_stage,seed,manual,0.8
startup-2,tech_depth,deep,manual,0.95
```

Luego:
```bash
python pipeline.py ingest-entity-enrichments --file staging/entity_enrichments_audit.csv
```

### 2C. Validar cambios

```bash
# Ver cuántos gaps quedan
python pipeline.py status

# Chequear audit_log
SELECT * FROM audit_log ORDER BY updated_at DESC LIMIT 20;
```

---

## Paso 3: Re-ejecutar Clustering

Una vez que la mayoría de high-severity gaps estén `completed`:

```bash
python pipeline.py audit-cluster --apply-fix
```

**Qué hace:**
- Re-vectoriza todas las startups con el modelo `intfloat/multilingual-e5-small`
- Re-ejecuta UMAP (10D) + HDBSCAN
- Regenera `pilot/startup-themes-data.js`
- Actualiza clusters en la BD

**Tiempo:** ~8-10 minutos (depende del hardware)

---

## Paso 4: Evaluar Impacto

### 4A. Comparar clusters antes/después

```bash
# Antes de Paso 3: grabar estado
git show HEAD:pilot/startup-themes-data.js > /tmp/clusters_before.js

# Después de Paso 3
git diff /tmp/clusters_before.js pilot/startup-themes-data.js | \
  grep -E "^[+-].*cluster_id|^[+-].*cluster_label" | head -50
```

### 4B. Métricas de calidad

```bash
# Ver salud del sistema
python pipeline.py health

# Ver cobertura por tema × país
python pipeline.py coverage
```

### 4C. Inspección visual

Abre `file:///C:/Users/Pablo%20A/Desktop/Exploraci%C3%B3n%20Semantica%20y%20Grafo/pilot/startup-themes.html`

Recarga con **Ctrl+Shift+R** y verifica:
- ¿Se rellenaron los espacios vacíos en el árbol?
- ¿Se agruparon bien las startups por sub_cluster?
- ¿Hay nuevos clusters coherentes?

---

## Paso 5: Iterar

Si quedaron gaps o clusters débiles:

1. Marca como `needs_review` en triage CSV
2. Ajusta datos
3. Vuelve a Paso 3

---

## Flujo Rápido (TL;DR)

```bash
# 1. Identificar gaps
python pipeline.py audit-cluster

# 2. Editar triage + actualizar BD
# (manual)

# 3. Re-cluster
python pipeline.py audit-cluster --apply-fix

# 4. Verificar
python pipeline.py health
# Abre pilot/startup-themes.html
```

---

## Campos Críticos Explicados

| Campo | Rango | Impacto en Clustering |
|-------|-------|----------------------|
| `funding_stage` | pre-seed, seed, accelerator, series-a, series-b, series-c, growth | Color del dot; agrupa cohortes |
| `computed_quality_score` | 0-10 | Tamaño del dot; influye en ranking dentro de cluster |
| `tech_depth` | deep, medium, shallow, unclassified, enabler | Marca de especialización; afecta HDBSCAN |
| `short_description` | texto libre (50-200 chars) | Insumo para embeddings; crítico para clustering semántico |

---

## Troubleshooting

**Q: Mis cambios no aparecen en el HTML**
- A: Borra caché del navegador (**Ctrl+Shift+R** en startup-themes.html)
- Si aún no aparece, chequea que los timestamps de los archivos JS sean recientes

**Q: El clustering fallou ("No module named 'sentence_transformers'")**
- A: Instala: `.venv\Scripts\pip.exe install sentence-transformers`

**Q: Tengo 145 gaps pero solo quiero arreglar los top 20**
- A: Ordena triage CSV por `severity` DESC, marca solo top 20 como `in_progress`, re-cluster

**Q: ¿Cuándo debería ejecutar esto?**
- A: Cada vez que agregues startups nuevas vía `ingest-discovered` o manualmente
- O si notas que el árbol tiene espacios vacíos / clusters débiles
- O como mantenimiento trimestral de calidad

---

## Próximas Mejoras

- [ ] Script automático que score cada startup en escala 0-10 (vs. promedio del tema)
- [ ] Alerta si un cluster se vuelve muy heterogéneo (baja coherencia semántica)
- [ ] Dashboard de "audit health" que muestre gaps por tema
- [ ] Integración con fuzzy-match para detectar startups duplicadas al ingerir
