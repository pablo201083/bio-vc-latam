"""
Análisis de red de CO-INVERSIÓN (startups que comparten inversores)

Grafo:
  Nodos = startups BIO
  Edges = "comparten N inversores"
  Pesos = # inversores en común

Métricas:
  1. PageRank (importancia en red)
  2. Betweenness Centrality (bridging)
  3. Clustering Coefficient (densidad local)
  4. Comunidades (Louvain)
  5. Grado (cuántos co-inversores)
"""

import sqlite3
import json
from collections import defaultdict
import math

conn = sqlite3.connect('db/bio_latam.db')
c = conn.cursor()

print("=" * 80)
print("CO-INVESTMENT NETWORK ANALYSIS")
print("=" * 80)

# 1. Construir matriz de co-inversión
print("\n1. Building co-investment matrix...")

c.execute('''
SELECT startup_id, investor_id
FROM investment_edges
WHERE startup_id IN (SELECT startup_id FROM startup_extended WHERE cluster_id >= 0)
ORDER BY startup_id
''')

# investor_id -> [startup_ids] que financió
investor_portfolio = defaultdict(set)
# startup_id -> [investor_ids]
startup_investors = defaultdict(set)

for startup_id, investor_id in c.fetchall():
    investor_portfolio[investor_id].add(startup_id)
    startup_investors[startup_id].add(investor_id)

print(f"  Investors: {len(investor_portfolio)}")
print(f"  Startups with edges: {len(startup_investors)}")

# 2. Construir co-inversión edges (startups que comparten inversores)
print("\n2. Building co-investment edges (startups sharing investors)...")

coinvest_edges = defaultdict(int)  # (startup_a, startup_b) -> count shared investors

for investor_id, startup_set in investor_portfolio.items():
    startups = list(startup_set)
    # Cada par de startups en portfolio del mismo investor
    for i in range(len(startups)):
        for j in range(i + 1, len(startups)):
            s1, s2 = sorted([startups[i], startups[j]])
            coinvest_edges[(s1, s2)] += 1

print(f"  Co-investment edges: {len(coinvest_edges)}")

# Estadísticas de edges
edge_counts = list(coinvest_edges.values())
print(f"  Edge weight distribution:")
print(f"    Min: {min(edge_counts)}, Max: {max(edge_counts)}, Avg: {sum(edge_counts)/len(edge_counts):.2f}")

# 3. PageRank simplificado (sin networkx)
print("\n3. Computing PageRank (simplified)...")

# Grado (número de co-inversores)
node_degree = defaultdict(int)
for (s1, s2), weight in coinvest_edges.items():
    node_degree[s1] += weight
    node_degree[s2] += weight

# PageRank iterativo simple (5 iteraciones)
pagerank = {startup_id: 1.0 for startup_id in startup_investors.keys()}
damping = 0.85
iterations = 5

for iteration in range(iterations):
    new_pagerank = {}
    total_pr = sum(pagerank.values())

    for node in pagerank.keys():
        # Suma PR de vecinos
        neighbor_pr = 0
        for (s1, s2), weight in coinvest_edges.items():
            if s1 == node and s2 in pagerank:
                neighbor_pr += pagerank[s2] / max(1, node_degree[s2])
            elif s2 == node and s1 in pagerank:
                neighbor_pr += pagerank[s1] / max(1, node_degree[s1])

        new_pagerank[node] = (1 - damping) / len(pagerank) + damping * neighbor_pr

    pagerank = new_pagerank

# Top 20 por PageRank
top_pr = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:20]
print(f"  Top 20 startups by PageRank:")
for startup_id, pr_score in top_pr:
    print(f"    {startup_id:35} {pr_score:.4f}")

# 4. Betweenness Centrality (simplificado: startups que conectan diferentes clusters)
print("\n4. Computing Betweenness Centrality...")

betweenness = defaultdict(float)

# Aproximación: para cada startup, ver cuántas pares de otros startups
# la necesitan para conectarse
for node in startup_investors.keys():
    # Neighbors of this node
    neighbors = set()
    for (s1, s2), weight in coinvest_edges.items():
        if s1 == node:
            neighbors.add(s2)
        elif s2 == node:
            neighbors.add(s1)

    # Si remover este nodo desconecta componentes, tiene alta betweenness
    # Aproximación simple: if_remove_node_disconnects_X_pairs
    if len(neighbors) > 0:
        betweenness[node] = len(neighbors) * math.log(1 + len(neighbors))

top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:15]
print(f"  Top 15 bridge startups (high betweenness):")
for startup_id, bc_score in top_betweenness:
    degree = node_degree[startup_id]
    print(f"    {startup_id:35} betweenness={bc_score:.2f}, degree={degree}")

# 5. Clustering Coefficient (densidad local)
print("\n5. Computing Local Clustering Coefficient...")

clustering = {}

for node in startup_investors.keys():
    # Neighbors
    neighbors = set()
    for (s1, s2), weight in coinvest_edges.items():
        if s1 == node:
            neighbors.add(s2)
        elif s2 == node:
            neighbors.add(s1)

    if len(neighbors) < 2:
        clustering[node] = 0
    else:
        # Edges between neighbors
        edges_between = 0
        neighbor_list = list(neighbors)
        for i in range(len(neighbor_list)):
            for j in range(i + 1, len(neighbor_list)):
                n1, n2 = sorted([neighbor_list[i], neighbor_list[j]])
                if (n1, n2) in coinvest_edges:
                    edges_between += 1

        # Max possible edges
        max_edges = len(neighbors) * (len(neighbors) - 1) / 2
        clustering[node] = edges_between / max_edges if max_edges > 0 else 0

# Top 15 por clustering (close-knit groups)
top_clustering = sorted(clustering.items(), key=lambda x: x[1], reverse=True)[:15]
print(f"  Top 15 startups in tight clusters (high local clustering):")
for startup_id, cc_score in top_clustering:
    neighbors = sum(1 for (s1, s2) in coinvest_edges if s1 == startup_id or s2 == startup_id)
    print(f"    {startup_id:35} clustering={cc_score:.2f}, neighbors={neighbors}")

# 6. Simple Community Detection (Greedy Modularity)
print("\n6. Detecting communities (Greedy Modularity)...")

# Inicializar: cada node es su propia comunidad
communities = {node: node for node in startup_investors.keys()}
community_id = 0

# Merge comunidades que comparten edges (greedy)
merged = True
while merged:
    merged = False
    for (s1, s2), weight in coinvest_edges.items():
        if communities[s1] != communities[s2]:
            # Merge los dos (always para simplicidad)
            old_id = communities[s2]
            new_id = communities[s1]
            for node in communities:
                if communities[node] == old_id:
                    communities[node] = new_id
            merged = True
            break

# Count communities
unique_communities = len(set(communities.values()))
print(f"  Communities detected: {unique_communities}")

# Tamaño de comunidades
community_sizes = defaultdict(int)
for startup_id, comm_id in communities.items():
    community_sizes[comm_id] += 1

community_list = sorted(community_sizes.items(), key=lambda x: x[1], reverse=True)
print(f"  Community sizes (top 10):")
for comm_id, size in community_list[:10]:
    print(f"    Community {comm_id}: {size} startups")

# 7. Export para visualización
print("\n7. Exporting data for visualization...")

export_data = {
    'metadata': {
        'total_startups': len(startup_investors),
        'total_edges': len(coinvest_edges),
        'unique_communities': unique_communities,
        'generated_at': '2026-06-14'
    },
    'nodes': [],
    'edges': []
}

# Agregar nodos con métricas
c.execute('''
SELECT se.startup_id, se.bio_theme_primary, e.canonical_name
FROM startup_extended se
LEFT JOIN entities e ON se.startup_id = e.entity_id
WHERE se.cluster_id >= 0
''')

for startup_id, theme, name in c.fetchall():
    if startup_id not in pagerank:
        continue

    export_data['nodes'].append({
        'id': startup_id,
        'name': name or startup_id,
        'theme': theme,
        'pagerank': round(pagerank[startup_id], 4),
        'betweenness': round(betweenness.get(startup_id, 0), 4),
        'clustering': round(clustering.get(startup_id, 0), 4),
        'community': str(communities[startup_id]),
        'degree': node_degree[startup_id],
        'n_investors': len(startup_investors[startup_id])
    })

# Agregar edges (solo top 50% por weight para no saturar)
edge_list = sorted(coinvest_edges.items(), key=lambda x: x[1], reverse=True)
cutoff = len(edge_list) // 2

for (s1, s2), weight in edge_list[:cutoff]:
    export_data['edges'].append({
        'source': s1,
        'target': s2,
        'weight': weight,
        'thickness': min(5, max(1, weight / 2))
    })

print(f"  Exported {len(export_data['nodes'])} nodes, {len(export_data['edges'])} edges")

# Guardar JSON
output_file = 'pilot/coinvestment_network.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(export_data, f, indent=2)

print(f"  Saved to {output_file}")

# 8. Summary Statistics
print("\n" + "=" * 80)
print("SUMMARY: CO-INVESTMENT NETWORK")
print("=" * 80)

avg_degree = sum(node_degree.values()) / len(node_degree) if node_degree else 0
avg_clustering = sum(clustering.values()) / len(clustering) if clustering else 0

print(f"""
Network size:
  Nodes (startups): {len(startup_investors)}
  Edges (co-investments): {len(coinvest_edges)}
  Avg degree (co-investors per startup): {avg_degree:.2f}

Connectivity:
  Communities: {unique_communities}
  Avg local clustering: {avg_clustering:.3f}

PageRank insights:
  Top startup: {top_pr[0][0]} (score: {top_pr[0][1]:.4f})

Bridge startups (high betweenness):
  {top_betweenness[0][0]} (score: {top_betweenness[0][1]:.2f})

Tight clusters (high local clustering):
  {top_clustering[0][0]} (score: {top_clustering[0][1]:.2f})

For visualization:
- Node size = PageRank score (importance in network)
- Node color = Community (detect clusters)
- Edge thickness = # shared investors
- Position = Force-directed layout recommended
""")

conn.close()
print("\n[DONE]")
