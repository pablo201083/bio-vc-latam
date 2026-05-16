"""
Computa valuation_estimate_usd para todas las startups en startup_extended.

Metodología (en orden de prioridad y confianza):

  1. 'gridx_valuation'   → valuation_bucket_usd del Excel GRIDX (dato histórico)
  2. 'stage_estimate'    → mediana de valuación por etapa, LatAm biotech
  3. 'investors_proxy'   → número de inversores mapeados como proxy de etapa alcanzada
  4. 'emergente'         → sin señal financiera, valor mínimo por defecto

Las estimaciones son explícitas y trazables, no pretenden ser precisas.
Cuando llegue Pitchbook se sobreescribe solo con fuente='pitchbook'.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB   = ROOT / "db" / "bio_latam.db"

# ── Medianas de valuación LatAm biotech por etapa (en $M USD) ─────────────────
# Conservadoras: no son unicorn medians, son distribución real de la región
STAGE_VALUATION = {
    "pre-seed":  2.5,
    "seed":      8.0,
    "series-a":  30.0,
    "series-b":  90.0,
    "series-c+": 250.0,
    "growth":    700.0,
}

# Proxy por cantidad de inversores mapeados (cuando no hay dato de etapa)
# La lógica: más inversores documentados → más rondas levantadas → más avanzado
def investors_to_valuation(n):
    if n >= 5:  return 25.0   # serie A territory
    if n >= 3:  return 10.0   # seed+ / serie A early
    if n >= 1:  return 4.0    # seed
    return 1.5                # sin inversores mapeados

conn = sqlite3.connect(DB)
c = conn.cursor()

# Cargar datos necesarios
c.execute("""
    SELECT se.startup_id, se.valuation_bucket_usd, se.funding_stage,
           COUNT(ie.investment_id) as n_inv
    FROM startup_extended se
    LEFT JOIN investment_edges ie ON ie.startup_id = se.startup_id
    GROUP BY se.startup_id
""")
rows = c.fetchall()

updates = []
stats = {"gridx_valuation": 0, "stage_estimate": 0, "investors_proxy": 0, "emergente": 0}

for startup_id, val_bucket, stage, n_inv in rows:
    if val_bucket is not None:
        # Fuente 1: GRIDX valuation bucket (el bucket ES la valuación en $M)
        # bucket=0 (<$1M) → usamos 0.8M; resto es el valor directo
        estimate = 0.8 if val_bucket == 0 else float(val_bucket)
        source   = "gridx_valuation"
    elif stage and stage in STAGE_VALUATION:
        # Fuente 2: mediana por etapa
        estimate = STAGE_VALUATION[stage]
        source   = "stage_estimate"
    elif n_inv > 0:
        # Fuente 3: proxy por inversores mapeados
        estimate = investors_to_valuation(n_inv)
        source   = "investors_proxy"
    else:
        # Fuente 4: default emergente
        estimate = 1.5
        source   = "emergente"

    updates.append((estimate, source, startup_id))
    stats[source] += 1

c.executemany("""
    UPDATE startup_extended
    SET valuation_estimate_usd = ?, valuation_estimate_source = ?
    WHERE startup_id = ?
""", updates)
conn.commit()

print(f"Updated: {len(updates)} startups")
print(f"\nSource breakdown:")
for src, cnt in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"  {src:20}: {cnt:4}")

# Sanity check — muestra la distribución de valuaciones estimadas
c.execute("""
    SELECT valuation_estimate_source,
           MIN(valuation_estimate_usd), AVG(valuation_estimate_usd), MAX(valuation_estimate_usd)
    FROM startup_extended
    WHERE scope_decision='include'
    GROUP BY valuation_estimate_source
""")
print(f"\nValuation distribution (include only):")
print(f"{'source':20} | {'min':8} | {'avg':8} | {'max':8}")
for r in c.fetchall():
    print(f"  {str(r[0]):20} | {r[1]:8.1f} | {r[2]:8.1f} | {r[3]:8.1f}")

conn.close()
