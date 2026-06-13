# Web Research Plan: 60 Orphan Startups (Sin Tema)

**Objetivo:** Completar 4 campos críticos para 60 startups sin clasificación de bio_theme

**Impacto:** Re-clustering mejora coherencia semántica + 60 nuevas startups clasificadas

---

## Distribución por País

| País | Count | Status |
|------|-------|--------|
| BR (Brasil) | 14 | ⏳ Pendiente |
| BO (Bolivia) | 9 | ⏳ Pendiente |
| CR (Costa Rica) | 9 | ⏳ Pendiente |
| CO (Colombia) | 8 | ⏳ Pendiente |
| EC (Ecuador) | 7 | ⏳ Pendiente |
| MX (México) | 6 | ⏳ Pendiente |
| DO (República Dominicana) | 4 | ⏳ Pendiente |
| VE (Venezuela) | 2 | ⏳ Pendiente |
| GT (Guatemala) | 1 | ⏳ Pendiente |

**TOTAL: 60 startups**

---

## Campos a Completar

Para cada startup, buscar y completar:

1. **funding_stage** (1 campo obligatorio)
   - Valores válidos: pre-seed, seed, accelerator, series-a, series-b, series-c, series-c+, growth
   - Estrategia: Buscar en Crunchbase, LinkedIn, Google News
   - Si no encuentra: `pre-seed` (default conservador)

2. **computed_quality_score** (0-10)
   - Basado en: presencia web, LinkedIn profile, recepción de fondos, noticias
   - Escala: 0-3 (sin web), 4-6 (web básico), 7-8 (fundado, activo), 9-10 (funded)
   - Si no encuentra: calcular como `6.0` (mediana)

3. **tech_depth** (una palabra)
   - Valores: deep, medium, shallow, enabler, unclassified
   - Deep = biotech/synbio core; Medium = agtech/biotech híbrido; Shallow = software/SaaS con toque bio
   - Si no encuentra: `medium`

4. **short_description** (50-200 caracteres)
   - Extraer de sitio web, LinkedIn, Crunchbase
   - Formato: "Breve descripción de qué hacen + solución biológica"
   - Ej: "Plataforma de fermentación de precisión para bioplásticos"

---

## Proceso de Investigación

### Paso 1: Búsquedas iniciales (5-10 min por startup)

Para cada startup:

1. **Google Search**: `"[nombre]" biotech startup`
2. **Crunchbase**: Buscar nombre + país
3. **LinkedIn**: Buscar empresa
4. **Twitter/X**: Verificar si tienen cuenta activa

### Paso 2: Consolidar en CSV

Crear `staging/research_results_60_orphans.csv` con:

```csv
startup_id,funding_stage,computed_quality_score,tech_depth,short_description,source,confidence
agritech-bolivia-bo,seed,7.0,medium,Soluciones de agricultura de precisión con sensores IoT,Crunchbase,0.8
agricultic-do,pre-seed,5.0,medium,Plataforma de seguimiento agrícola basada en datos,Google,0.6
...
```

### Paso 3: Validación + Actualización BD

```bash
python pipeline.py ingest-entity-enrichments --file staging/research_results_60_orphans.csv
```

---

## Lista de Investigación

### Brasil (14 startups)

```
1. Agronow (agronow-br)
   Search: "Agronow" Brazil agriculture precision
   
2. Aimirim (aimirim-br)
   Search: "Aimirim" Brazil biotech fermentation
   
3. Alecrim Biotech (alecrim-biotech-br)
   Search: "Alecrim Biotech" Brazil therapeutic
   
4. BioDiverso Insumos (biodiverso-insumos-br)
   Search: "BioDiverso" Brazil crop resilience
   
5. BioProcess Automation Brasil (bioprocess-automation-brasil-br)
   Search: "BioProcess Automation" Brazil
   
6. Biocentis (biocentis-br)
   Search: "Biocentis" Brazil crop protection
   
7. Beep Saúde (beep-saude-br)
   Search: "Beep Saúde" Brazil diagnostics
   
8. BioFactory (biofactory-br)
   Search: "BioFactory" Brazil bioplastics
   
9. BioFresh (biofresh-br)
   Search: "BioFresh" Brazil fermentation
   
10. Aptah Bio (aptah-bio-br)
    Search: "Aptah Bio" Brazil drug discovery
    
11. Ascribe Bio (ascribe-bio-br)
    Search: "Ascribe Bio" Brazil biotech
    
12. Autem Therapeutics (autem-therapeutics-br)
    Search: "Autem" Brazil therapeutic
    
13. BIoIn (bioin-br)
    Search: "BIoIn" Brazil crop resilience
    
14. Biofabrica Siglo XXI (biofabrica-siglo-xxi-mx)
    Search: "Biofabrica" Mexico bioinputs
```

### Bolivia (9 startups)

```
1. AgriTech Bolivia (agritech-bolivia-bo)
2. Agrobit (Bolivia operations) (agrobit-bolivia-operations-bo)
3. BioLife Innovations (biolife-innovations-bo)
[... completar con búsquedas específicas]
```

### Costa Rica (9 startups)

```
1. BioMar (biomar-cr)
2. BioTech (biotech-cr)
3. [... 7 más]
```

---

## Notas Operativas

- **Confianza:** Registrar en CSV (`confidence` 0.0-1.0)
  - 0.9-1.0: Crunchbase confirmado
  - 0.7-0.8: LinkedIn + sitio web
  - 0.5-0.6: Google search + inferencia
  
- **Si no encuentra:** Usar defaults (pre-seed, 5.0, medium, "")

- **Después de consolidar:** 
  ```bash
  python pipeline.py audit-cluster --apply-fix
  ```
  Para re-cluster con 60 nuevas startups clasificadas

---

## Checklist

- [ ] Brasil (14)
- [ ] Bolivia (9)
- [ ] Costa Rica (9)
- [ ] Colombia (8)
- [ ] Ecuador (7)
- [ ] México (6)
- [ ] República Dominicana (4)
- [ ] Venezuela (2)
- [ ] Guatemala (1)
- [ ] CSV consolidado: `staging/research_results_60_orphans.csv`
- [ ] Ingestado a BD: `ingest-entity-enrichments`
- [ ] Re-cluster: `audit-cluster --apply-fix`
- [ ] Validar: `python pipeline.py health`

---

## Próximo Paso Después

Una vez completes los 60:
1. Re-cluster
2. Si quedan gaps, iteramos con los 47 startups "medium-severity" (1-2 campos)
3. Luego los 98 "medium-severity" generales

**Estimación:** 60 startups × 5 min = 300 min (~5 horas) si trabajas continuado
