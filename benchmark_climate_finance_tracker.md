# Benchmark: Climate Finance Tracker Como Referencia

## Referencia Mirada

Tome como referencia principal el Climate Finance Tracker de Vibrant Data Labs / One Earth:

- [Climate Finance Tracker](https://www.climatefinancetracker.com/)
- [FAQ](https://www.climatefinancetracker.com/faq)
- [One Earth: Climate Finance Tracker](https://www.oneearth.org/who-we-fund/science-policy-grants/climate-finance-tracker/)

## Lo Que Hace Bien El Climate Finance Tracker

Hay cuatro cosas muy valiosas en ese producto.

### 1. No es una base, es una interfaz de inteligencia

No se presenta como directorio, sino como una manera de explorar:

- quien financia que
- donde hay gaps
- donde hay redundancias
- con quien hablar
- donde hay patrones invisibles a primera vista

Eso esta muy alineado con tu objetivo.

### 2. Permite ver big picture y drill-down

Uno de sus puntos mas fuertes es que no obliga a elegir entre:

- mapa general
- detalle por entidad

Permite las dos cosas a la vez:

- clusters emergentes
- filtros
- busqueda
- vistas guardadas
- detalle por organizacion

Esa combinacion es clave.

### 3. La taxonomia no esta cerrada del todo

El tracker usa lenguaje, clustering y enriquecimiento para dejar que los temas emerjan del dataset en vez de imponer solo una taxonomia fija desde arriba.

Eso es especialmente importante para biotech, porque:

- las fronteras entre verticales se mueven rapido
- muchas startups cruzan health, food, materials, agriculture y platform technologies
- una taxonomia excesivamente rigida se vuelve vieja rapido

### 4. Tiene una segunda vista de coinversion

La inversion de la red para ver funders conectados por coinversion es muy buena idea.

En tu caso eso puede ser todavia mas potente, porque el proyecto no trata solo de funding, sino tambien de:

- articulacion ecosistemica
- demanda
- ESOs
- capacidades

## Donde Tu Proyecto Deberia Ser Mejor

El Climate Finance Tracker es muy buena referencia, pero para tu caso yo no trataria de imitarlo sin mas.

Tu observatorio puede ser mejor en al menos seis dimensiones.

## 1. Mas verificable

El CFT mismo admite que:

- no es un censo
- no es exhaustivo
- hay errores y falsos positivos
- depende de fuentes subyacentes como Crunchbase y Candid

En tu caso conviene mejorar eso con:

- `source_id` por hecho importante
- `confidence_score`
- `last_verified_at`
- distincion clara entre dato observado y dato inferido
- workflow de correccion y feedback

Tu base deberia ser mas auditable.

## 2. Mas orientado a intervencion

El CFT es muy bueno para exploracion.

Tu observatorio tiene que dar un paso mas:

- matchmaking
- priorizacion
- deteccion de gaps accionables
- articulacion de actores
- soporte para advocacy y politica

O sea:

**no solo ver el ecosistema, sino moverlo.**

## 3. Mas rico en tipos de actor

El CFT gira sobre todo alrededor de funders y recipients.

Tu producto tiene que incluir explicitamente:

- startups
- inversores
- corporates
- universidades
- labs
- ESOs
- camaras
- organismos publicos
- instrumentos
- necesidades de mercado
- pilotos y validaciones

Eso lo vuelve mucho mas util para CAB, Fundar y EGLC.

## 4. Mas fuerte en demanda

Esta es la gran diferencia.

El documento del proyecto dice claramente que uno de los tres problemas estructurales es la debilidad del vinculo entre startups y demanda.

Entonces tu producto no puede quedarse en:

- who funds what

Tiene que pasar a:

- who needs what
- who can solve what
- who validated what
- where are the adoption bottlenecks

Eso seria una mejora real sobre el Climate Finance Tracker.

## 5. Mas util para construccion de narrativa

El CFT ya tiene una capa narrativa fuerte, pero en tu caso eso es central.

El observatorio deberia servir para producir:

- mapas
- rankings
- historias de cluster
- casos de exito
- cuellos de botella del sistema
- materiales para advocacy
- insumos para policy design

No solo para exploracion interactiva.

## 6. Mejor curacion humana

El CFT apuesta bastante a la automatizacion y a un pipeline escalable.

Tu proyecto necesita una mezcla mas fuerte entre:

- automatizacion
- curacion editorial
- validacion sectorial

Porque el universo biotech argentino y del Cono Sur es mas chico, mas denso y mas relacional.

La calidad de la representacion importa mucho.

## Mi Lectura Del Producto Objetivo

Si tomo la referencia del CFT y la cruzo con tu documento, lo que ustedes deberian construir es algo asi:

**un biotech ecosystem intelligence tracker**

No una copia del CFT.

Seria una mezcla de:

- Climate Finance Tracker
- Crunchbase tematico
- directorio ecosistemico
- mapa de coinversion
- mapa de capacidades y demanda
- herramienta de matchmaking
- soporte de advocacy

## Componentes Del Producto

## 1. Vista Ecosistema

Un mapa explorable de actores del ecosistema:

- startups
- fondos
- universidades
- labs
- corporates
- ESOs

## 2. Vista Capital

Una vista de:

- quien invierte en quien
- coinversion
- gaps por etapa
- fondos puente
- subverticales con mas y menos capital

## 3. Vista Demanda

Una vista de:

- necesidades tecnologicas
- startups potencialmente matcheables
- validaciones existentes
- corporates con mayor capacidad de absorcion

## 4. Vista Coordinacion

Una vista de:

- ESOs
- programas
- instrumentos
- referral pathways
- zonas de duplicacion y vacio institucional

## 5. Vista Region

Una vista comparable para:

- Argentina
- Chile
- Uruguay
- Paraguay
- otros nodos del Cono Sur

## 6. Vista Perfil

Cada entidad deberia tener un perfil fuerte, tipo ficha:

- descripcion
- tags
- relaciones
- fuentes
- historial
- validaciones
- related actors

## Funcionalidades Que Vale La Pena Tomar Del CFT

- busqueda global
- filtros combinables
- vistas guardadas o snapshots
- mapa de clusters
- lista lateral de seleccion
- ficha detallada por entidad
- capa de coinversion

## Funcionalidades Que Deberian Superarlo

- feedback y correccion de datos
- mayor trazabilidad de fuentes
- mejor capa de demanda
- mejor capa de validaciones y pilotos
- mejor modelado de universidades, labs y ESOs
- indicadores directamente ligados a intervenciones del proyecto
- capacidad de generar shortlists de matchmaking

## Principios De Producto

Si lo encaramos bien, yo trabajaria con estos principios:

### 1. Explorable, no solo explicativo

El usuario tiene que poder descubrir cosas, no solo leer una conclusion prearmada.

### 2. Canonico, pero no rigido

La base tiene que estar limpia, pero la taxonomia no puede volverse una jaula.

### 3. Transparente en incertidumbre

El producto tiene que mostrar que hay datos confirmados, inferidos y pendientes de revision.

### 4. Multiproposito

Tiene que servir a la vez para:

- analisis
- narrativa
- matchmaking
- politica publica

### 5. Actualizable

No puede depender de rehacer todo a mano cada vez.

## Implicancias Para La Base

Esto empuja a que la base final tenga, ademas de entidades y relaciones:

- `sources`
- `confidence_score`
- `last_verified_at`
- `relationship_status`
- `snapshot` o `saved_view`
- `matchmaking_status`
- `intervention_outcome`

## Mi Recomendacion Clara

Si el objetivo es "algo como el Climate Finance Tracker pero mejor", yo lo traduciria asi:

**tomar la potencia de exploracion visual y clustering del CFT, pero combinarla con una base mas curada, mas verificable y mucho mas orientada a intervencion ecosistemica.**

Ese “mejor” no deberia significar:

- mas features

Deberia significar:

- mas verdad
- mas utilidad operativa
- mas capacidad de accionar sobre gaps reales

## Siguiente Paso Recomendado

Ahora que ya tenemos:

- staging
- merges sugeridos
- esquema v2
- benchmark del CFT

el siguiente paso correcto seria:

**crear una primera capa canonica derivada de staging, aplicando solo merges de alta confianza y dejando trazabilidad completa.**

Eso nos acerca de verdad al producto.
