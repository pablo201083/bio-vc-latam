import sqlite3
conn = sqlite3.connect("db/bio_latam.db")

print("=== SIZE PER THEME ===")
q1 = "SELECT bio_theme_primary, count(*) as n FROM startup_extended WHERE scope_decision='include' GROUP BY bio_theme_primary ORDER BY n DESC"
rows = conn.execute(q1).fetchall()
total = sum(r[1] for r in rows)
for t, n in rows:
    bar = "#" * (n // 3)
    print(f"  {(t or 'Unclassified'):<36}  {n:>4}  {round(100*n/total):>3}%  {bar}")

print()
print("=== SECONDARY FLOWS (top 15) ===")
q2 = "SELECT bio_theme_primary, bio_theme_secondary, count(*) as n FROM startup_extended WHERE scope_decision='include' AND bio_theme_secondary IS NOT NULL AND bio_theme_secondary!='' GROUP BY bio_theme_primary, bio_theme_secondary ORDER BY n DESC LIMIT 15"
rows2 = conn.execute(q2).fetchall()
for a, b, n in rows2:
    print(f"  {(a or '?'):<30} -> {(b or '?'):<30}  ({n})")

print()
print("=== SUB-CLUSTERS PER THEME ===")
q3 = "SELECT bio_theme_primary, cluster_label, count(*) as n FROM startup_extended WHERE scope_decision='include' AND cluster_label IS NOT NULL GROUP BY bio_theme_primary, cluster_label ORDER BY bio_theme_primary, n DESC"
rows3 = conn.execute(q3).fetchall()
cur = None
for theme, label, n in rows3:
    if theme != cur:
        cur = theme
        print(f"\n  {theme}")
    clean = (label.split("||")[0] if "||" in label else label).strip()
    print(f"    {n:>3}  {clean}")

conn.close()
