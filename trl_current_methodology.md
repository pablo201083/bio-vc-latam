**TRL Current Methodology**

Objetivo: dejar de usar `TRL` heredado del grafo y reemplazarlo por una capa actual, verificable y fechada.

**Principio**

No asumir que el `TRL` de una startup existe publicado de forma explicita.

En la practica, la mayoria de las startups no comunican `TRL` en sus webs. Lo que si comunican es evidencia operativa:
- producto disponible
- pilotos
- validacion por terceros
- field trials
- early access
- planta piloto
- produccion o ventas
- clientes o despliegues

Por eso la mejor metodologia es:
1. recolectar evidencia operativa actual
2. inferir `TRL current`
3. guardar fuente, fecha y confianza

**Campos recomendados**

- `trl_current`
- `trl_current_confidence`
- `trl_current_status`
- `trl_current_basis`
- `trl_current_source_url`
- `trl_current_last_checked`
- `trl_current_notes`

**Regla de inferencia**

- `TRL 4-5`
  laboratorio, prototipo temprano, validacion interna
- `TRL 6`
  prototipo relevante o piloto inicial
- `TRL 7`
  sistema o producto validado en entorno operativo relevante, early access o despliegue piloto fuerte
- `TRL 8`
  producto casi listo o ya validado para uso comercial, con despliegue serio
- `TRL 9`
  producto o servicio ya en uso comercial real

**Niveles de confianza**

- `high`
  la evidencia oficial describe despliegue, producto disponible o uso comercial de manera clara
- `medium`
  hay señales fuertes, pero la inferencia sigue siendo indirecta
- `low`
  hay solo indicios vagos

**Fuentes preferidas**

1. web oficial de la startup
2. pagina de producto oficial
3. press release oficial
4. documentacion regulatoria o de partners
5. base de inversores o medios, solo como apoyo secundario

**Regla editorial**

Si no hay evidencia actual suficiente:
- no adivinar
- dejar `trl_current_status = pending_research`

**Ejemplos de evidencia fuerte**

- `Puna Bio`
  productos listados, red de distribuidores, `How To Buy`, field trials en 35+ sitios
- `Stamm`
  plataforma lanzada y disponible para `Research Use Only`, early access partnerships
- `Bioeutectics`
  sitio oficial habla de planta de produccion, productos por industria y millones de litros reemplazados

**Conclusión**

El reemplazo correcto no es:
- `TRL viejo -> TRL nuevo inventado`

Sino:
- `TRL viejo eliminado`
- `evidencia actual -> TRL inferido con fuente y confianza`
