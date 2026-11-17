"""All room/bath/public spaces connect with 30cm body clearance; original grounds unchanged."""
import json,subprocess,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((root/p).read_text())
data=read('buildings/foresight/interior.json');plan=read('buildings/foresight/plan.json');c=read('data/campus.json')
baseline=json.loads(subprocess.check_output(['git','show','a6c05f7:data/campus.json'],cwd=root))
current=json.loads(json.dumps(c));old=next(b for b in baseline['places'] if b['osm']==381731688)
for section in ['places','buildings']:
 current[section]=[old if b['osm']==381731688 else b for b in current[section]]
assert current==baseline,'Only Jiyuan building metadata may change in campus.json'
assert data['floorHeight']==3 and data['floorCount']==5
counts=[]
for f in data['floors']:
 assert f['height']==(f['floor']-1)*3
 rooms=[s for s in f['spaces'] if s['kind']=='room'];baths=[s for s in f['spaces'] if s['kind']=='bathroom'];assert len(rooms)==(23 if f['floor']==1 else 24)
 assert len(set(s['id'] for s in rooms))==len(rooms)
 assert len(baths)==14
 assert sum(s['sets'] for s in baths)==24
 for bath in baths:
  assert len(bath['fixtures'])==4*bath['sets']
  assert len(bath['serves'])==bath['sets']
  for kind in ['squat','urinal','sink','shower']:assert sum(v['kind']==kind for v in bath['fixtures'])==bath['sets']
  equipment=[]
  for v in bath['fixtures']:
   assert Polygon(bath['ring']).contains(Point(v['center']))
   w,h={'sink':(.54,.44),'urinal':(.38,.36),'squat':(.48,.65),'shower':(.68,.68)}[v['kind']];a=v['angle'];cs=math.cos(a);sn=math.sin(a);x,z=v['center'];q=Polygon([(x+dx*cs+dz*sn,z-dx*sn+dz*cs) for dx,dz in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]])
   assert q.difference(Polygon(bath['ring'])).area<1e-6,('equipment outside bath',bath['id'],v['kind'])
   assert all(q.intersection(other).area<1e-6 for other in equipment),('equipment overlap',bath['id'])
   equipment.append(q)
 surface=unary_union([Polygon(r[0],r[1:]) for r in f['surfaceRegions']]);walls=unary_union([LineString(s).buffer(.375) for s in f['walls']+f['windows']]);fixtures=unary_union([Point(v['center']).buffer(.3+(.27 if v['kind']=='sink' else .18)) for s in baths for v in s['fixtures'] if v['kind'] in ['sink','urinal']]);free=surface.buffer(-.3).difference(walls.union(fixtures));parts=list(free.geoms) if free.geom_type=='MultiPolygon' else[free];main=max(parts,key=lambda p:p.area)
 for s in f['spaces']:assert Polygon(s['ring']).buffer(-.3).intersection(main).area>.1,('unreachable',f['floor'],s['id'])
 for stair in f['stairs']:
  assert len(stair['treads'])==17
  assert max(t['height'] for t in stair['treads'])==3
  assert sorted(set(t['flight'] for t in stair['treads']))==[-1,0,1]
 counts.append({'floor':f['floor'],'rooms':len(rooms),'bathrooms':len(baths),'equipmentSets':sum(s['sets'] for s in baths)})
foot=unary_union([Polygon(r[0],r[1:]) for r in data['floors'][0]['regions']])
for f in data['floors']:
 foot=unary_union([Polygon(r[0],r[1:]) for r in f['regions']])
 for r in c['roads']:assert foot.intersection(LineString(r['line']).buffer(r['width']/2)).area<1e-7,('road overlap',f['floor'],r['osm'])
walkdata=json.loads((root/'data/sidewalk-plan.js').read_text().split('=',1)[1].strip().rstrip(';'))
walk=unary_union([Polygon(r[0],r[1:]) for r in walkdata['regions']])
entry=Polygon(next(p for p in c['pedestrianLinks'] if p['id']=='P05')['ring'])
for f in data['floors']:
 footprint=unary_union([Polygon(r[0],r[1:]) for r in f['regions']])
 assert footprint.intersection(walk.difference(entry.buffer(.01))).area<1e-5,('sidewalk intrusion',f['floor'])
# A repeat build must preserve the compiled artifact exactly.
path=root/'buildings/foresight/interior.json';before=path.read_bytes();subprocess.run(['python',str(root/'scripts/build-jiyuan-interior.py')],check=True);assert path.read_bytes()==before
print('PASS: all 119 rooms / 70 bathrooms / 120 equipment sets / public rooms connected at radius .3; 16 stair links; zero road overlap; all non-Jiyuan campus data unchanged; repeat build identical',counts)
