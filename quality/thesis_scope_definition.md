# Thesis Scope Definition

Base de referencia: `startup_taxonomy_assignments_v1.csv`

## Regla editorial

Una startup queda **dentro** del universo thesis-first si muestra una de estas señales:

- materialidad bio-based
- enfoque biocentrico
- regeneracion dentro de limites planetarios
- clima / energia / recursos con impacto material claro
- software claramente acoplado a agricultura, biotech, materiales o sistemas de recursos

Una startup queda **afuera** si es:

- full digital generalista
- fintech / commerce / SaaS sin relacion material
- software horizontal sin acople a bio, clima, recursos o regeneracion

Una startup queda en **review** si:

- hoy no hay evidencia suficiente
- aparece en `Other / Unclassified`
- podria tocar clima, materiales o regeneracion pero todavia no esta bien descrita

## Estado actual

- `161` startups `include`
- `73` startups `review`
- `71` startups `exclude`
- `234` startups visibles en ambas vistas

## Fuente operativa

La decision final por startup vive en:

- `scope_decision`: `include`, `review`, `exclude`
- `scope_reason`
- `scope_source`

Archivo operativo:

- `quality/startup_scope_decisions.csv`

## Notas

- `peripheral or underclassified ventures` ya no debe leerse como categoria semantica final.
- En la UI se trata como `Unclassified / Needs Review`.
- Las dos visualizaciones deben leer el mismo universo: `include + review`.
