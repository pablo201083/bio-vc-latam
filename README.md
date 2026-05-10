# BIO VC LATAM Ecosystem Tracker

Documento de bienvenida para entender rapido que es este proyecto, que ya construimos y como seguir trabajando sin perder el hilo.

## Que estamos buscando lograr

Este proyecto construye una base de referencia y una capa visual de inteligencia ecosistemica para mapear startups BIO VC LATAM y la red de capital que las financia.

No es solamente una lista de startups. La ambicion es hacer que el universo BIO de America Latina sea reconocible, buscable, comparable, invertible y accionable: que podamos ver que empresas existen, por que entran o salen de la tesis, que tan buena es la evidencia, como se agrupan semanticamente y que fondos o actores de capital las conectan.

La tesis BIO se usa en sentido amplio. Incluye startups bio-based, biocentricas, de transicion material basada en sistemas vivos, regenerativas o que ayudan a gestionar limites planetarios. Tambien puede incluir software, sensores, IA, infraestructura o energia si estan claramente acoplados a agricultura, biologia, materiales, recursos, resiliencia climatica o sistemas planetarios.

## Principio rector

La base debe ser auditable. Queremos pasar de inferencias internas o resumentes generados desde taxonomia a perfiles respaldados por fuentes externas: web de la startup, portfolios de fondos, notas publicas, registros institucionales o fuentes verificables.

Las decisiones importantes tienen que ser defendibles:

- `include` significa que la startup pertenece al universo BIO VC LATAM segun la tesis.
- `exclude` significa que no pertenece, aunque sea una startup valida o interesante.
- `confirmed` significa que hay evidencia externa suficiente.
- `provisional` significa que todavia falta evidencia o curaduria.
- `reviewed` es una curaduria editorial mas fuerte.
- `seeded` significa que ya existe una buena semilla de informacion externa, pero no necesariamente una ficha completa.
- `taxonomy_stub` es una ficha provisoria generada desde taxonomia, scope y atributos estructurados; no debe ser tratada como evidencia final.

## Que construimos hasta ahora

Construimos una base unica en capas, un pipeline de reconstruccion y varias vistas HTML locales en `pilot/`. La portada actual funciona como command center: prioriza las tres preguntas centrales del proyecto y deja las demas pantallas como soporte de curaduria.

Las vistas principales son:

- `pilot/index.html`: command center del proyecto; entrada priorizada a mapa, atlas y matchmaker.
- `pilot/startup-themes.html`: mapa principal del universo BIO, ordenado por proximidad semantica y categoria operativa.
- `pilot/capital-atlas.html`: mapa navegable de capital, conectividad, weighted degree, hover explicativo y relaciones clickeables.
- `pilot/matchmaking.html`: recomendador explicable startup-fondo y fondo-startup.

Vistas de soporte:

- `pilot/startup-profiles.html`: fichas de startups, filtros, calidad de datos y estado editorial.
- `pilot/quality.html`: tracker de calidad y cobertura de la base.
- `pilot/semantic-single-level.html`: exploracion semantica con selector de `k` y pesos.
- `pilot/semantic-taxonomy-beta.html`: beta metodologica para comparar cortes semanticos.
- `pilot/funds.html`: analitica de fondos y carteras.

Las vistas son producto, no decoracion: sirven para detectar duplicados, edge cases, clusters malos, fuentes flojas, fondos subrepresentados y regiones incompletas.

## Capas de datos

La base vive repartida en capas para que sea mantenible:

- `startup_master_dataset.csv`: base maestra de startups, scope, paises, descripcion, fuente, calidad y taxonomia operativa.
- `startup_profiles_minimum_viable.csv`: perfil minimo auditable para las startups.
- `quality/`: auditorias, colas de curaduria, reportes de calidad, definiciones y resultados intermedios.
- `quality/data_contract.md`: contrato de datos; leer antes de cambiar columnas o criterios.
- `quality/thesis_scope_definition.md`: definicion de inclusion/exclusion de la tesis.
- `quality/project_context_from_pitch.md`: contexto estrategico del proyecto.
- `quality/semantic_single_level_report.md`: evaluacion de cortes semanticos y tradeoffs de `k`.
- `quality/strategic_tag_dictionary.csv`: diccionario de etiquetas multi-label como bio-based, biocentric, escalas, tecnologias y dominios.
- `canonical/`: entidades, aliases y aristas canonicas para evitar duplicados y trabajar con una sola base.
- `quality/capital_allocator_edges.csv`: relaciones de capital tipo LP, fondo de fondos, aceleradora o actor institucional.
- `pilot/*-data.js`: bundles generados para que las vistas HTML funcionen sin servidor complejo.

## Taxonomia y semantica

La taxonomia operativa actual es single-level: una categoria por startup para representar el universo BIO confirmado en el mapa. Evitamos mezclar macro/micro themes como si fueran niveles equivalentes.

La capa semantica es una herramienta de exploracion. Sirve para probar distintos `k`, pesos de tecnologia/industria/descripcion y calidad de compresion. No debe reemplazar automaticamente la taxonomia adoptada sin revisar si los clusters son explicativos, estables y creibles.

Los nombres de clusters deben salir de contenido real: descripcion, industrias, tecnologias, startups tipo y tokens distintivos utiles. Hay que evitar tokens basura como paises, conectores, frases editoriales o palabras de pipeline.

Cuando el clustering puro ubica mal un caso ya curado con fuente externa, usamos `quality/manual_semantic_theme_overrides.csv`. Esa capa no es una segunda base: es una compuerta auditable para que la asignacion operativa de producto respete evidencia externa en edge cases conocidos. La exploracion de cortes sigue existiendo, pero mapa, capital y matchmaker consumen la asignacion operativa corregida.

## Capital y grafo ecosistemico

El proyecto tambien mapea la red de capital alrededor del universo BIO LATAM: fondos, aceleradoras, instituciones, allocators y relaciones startup-fondo.

Reglas de calidad para capital:

- Priorizar relaciones publicas o auditables.
- Consolidar sinonimos de fondos antes de graficar.
- Evitar aristas privadas, aisladas o heredadas si no sirven al analisis.
- Distinguir startup, fondo/inversor, allocator, institucion y fuente.
- Usar el grafo para ver estructura: hubs, vacios, fondos especializados, carteras por theme y startups sin capital documentado.

El `Capital Atlas` usa diametros por `weighted degree`: no solo cuenta conexiones, sino que pondera el peso/evidencia de las aristas visibles. El hover sirve como lectura rapida sin seleccionar; el click fija nodos o relaciones para navegar vecindarios y evidencia.

## Matchmaking

El proyecto ya incluye una primera capa de recomendacion explicable:

- Modo startup: sugiere fondos a contactar por fit tematico, pais, tags BIO, profundidad de cartera, comparables y calidad de evidencia.
- Modo fondo: sugiere startups no invertidas que se parecen a la cartera o cubren adyacencias relevantes.
- Cada recomendacion muestra score, razones ponderadas y comparables. No es una caja negra: debe ayudar a priorizar conversaciones, no reemplazar criterio editorial.

## Como reconstruir

Los scripts estan en `scripts/`. Normalmente conviene correr solo el script necesario, pero si cambia la base canonica o la base maestra hay que regenerar las capas dependientes.

Comandos utiles en PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\rebuild_reference_pipeline.ps1

# Si se necesita correr por capas:
powershell -ExecutionPolicy Bypass -File scripts\build_startup_master_dataset.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_startup_profiles_minimum_viable.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_startup_taxonomy_layer.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_semantic_single_level_sweep.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_semantic_quality_queue.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_canonical_layer.ps1
powershell -ExecutionPolicy Bypass -File scripts\validate_reference_base.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_capital_atlas_data.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_capital_quality_dashboard_data.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_fund_analytics_data.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_matchmaking_recommendations.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_quality_dashboard_data.ps1
powershell -ExecutionPolicy Bypass -File scripts\validate_product_surface.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_pilot_data.ps1
```

Validaciones minimas antes de confiar en una nueva version:

- `quality/reference_validation_report.csv`: errores en cero; warnings de edges canonicos en descenso.
- `quality/semantic_quality_queue.csv`: high semantic risk por debajo de 15 antes de usar el mapa como producto.
- `pilot/capital-quality-data.js`: mirar `capital_readiness_pct`, `public_edge_pct` y `specific_edge_pct`.
- `quality/product_surface_validation.csv`: las pantallas de producto no deben filtrar labels internos de backoffice.

Si se toca una visualizacion, abrirla y mirarla. El feedback visual importa: zoom inicial, jerarquia, legibilidad, hover, filtros, opacidad, etiquetas y tamanos de nodos son parte del producto.

## Si sos una IA trabajando en este repo

Arranca por leer este README, `quality/data_contract.md`, `quality/project_context_from_pitch.md` y `quality/thesis_scope_definition.md`.

Antes de editar, revisa `git status`. Puede haber cambios del usuario o de otra pasada de trabajo. No reviertas cambios que no hiciste.

Cuando mejores datos, no llenes huecos con inferencia endogena como si fuera fuente. Si usas una fuente externa, preserva URL, tipo de fuente, resumen y criterio de inclusion/exclusion.

Cuando mejores visualizaciones, no optimices solo el codigo: mira la pantalla como usuario. Este proyecto necesita mapas que ayuden a pensar, no solo graficos que rendericen.

Cuando incorpores nuevas startups o fondos, busca la minima entidad canonica posible. No dupliques Puna Bio, GridX, SF500, etc. Usa aliases cuando haga falta.

## Estado mental del proyecto

Estamos en una etapa de consolidacion: ya hay una base grande, una taxonomia operativa, una exploracion semantica, un tracker de calidad, una vista de perfiles y un atlas de capital. El foco ahora es subir calidad, completitud y confianza.

Prioridades proximas:

- Completar fuentes externas para todo el universo `include` y mejorar tambien los `exclude`.
- Agotar busqueda por fondos clave, especialmente Brasil y fondos regionales subrepresentados.
- Consolidar fondos, allocators y sinonimos para enriquecer el grafo de capital.
- Mejorar aristas relevantes con evidencia publica.
- Auditar clusters que pierden credibilidad por startups mal ubicadas.
- Mantener la taxonomia operativa estable, pero seguir explorando cortes semanticos mejores.
- Convertir las vistas en herramientas de decision: claras, navegables, comparables y honestas sobre calidad.

## Nota de orientacion

El nombre del producto es BIO VC LATAM Ecosystem Tracker. La carpeta local puede conservar un nombre historico de una etapa anterior del trabajo; no usar ese nombre viejo para interpretar el alcance del proyecto.
