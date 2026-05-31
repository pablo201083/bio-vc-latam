"""Quick validation of ecosystem-graph-data.js"""
import re
from pathlib import Path

js = Path('pilot/ecosystem-graph-data.js').read_text('utf-8')

# Extract JSON arrays
nodes_json = re.search(r'const EG_NODES = (\[.*?\]);', js, re.DOTALL)
edges_json = re.search(r'const EG_EDGES = (\[.*?\]);', js, re.DOTALL)

import json
nodes = json.loads(nodes_json.group(1))
edges = json.loads(edges_json.group(1))

print(f"Nodes: {len(nodes)} | Edges: {len(edges)}")

by_layer = {}
for n in nodes:
    by_layer[n['layer']] = by_layer.get(n['layer'], 0) + 1
print("By layer:", by_layer)

by_edge = {}
for e in edges:
    by_edge[e['edgeType']] = by_edge.get(e['edgeType'], 0) + 1
print("By edge:", by_edge)

eco = [n for n in nodes if n['layer'] in ('organization','eso','corporate')]
print(f"\nEco nodes ({len(eco)}):")
for n in eco:
    conns = sum(1 for e in edges if e['source']==n['id'] or e['target']==n['id'])
    print(f"  [{n['layer']:12}] {n['label']:35} deg={conns}")

mem_edges = [e for e in edges if e['edgeType']=='membership']
print(f"\nMembership edges ({len(mem_edges)}):")
for e in mem_edges:
    sn = next((n['label'] for n in nodes if n['id']==e['source']), e['source'])
    tn = next((n['label'] for n in nodes if n['id']==e['target']), e['target'])
    print(f"  {sn} → {tn}")
