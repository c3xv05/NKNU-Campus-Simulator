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
bio=c['bioConnection'];assert math.isclose(bio['width'],(537.4-503.32)/(409.92/43.575),abs_tol=1e-6),'Hall width from the Bio A 1F drawing'
assert bio['corridor']['roof'] is False
center=bio['corridor']['joint'];stem=next(a for a in c['campusTransitions']if a['id']=='biology-s05');assert stem['width']==12 and math.dist(stem['line'][-1],center)<1e-7;assert abs(dot(delta(stem['line']),c['courtyard']['alignment']['along']))<1e-6,'Stem perpendicular to S05'; target=[sum(p[i]for p in c['levelLink']['line'])/2 for i in range(2)]; assert abs(dot([center[i]-target[i]for i in range(2)],c['courtyard']['alignment']['along']))<1e-6,'Connectors aligned across S05'
stair=bio['stairs'];assert stair['kind']=='terraces' and len(stair['pieces'])==25;ring=stair['ring'];edges=[delta([ring[i],ring[(i+1)%4]])for i in range(4)];assert abs(dot(edges[0],edges[1]))<1e-5;assert math.isclose(math.hypot(*edges[0]),math.hypot(*edges[2]),abs_tol=1e-6);assert math.isclose(math.hypot(*edges[1]),math.hypot(*edges[3]),abs_tol=1e-6)
buildings=unary_union([Polygon(b['ring'])for b in c['places']+c['buildings']if b.get('height')]);assert Polygon(ring).intersection(buildings).area<1e-5;assert Polygon(ring).intersection(motor).area<.001
for key in ['roads','buildings','levelLink','teachingAccess','courtParking','gaussStop']:assert c[key]==old[key],key
print('PASS: S05-parallel boundaries, square L, restored lower access, drawing-width Bio hall, centred double-width T, open upper deck and rectangular terraced ramp/stairs; no road/building overlap')

for building in c['places']:
 previous=next(b for b in old['places']if b['osm']==building['osm'])
 if building['osm'] not in [bio['from'],bio['to']]:assert building==previous;continue
 for p,q in zip(building['ring'],building['ring'][1:]+building['ring'][:1]):
  edge=delta([p,q]);assert min(abs(dot(edge,along)),abs(cross(edge,along)))<1e-5,'Every building edge must follow S05 or its normal'
 assert Polygon(building['ring']).is_valid and len(building['ring'])==10  # 2026-11-23 drawing outlines
 assert Polygon(building['ring']).intersection(motor).area<1e-6
assert abs(cross(delta(bio['line']),along))<1e-6,'The T crossbar must parallel S05'
landing=next(a for a in c['campusTransitions']if a['id']=='biology-east-landing');shape=union(landing['regions'])
assert landing['targetFloor']==1 and math.isclose(shape.area,landing['width']*landing['depth'],abs_tol=1e-4)
assert math.dist(landing['line'][1],stair['line'][0])<1e-7
assert shape.intersection(Polygon(stair['ring'])).area<1e-6
assert shape.intersection(union(bio['corridor']['regions'])).area<1e-6
assert shape.intersection(buildings).area<1e-6
print('PASS: drawing-traced orthogonal wings, S05-parallel hall, flower plaza meeting the terraced ramp/stairs')
