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
no genérico.
**Señales:** agronomía de precisión sobre el cultivo, monitoreo satelital de
bosques/biodiversidad, digital twin de bioproceso, plataformas de fenotipado.
**Ejemplos:** Agrosmart (inteligencia agronómica), Mombak (reforestación + monitoreo),
Aimirim (digital twin de fermentación en biorrefinería).

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

---

## 6. Changelog

- **2026-06-10** — Creación del documento. Se introduce el eje de *intensidad biológica*
  (`is_bio_universe`) como independiente de la *pertenencia* (`scope_decision`), y los
  cuatro niveles bio-core / bio-coupled / eco-adjacent / out. Se confirman los 17 precedentes:
  11 de la tanda 1 (override de bio_theme) + 6 del Patrón 3. Primer uso del eje eco-adjacent:
  CIRCCLO, MUTA, Nexxto, Pixed marcadas `include + is_bio_universe=0` (pertenecen sin ser
  núcleo bio). Total `is_bio_universe=0` resultante: ver `python pipeline.py health`.
