# Diseno Del Observatorio Del Ecosistema Biotech

## Para Que Tiene Que Servir

Leyendo el documento de CAB, Fundar y EGLC, el observatorio no debe ser un repositorio pasivo ni un grafo para exploracion interna.

Tiene que funcionar como infraestructura de inteligencia para tres objetivos del proyecto:

- movilizar capital hacia startups biotech
- reducir fragmentacion y mejorar coordinacion ecosistemica
- conectar capacidades tecnologicas con demanda real

En otras palabras:

**el observatorio tiene que ayudar a intervenir en el ecosistema, no solo describirlo.**

## Traduccion Del Documento A Requisitos De Producto

El documento identifica tres cuellos de botella:

1. insuficiente movilizacion de capital
2. fragmentacion del ecosistema y baja capacidad de coordinacion
3. debiles vinculos entre startups y demanda

Eso implica que el observatorio debe responder tres familias de preguntas.

### A. Capital

- que startups estan mas cerca de ser invertibles
- que fondos invierten en que tipo de startups
- donde estan los gaps de financiamiento por etapa
- que inversores son mas activos, especializados o conectores
- que startups no estan conectadas a capital adecuado

### B. Coordinacion ecosistemica

- quienes son los actores relevantes del ecosistema
- como se conectan entre si
- donde hay fragmentacion, duplicacion o vacios
- que ESOs, universidades, camaras o instituciones actuan como puentes
- que instrumentos o programas ya existen y para quien

### C. Demanda y adopcion

- que corporates, empresas o instituciones tienen necesidades tecnologicas
- que startups podrian responder a cada necesidad
- donde ya existen validaciones, pilotos o adopciones
- que verticales o subverticales tienen mas friccion para llegar a mercado

## Tesis De Diseno

La base no deberia organizarse solo alrededor de `startups` e `investors`.

La unidad real del proyecto es:

**capacidades + actores + relaciones + necesidades + evidencia + oportunidades de intervencion**

## Modulos Del Observatorio

## 1. Directorio Canonico De Actores

Debe incluir:

- startups
- fondos
- company builders
- incubadoras y aceleradoras
- universidades
- laboratorios y centros de I+D
- corporates y empresas demandantes
- camaras y asociaciones
- ESOs
- organismos publicos
- personas clave

Cada actor necesita:

- identidad canonica
- aliases
- ubicacion
- descripcion
- foco tematico
- rol ecosistemico
- estado de actividad
- fuente y fecha de verificacion

## 2. Mapa De Relaciones

Debe registrar relaciones tipadas entre actores, no solo aristas genericas.

Relaciones minimas:

- `invested_in`
- `co_invested_with`
- `accelerated_by`
- `incubated_by`
- `spinout_of`
- `partnered_with`
- `validated_with`
- `piloted_with`
- `demands_solution_in`
- `funded_by_public_instrument`
- `member_of`
- `coordinated_with`

Cada relacion deberia tener:

- fecha o periodo
- fuente
- confianza
- estado
- notas

## 3. Capa De Capacidades

Esta es clave para que el observatorio no quede reducido a networking.

Hay que modelar:

- vertical biotech
- subvertical
- dominio cientifico
- tipo de plataforma tecnologica
- materiales o bioinsumos
- infraestructura disponible
- readiness tecnologica o comercial
- capacidad de escalado

Ejemplos:

- precision fermentation
- synthetic biology
- ag-biotech
- biomaterials
- diagnostics
- therapeutics
- industrial biotech

## 4. Capa De Demanda

Es una parte central del proyecto y no aparecia tan fuerte en tu base previa.

Debe incluir:

- empresas demandantes
- necesidad o problema tecnologico
- vertical de demanda
- nivel de urgencia
- estado del problema
- si requiere piloto, validacion, regulatory path o co-development

Y luego relaciones como:

- `startup_can_address_need`
- `startup_piloting_with_company`
- `company_seeking_solution_in_domain`

## 5. Capa De Instrumentos E Intervencion

Como el proyecto quiere influir en decisiones, politicas e instrumentos, hace falta modelar tambien:

- programas publicos
- convocatorias
- subsidios
- creditos
- instrumentos de coinversion
- eventos de articulacion
- matchmaking facilitado
- workshops o espacios de advocacy

Esto permite mostrar no solo el ecosistema, sino las palancas activas para moverlo.

## 6. Capa Analitica

Recien arriba de todo eso tiene sentido correr analitica de red:

- centralidad
- conectividad
- modularidad
- densidad por subred
- puentes entre clusters
- cobertura geografica
- gaps de capital
- gaps de demanda

## Que Tipo De Producto Es

Veo al observatorio como una mezcla de cuatro productos:

1. directorio estructurado
2. knowledge graph
3. mapa de oportunidades y cuellos de botella
4. herramienta de accion para equipos de ecosistema

No es solo:

- una web narrativa
- una base interna
- un CRM
- una visualizacion Gephi

Toma un poco de cada uno, pero con foco claro en intervencion.

## Usuarios Del Observatorio

### CAB

Lo usaria para:

- mapear actores
- detectar oportunidades de vinculacion
- priorizar startups y corporates
- mostrar densidad y valor del ecosistema

### Fundar

Lo usaria para:

- producir evidencia
- identificar fallas sistemicas
- construir insumos para politica publica
- argumentar sobre capital, coordinacion y demanda

### EGLC

Lo usaria para:

- construir narrativa estrategica
- generar visualizaciones
- convertir datos complejos en materiales comprensibles
- disenar experiencias de articulacion y advocacy

### Inversores

Lo usarian para:

- explorar dealflow
- identificar coinversores
- entender subverticales y thesis fit
- ver que startups tienen mas capacidad de validacion

### Corporates Y Demandantes

Lo usarian para:

- detectar startups o capacidades relevantes
- entender oferta tecnologica
- priorizar pilotos y validaciones

### ESOs Y Actores De Soporte

Lo usarian para:

- coordinar referral
- no duplicar esfuerzos
- ver vacios institucionales
- construir gobernanza compartida

## Entidades Recomendadas

La version anterior del esquema estaba bien para un knowledge graph general, pero para este proyecto conviene explicitar entidades adicionales.

Entidades minimas:

- `startup`
- `investor`
- `corporate`
- `university`
- `lab_or_research_center`
- `eso`
- `association_or_chamber`
- `public_agency`
- `program_or_instrument`
- `company_builder`
- `accelerator`
- `person`
- `technology_domain`
- `market_need`
- `event_or_intervention`
- `geography`

## Relaciones Recomendadas

- `invested_in`
- `co_invested_with`
- `founded_by`
- `spinout_of`
- `member_of`
- `supported_by`
- `graduated_from`
- `participated_in`
- `connected_by_project`
- `has_need`
- `addresses_need`
- `validated_with`
- `piloted_with`
- `has_capability_in`
- `active_in_geography`
- `eligible_for_instrument`
- `received_instrument`

## Indicadores Alineados Con El Documento

El documento menciona o implica varios indicadores. Conviene modelarlos desde el principio.

### Indicadores De Capital

- numero de startups conectadas con inversores relevantes
- numero de linkages investor-startup facilitados
- gap de capital por etapa
- inversion estimada movilizada
- cantidad de startups con narrativa de inversion desarrollada

### Indicadores De Conectividad Ecosistemica

- Ecosystem Connectivity Index
- densidad de relaciones entre tipos de actores
- numero de ESOs bajo mecanismos compartidos
- numero de referral pathways activos
- cantidad de actores con informacion actualizada y verificable

### Indicadores De Demanda

- numero de company-startup linkages facilitados
- cantidad de pilotos o validaciones disparadas
- necesidades tecnológicas mapeadas por vertical
- tasa de match entre necesidades y capacidades

### Indicadores De Politica Y Bienes Publicos

- casos de politicas o instrumentos informados por el proyecto
- numero de datasets abiertos publicados
- uso del observatorio por actores externos
- frecuencia de actualizacion

## Que Falta En Tu Base Actual Para Llegar A Esto

Hoy tu base ya cubre una parte importante del modulo capital:

- startups
- fondos
- relaciones de inversion
- centralidad de red

Pero le faltan casi por completo:

- corporates y demanda
- ESOs y capacidad de articulacion
- instrumentos y programas
- fuentes y verificabilidad
- temporalidad robusta
- datos de readiness, piloto y adopcion
- capas regionales para Cono Sur

## Arquitectura Recomendada

### Capa 1. Master Data

Base canonica de entidades y aliases.

### Capa 2. Relational Facts

Hechos verificables:

- inversiones
- membresias
- spinouts
- programas
- pilotos
- validaciones
- necesidades

### Capa 3. Derived Intelligence

Metricas, clusters, indices y scores.

### Capa 4. Product Outputs

Salidas visibles:

- observatorio web
- dashboard interno
- mapas de ecosistema
- materiales de advocacy
- listas de matchmaking

## Vistas De Producto Que Tendria Sentido Construir

### Vista 1. Ecosistema

Mapa general de actores, clusters y relaciones.

### Vista 2. Capital

Startups por etapa, readiness e historial de inversion.

### Vista 3. Demanda

Problemas tecnologicos por sector y startups conectables.

### Vista 4. Coordinacion

ESOs, programas, referidos, vacios institucionales y governance.

### Vista 5. Region

Expansion a Southern Cone:

- Argentina
- Chile
- Uruguay
- Paraguay
- eventualmente Brasil sur y otros nodos relevantes

## Mi Lectura Mas Precisa De Tu Objetivo

Con el documento en mano, tu objetivo no es simplemente:

- hacer una base de fondos y startups

Tu objetivo es mas ambicioso:

**construir la capa de inteligencia de un observatorio capaz de volver al ecosistema biotech mas visible, conectable, invertible y coordinado.**

## Recomendacion Practica

El proximo salto no deberia ser sumar mas nodos al grafo sin estructura.

Deberia ser:

1. redisenar el esquema de datos segun los tres pilares del proyecto
2. definir vistas e indicadores del observatorio
3. empezar con Argentina pero con modelo regionalizable
4. separar claramente datos base, evidencia y analitica derivada

## Proximo Paso Ideal

Si seguimos bien, el siguiente entregable deberia ser:

**un esquema de base de datos v2 especificamente alineado al observatorio biotech CAB + Fundar + EGLC**

Eso nos permitiria pasar de interpretacion estrategica a implementacion.
