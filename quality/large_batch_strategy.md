# Large Batch Strategy V2

## Why this shift

The project should prioritize strengthening the base before building a more ambitious semantic clustering layer.

Current bottleneck:

- `175` startups in scope as `include`
- `90` `include, confirmed`
- `85` `include, provisional`

That means the next big gain does not come from a more sophisticated taxonomy model. It comes from reducing the provisional core quickly and safely.

## Operating principle

Use two rhythms together:

1. `Large acquisition batches`
   Pull auditable external sources in groups of `15-50` startups at a time.

2. `Small hardening batches`
   Review and refine the riskiest or most thesis-defining cases in groups of `5-12`.

Rule:

- a large batch only counts as progress if it moves startups to at least `source-backed seeded`
- `reviewed` still requires a second pass or stronger source

## The three batch families

### 1. Portfolio sweeps

Best when a portfolio has:

- startup pages or a portfolio index
- a short usable description
- a meaningful thesis signal

Highest-priority portfolio batches now:

1. `IndieBio / SOSV`
2. `CITES`
3. `The Ganesha Lab`
4. `AIR Capital`
5. `Kamay Ventures`

Expected effect:

- faster `source_url` coverage
- faster `scope_status = confirmed`
- better seed descriptions for biotech-heavy startups

### 2. Theme sweeps

Best when a macrotheme has many `include, provisional` startups.

Current biggest macrotheme opportunities:

1. `food biotech and novel ingredients` = `21`
2. `computational biology and scientific software` = `12`
3. `diagnostics and medtech` = `12`
4. `climate, energy and resource systems` = `10`
5. `biomanufacturing and bioindustrial platforms` = `9`

Expected effect:

- better taxonomic stability
- better semantic clustering inputs
- cleaner mini-descriptions per emergent theme

### 3. Border-case sweeps

Best for tightening the universe definition.

These should focus on startups that are:

- not strictly bio-based
- but may still belong through a biocentric or planetary-boundaries lens
- or may actually belong outside thesis and need to be dropped

Priority frontier:

- `Satellites on Fire`
- `Solfium`
- `Cargo Sapiens`
- `Aerialoop`
- `Satellogic`
- `Quantum South`
- `Skyloom`
- `Innova Space`

Expected effect:

- stronger inclusion logic
- less semantic noise
- clearer thesis boundary

## Recommended execution order

### Phase 1: big wins with external source coverage

1. `Portfolio sweep: IndieBio / SOSV`
2. `Portfolio sweep: CITES`
3. `Theme sweep: food biotech and novel ingredients`

Goal:

- push `include confirmed` well above `100`
- reduce `include provisional` below `70`

### Phase 2: stabilize the semantic core

4. `Theme sweep: computational biology and scientific software`
5. `Theme sweep: diagnostics and medtech`
6. `Theme sweep: biomanufacturing and bioindustrial platforms`

Goal:

- improve clustering inputs for the core thesis universe
- reduce `taxonomy_stub` inside key themes

### Phase 3: clean the frontier

7. `Border-case sweep: climate / hardware / planetary systems`
8. `Portfolio sweep: AIR Capital + Kamay + Ganesha`

Goal:

- clarify what stays because it is biocentric or planetary-boundary aligned
- remove what remains only as weak scope inference

## Decision rules for large batches

### Keep as `include`

When the startup is clearly:

- `bio-based`
- `biocentric`
- or materially/regeneratively tied to planetary boundaries

### Keep as `include, border`

When it is not bio-based but does one of these strongly:

- prevents or monitors ecosystem degradation
- improves MRV, traceability or intervention over natural/material systems
- works directly on climate / fire / water / soil / biodiversity / resource resilience

### Move to `exclude`

When it is:

- generic software
- generic finance
- generic enterprise infrastructure
- frontier hardware with no strong planetary/material coupling

## What not to do

- do not build a final semantic map from `include + provisional`
- do not let `taxonomy_stub` rows dominate cluster naming
- do not treat portfolio presence alone as perfect semantic truth

## Success metrics

Near-term:

- `include confirmed > 120`
- `include provisional < 55`

Semantic readiness:

- each core macrotheme has at least `60%` source-backed coverage
- each emergent theme has a short description written from auditable evidence

Product readiness:

- semantic beta uses mostly confirmed startups
- the visual map reflects real source-backed clusters rather than inherited heuristics
