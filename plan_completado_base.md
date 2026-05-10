# Plan De Completado De La Base

## Respuesta Corta

Si, podemos completar la base.

Pero hay dos sentidos posibles de "completar":

### 1. Completar la base estructural

Esto si lo podemos hacer ya.

Incluye:

- esquema definitivo
- tablas y plantillas de carga
- reglas de naming y canonizacion
- mapeo desde tus grafos y CSV actuales
- definicion de KPIs y vistas del observatorio

### 2. Completar la base factual

Esto lo podemos avanzar mucho, pero no cerrar al 100% solo con los grafos actuales.

Faltan datos que no estan hoy en los archivos auditados:

- fechas de rondas
- montos
- fuentes
- corporates y necesidades tecnologicas
- ESOs e instrumentos
- validaciones, pilotos y adopcion
- datos regionales del Cono Sur

## Que Podemos Completar Ya Mismo

Con lo que ya tienes podemos poblar una v1 seria de estas capas:

### Capa A. Actores

- startups
- inversores
- algunas organizaciones si ya aparecen en los grafos

### Capa B. Relaciones

- inversiones
- coinversion derivada
- algunos vinculos con organizaciones cuando aparezcan en tus otros grafos

### Capa C. Analitica

- centralidad
- conectividad
- clusters
- rankings por actividad

### Capa D. Observatorio estructural

- tabla de entidades
- aliases
- fuentes
- snapshots
- KPIs base

## Que Requiere Nueva Recoleccion

Para que la base quede alineada al proyecto CAB + Fundar + EGLC, necesitaremos levantar o consolidar ademas:

- corporates relevantes
- demandas tecnologicas por vertical
- programas e instrumentos
- ESOs y mecanismos de referral
- startups con pilotos y validaciones
- relaciones con universidades, labs y spinouts
- evidencia y fecha de cada hecho relevante

## Estrategia Recomendada

No intentaria completar todo junto.

Haria cuatro fases.

## Fase 1. Canonizacion Y Carga De Lo Ya Existente

Objetivo:

- convertir tus grafos y CSV en una base canonica consistente

Resultado:

- tabla de entidades limpia
- startups e inversores cargados
- relaciones de inversion normalizadas

## Fase 2. Enriquecimiento De Capital

Objetivo:

- transformar la red de inversion en una capa util para scouting y movilizacion de capital

Resultado:

- tipo de fondo
- thesis
- etapas objetivo
- geografia
- verticales
- dealflow y gaps

## Fase 3. Enriquecimiento Ecosistemico

Objetivo:

- sumar universidades, labs, ESOs, instrumentos y organizaciones puente

Resultado:

- mapa de coordinacion y fragmentacion

## Fase 4. Demanda E Intervencion

Objetivo:

- modelar necesidades tecnologicas y match con startups

Resultado:

- observatorio accionable para CAB, Fundar y EGLC

## Criterio De "Completitud"

Yo consideraria la base suficientemente completa para una v1 del observatorio cuando cumpla estas condiciones:

- `80%+` de startups objetivo con identidad canonica
- `80%+` de inversores objetivo con identidad canonica
- `90%+` de las aristas de inversion actuales ya migradas
- fuentes registradas para los hechos mas importantes
- al menos una capa inicial de corporates o demandas
- capacidad de responder preguntas clave del proyecto sin corregir a mano

## Preguntas Que La V1 Deberia Poder Responder

- que fondos invierten en biotech en Argentina
- que startups estan mas conectadas a capital
- que fondos son puentes entre clusters
- que actores concentran capacidad de articulacion
- que verticales parecen mas densas o mas fragmentadas
- donde hay vacios de capital, coordinacion o adopcion

## Siguiente Paso Recomendado

Si seguimos bien, el orden ideal es:

1. cargar y normalizar `startups`, `investors` e `investment_edges`
2. generar una lista de nombres a corregir y aliases
3. definir un set inicial de `organizations`, `esos`, `corporates` e `instruments`
4. abrir una planilla o CSV de enriquecimiento manual para la informacion que no esta en los grafos

## Mi Recomendacion Franca

Si quieres que la base realmente se use en este proyecto, hay que tratarla como:

- base canonica
- motor de observatorio
- soporte de matchmaking
- insumo de narrativa

No como export de Gephi.

Por eso, si: podemos completarla.

La forma mas solida de hacerlo es empezar por cargar bien lo que ya tienes y abrir desde ahora una capa de enriquecimiento manual guiado.
