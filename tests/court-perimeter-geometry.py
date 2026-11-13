import json
from pathlib import Path
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());readplan=lambda p:json.loads((root/p).read_text().split('=',1)[1].rstrip(';\n'));walk=unary_union([Polygon(r[0],r[1:])for r in readplan('data/sidewalk-plan.js')['regions']]);roads=unary_union([Polygon(r[0],r[1:])for r in readplan('data/motor-pavement-plan.js')['regions']]);courts=[]
for zone in c['sportsZones']:
 p=zone['ring'];vectors=[[p[(i+1)%4][j]-p[i][j]for j in range(2)]for i in range(4)]
 for i in range(4):assert abs(sum(vectors[i][j]*vectors[(i+1)%4][j]for j in range(2)))<.00002
 shape=Polygon(p);assert shape.intersection(walk).area<1e-7 and shape.intersection(roads).area<1e-7;courts.append(shape)
regions=[]
for a in c['sportsAccess']['surfaces']:
 shape=unary_union([Polygon(r[0],r[1:])for r in a['regions']]);assert shape.area>1;assert shape.intersection(walk).area<1e-5;assert shape.intersection(roads).area<1e-5;assert all(shape.intersection(p).area<1e-5 for p in courts);regions.append(shape)
assert sum(p.area for p in regions)-unary_union(regions).area<1e-5
for a in c['sportsAccess']['surfaces']:
 if a['kind']=='ramp':assert LineString(a['line']).distance(roads.union(walk))<1e-6
assert {f['side']for f in c['sportsAccess']['fences']}=={'east','south','west'};stairs=next(a for a in c['sportsAccess']['surfaces']if a['kind']=='stairs');assert stairs['steps']==6 and stairs['rise']==.9
print('PASS: two rectangular zones, zero road/walk overlap, non-overlapping shoulders/access, both exits touch exterior pavement, six short eastern steps, east/south/west fence segments')
