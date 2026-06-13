# Cómo Hacer Web Research para los 60 Orphans

## Paso 1: Preparar el CSV de trabajo

1. Abre `staging/research_results_60_orphans_TEMPLATE.csv` en Excel o Google Sheets
2. **NO** renombres el archivo - trabaja en el original
3. Verás 60 filas con valores **por defecto** (pre-seed, 5.0, medium)

## Paso 2: Buscar cada startup

Para **cada fila**, sigue este proceso (5-10 min):

### 2A. Búsqueda en Google

```
Busca: "[nombre startup]" biotech OR startup [país]
Ejemplo: "AgriTech Bolivia" biotech startup Bolivia
```

**Qué mirar:**
- Sitio web oficial (si existe)
- LinkedIn company page
- Crunchbase profile
- Noticia de prensa / fundación

### 2B. LinkedIn (más confiable)

```
Linkedin.com → Search → "[nombre startup]"
Mirar: Company page → About section
```

**Extrae:**
- Año de fundación
- Descripción oficial
- Empleados (estimador de tamaño)
- Si tiene inversión registrada

### 2C. Crunchbase (si puedes acceder)

```
Crunchbase.com → Search → "[nombre]"
```

**Extrae:**
- Funding stage (seed, series-a, etc)
- Total raised
- Founded date
- Description

### 2D. Google Maps + Verificación

```
Si tienes dirección: Google Maps search
Verifica que es una empresa real y activa
```

---

## Paso 3: Llenar el CSV

Para cada startup **encontrada**, actualiza:

| Campo | Valor | Cómo decidir |
|-------|-------|-------------|
| **funding_stage** | seed, pre-seed, series-a, growth, etc | De Crunchbase o LinkedIn |
| **computed_quality_score** | 0-10 | Ver tabla abajo |
| **tech_depth** | deep, medium, shallow, enabler | Ver tabla abajo |
| **short_description** | 50-200 chars | De website o LinkedIn |
| **source** | Crunchbase, LinkedIn, Google, Website | Dónde encontraste la info |
| **confidence** | 0.5-1.0 | Cuán seguro estás (0.5=inferencia, 1.0=confirmado) |
| **notes** | Libre | "Fundado 2019, URL activa", etc |

### Quality Score (0-10)

```
0-3   = No tiene web, no existe, ghost company
4-6   = Sitio web básico, LinkedIn inactivo, sin financiamiento
7-8   = Fundado, web activo, LinkedIn con empleados, seed/series
9-10  = Financiado públicamente, noticias recientes, equipo visible
```

**Cálculo rápido:**
- Tiene website + LinkedIn activo = +6 puntos de base
- Series-A+ = +9-10
- Seed = +7-8
- Pre-seed = +5-6
- Sin info = +5 (default)

### Tech Depth

```
DEEP        = Core biotech/synbio (fermentación, genómica, cell culture)
MEDIUM      = Agtech + biotech (sensores + bioinsumos), medtech
SHALLOW     = Software/SaaS con aplicación bio
ENABLER     = Servicios genéricos (plataforma, software, consultoría)
UNCLASSIFIED = No sabes
```

---

## Paso 4: Si NO encuentras info

**Deja los defaults** (pre-seed, 5.0, medium):

```
Significa: "Spinoff, sin web activa, info insuficiente"
```

**Pero sí registra:**
- confidence = 0.0 (no verificado)
- notes = "No web encontrado" 
- source = "Default"

---

## Paso 5: Cuando termines

### 5A. Consolidar

```bash
# Renombra el CSV cuando termines TODAS las 60
mv staging/research_results_60_orphans_TEMPLATE.csv \
   staging/research_results_60_orphans.csv
```

### 5B. Ingesta a la BD

```bash
python pipeline.py ingest-entity-enrichments \
  --file staging/research_results_60_orphans.csv
```

### 5C. Re-cluster

```bash
python pipeline.py audit-cluster --apply-fix
```

### 5D. Validar

```bash
python pipeline.py health
```

Debe mostrar menos startups en gaps críticos.

---

## Ejemplos Completos

### Ejemplo 1: Startup con mucha info (Crunchbase)

```
Buscas: AgriTech Bolivia biotech startup
Encuentras: Crunchbase + LinkedIn + website

Llenas:
- funding_stage: seed (confirmado en Crunchbase)
- computed_quality_score: 7.5 (seed, website activo, LinkedIn con 20 empleados)
- tech_depth: deep (fermentación + microorganismos)
- short_description: "Plataforma de fermentación de precisión para cultivo de proteínas"
- source: Crunchbase
- confidence: 0.95 (muy confiable)
- notes: "Fundada 2021, 23 empleados, Serie A potencial"
```

### Ejemplo 2: Startup con poca info (solo Google)

```
Buscas: BioHack UIO
Encuentras: Solo LinkedIn básico + una noticia de 2019

Llenas:
- funding_stage: accelerator (participó en programa de aceleración)
- computed_quality_score: 6.0 (LinkedIn activo pero minimal)
- tech_depth: medium (ambigua, infieres agtech)
- short_description: "Plataforma de innovación biológica abierta"
- source: LinkedIn
- confidence: 0.6 (algunos datos son inferencia)
- notes: "LinkedIn minimal, no web oficial encontrada"
```

### Ejemplo 3: Ghost company (sin info)

```
Buscas: BioTech Costa Rica
No encuentras nada confiable

Llenas:
- funding_stage: pre-seed (default)
- computed_quality_score: 5.0 (default)
- tech_depth: medium (default)
- short_description: [vacío]
- source: Default
- confidence: 0.0 (no verificado)
- notes: "No web encontrado, posiblemente inactiva"
```

---

## Tips de Velocidad

1. **Abre 3 tabs:** Google + LinkedIn + Crunchbase
2. **Búsqueda rápida:** 3-5 min por startup si encuentras info, 1-2 min si no
3. **Atajos:**
   - site:linkedin.com "[nombre]"
   - site:crunchbase.com "[nombre]"
4. **Botes:** Si ves "404 / página no encontrada" después de 2 min, usa defaults
5. **Agrupación:** Haz Brasil primero (14), luego Bolivia (9), etc.

---

## Checklist por País

### Brasil (14)
- [ ] Agronow
- [ ] Aimirim
- [ ] Alecrim Biotech
- [ ] BioDiverso Insumos
- [ ] BioProcess Automation Brasil
- [ ] Biocentis
- [ ] Beep Saúde
- [ ] BioFactory
- [ ] BioFresh
- [ ] Aptah Bio
- [ ] Ascribe Bio
- [ ] Autem Therapeutics
- [ ] BIoIn
- [ ] [Otra]

### Bolivia (9)
- [ ] AgriTech Bolivia
- [ ] Agrobit (Bolivia operations)
- [ ] BioLife Innovations
- [ ] [etc...]

(Continúa con otros países...)

---

## Tiempo Estimado

- **60 startups × 5 min promedio = 300 minutos (~5 horas)**
- Si trabajas 1 hora/día: 5 días
- Si trabajas 2 horas/día: 2.5 días

**Pro tip:** Hazlo en bloques de 10-15 startups (1 país a la vez), toma descansos entre bloques.
