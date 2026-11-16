import json,subprocess,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());old=json.loads(subprocess.check_output(['git','show','538c759:data/campus.json'],cwd=root))
def plan(name):return json.loads((root/('data/'+name+'-plan.js')).read_text().split('=',1)[1].rstrip(';\n'))
walk=plan('sidewalk');motor=plan('motor-pavement');sw=unary_union([Polygon(p[0],p[1:])for p in walk['regions']]);road=unary_union([Polygon(p[0],p[1:])for p in motor['regions']]);access=c['teachingAccess'];origin=access['anchor'];n=access['outward'];t=access['along'];project=lambda p,v:sum((p[i]-origin[i])*v[i]for i in [0,1]);stairs=c['levelLink']['stairs']
for i,s in enumerate(stairs):
 assert s['steps']==8 and s['flights']==1
 assert math.isclose(math.dist(*s['line']),3.2,abs_tol=1e-6)
 assert Polygon(s['ring']).intersection(sw).area<1e-5
 assert Polygon(s['ring']).intersection(road).area<1e-5
 assert min(project(p,t)for p in s['ring'])>=access['northClearance']-1e-6
 assert max(project(p,n)for p in s['ring'])<=-access['frontInset']+1e-6
 assert s['width']==old['levelLink']['stairs'][i]['width']
low=stairs[0];assert math.isclose(project(low['line'][1],n),-access['frontInset'],abs_tol=1e-6)
for k in range(1,12):
 for u in [0,.5,1,2,3]:
  p=[origin[i]+n[i]*u+t[i]*(access['northClearance']+k)for i in[0,1]]
  assert sw.distance(Point(p))<.002,('missing restored walkway',p)
floors=unary_union([Polygon(p[0],p[1:])for p in c['courtyard']['floorRegions']['lower']]);assert floors.buffer(.001).covers(LineString([low['line'][0],stairs[1]['line'][1]]))
upperFloor=unary_union([Polygon(p[0],p[1:])for p in c['courtyard']['floorRegions']['upper']]);upperStart=stairs[1]['line'][0];assert upperFloor.covers(Point([upperStart[i]-n[i]*.5 for i in[0,1]]))
# Geometry outside this local teaching access remains untouched.
assert c['roads']==old['roads'];assert c['places']==old['places'];assert c['buildings']==old['buildings'];assert c['bioConnection']==old['bioConnection'];assert c['courtParking']==old['courtParking'];assert c['gaussStop']==old['gaussStop']
oldWalk=json.loads(subprocess.check_output(['git','show','538c759:data/sidewalk-plan.js'],cwd=root,text=True).split('=',1)[1].rstrip(';\n'));oldSw=unary_union([Polygon(p[0],p[1:])for p in oldWalk['regions']]);change=sw.symmetric_difference(oldSw);outside=change.difference(box(-140,-245,-90,-210));assert outside.area<.25 and outside.buffer(-.003).area<1e-6,change.area
print('PASS: two eight-step 3.2m runs aligned behind Zhili facade, zero road/walk overlap, full restored paving, connecting landing, unchanged roads/buildings/garage/shelter',{'recoveredWalkway':round(sw.difference(oldSw).area,3),'oldWalkRemoved':round(oldSw.difference(sw).area,3)})
