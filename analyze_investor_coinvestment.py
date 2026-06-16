"""
Red de co-inversión INVERSOR-INVERSOR

Nodos  = fondos + alocadores con aristas en universo BIO
Edges  = dos inversores comparten >= 1 startup en portfolio
Peso   = # startups en comun
"""

import sqlite3
import json
from collections import defaultdict
import math

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 70)
print("INVESTOR CO-INVESTMENT NETWORK")
print("=" * 70)

# 1. Cargar portfolio de cada inversor
print("\n1. Loading investor portfolios...")

c.execute('''
SELECT ie.investor_id, ie.startup_id
FROM investment_edges ie
WHERE ie.startup_id IN (
    SELECT startup_id FROM startup_extended WHERE cluster_id >= 0
)
''')

investor_portfolio = defaultdict(set)  # investor_id -> {startup_ids}
startup_investors  = defaultdict(set)  # startup_id  -> {investor_ids}

for investor_id, startup_id in c.fetchall():
    investor_portfolio[investor_id].add(startup_id)
    startup_investors[startup_id].add(investor_id)

print(f"  Investors: {len(investor_portfolio)}")
print(f"  BIO startups with edges: {len(startup_investors)}")

# 2. Construir grafo inversor-inversor
print("\n2. Building investor-investor co-investment edges...")

coinvest_edges = defaultdict(int)  # (inv_a, inv_b) -> # startups en comun

for startup_id, investors in startup_investors.items():
    inv_list = sorted(investors)
    for i in range(len(inv_list)):
        for j in range(i + 1, len(inv_list)):
            pair = (inv_list[i], inv_list[j])
            coinvest_edges[pair] += 1

print(f"  Investor-investor co-invest edges: {len(coinvest_edges)}")

edge_vals = list(coinvest_edges.values())
print(f"  Weight range: {min(edge_vals)} - {max(edge_vals)}")
print(f"  Avg shared startups: {sum(edge_vals)/len(edge_vals):.2f}")

# 3. Grado de cada inversor (# co-inversores)
investor_degree = defaultdict(int)
for (a, b), w in coinvest_edges.items():
    investor_degree[a] += 1
    investor_degree[b] += 1

# 4. PageRank en grafo de inversores
print("\n3. Computing PageRank on investor graph...")

all_investors = set(investor_portfolio.keys())
pagerank = {inv: 1.0 for inv in all_investors}
damping = 0.85

# Precalcular vecinos de cada nodo
neighbors = defaultdict(dict)  # inv -> {neighbor: weight}
for (a, b), w in coinvest_edges.items():
    neighbors[a][b] = w
    neighbors[b][a] = w

for iteration in range(10):
    new_pr = {}
    for node in all_investors:
        incoming = 0.0
        for nbr, w in neighbors[node].items():
            # PR ponderado por peso del edge
            total_w = sum(neighbors[nbr].values()) or 1
            incoming += pagerank[nbr] * (w / total_w)
        new_pr[node] = (1 - damping) / len(all_investors) + damping * incoming
    pagerank = new_pr

# Normalizar: max = 1.0
max_pr = max(pagerank.values()) or 1
pagerank = {k: v / max_pr for k, v in pagerank.items()}

top_pr = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:15]
print("  Top 15 investors by PageRank:")
for inv_id, score in top_pr:
    print(f"    {inv_id:35} {score:.4f}  (degree={investor_degree[inv_id]})")

# 5. Betweenness aproximado
print("\n4. Computing betweenness (approximated)...")

betweenness = {}
for node in all_investors:
    deg = investor_degree[node]
    betweenness[node] = deg * math.log(1 + deg) if deg > 0 else 0

# 6. Deteccion de comunidades — componentes conectados en subgrafo weight >= 2
print("\n5. Community detection (connected components on weight >= 2 edges)...")

strong_neighbors = defaultdict(set)
for (a, b), w in coinvest_edges.items():
    if w >= 2:
        strong_neighbors[a].add(b)
        strong_neighbors[b].add(a)

visited = {}
comp_id = 0
for seed in sorted(all_investors):
    if seed in visited:
        continue
    if seed not in strong_neighbors:
        visited[seed] = f'iso_{seed}'
        continue
    queue = [seed]
    label = str(comp_id)
    comp_id += 1
    while queue:
        node = queue.pop()
        if node in visited:
            continue
        visited[node] = label
        for nbr in strong_neighbors[node]:
            if nbr not in visited:
                queue.append(nbr)

community = visited

comm_members = defaultdict(list)
for inv, comm in community.items():
    comm_members[comm].append(inv)

real_comps = [(cid, m) for cid, m in comm_members.items() if not cid.startswith('iso_')]
iso_nodes  = [(cid, m) for cid, m in comm_members.items() if cid.startswith('iso_')]
real_comps.sort(key=lambda x: len(x[1]), reverse=True)

comm_remap = {}
for i, (old_id, _) in enumerate(real_comps):
    comm_remap[old_id] = str(i)
for old_id, _ in iso_nodes:
    comm_remap[old_id] = 'iso'

community = {inv: comm_remap[community[inv]] for inv in all_investors}

community_sizes = defaultdict(int)
for comm in community.values():
    community_sizes[comm] += 1

comm_sorted = sorted(comm_members.keys(), key=lambda c: len(comm_members[c]), reverse=True)

print(f"  Real clusters (weight>=2): {len(real_comps)}")
print(f"  Isolated nodes: {len(iso_nodes)}")
for i, (old_id, members) in enumerate(real_comps[:10]):
    top_inv = sorted(members, key=lambda x: pagerank.get(x, 0), reverse=True)[:3]
    print(f"    Cluster {i} ({len(members)} inv): {', '.join(top_inv)}")

# 7. Cargar metadatos de inversores desde entities
print("\n6. Loading investor metadata...")

c.execute('''
SELECT e.entity_id, e.canonical_name, e.entity_type, e.country_code, i.investor_type
FROM entities e
LEFT JOIN investors i ON e.entity_id = i.investor_id
WHERE e.entity_id IN (
    SELECT DISTINCT investor_id FROM investment_edges
)
''')

investor_meta = {}
for eid, name, etype, country, inv_type in c.fetchall():
    investor_meta[eid] = {
        'name': name or eid,
        'entity_type': etype or 'investor',
        'investor_type': inv_type or etype or 'investor',
        'country': country or '?'
    }

# 8. Exportar
print("\n7. Exporting investor co-investment network...")

export = {
    'metadata': {
        'n_investors': len(all_investors),
        'n_edges': len(coinvest_edges),
        'n_communities': len(community_sizes),
        'generated_at': '2026-06-14'
    },
    'nodes': [],
    'edges': []
}

for inv_id in all_investors:
    meta = investor_meta.get(inv_id, {})
    # Top 5 portfolio startups por nombre
    c.execute('''
        SELECT e.canonical_name
        FROM investment_edges ie
        JOIN entities e ON ie.startup_id = e.entity_id
        WHERE ie.investor_id = ? AND ie.startup_id IN (
            SELECT startup_id FROM startup_extended WHERE cluster_id >= 0
        )
        ORDER BY ie.confidence_score DESC
        LIMIT 5
    ''', (inv_id,))
    top_portfolio = [row[0] for row in c.fetchall() if row[0]]

    export['nodes'].append({
        'id': inv_id,
        'name': meta.get('name', inv_id),
        'investor_type': meta.get('investor_type', 'investor'),
        'country': meta.get('country', '?'),
        'pagerank': round(pagerank.get(inv_id, 0), 4),
        'betweenness': round(betweenness.get(inv_id, 0), 2),
        'community': community.get(inv_id, '0'),
        'degree': investor_degree.get(inv_id, 0),
        'portfolio_size': len(investor_portfolio.get(inv_id, [])),
        'top_portfolio': top_portfolio
    })

# Edges: todos (674 es manejable), ordenados por peso desc
# Exportar todas las aristas (FA2 necesita la topología completa)
edge_list = sorted(coinvest_edges.items(), key=lambda x: x[1], reverse=True)

for (a, b), weight in edge_list:
    export['edges'].append({
        'source': a,
        'target': b,
        'weight': weight,
        'thickness': round(min(6, max(0.5, math.log(1 + weight) * 1.2)), 2)
    })

# Output como JS variable para evitar CORS
js_path = 'pilot/investor-coinvest-data.js'
with open(js_path, 'w', encoding='utf-8') as f:
    f.write('/* Auto-generated by analyze_investor_coinvestment.py - do not edit */\n')
    f.write('var INVESTOR_COINVEST_DATA = ')
    json.dump(export, f, ensure_ascii=False)
    f.write(';\n')

print(f"  Saved {len(export['nodes'])} nodes, {len(export['edges'])} edges -> {js_path}")

# 9. Summary
print("\n" + "=" * 70)
print("INVESTOR CO-INVESTMENT NETWORK SUMMARY")
print("=" * 70)
print(f"""
Nodes (investors):   {len(all_investors)}
Edges (co-invest):   {len(coinvest_edges)}
Communities:         {len(community_sizes)}
Top investor:        {top_pr[0][0]} (PageRank={top_pr[0][1]:.4f})
Biggest community:   {len(comm_members[comm_sorted[0]])} investors
""")

conn.close()
print("[DONE]")
