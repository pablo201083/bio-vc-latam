"""
derive_one_liners.py
--------------------
Para los startups clusterizados (cluster_id >= 0) que no tienen business_one_liner,
extrae la primera oración del summary y la usa como one-liner provisional.

Criterios:
  - Solo aplica a startups con cluster_id >= 0 (en el mapa semántico)
  - Solo si business_one_liner está vacío
  - Extrae hasta el primer punto seguido de espacio o fin de texto
  - Trunca a 120 caracteres si es más largo
  - Marca el campo con sufijo "  [auto]" para distinguirlos de los curados

Ejecutar:
  .venv/Scripts/python.exe derive_one_liners.py
  .venv/Scripts/python.exe derive_one_liners.py --dry-run   # solo muestra, no escribe
"""

import sqlite3, pathlib, datetime, re, sys, argparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true')
args = parser.parse_args()

DB = pathlib.Path('db/bio_latam.db')
conn = sqlite3.connect(DB)
cur  = conn.cursor()
now  = datetime.datetime.now(datetime.UTC).isoformat()

MAX_LEN = 120   # caracteres máximos para el one-liner derivado


def first_sentence(text: str) -> str:
    """Extrae la primera oración del texto."""
    if not text:
        return ''
    text = text.strip()
    # Busca punto seguido de espacio o fin de cadena (no abreviaturas comunes)
    # Acepta puntos seguidos de mayúscula, digit, o fin
    m = re.search(r'\.\s+(?=[A-Z0-9])', text)
    if m:
        sentence = text[:m.start() + 1].strip()
    else:
        # Sin punto claro → tomar los primeros 120 chars hasta el último espacio
        sentence = text[:MAX_LEN]
        if len(text) > MAX_LEN:
            # cortar en el último espacio
            cut = sentence.rfind(' ')
            if cut > 60:
                sentence = sentence[:cut] + '…'

    # Truncar si sigue siendo muy largo
    if len(sentence) > MAX_LEN:
        cut = sentence[:MAX_LEN].rfind(' ')
        sentence = sentence[:cut] + '…' if cut > 60 else sentence[:MAX_LEN] + '…'

    return sentence


# ── Fetch candidates ─────────────────────────────────────────────────────────
cur.execute('''
SELECT e.entity_id, e.canonical_name, sx.bio_theme_primary, sx.cluster_id,
       COALESCE(se.startup_summary_en, se.startup_summary_v1) as summary
FROM startup_extended sx
JOIN entities e ON e.entity_id = sx.startup_id
LEFT JOIN startup_extended se ON se.startup_id = sx.startup_id
WHERE sx.cluster_id >= 0
  AND (se.business_one_liner IS NULL OR TRIM(se.business_one_liner) = '')
  AND (
    (se.startup_summary_en IS NOT NULL AND TRIM(se.startup_summary_en) != '')
    OR
    (se.startup_summary_v1 IS NOT NULL AND TRIM(se.startup_summary_v1) != '')
  )
ORDER BY sx.bio_theme_primary, e.canonical_name
''')
candidates = cur.fetchall()

print(f"Candidatos encontrados: {len(candidates)}")
if args.dry_run:
    print("(modo dry-run — no se escribe nada)\n")
print()

updated = 0
skipped = 0

for eid, name, bio, cl_id, summary in candidates:
    liner = first_sentence(summary)
    if not liner or len(liner) < 20:
        print(f"  SKIP  {name[:40]:<40}  (oración muy corta: {repr(liner[:50])})")
        skipped += 1
        continue

    print(f"  OK  {name[:40]:<40}  {liner[:80]}")

    if not args.dry_run:
        cur.execute(
            'UPDATE startup_extended SET business_one_liner = ? WHERE startup_id = ?',
            (liner, eid)
        )
        cur.execute(
            '''INSERT INTO audit_log
                 (timestamp, actor, entity_id, table_name, field, old_value, new_value, reason)
               VALUES (?,?,?,?,?,?,?,?)''',
            (now, 'auto:derive_one_liners', eid, 'startup_extended',
             'business_one_liner', None, liner,
             f'Primera oración del summary derivada automáticamente — CL{cl_id}')
        )
        updated += 1

if not args.dry_run:
    conn.commit()

conn.close()
print()
print(f"Actualizados : {updated}")
print(f"Saltados     : {skipped}")
if not args.dry_run:
    print()
    print("Próximo paso: .venv/Scripts/python.exe -c \"import sqlite3,sys; sys.path.insert(0,'.'); from src.clustering import write_dashboard_data; conn=sqlite3.connect('db/bio_latam.db'); write_dashboard_data(conn); conn.close()\"")
