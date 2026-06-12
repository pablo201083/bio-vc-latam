# Definición Operativa de "BIO" — documento vivo

> **Propósito.** Hacer que la decisión "¿esto es BIO, y con qué intensidad?" sea
> reproducible, defendible y consistente entre curadores y entre sesiones. No
> reemplaza a `thesis_scope_definition.md` (que define inclusión/exclusión del
> universo) ni a `data_contract.md`; los **complementa** agregando el eje de
> *intensidad biológica* y un registro de precedentes que crece con cada caso
> límite que resolvemos.
>
> **Cómo se actualiza.** Cada vez que resolvemos un edge case no trivial, se
> agrega una fila al **Registro de precedentes** con la regla que lo decidió. Si
> un caso obliga a cambiar una regla, se anota en el **Changelog**. Mantener este
> archivo es parte del trabajo de clasificación, no un extra.

---

## 1. Principio rector

BIO se entiende **en sentido amplio**: una tecnología de propósito general para
**transformar la base material de la economía** usando sistemas vivos, biomoléculas
o lógica de transición material / límites planetarios (del pitch). El universo no
es "biotech" en sentido estrecho: incluye agricultura, salud, materiales, alimentos,
recursos, clima y naturaleza cuando el vínculo material es claro.

La consecuencia operativa: **"pertenecer al universo" y "ser biológicamente intenso"
son preguntas distintas.** Una empresa puede pertenecer a la tesis amplia sin que la
biología sea su motor. Confundir ambas cosas es lo que produce clasificaciones
indefendibles (un marketplace de reciclaje etiquetado como "biomaterial").

---

## 2. Los dos ejes de decisión

Toda startup se evalúa en **dos ejes independientes**, que mapean a dos campos:

| Eje | Campo | Pregunta |
|-----|-------|----------|
| **Pertenencia** | `scope_decision` (include / review / exclude) | ¿Está dentro de la tesis BIO LATAM amplia? |
| **Intensidad biológica** | `is_bio_universe` (1 / 0) | ¿Los sistemas vivos/biomoléculas son el **core**, o es tech acoplada a un dominio bio/recursos? |

Una celda `include + is_bio_universe=0` es **legítima y deseable**: marca una empresa
eco-adyacente que pertenece al ecosistema pero cuyo motor no es biológico. No la
escondemos ni la forzamos a un tema biológico que no le corresponde.

---

## 3. Niveles de intensidad biológica

Cuatro niveles, de más a menos biológico. Los dos primeros son `is_bio_universe=1`;
los dos últimos, `=0` (aunque el tercero suele seguir `include`).

### A. `bio-core` — los sistemas vivos SON el producto · `is_bio_universe=1`
La biología, las biomoléculas o los organismos son el mecanismo central.
**Señales:** fermentación, biocontrol, biofertilizantes, terapias, diagnóstico
molecular, edición génica, enzimas, biomateriales producidos por organismos,
biorremediación microbiana.
**Ejemplos:** Caspr Biotech (diagnóstico CRISPR), Future Cow (caseína por fermentación),
INMET (PHB biopolímero), NotFossil (biofiltros microbianos).

### B. `bio-coupled` — tech directamente acoplada a un sistema vivo/recurso · `is_bio_universe=1`
Software, sensores, IA o hardware cuyo valor depende de y actúa sobre un sistema
biológico o de recursos naturales concreto. El acople es **directo y específico**,
no genérico. Tiene dos sub-formas:

- **B1 · acople físico/operacional** — sensa o actúa sobre un sistema vivo concreto
  (agronomía de precisión sobre el cultivo, monitoreo satelital de bosques, riego de
  precisión). Cuenta solo si lee/modula un estado biológico, no si es telemetría o
  plomería de datos genérica.
- **B2 · TechBio / representación biológica** — sistema digital que **modela, predice o
  representa** un estado o proceso biológico concreto, incorporando entendimiento
  biológico real (estructura proteica, genoma, microbioma, fisiología del cultivo,
  patología, fenotipo). El soporte es puramente computacional pero su **objeto es la
  biología**. → **Principio Isomorphic:** un sistema cuyo objeto es modelar biología
  pertenece al universo aunque no toque un tubo de ensayo (AlphaFold/Isomorphic Labs:
  predicción de estructura proteica = bio, aunque sea 100% software). No se descuenta
  por ser "software".

**Señales:** agronomía de precisión sobre el cultivo, digital twin de bioproceso,
plataformas de fenotipado, genómica/microbioma/patología predictiva, modelos de
mejoramiento o de resistencia a enfermedad.
**Ejemplos:** Agrosmart (inteligencia agronómica · B1), Mombak (reforestación + monitoreo · B1),
Aimirim (digital twin de fermentación · B1), Inkus Biotech (AI+genómica de resistencia · B2),
Codebreaker (inteligencia de microbioma · B2).

### C. `eco-adjacent` — aborda transición material/límites planetarios SIN biología · `is_bio_universe=0`
Pertenece a la tesis amplia (recursos, circularidad, clima) pero **no hay proceso
biológico ni acople directo a un sistema vivo**. Suele seguir `include` por la tesis
de transición material, pero NO es núcleo bio.
**Señales:** logística circular, marketplace de reciclaje, trazabilidad/IoT genérico,
optimización de red energética sin componente bio.
**Ejemplos:** CIRCCLO (packaging reutilizable + RFID), MUTA (marketplace de reciclaje),
Nexxto (IoT de cadena de frío).

### D. `out-of-scope` — fuera de la tesis · `scope_decision=exclude`
Digital generalista, fintech/commerce/SaaS horizontal sin relación material, hardware
de consumo sin valor bio/clínico.
**Ejemplos:** BitMEX (exchange cripto), Formlabs/Opentrons (hardware genérico).

---

## 4. Tests de decisión (en orden)

Aplicar a cada caso límite, en este orden. El primero que dispara, decide.

1. **Test de mecanismo.** ¿El valor central proviene de un sistema vivo, biomolécula u
   organismo? → **bio-core**.
2. **Test de acople.** Si es software/sensor/hardware: ¿actúa sobre y depende de un
   sistema biológico o recurso natural **específico** (este cultivo, este bosque, este
   bioproceso)? → **bio-coupled**. Si el acople es genérico (sirve a cualquier industria),
   no cuenta.

   **Gate de admisión TechBio (para software que reclama pertenencia bio).** Para *quedarse*
   dentro del universo, una empresa de software/datos/IA debe cumplir las **tres**:
   1. **Foco bio específico** — apunta a un organismo o sistema vivo concreto (este patógeno,
      este cultivo, este hato, este genoma), no "el agro" o "la salud" en general.
   2. **Entendimiento bio clave** — incorpora conocimiento biológico real (genómica, fisiología,
      microbioma, patología, fenotipo), no solo datos/transacciones genéricas.
   3. **Soporte tech = representación de la biología** — el sistema digital modela, predice o
      representa ese estado biológico (clase Isomorphic). Sensar/rociar/mover datos **no** alcanza
      si no hay un modelo de la biología detrás.

   Si cumple las tres → dentro (`is_bio_universe=1`). Si es telemetría, plomería de datos,
   marketplace, crédito o logística → **eco-adjacent** (`is_bio_universe=0`). El **tema** lo fija
   el objeto/output (agro → Farm Intelligence; fármaco → Therapeutics/Biomanufacturing), no el gate.
3. **Test de transición material.** ¿Aborda circularidad, recursos o límites planetarios
   con impacto material claro, pero sin biología ni acople directo? → **eco-adjacent**
   (`include` + `is_bio_universe=0`).
4. **Test de output (desambiguación de tema).** Una vez dentro, el **destino del output**
   define el tema, no el mecanismo: si se ingiere → Food Systems; si es material/químico/
   energía → Biomaterials; si trata → Therapeutics; si mide → Diagnostics; si es la
   plataforma de producción → Biomanufacturing. (Ver `taxonomy_cards.md`.)
5. **Test de evidencia.** ¿La decisión se sostiene con fuente externa? Si no, `review`.

### Reglas de desempate aprendidas
- **Salud animal / veterinaria / acuicultura ≠ Bioinputs.** Vacunas, inmunidad,
  reproducción o medicinas para animales son **Therapeutics**, aunque el dominio sea
  agri-food. El código `row_crops` o el dominio `agri-food` **no** alcanzan para
  clasificar como insumo de cultivo.
- **Plataforma vs producto final.** Si la empresa *vende la capacidad de producir*
  (fermentación, biofoundry, digital twin, biosintéticos) → **Biomanufacturing**. Si
  vende el *producto final* (alimento, material, terapia) → el tema de ese producto.
- **Circularidad sin biología no es Biomaterials.** Reciclaje, packaging reutilizable
  y trazabilidad sin transformación biológica son **eco-adjacent**, no biomaterial.
- **Marca de consumo ≠ Farm Intelligence.** Un producto alimenticio plant-based es
  **Food Systems**, aunque tenga claims de carbono/sustentabilidad.
- **Inteligencia agrícola: bio-coupled vs eco-adjacent (split 2026-06-12).**
  *Farm Intelligence* nombra **solo** la inteligencia digital **bio-coupled**: software,
  sensores o IA cuyo valor *depende de y actúa sobre un sistema vivo específico* — este
  cultivo, este hato (agronomía de precisión, fenotipado, monitoreo de plagas/enfermedad,
  sanidad animal, riego de precisión atado a la biología del cultivo). La capa **digital
  o financiera genérica** del agro — agrifintech, crédito/seguro rural, marketplaces,
  tokenización de granos, trade-finance, trazabilidad/logística, ERP de gestión sin lectura
  biológica — **falla el test de acople** y va a **Digital AgTech & Agrifintech**
  (`is_bio_universe=0`, eco-adjacent). El dominio `agri-food` por sí solo **no** es acople.
- **Un tema debe ser homogéneo en intensidad.** Si un tema acumula una fracción grande de
  `is_bio_universe=0`, está mal cortado: mezcla núcleo bio con eco-adjacent y diluye el
  recorte. Señal medible: Farm Intelligence tenía **47% bio=0** (31 de 66) y concentraba el
  **55% de todo el `is_bio_universe=0` del universo** → se partió en dos. Regla: revisar
  cualquier tema que pase ~15% bio=0.

---

## 5. Registro de precedentes (case law)

Crece con cada caso resuelto. `nivel` ∈ {bio-core, bio-coupled, eco-adjacent, out}.
Estado: `confirmed` (decidido) / `proposed` (pendiente de confirmación del curador).

| startup | decisión | nivel | regla aplicada | estado |
|---------|----------|-------|----------------|--------|
| Aquit | Therapeutics, bio=1 | bio-core | salud animal ≠ Bioinputs (test desempate) | confirmed |
| Inprenha | Therapeutics, bio=1 | bio-core | reproducción animal = Therapeutics | confirmed |
| WerkénVac | Therapeutics, bio=1 | bio-core | vacuna animal = Therapeutics | confirmed |
| Imeve | Therapeutics, bio=1 | bio-core | medicina/probiótico veterinario = Therapeutics | confirmed |
| Aimirim | Biomanufacturing, bio=1 | bio-coupled | digital twin de bioproceso (test de acople) | confirmed |
| Algalife | Biomanufacturing, bio=1 | bio-core | plataforma de bioproceso (test plataforma) | confirmed |
| Granatum Bioworks | Biomanufacturing, bio=1 | bio-core | plataforma de biosintéticos | confirmed |
| Outpost | Biomanufacturing, bio=1 | bio-core | plataforma TechBio; explícito "not diagnostics" | confirmed |
| Trebe Biotech | Biomanufacturing, bio=1 | bio-core | se autodescribe biomanufacturing | confirmed |
| Nude | Food Systems, bio=1 | bio-core | plant-based ≠ Farm Intelligence (test output) | confirmed |
| AGES | Food Systems, bio=1 | bio-core | bioactivos/nutracéutico = Food (healthspan) | confirmed |
| CIRCCLO | Biomaterials, bio=0 | eco-adjacent | circularidad sin biología (test transición) | confirmed |
| MUTA | Biomaterials, bio=0 | eco-adjacent | marketplace de reciclaje sin biología | confirmed |
| Nexxto | Health Access, bio=0 | eco-adjacent | IoT genérico de cadena de frío (acople no específico) | confirmed |
| Pixed | Health Access, bio=0 | eco-adjacent | prótesis biónica: medtech de bajo contenido bio | confirmed |
| NoCarbon Milk | Food Systems, bio=1 | bio-core | producto alimenticio = Food (test output); marca de bajo deep-tech pero en food transition | confirmed |
| Sistema.bio | Biomaterials, bio=1 | bio-coupled | biodigestor biogás+fertilizante; circular/energía > Nature | confirmed |
| Agrolend | Digital AgTech & Agrifintech, bio=0 | eco-adjacent | crédito agrícola puro, sin acople (test de acople) | confirmed |
| Agrotoken | Digital AgTech & Agrifintech, bio=0 | eco-adjacent | tokenización de granos = fintech, no bio | confirmed |
| Agrofy | Digital AgTech & Agrifintech, bio=0 | eco-adjacent | marketplace agrícola, sin biología | confirmed |
| goFlux | Digital AgTech & Agrifintech, bio=0 | eco-adjacent | freight SaaS B2B; dominio agri ≠ acople | confirmed |
| Agrosmart | Farm Intelligence, bio=1 | bio-coupled (B1) | agronomía climática sobre el cultivo; corrige flag bio=0 erróneo | proposed |
| Codebreaker | Farm Intelligence, bio=1 | TechBio (B2) | inteligencia de microbioma → recomendación (gate 3/3) | proposed |
| Inkus Biotech | Farm Intelligence, bio=1 | TechBio (B2) | AI+genómica de resistencia a patógenos (gate 3/3) | proposed |
| DeepAgro | Farm Intelligence o Digital AgTech | borde | CV de spraying: ¿modela biología o solo detecta+actúa? → curador | proposed |
| Instacrops | borde | borde | IoT/satélite: telemetría sin modelo bio → posible eco-adjacent | proposed |
| Leaf | Digital AgTech, bio=0 | eco-adjacent | data-infrastructure / API: plomería, sin representación bio | proposed |

> **Principio Isomorphic (gate TechBio).** Un sistema puramente computacional cuyo *objeto es
> modelar biología* pertenece al universo bio aunque sea 100% software (AlphaFold/Isomorphic Labs).
> El gate de admisión (§4) exige las tres: foco bio específico + entendimiento bio + tech que
> **representa** la biología. El borde real en agtech es sensing/operacional (IoT, spraying,
> data-infra): cuenta solo si hay un modelo biológico detrás, no por tocar un campo.

> **Nota de calidad del flag (2026-06-12).** El re-audit reveló que `is_bio_universe` estaba
> aplicado de forma **inconsistente** dentro de Farm Intelligence: marketplaces y fintech
> (Agrotoken, Agrofy) figuraban como bio=1, mientras agronomía de precisión seria (Agrosmart,
> DeepAgro) figuraba como bio=0. El split no es "mover los 31 bio=0" sino **re-auditar los 66
> contra el test de acople**. Los precedentes `proposed` esperan confirmación del curador en
> esa pasada. Ver cola en `quality/farm_intelligence_reaudit.csv` (pendiente de generar).

---

## 6. Changelog

- **2026-06-12 (b)** — **Gate de admisión TechBio.** Refinamiento del eje bio-coupled (§3 B) en dos
  sub-formas: **B1** acople físico/operacional (sensa/actúa sobre el sistema vivo) y **B2** TechBio /
  representación biológica (modela/predice la biología; clase Isomorphic Labs/AlphaFold). Se agrega el
  **gate de 3 condiciones** para software que reclama pertenencia bio (foco bio específico + entendimiento
  bio + tech que representa la biología). El borde a vigilar es agtech operacional/sensing (IoT, spraying,
  data-infra): solo entra si hay modelo biológico detrás. Disparado por el criterio del curador:
  "garantizar que las que mantenemos tienen foco bio, entendimiento bio y soporte TechBio".
- **2026-06-12** — **Split de Farm Intelligence.** Medición: el tema era 47% `is_bio_universe=0`
  (31/66) y concentraba el 55% de todo el eco-adjacent del universo — único tema no homogéneo en
  intensidad (los otros 7 son ~95% bio-core). Causa raíz en el clasificador: `src/reclassify.py`
  define Farm Intelligence con `"is_bio_default": False` y keywords financieras top-weighted
  (`agrifintech 3.0`, `rural.credit`, `farm.loan`, `crop.insurance`) — nunca fue un tema bio-core.
  Decisión (path "partir en dos"): *Farm Intelligence* queda solo para inteligencia digital
  **bio-coupled** (acople a cultivo/hato específico); se crea **Digital AgTech & Agrifintech**
  como tema eco-adjacent (`is_bio_universe=0`) para agrifintech, crédito/seguro rural, marketplaces,
  tokenización, trazabilidad y ERP genérico. Nueva regla de homogeneidad de intensidad por tema
  (sección 4). Pendiente operativo: re-audit de los 66 + split del clasificador en `reclassify.py`.
- **2026-06-10** — Creación del documento. Se introduce el eje de *intensidad biológica*
  (`is_bio_universe`) como independiente de la *pertenencia* (`scope_decision`), y los
  cuatro niveles bio-core / bio-coupled / eco-adjacent / out. Se confirman los 17 precedentes:
  11 de la tanda 1 (override de bio_theme) + 6 del Patrón 3. Primer uso del eje eco-adjacent:
  CIRCCLO, MUTA, Nexxto, Pixed marcadas `include + is_bio_universe=0` (pertenecen sin ser
  núcleo bio). Total `is_bio_universe=0` resultante: ver `python pipeline.py health`.
