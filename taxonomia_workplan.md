# Workplan para construir la taxonomia hibrida

## Fase 1. Corpus

### Startup corpus

Recolectar para cada startup:

- website title
- one-line tagline
- website about
- Crunchbase description
- LinkedIn description
- deck snippet si existe

Salida:

- `templates/startup_description_corpus_template.csv`

### Top-down corpus

Recolectar lenguaje desde:

- fondos
- aceleradoras
- venture builders
- reports
- landscape maps

Salida:

- `templates/top_down_vertical_language_template.csv`

## Fase 2. Normalizacion conceptual

Construir un diccionario de:

- mechanisms
- outputs
- feedstocks
- destinations
- transition verbs

Ejemplos:

- microbes, strains, fermentation, enzymes
- proteins, inputs, materials, ingredients
- residues, biomass, CO2, minerals
- agriculture, food, chemicals, textiles
- replace, decarbonize, valorize, regenerate

## Fase 3. Enrichment

Por startup, extraer:

- `technical_stack`
- `output_class`
- `feedstock`
- `industry_destination`
- `transition_function`

## Fase 4. Clustering

### Bottom-up

- embeddings de descripcion consolidada
- clustering exploratorio
- revision de microclusters

### Top-down alignment

- mapear clusters emergentes a market labels
- conservar sinonimos y variantes

## Fase 5. Producto

Usar la taxonomia para:

- vista startup-themes
- filtros por dimension
- ficha explicable por startup
- leyenda y narrativas del observatorio

## Entregables sugeridos de la siguiente iteracion

1. `startup_corpus_seed.csv`
2. `top_down_vertical_language_seed_expanded.csv`
3. `taxonomy_dictionary_v1.csv`
4. `startup_taxonomy_assignments_v0.csv`
5. `startup_themes.html` conectado a esas nuevas dimensiones
