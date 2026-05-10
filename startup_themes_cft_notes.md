# Startup themes y Climate Finance Tracker

## Lo que pude verificar del CFT

Con base en la FAQ del Climate Finance Tracker y materiales de One Earth / ImpactAlpha:

- El `LLM fine-tuned de OpenAI (babbage GPT-3)` se uso para `filtrar relevancia`, no como clasificador final de themes.
- La capa de themes parece construirse con:
  - descripciones propias de cada organizacion
  - enrichment de keywords climate-relevant
  - comparacion de similitud entre "keyword signatures"
  - clustering automatico / self-organizing

## Fuentes usadas

- [FAQ del Climate Finance Tracker](https://www.climatefinancetracker.com/faq)
- [One Earth: Climate Finance Tracker](https://www.oneearth.org/who-we-fund/science-policy-grants/climate-finance-tracker/)
- [ImpactAlpha sobre la taxonomia](https://impactalpha.com/three-pillars-of-climate-action-turning-gaps-into-opportunities-with-the-climate-finance-tracker/)
- [Primer.ai sobre el tracker](https://primer.ai/business-solutions/primer-partners-with-oneearth-using-ai-to-fight-climate-change/)

## Traduccion correcta a nuestro caso

Si queremos una vista startup-only equivalente, el pipeline correcto no es:

`startup -> LLM -> cluster final`

Sino algo mas parecido a:

1. `description ingestion`
   sitio, Crunchbase, deck, tagline, descripcion corta, pitch.

2. `relevance / scope filter`
   biotech non-pharma, material transition, etc.

3. `keyword or concept enrichment`
   tags, terms, concepts, application domains, materials, methods.

4. `theme signatures`
   vector o bolsa de conceptos por startup.

5. `similarity + clustering`
   self-organizing themes.

6. `human naming`
   nombre legible de cada cluster emergente.

## Lo que hice hoy

Como todavia no tenemos descripciones propias limpias para todas las startups, deje una vista piloto que emula la interfaz correcta pero usa como proxy:

- `structured_sector / gridx_vertical` del grafo completo
- solo `startups`
- layout por clusters tematicos

## Implicancia

La nueva vista es buena para:

- probar el formato tipo CFT
- discutir taxonomia
- separar lectura tematica de lectura de red

Pero todavia no es el clasificador final tipo CFT.

Para llegar a eso necesitamos importar `descripciones propias por startup`.
