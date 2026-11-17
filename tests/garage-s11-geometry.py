"""Confirmed corner/road, restored old sidewalk and exposed basement sides."""
import json,subprocess
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());old=json.loads(subprocess.check_output(['git','show','b0868ac:data/campus.json'],cwd=root));p=c['courtParking'];a=p['entrance'];lo,hi,left,right=p['bounds'];u=p['axis'];v=[-u[1],u[0]]
def union(r):return unary_union([Polygon(x[0],x[1:])for x in r])
def plan(text):return union(json.loads(text.split('=',1)[1].rstrip(';\n'))['regions'])
walk=plan((root/'data/sidewalk-plan.js').read_text());before=plan(subprocess.check_output(['git','show','b0868ac:data/sidewalk-plan.js'],cwd=root,text=True));ramp=Polygon(a['ring']);oldramp=Polygon(old['courtParking']['entrance']['ring'])
assert a['road']==218881799 and p['vehicleEntrance']=='southeast-facing-s11'
assert a['portalAcross']<left+8 and a['portalAcross']>left+a['openingWidth']/2
assert ramp.intersection(walk).area<.001
assert walk.difference(before).intersection(oldramp).area>10,'Restore old driveway sidewalk'
assert before.difference(walk).intersection(ramp).area>10,'Clear new driveway crossing'
shoulder=union(next(x for x in c['sportsAccess']['surfaces']if x['id']=='basketball-shoulder')['regions'])
for r in next(x for x in c['sportsAccess']['surfaces']if x['kind']=='garage-ground')['regions']:
 assert Polygon(r[0],r[1:]).intersection(ramp).area<.001
for x,z in shoulder.exterior.coords if shoulder.geom_type=='Polygon'else [p for s in shoulder.geoms for p in s.exterior.coords]:
 assert x*u[0]+z*u[1]<=hi+.001 and x*v[0]+z*v[1]>=left-.001,'No upper soil shoulder on exposed sides'
for key in ['roads','places','buildings','courts','sportsZones','bioConnection','gaussStop','levelLink']:assert c[key]==old[key],key
print('PASS: S11 southeast corner, new crossing clear, old sidewalk restored, upper east/south shoulders removed, preserved courts/roads/buildings')
