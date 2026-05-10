# Auditoria De La Base De Fondos Y Startups

## Lo Que Parece Que Estas Buscando

La estructura de tus grafos sugiere que no estas construyendo solo una visualizacion, sino una base de inteligencia relacional del ecosistema.

El objetivo implícito parece ser:

- mapear que fondos invierten en que startups
- detectar patrones de coinversion
- identificar startups centrales o prometedoras
- conectar startups con universidades, laboratorios y origen tecnologico
- ubicar clusters por vertical, materiales o areas cientificas
- encontrar oportunidades de scouting, thesis building y alianzas

En una frase:

> quieres un knowledge graph operativo del ecosistema, no solo un grafo bonito.

## Evidencia Encontrada En Tus Archivos

### 1. Red startup-inversor

En `latam_coinvest_network_v3.graphml` aparecen:

- `250` nodos
- `203` startups
- `47` inversores
- `274` aristas

Los nodos tienen al menos estos atributos:

- `label`
- `type`

Las aristas tienen al menos estos atributos:

- `type`
- `startup`
- `investor`

La muestra de aristas indica relaciones startup -> inversor, por ejemplo:

- `stamm -> indiebio`
- `stamm -> draper_associates`
- `beeflow -> future_ventures`

### 2. CSV operativo mas chico

En `nodoseco.csv` y `edgeseco.csv` aparece un recorte de la red con:

- `217` nodos
- `207` startups
- `10` inversores
- `226` aristas
- una sola etiqueta de arista dominante: `investment`

Tambien aparecen metricas de red ya calculadas:

- `pageranks`
- `indegree`
- `outdegree`
- `Degree`
- `weighted indegree`
- `weighted outdegree`
- `Weighted Degree`

### 3. Fondos claramente centrales

En el CSV auditado, los inversores con mayor `outdegree` son:

- `GridX` con `78`
- `The Ganesha Lab` con `35`
- `AIR Capital` con `30`
- `SF500` con `24`
- `DraperCygnus` con `22`

Esto confirma que estas pensando la base tambien como herramienta para detectar nodos estrategicos del ecosistema.

### 4. Proyecto Gephi con analitica

El archivo `Ecosistema Startups Materiales Universidades Fondos Startups 426112025.gephi` guarda estadisticas como `PageRank`, lo cual indica que el grafo no esta siendo usado solo como mapa visual, sino como instrumento de analisis estructural.

## Diagnostico De La Base Actual

La base actual tiene bastante valor, pero hoy esta mas cerca de un grafo exploratorio que de una base canonica y escalable.

### Fortalezas

- ya separas al menos `startup` e `investor`
- ya capturas relaciones de inversion
- ya calculas centralidad y conectividad
- ya piensas en extensiones hacia `universidades`, `materiales` y ecosistema ampliado

### Debilidades

- los nodos tienen pocos atributos de negocio
- las aristas son demasiado pobres para analisis historico serio
- no se ve capa de fuentes, evidencia o confianza
- hay inconsistencias de naming
- hay posibles inconsistencias de direccion semantica entre archivos
- parte de la informacion esta embebida en el layout o en el proyecto Gephi, no en una base reusable

### Problemas concretos observables

- `Stämm` aparece mal codificado como `StÃ¤mm`
- `sillicon_catalyst` parece typo de `Silicon Catalyst`
- en un archivo la relacion parece `startup -> investor`
- en otro CSV la relacion aparece `investor -> startup`
- `KEM Ventures` aparece como inversor pero con `outdegree = 0`, lo que sugiere nodo incompleto o dato faltante

## Hipotesis Central

La base que realmente necesitas no es:

- una tabla de startups
- una tabla de fondos
- un Gephi mas prolijo

La base que realmente necesitas es:

**un knowledge graph verificable, con entidades canonicas, relaciones tipadas, temporalidad, fuentes y score de confianza.**

## Modelo Recomendado

## Entidades Principales

### `startup`

Campos recomendados:

- `startup_id`
- `canonical_name`
- `aliases`
- `country`
- `city`
- `founded_year`
- `status`
- `stage`
- `vertical`
- `subvertical`
- `materials_focus`
- `science_domain`
- `website`
- `description`
- `founders`
- `origin_type`
- `origin_org_id`
- `last_verified_at`

### `investor`

Campos recomendados:

- `investor_id`
- `canonical_name`
- `aliases`
- `investor_type`
- `country`
- `hq_city`
- `thesis`
- `preferred_stages`
- `ticket_min`
- `ticket_max`
- `lead_behavior`
- `focus_verticals`
- `website`
- `active_status`
- `last_verified_at`

### `organization`

Para universidades, labs, incubadoras, corporates y centros de investigacion.

Campos recomendados:

- `org_id`
- `canonical_name`
- `org_type`
- `country`
- `city`
- `website`
- `description`
- `parent_org_id`

### `person`

Para founders, investigadores clave, angels, operadores, etc.

Campos recomendados:

- `person_id`
- `full_name`
- `aliases`
- `country`
- `linkedin_or_profile`
- `primary_role`

### `technology_domain`

Para materiales, areas cientificas y focos tecnologicos.

Campos recomendados:

- `domain_id`
- `domain_name`
- `domain_type`
- `parent_domain_id`

## Relaciones Principales

### `invested_in`

Relacion entre inversor y startup.

Campos recomendados:

- `edge_id`
- `investor_id`
- `startup_id`
- `round_name`
- `round_stage`
- `announced_date`
- `amount`
- `currency`
- `is_lead`
- `source_url`
- `source_excerpt`
- `confidence_score`
- `last_verified_at`

### `co_invested_with`

Relacion derivada entre dos inversores.

Campos recomendados:

- `edge_id`
- `investor_a_id`
- `investor_b_id`
- `shared_startups_count`
- `first_shared_deal_date`
- `last_shared_deal_date`
- `strength_score`

### `founded_by`

- `startup_id`
- `person_id`
- `role`
- `start_date`

### `spinout_of`

- `startup_id`
- `org_id`
- `spinout_type`
- `evidence`
- `confidence_score`

### `graduated_from`

- `startup_id`
- `org_id`
- `program_name`
- `cohort`
- `date`

### `focused_on`

- `startup_id` o `investor_id`
- `domain_id`
- `strength`

## Reglas De Modelado

### 1. Nombre canonico + alias

Nunca usar el label del grafo como unica identidad.

Necesitas:

- un nombre canonico
- variantes y aliases
- un slug estable
- ids internos

Ejemplo:

- canonico: `Draper Cygnus`
- alias: `DraperCygnus`, `draper_cygnus`

### 2. Separar hechos de derivadas

No guardar PageRank o modularidad como si fueran hechos de negocio.

Separar:

- hechos observables: inversion, origen, aceleracion, partnership
- metricas derivadas: PageRank, betweenness, outdegree, comunidad

Las metricas derivadas deberian regenerarse, no ser la fuente principal.

### 3. Toda relacion importante debe tener fuente

Cada arista relevante deberia poder responder:

- de donde sale este dato
- cuando fue verificado
- cuan confiable es

### 4. La temporalidad importa

Sin tiempo, pierdes la posibilidad de responder:

- que fondo fue primero en entrar
- quien coinvirtió en una misma etapa
- que startups estan activas recientemente
- como evoluciono una tesis de inversion

## Estructura Minima Viable

Si quisieras llevar esto rapido a una base util, el MVP deberia tener al menos estas tablas:

1. `startups`
2. `investors`
3. `organizations`
4. `domains`
5. `investment_edges`
6. `startup_org_edges`
7. `entity_aliases`
8. `sources`

## Scorecard De Calidad De La Base

Puedes usar esta rubric para medir si la base esta mejorando:

- `Cobertura`: cuantas startups y fondos relevantes estan cargados
- `Profundidad`: cuantos atributos utiles tiene cada entidad
- `Conectividad`: cuantas relaciones validas y tipadas existen
- `Temporalidad`: cuanto de la red tiene fecha o ventana temporal
- `Verificabilidad`: cuantas relaciones tienen fuente
- `Normalizacion`: cuantos nombres ya estan canonizados
- `Utilidad`: cuantas preguntas reales puedes responder sin corregir a mano

## Preguntas Que La Base Ideal Deberia Poder Responder

- que fondos mas invierten en startups de materiales en LatAm
- que startups comparten coinversores
- que universidades originan mas startups invertibles
- que inversores conectan biotech con materials
- que clusters aparecen por pais, etapa y area cientifica
- donde hay startups prometedoras sin fondos de referencia
- que fondos parecen mejores socios para una startup especifica

## Prioridades Inmediatas

### Prioridad 1. Canonizacion

- unificar nombres
- corregir typos
- definir ids estables
- consolidar aliases

### Prioridad 2. Direccion semantica

Definir una sola convención:

- o `investor -> startup`
- o `startup <- investor`

Mi recomendacion:

- usar semanticamente `investor -> startup`
- y derivar vistas inversas cuando haga falta

### Prioridad 3. Enriquecimiento de aristas

Agregar a inversiones:

- fecha
- ronda
- monto
- fuente
- confianza

### Prioridad 4. Ampliar tipos de entidad

Incorporar de forma canonica:

- universidades
- labs
- aceleradoras
- corporates
- founders
- dominios tecnologicos

### Prioridad 5. Separar analitica de datos base

Mantener Gephi para exploracion y visualizacion, pero no como base maestra.

La base maestra deberia vivir en tablas limpias, desde donde luego exportas al grafo.

## Recomendacion Operativa

La mejor arquitectura para ti probablemente sea:

1. una base maestra tabular o relacional
2. una capa de limpieza y canonizacion
3. una exportacion a formato de grafo para analitica y visualizacion

Flujo recomendado:

`fuentes crudas -> tablas canonicas -> relaciones verificadas -> export a graph -> analitica`

## Siguiente Paso Sugerido

El siguiente paso con mayor retorno no es seguir dibujando el grafo.

Es este:

**tomar tus archivos actuales y convertirlos en una primera base canonica con esquema fijo, nombres normalizados y relaciones enriquecibles.**

Eso te permitiria:

- crecer sin romper consistencia
- incorporar universidades y materiales de verdad
- hacer scouting mucho mejor
- comparar ecosistemas y subredes
- generar visualizaciones mas potentes despues

## Mi Conclusión

Si mi inferencia es correcta, tu proyecto apunta a construir una especie de:

**atlas relacional del ecosistema science-based y materials en LatAm, centrado en startups, fondos y origen tecnologico.**

Ese objetivo tiene mucho sentido y tus grafos ya contienen una base muy valiosa.

Lo que falta ahora no es intuicion.

Lo que falta es convertir esa intuicion en una base canonica, verificable y escalable.
