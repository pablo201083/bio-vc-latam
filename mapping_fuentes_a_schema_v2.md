# Mapping De Fuentes Actuales A Schema V2

## Fuentes Ya Detectadas

- `nodoseco.csv`
- `edgeseco.csv`
- `latam_coinvest_network_v3.graphml`
- proyectos `*.gephi` con metricas derivadas

## Mapping Inicial

## 1. `nodoseco.csv`

Campos observados:

- `Id`
- `Label`
- `0`
- `pageranks`
- `indegree`
- `outdegree`
- `Degree`
- `weighted indegree`
- `weighted outdegree`
- `Weighted Degree`

Destino:

- `entities`
- `startups`
- `investors`
- `derived_graph_metrics`

Mapping recomendado:

- `Id` -> `entities.entity_id`
- `Label` -> `entities.canonical_name`
- `0` -> `entities.entity_type`
- `pageranks` -> `derived_graph_metrics.pagerank`
- `indegree` -> `derived_graph_metrics.indegree`
- `outdegree` -> `derived_graph_metrics.outdegree`
- `Degree` -> `derived_graph_metrics.degree_total`
- `Weighted Degree` -> `derived_graph_metrics.weighted_degree`

## 2. `edgeseco.csv`

Campos observados:

- `Source`
- `Target`
- `Type`
- `Id`
- `Label`
- `Weight`
- `1`

Destino:

- `investment_edges`

Mapping recomendado:

- si `1 = investment`, usar la convencion canonica `investor_id -> startup_id`
- `Id` -> `investment_edges.investment_id`
- `Source` o `Target` -> `investor_id`
- `Target` o `Source` -> `startup_id`
- `Weight` -> se puede conservar en `notes` o como proxy de intensidad si hiciera falta

Nota:

Antes de importar hay que resolver la direccion semantica, porque hoy no es consistente entre archivos.

## 3. `latam_coinvest_network_v3.graphml`

Campos observados en nodos:

- `label`
- `type`

Campos observados en aristas:

- `type`
- `startup`
- `investor`

Destino:

- `entities`
- `startups`
- `investors`
- `investment_edges`
- `entity_aliases`

Uso recomendado:

- usarlo como fuente mas rica para reconstruir nombres y relaciones
- usar `startup` e `investor` como ayuda para corregir direccion y naming

## 4. Proyectos Gephi

Uso recomendado:

- no usarlos como fuente maestra
- si usarlos para:
  - snapshots
  - metricas derivadas
  - modularidad
  - layouts y visualizaciones

## Campos Que No Estan En Las Fuentes Actuales

Habra que enriquecerlos aparte:

- `website`
- `country_code`
- `city`
- `stage`
- `biotech_vertical`
- `technology_platform`
- `thesis`
- `ticket_min_usd`
- `ticket_max_usd`
- `source_id`
- `confidence_score`
- `announced_date`
- `amount`
- `currency`
- `market_needs`
- `policy_instruments`
- `interventions`

## Regla De Importacion

Orden recomendado:

1. `entities`
2. `entity_aliases`
3. `startups`
4. `investors`
5. `investment_edges`
6. `ecosystem_metrics_snapshots`
7. `derived_graph_metrics`

## Regla De Calidad

Antes de importar:

- corregir nombres rotos
- unificar mayusculas y separadores
- resolver duplicados
- decidir direccion canonica de `investment_edges`
