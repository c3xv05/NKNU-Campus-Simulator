import json
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
r=Path(__file__).resolve().parents[1];d=json.loads((r/'campuses/heping/campus.json').read_text())
union=lambda k:unary_union([Polygon(t) for t in d[k]])
ground,road,paths,area=[union(k) for k in ['ground','road','paths','campusTriangles']]
buildings=unary_union([Polygon(b['ring']) for b in d['buildings']]);courts=unary_union([Polygon(c['ring']) for c in d['courts']])
for a,b in [(road,paths),(ground,road),(ground,paths),(road,buildings),(paths,buildings)]:assert a.intersection(b).area<.2
coverage=unary_union([ground,road,paths,buildings,courts,union('track')]);assert area.difference(coverage).area<.3
assert road.boundary.intersection(ground.buffer(.002)).length>100
print('PASS: shared flat terrain/pavement seams, no building/road/path overlaps, campus covered without open gaps')
