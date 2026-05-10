# Taxonomia hibrida top-down + bottom-up para startups bio

Fecha de trabajo: 19 de abril de 2026

## Objetivo

Construir una taxonomia propia para startups biotech non-pharma y life-centered material transition que:

- emerja desde como las startups se describen a si mismas
- sea legible para fondos, builders y policy makers
- permita clusterizar, navegar y comparar empresas
- no dependa de una lista rigida de verticales heredada

## Hipotesis central

La mejor taxonomia no sale ni solo desde arriba ni solo desde abajo.

- `bottom-up` descubre patrones reales en el lenguaje, la tecnica y la trayectoria de las startups
- `top-down` aporta nombres comparables, tesis de mercado y categorias con poder de coordinacion

La taxonomia final tiene que ser una capa de traduccion entre:

- el lenguaje de las startups
- el lenguaje de los fondos y market shapers
- el lenguaje del observatorio

## Principio de diseno

No clasificar una startup con una sola etiqueta.

Cada startup deberia poder describirse en varias dimensiones independientes.
Eso permite:

- evitar categorias planas y confusas
- capturar startups hibridas
- explorar el ecosistema por distintos lentes
- hacer vistas tipo CFT sin perder profundidad tecnica

## Propuesta de taxonomia en 6 dimensiones

### 1. Emergent Theme

Es la capa mas parecida al Climate Finance Tracker.

Sale del clustering semantico de descripciones de startups y representa familias emergentes de empresas que comparten lenguaje y propuesta.

Ejemplos de themes posibles:

- programmable biomaterials for industrial substitution
- microbial inputs for resilient agriculture
- continuous biomanufacturing infrastructure
- precision fermentation for food ingredients
- biologically-enabled remediation and environmental services

Esta capa:

- no se define primero
- se descubre por clustering
- se nombra despues con curacion humana

### 2. Transition Function

Describe que transicion material o productiva habilita la empresa.

No dice como funciona tecnicamente, sino que reemplaza o reconfigura.

Ejemplos:

- fossil-to-bio inputs
- extractive-to-regenerative agriculture
- animal-to-biofabricated proteins
- petrochemical-to-biobased materials
- centralized-to-distributed bioproduction
- waste-to-feedstock valorization

Esta capa es crucial para la narrativa del proyecto, porque conecta startups con la tesis mayor de transicion material basada en la vida.

### 3. Technical Stack

Describe el mecanismo tecnico o cientifico principal.

Ejemplos:

- precision fermentation
- industrial fermentation
- synthetic biology
- microbial engineering
- enzyme engineering
- plant molecular systems
- mycelium systems
- cell-based production
- computational bio / biodata infrastructure
- continuous bioprocessing
- bioelectrochemical systems

Esta capa es importante para:

- mapear afinidad tecnica
- detectar infraestructura comun
- identificar plataformas y enabling technologies

### 4. Output Class

Describe el tipo de producto o servicio que sale al mercado.

Ejemplos:

- biomaterials
- food ingredients
- ag inputs
- biologics tools
- manufacturing platforms
- diagnostics tools
- environmental services
- molecular design / bioinformatics software

Esto permite comparar startups que usan mecanismos distintos pero venden outputs parecidos.

### 5. Market Interface

Describe como la startup se conecta con el mercado.

Ejemplos:

- ingredient supplier
- full-stack product company
- platform / foundry
- developer tools
- IP / licensing model
- science spinout
- hardware-enabled bio company
- services + product hybrid

Esto ayuda mucho a fondos y a actores de ecosistema porque traduce tecnica a modelo de negocio e interface comercial.

### 6. Maturity / Translation Path

Describe en que tramo del camino ciencia -> empresa -> mercado esta la startup.

Ejemplos:

- research-heavy
- proof of concept
- pilot
- validation
- commercial deployment
- scale-up constrained

Puede aprovechar TRL, pero no conviene depender solo de TRL.

## Como construirla de verdad

### Fase A. Corpus bottom-up

Recolectar por startup:

- website title
- one-line tagline
- about / description
- Crunchbase description
- LinkedIn description
- application text si existe
- pitch / deck text si existe

No usar una sola fuente.

El texto final por startup deberia ser un `canonical description bundle`.

### Fase B. Corpus top-down

Recolectar lenguaje desde:

- fondos especializados
- aceleradoras
- company builders
- reports y landscape maps
- tesis de inversion
- llamados a aplicar / sector pages

Esto no define clusters.
Sirve para:

- proponer nombres canónicos
- detectar sinonimos
- generar aliases de verticales
- traducir clusters emergentes a lenguaje de mercado

### Fase C. Enrichment semantico

A cada startup deberiamos extraerle:

- mechanisms
- organisms / systems
- feedstocks
- outputs
- industries served
- replacement logic
- climate / bioeconomy / material transition language

### Fase D. Clustering

No usar una unica corrida.

Haria tres niveles:

- `microclusters`
  similitud alta entre startups muy cercanas

- `mesoclusters`
  familias de trabajo

- `macrothemes`
  narrativas mas grandes para interfaz publica

### Fase E. Naming

Cada cluster deberia tener:

- `emergent_theme_label`
- `market_label`
- `definition`
- `aliases`
- `representative_startups`

## Que aprendemos de Climate Finance Tracker

Lo verificable hoy del CFT:

- usa machine learning / NLP para dejar emerger themes desde el lenguaje de las organizaciones
- el modelo fine-tuned de OpenAI se uso para `relevance filtering`, no parece ser el clasificador final de themes
- la clusterizacion se apoya en keyword enrichment y similitud semantica, no en una taxonomia cerrada previa

## Traduccion al producto

La vista tipo CFT para nosotros deberia permitir:

- colorear por `emergent_theme`
- agrupar por `emergent_theme`
- filtrar por `transition_function`
- filtrar por `technical_stack`
- cambiar tamano por una metrica elegida
- abrir una ficha donde se vea por que esa startup cayo ahi

## Reglas de calidad

La taxonomia solo sirve si:

- una startup puede pertenecer a varias dimensiones sin contradiccion
- podemos explicar por que fue clasificada ahi
- podemos mapear sinonimos entre lenguaje startup y lenguaje investor
- podemos revisar clusters sin rehacer toda la estructura

## Recomendacion operativa

Orden de trabajo:

1. construir corpus startup
2. construir corpus top-down
3. crear diccionario de conceptos inicial
4. generar embeddings y clusters exploratorios
5. nombrar clusters
6. convertir eso en vistas del sitio

## Resultado esperado

No una lista de "verticales".

Sino una infraestructura taxonomica que permita decir:

- que problema de transicion material aborda la startup
- con que stack tecnico lo hace
- que output genera
- como llega al mercado
- en que theme emergente cae

Esa es la base correcta para una vista de startups estilo Climate Finance Tracker, pero mejor adaptada al dominio bio.
