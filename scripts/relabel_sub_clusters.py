"""
relabel_sub_clusters.py
Recomputa sub_cluster_label desde los bigrams semánticos colectivos de cada
familia (bio_theme_primary × sub_cluster_label_actual), reemplazando el label
original que fue asignado por el startup más prominente (sesgo individual).

Uso:
  python scripts/relabel_sub_clusters.py          # dry-run (no escribe)
  python scripts/relabel_sub_clusters.py --apply  # aplica cambios con audit log
"""

import sys, re, sqlite3, collections
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB   = ROOT / "db" / "bio_latam.db"

# ── Stop words (mismas que el frontend) ─────────────────────────────────────
STOP = {
    # artículos / preposiciones / conjunciones
    'and','the','of','in','for','to','a','with','by','from','or','is','are',
    'that','on','at','its','an','as','via','into','through','which','this',
    'they','both','each','such','other','also','more','than',
    # verbos genéricos
    'using','based','provides','develops','creates','enables','help','helps',
    'provide','offer','build','builds','built','makes','make','uses','designed',
    'produces','produced','produce','developed','allow','allows','allowing',
    'improve','improves','improving','reduce','reducing','increase','increasing',
    'combining','integrate','integrates','leveraging','leverage','focused',
    'focus','approach','including','developing','developed','applying',
    # sustantivos demasiado genéricos
    'solutions','systems','technology','platform','development','company',
    'startup','process','product','products','services','service','market',
    'industry','industries','sector','sectors','business','businesses',
    'biotech','biotechnology','companies','organization','organizations',
    # adjetivos genéricos
    'their','across','while','used','new','novel','innovative','first','next',
    'generation','world','global','latin','america','latam','high','full',
    'core','main','real','open','different','specific','multiple','various',
    'unique','alternative','traditional','sustainable','environmental',
    'natural','organic','cutting','edge','state','arte','powered','driven',
    'scale','without','without','access',
    # gentilicios y geografía — no discriminan el dominio tecnológico
    'brazilian','chilean','mexican','colombian','argentinian','peruvian',
    'latin','latam','america','global','regional','local','national',
    # energía genérica (aparece en muchos contextos no energéticos)
    'renewable','energy','solar','wind','clean',
    # boilerplate que no caracteriza
    'ethnic','ultra','thin','collaborative','freight','improves',
}


def tokenize(text: str) -> list[str]:
    return [
        w for w in re.sub(r'[^a-záéíóúñ\s]', ' ', text.lower()).split()
        if len(w) > 3 and w not in STOP
    ]


def cluster_label(one_liners: list[str]) -> str | None:
    """
    Devuelve el top bigram si supera umbral de confianza, o None si no hay
    suficiente señal para derivar un label fiable.

    Umbral de confianza: el bigram ganador debe aparecer en
      >= max(2, ceil(n * 0.05))  startups   [al menos 5% del cluster]
    Esto filtra labels que emergen de 2 startups en un cluster de 50.
    """
    import math
    n = len(one_liners)
    if n < 4:
        return None  # demasiado pequeño

    uni: dict = {}
    bi: dict  = {}
    for text in one_liners:
        words = tokenize(text)
        for i, w in enumerate(words):
            uni[w] = uni.get(w, 0) + 1
            if i < len(words) - 1:
                bg = w + ' ' + words[i + 1]
                bi[bg] = bi.get(bg, 0) + 1

    min_freq = max(2, math.ceil(n * 0.05))
    ranked = sorted(bi.items(), key=lambda x: -x[1])
    top_bi = [(bg, cnt) for bg, cnt in ranked if cnt >= min_freq]

    if top_bi:
        return top_bi[0][0].title()

    # fallback: top 2 unigrams (sin umbral de %) — para clusters con vocabulario muy diverso
    top_uni = sorted(uni.items(), key=lambda x: -x[1])
    if top_uni:
        label = ' '.join(w for w, _ in top_uni[:2]).title()
        return label
    return None


def main():
    apply = '--apply' in sys.argv
    conn  = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur   = conn.cursor()

    # ── Cargar startups con one_liner y label actual ─────────────────────────
    cur.execute("""
        SELECT se.startup_id, e.canonical_name,
               se.bio_theme_primary  AS theme,
               se.sub_cluster_label  AS old_label,
               se.business_one_liner AS one_liner
        FROM startup_extended se
        JOIN entities e ON e.entity_id = se.startup_id
        WHERE se.sub_cluster_label IS NOT NULL
          AND se.bio_theme_primary  IS NOT NULL
    """)
    rows = cur.fetchall()

    # ── Agrupar por (theme, old_label) ───────────────────────────────────────
    groups: dict = {}
    for r in rows:
        key = (r['theme'], r['old_label'])
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    print(f"{'THEME':<42} {'OLD LABEL':<28} {'NEW LABEL':<28} N  CAMBIA")
    print('-' * 110)

    changes: list = []   # (startup_id, canonical_name, new_label)
    changed_groups = 0

    for (theme, old_label), members in sorted(groups.items()):
        one_liners = [m['one_liner'] or '' for m in members]
        new_label  = cluster_label(one_liners)
        if new_label is None:
            # cluster demasiado pequeño — no cambiar
            print(f"{theme:<42} {old_label:<28} {'(mantener)':<28} {len(members):<3}")
            continue
        changed    = new_label.lower() != (old_label or '').lower()
        if changed:
            changed_groups += 1
        marker = '<--' if changed else ''
        print(f"{theme:<42} {old_label:<28} {new_label:<28} {len(members):<3} {marker}")
        if changed:
            for m in members:
                changes.append((m['startup_id'], m['canonical_name'], new_label))

    print()
    print(f"Total grupos: {len(groups)}  |  Con cambio: {changed_groups}  |  Startups afectados: {len(changes)}")

    if not apply:
        print("\n[DRY RUN] Pasá --apply para escribir los cambios.")
        conn.close()
        return

    # ── Aplicar con audit log ────────────────────────────────────────────────
    try:
        from src.audit import diff_and_log_update
        use_audit = True
    except ImportError:
        use_audit = False
        print("WARN: src.audit no disponible — escribiendo sin audit log.")

    updated = 0
    for startup_id, name, new_label in changes:
        if use_audit:
            diff_and_log_update(
                conn, 'startup_extended', 'startup_id', startup_id,
                {'sub_cluster_label': new_label},
                actor='relabel_sub_clusters.py'
            )
        else:
            cur.execute(
                "UPDATE startup_extended SET sub_cluster_label=? WHERE startup_id=?",
                (new_label, startup_id)
            )
        updated += 1

    conn.commit()
    conn.close()
    print(f"\n✓ {updated} startups actualizados en DB.")
    print("Próximo paso: python pipeline.py rebuild --phase export  (o el comando que regenera startup-themes-data.js)")


if __name__ == '__main__':
    main()
