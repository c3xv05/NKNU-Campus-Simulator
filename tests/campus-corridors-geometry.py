import json,subprocess
from pathlib import Path
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());old=json.loads(subprocess.check_output(['git','show','022a0d9:data/campus.json'],cwd=root))
def union(regions):return unary_union([Polygon(r[0],r[1:]) for r in regions])
def plan(name):return union(json.loads((root/f'data/{name}-plan.js').read_text().split('=',1)[1].rstrip(';\n'))['regions'])
lower=union(c['courtyard']['floorRegions']['lower']);upper=union(c['courtyard']['floorRegions']['upper']);walk=plan('sidewalk');motor=plan('motor-pavement')
assert len(c['courtyard']['floorRegions']['upper'])==1,'Gallery must join the original L walkway'
source=json.loads((root/'facilities/campus-corridors/layout.json').read_text());assert upper.buffer(.001).covers(LineString(source['courtyardGallery']['line']).intersection(lower))
legacy=Polygon(old['courtyard']['accessRampRing']).intersection(Polygon(c['courtyard']['ring']));assert legacy.difference(lower).area<1e-5,'Old inclined cut must be filled'
for a in c['campusTransitions']:
 shape=union(a['regions']);assert shape.area>30
 for name,other in [('road',motor),('old tiles',walk),('plaza',lower)]:assert shape.intersection(other).area<.0001 and shape.intersection(other).buffer(-.001).is_empty,(a['id'],name,shape.intersection(other).area)
 assert abs(sum(Polygon(t).area for t in a['triangles'])-shape.area)<.0001
bio=union(c['bioConnection']['corridor']['regions']);assert bio.geom_type=='Polygon' and bio.area>150
for floor in ['lower','upper']:
 shape=union(c['courtyard']['floorRegions'][floor]);assert abs(shape.area-sum(Polygon(t).area for t in c['courtyard']['floorTriangles'][floor]))<.0001
for stair in c['levelLink']['stairs']+c['courtyard']['stairs']:assert upper.intersection(Polygon(stair['ring'])).area<1e-5
for key in ['roads','places','buildings','levelLink','teachingAccess','courtParking','gaussStop']:assert c[key]==old[key],key
assert c['bioConnection']['stairs']==old['bioConnection']['stairs']
print('PASS: connected flat gallery, former slope opening filled, non-overlapping road/tile/ramp footprints, stairwells preserved and all roads/buildings/rest stairs/garage/shelter unchanged')
