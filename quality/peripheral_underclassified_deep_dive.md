**Peripheral Underclassified Deep Dive**

Fecha: 2026-04-19

**Diagnostico**

`peripheral or underclassified ventures` no se comporta como categoria real.

Razones:
- tiene `73` startups
- `73/73` vienen de `Other / Unclassified`
- `73/73` fueron asignadas por `fallback_default`
- confianza uniforme y baja: `0.41`

En otras palabras:
- no expresa una familia semantica
- no representa una tesis
- no sirve como cluster para explorar
- funciona como cola de trabajo y revision

**Que hay adentro**

1. Empresas relevantes para ecosistema general, pero fuera de tesis:
- `Auth0`
- `Betterfly`

2. Casos posiblemente relevantes para clima/materialidad/regeneracion que merecen revision:
- `Alkemio`
- `CIRCCLO`
- `Courageous Land`
- `Luzid`
- `Nuclearis`
- `Nuvia`
- `OneInfinite`
- `SoyGREEN`
- `Wisy`

3. Resto:
- mezcla de nombres con poca metadata, baja conectividad y sin senal clara de materialidad o biocentrismo

**Senales de madurez**

La mayoria del bucket esta subdescripta:
- `61` casos sin `TRL`
- `61` casos con `valuation_tier = 1`

Eso refuerza que el problema principal no es de teoria, sino de falta de informacion estructurada.

**Casos mas conectados**

Top por degree dentro del bucket:
- `Auth0`
- `ArgenTAG`
- `Sima`
- `Eiwa`
- `Tracestory`
- `Arakion`
- `Fecundis`
- `Betterfly`
- `Courageous Land`
- `Wisy`

Lectura:
- algunos son conocidos
- pocos parecen centrales para una tesis bio/materiales
- la conectividad no alcanza para justificar el bucket como categoria

**Conclusion**

No es una buena categoria.

Lo correcto seria tratarla como una de estas dos cosas:
- `review queue`
- `unclassified / needs research`

No deberia aparecer primera en una vista publica thesis-first.

**Siguiente Paso Recomendado**

1. renombrarla en la UI a `Unclassified / Needs Review`
2. mandarla al final del orden visual
3. sacar de ahi primero los `9` casos con posible keep
4. bajar el resto si siguen sin señal de materialidad o regeneracion
