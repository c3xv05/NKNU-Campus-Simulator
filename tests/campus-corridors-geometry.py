"""Site requirements independent of the renderer: alignment, dimensions and clearances."""
import json,subprocess,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());old=json.loads(subprocess.check_output(['git','show','c0b9aa9:data/campus.json'],cwd=root))
def union(regions):return unary_union([Polygon(r[0],r[1:])for r in regions])
def plan(name):return union(json.loads((root/f'data/{name}-plan.js').read_text().split('=',1)[1].rstrip(';\n'))['regions'])
def delta(line):return [line[1][i]-line[0][i]for i in range(2)]
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
court=c['courtyard'];frame=court['alignment'];along=frame['along'];lower=union(court['floorRegions']['lower']);upper=union(court['floorRegions']['upper']);walk=plan('sidewalk');motor=plan('motor-pavement')
for key in ['storeEdge','huanyuCornerEdge']:assert abs(cross(delta(frame[key]),along))<1e-5,key
assert abs(dot(delta(frame['frontLine']),along))<1e-5
corner=frame['innerCorner'];assert upper.distance(Point(corner))<.001,'The actual L corner must meet the square construction point'
assert not upper.contains(Point(-137,-191)),'Withdraw the former diagonal 2F gallery'
assert court['interiorFillReverted'] and court['rampTargetFloor']==1
ramp=next(a for a in c['campusTransitions']if a['id']=='courtyard-s32');assert ramp['targetFloor']==1
assert not lower.contains(Point(-129,-184)),'Restore the interior lower-ramp opening'
for a in c['campusTransitions']:
 shape=union(a['regions']);assert shape.area>1
 for name,other in [('road',motor),('old tiles',walk),('lower plaza',lower)]:
  overlap=shape.intersection(other);assert overlap.area<.001 and overlap.buffer(-.001).is_empty,(a['id'],name,overlap.area)
 assert abs(sum(Polygon(t).area for t in a['triangles'])-shape.area)<.0002
bio=c['bioConnection'];b=next(b for b in c['places']if b['osm']==bio['to']);end=[b['ring'][i]for i in bio['corridor']['northEndVertices']];assert math.isclose(bio['width'],math.dist(*end),abs_tol=1e-9)
assert bio['corridor']['roof'] is False
center=[sum(p[i]for p in bio['line'])/2 for i in range(2)];stem=next(a for a in c['campusTransitions']if a['id']=='biology-s05');assert stem['width']==12 and math.dist(stem['line'][-1],center)<1e-7;assert abs(dot(delta(stem['line']),delta(bio['line'])))<1e-6,'True perpendicular T'
stair=bio['stairs'];assert stair['width']==stair['topWidth'] and stair['topLevel']=='biology-lower';ring=stair['ring'];edges=[delta([ring[i],ring[(i+1)%4]])for i in range(4)];assert abs(dot(edges[0],edges[1]))<1e-5;assert math.isclose(math.hypot(*edges[0]),math.hypot(*edges[2]),abs_tol=1e-6);assert math.isclose(math.hypot(*edges[1]),math.hypot(*edges[3]),abs_tol=1e-6)
buildings=unary_union([Polygon(b['ring'])for b in c['places']+c['buildings']if b.get('height')]);assert Polygon(ring).intersection(buildings).area<1e-5;assert Polygon(ring).intersection(motor).area<.001
for key in ['roads','places','buildings','levelLink','teachingAccess','courtParking','gaussStop']:assert c[key]==old[key],key
print('PASS: S05-parallel boundaries, square L, restored lower access, B-end constant width, centred double-width T, open upper deck and rectangular lower stairs; no road/building overlap')
