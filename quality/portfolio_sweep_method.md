# Portfolio Sweep Method

## Idea

Usar portfolios de fondos, venture builders y aceleradoras como una vía intermedia entre:

- `startup-by-startup research`, que da mucha calidad pero escala lento
- `taxonomy_stub`, que escala rápido pero es demasiado endógeno

La lógica buena es:

`portfolio auditable -> resumen mínimo source-backed -> taxonomía / scope`

No al revés.

## Qué nos enseñó GRIDX

El sweep de GRIDX fue útil porque el portfolio:

- tiene alto alineamiento con el universo bio-based / life-based
- trae one-liners bastante accionables
- ayuda a resolver aliases
- da una señal razonable de thesis fit, no solo de existencia

Por eso GRIDX no fue solo una fuente de “empresa existe”, sino una fuente de `source-backed seeded` bastante fuerte.

## No todos los fondos valen igual

Hay que separar tres niveles de utilidad.

### Tier A: Portfolio con señal fuerte de thesis fit

Sirve para:

- confirmar existencia
- cargar resumen mínimo
- empujar `scope_status` hacia `confirmed`
- subir a `source_backed_seeded`

Ejemplos:

- GRIDX
- IndieBio / SOSV
- SF500
- The Yield Lab LATAM

### Tier B: Portfolio con señal útil pero scope menos concluyente

Sirve para:

- confirmar existencia
- cargar one-liner y fuente
- mejorar taxonomía
- mover de `taxonomy_stub` a `seeded`

Pero no siempre alcanza por sí solo para confirmar thesis fit.

Ejemplos:

- CITES
- AIR Capital
- Kamay Ventures
- The Ganesha Lab
- DraperCygnus

### Tier C: Portfolio generalista

Sirve para:

- confirmar que la startup existe
- obtener un resumen breve

Pero no debería definir inclusión/exclusión de tesis salvo que la propia descripción muestre señal material, bio-based, biocéntrica o de límites planetarios.

## Regla editorial

### Portfolio source puede confirmar:

- startup name
- URL fuente
- business one-liner
- resumen mínimo

### Portfolio source no siempre puede confirmar:

- thesis fit fuerte
- taxonomía final
- TRL actual
- país o stage actual

## Resultado esperado por sweep

Cada sweep debería intentar producir:

- `startup_name`
- `source_url`
- `source_type = official_portfolio_profile`
- `evidence_excerpt`
- `startup_summary_v1`
- `review_status = seeded`
- mejora de aliases cuando corresponda

Y opcionalmente:

- mejora de `macro_theme`
- mejora de `emergent_theme`
- `scope_status = confirmed` solo cuando el portfolio sea Tier A o la evidencia textual sea muy clara

## Cómo usarlo en el proyecto

### Objetivo 1

Bajar `include provisional` en batch sin tener que investigar cada startup desde cero.

### Objetivo 2

Construir un corpus externo auditable más denso para la taxonomía semántica beta.

### Objetivo 3

Comparar qué themes emergen cuando aumentamos cobertura source-backed vía portfolios.

## Indicador clave

El portfolio sweep no debería medirse solo por “cuántas startups tocó”, sino por:

- cuántas quedaron con `source_url`
- cuántas pasaron a `source_backed_seeded`
- cuántas mejoraron taxonomía
- cuántas `include provisional` bajaron

## Próximo uso recomendado

Después de GRIDX, la mejor secuencia es:

1. `Tier A` completos
2. `Tier B` por retorno y densidad en la base
3. luego reemplazar parte de esos `seeded` por `official_website`

