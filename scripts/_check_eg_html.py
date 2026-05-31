"""Basic sanity check on ecosystem-graph.html"""
from pathlib import Path

html = Path('pilot/ecosystem-graph.html').read_text('utf-8')

# Check that key elements are present
checks = [
    ('EG_NODES', 'data variable reference'),
    ('EG_EDGES', 'edges variable reference'),
    ('EG_META', 'meta variable reference'),
    ('initGraph', 'initGraph function'),
    ('stepSim', 'force simulation'),
    ('applyPositions', 'position update'),
    ('renderAll', 'render function'),
    ('ecosystem-graph-data.js', 'data script tag'),
    ('eg-svg', 'main SVG element'),
    ('eg-root', 'root SVG group'),
    ('eg-nodes', 'nodes SVG group'),
    ('eg-edges', 'edges SVG group'),
    ('btn-reheat', 'reheat button'),
    ('btn-focus-eco', 'eco mode button'),
    ('tog-organization', 'org toggle'),
    ('tog-eso', 'eso toggle'),
    ('tog-corporate', 'corporate toggle'),
]

all_ok = True
for term, desc in checks:
    if term in html:
        print(f'  OK  {desc} ({term})')
    else:
        print(f'  MISS {desc} ({term})')
        all_ok = False

print()
if all_ok:
    print('All checks passed.')
else:
    print('Some elements missing.')
print(f'File size: {len(html):,} chars')
