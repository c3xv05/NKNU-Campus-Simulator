"""Validate the source topology, private access, actual corridor clearances and unchanged site."""
import json,math,subprocess
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((root/p).read_text())
plan=read('buildings/foresight/plan.json');data=read('buildings/foresight/interior.json');c=read('data/campus.json')
baseline=json.loads(subprocess.check_output(['git','show','0072855:data/campus.json'],cwd=root))
current=json.loads(json.dumps(c));old=next(b for b in baseline['places'] if b['osm']==381731688)
current['places']=[old if b['osm']==381731688 else b for b in current['places']]
assert current==baseline,'Non-Jiyuan campus data must remain identical'
assert data['modelScale']==1.1 and data['floorHeight']==3.3 and data['floorCount']==5
assert plan['placement']['scale']==.04176*1.1
core=unary_union([Polygon(p)for p in plan['corridors']]);occupied=[]
for key in ['rooms','bathrooms']:
 for cell in plan[key]:
  p=Polygon(cell['polygon']);assert p.intersection(core).area<1e-7,('corridor invaded',cell)
  assert all(p.intersection(other).area<1e-7 for other in occupied),('overlapping rooms or bathrooms',cell)
  occupied.append(p)
private={201,206,207,212,213,214,219,224}
shared={(202,203),(204,205),(208,209),(210,211),(215,216),(217,218),(220,221),(222,223)}
assert {b['rooms'][0]for b in plan['bathrooms']if len(b['rooms'])==1}==private
assert {tuple(sorted(b['rooms']))for b in plan['bathrooms']if len(b['rooms'])==2}==shared
for b in plan['bathrooms']:
 assert b['access']=='room-only'
 assert sorted(d['room']for d in b['doors'])==sorted(b['rooms'])
for f in data['floors']:
 assert abs(f['height']-(f['floor']-1)*3.3)<1e-10
 rooms=[s for s in f['spaces']if s['kind']=='room'];baths=[s for s in f['spaces']if s['kind']=='bathroom'];assert len(rooms)==(23 if f['floor']==1 else 24)
 assert len(baths)==16 and sum(b['sets']for b in baths)==24
 assert sum(b['sets']==1 for b in baths)==8 and sum(b['sets']==2 for b in baths)==8
 cells={s['id']:Polygon(s['ring'])for s in f['spaces']};hall=unary_union([Polygon(r[0],r[1:])for r in f['corridorRegions']]);bathdoors=[d for d in f['doors']if d['kind']=='bathroom']
 for bath in baths:
  doors=[d for d in bathdoors if d['to']==bath['id']];assert {d['from']for d in doors}==set(bath['serves'])
  assert len(doors)==bath['sets']
  for d in doors:
   portal=LineString(d['line']);assert cells[bath['id']].boundary.buffer(.00001).covers(portal)
   assert cells[d['from']].boundary.buffer(.00001).covers(portal)
   assert not portal.buffer(.0001).intersects(hall.buffer(-.001)),('bathroom hall door',bath['id'])
  fixtures=[]
  for v in bath['fixtures']:
   w,h={'sink':(.54,.44),'urinal':(.38,.36),'squat':(.48,.65),'shower':(.68,.68),'seat':(.42,.65),'showerhead':(.2,.14)}[v['kind']];w*=1.1;h*=1.1;a=v['angle'];cs=math.cos(a);sn=math.sin(a);x,z=v['center'];q=Polygon([(x+dx*cs+dz*sn,z-dx*sn+dz*cs)for dx,dz in[(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]])
   assert q.difference(cells[bath['id']]).area<1e-6
   assert all(q.intersection(other).area<1e-6 for other in fixtures)
   fixtures.append(q)
  kinds=[v['kind'] for v in bath['fixtures']]
  if bath['sets']==2:assert all(kinds.count(k)==2 for k in ['sink','urinal','squat','shower']),kinds
  # User-labelled private baths: 201/212 sink+seat toilet+shower head; 206/207 sink+urinal+squat+shower.
  else:assert kinds.count('sink')==1 and kinds.count('squat')+kinds.count('seat')==1 and kinds.count('shower')+kinds.count('showerhead')==1,(bath['id'],kinds)
 # No partition may cross the clear main corridor, even if all doors still happen to connect.
 assert all(not LineString(w).intersects(hall.buffer(-.19))for w in f['walls']),('partition squeezed corridor',f['floor'])
 floor=unary_union([Polygon(r[0],r[1:])for r in f['surfaceRegions']]);walls=unary_union([LineString(w).buffer(.3+.075*1.1)for w in f['walls']+f['windows']]);fixtures=unary_union([Point(v['center']).buffer(.3+(.27 if v['kind']=='sink' else .18)*1.1)for s in baths for v in s['fixtures']if v['kind']in['sink','urinal']]);free=floor.buffer(-.3).difference(walls.union(fixtures));parts=list(free.geoms)if free.geom_type=='MultiPolygon'else[free];main=max(parts,key=lambda p:p.area)
 for s in f['spaces']:assert cells[s['id']].buffer(-.3).intersection(main).area>.1,('unreachable space',f['floor'],s['id'])
 for stair in f['stairs']:assert len(stair['treads'])==17 and max(t['height']for t in stair['treads'])==3.3
 footprint=unary_union([Polygon(r[0],r[1:])for r in f['regions']])
 for r in c['roads']:assert footprint.intersection(LineString(r['line']).buffer(r['width']/2)).area<1e-6,('road overlap',f['floor'],r['osm'])
walkdata=json.loads((root/'data/sidewalk-plan.js').read_text().split('=',1)[1].strip().rstrip(';'));walk=unary_union([Polygon(r[0],r[1:])for r in walkdata['regions']]);entry=Polygon(next(p for p in c['pedestrianLinks']if p['id']=='P05')['ring'])
for f in data['floors']:assert unary_union([Polygon(r[0],r[1:])for r in f['regions']]).intersection(walk.difference(entry.buffer(.01))).area<1e-5
# Diagonal: measured between the facing shared-bath walls. The inner bath wall follows the original
# drawing (2026-11-18 user-approved), giving about 1.83-1.97m clear (1.1x) instead of the former widened 2.48m.
baths={b['id']:Polygon(b['polygon']) for b in plan['bathrooms']}
diagonal=min(baths[side+'-shared-'+a].boundary.distance(baths[side+'-shared-'+b].boundary) for side in ['left','right'] for a,b in [('202-203','208-209'),('204-205','210-211')])
clearances={'central':90*plan['placement']['scale']-.15*1.1,'upper-wing':48*plan['placement']['scale']-.15*1.1,'diagonal':diagonal*plan['placement']['scale']-.15*1.1}
assert clearances['central']>2 and clearances['upper-wing']>2 and clearances['diagonal']>1.8,clearances
# A stair must join the real corridor, not merely be walkable between two isolated points.
place=plan['placement'];cs=math.cos(place['angle']);sn=math.sin(place['angle'])
def pixel(p):
 x=(p[0]-place['origin'][0])/place['scale'];z=(p[1]-place['origin'][1])/place['scale']
 return [x*cs+z*sn+place['sourceOrigin'][0],x*sn-z*cs+place['sourceOrigin'][1]]
for i,f in enumerate(data['floors'][:-1]):
 for stair in f['stairs'][2:]:
  definition=next(s for s in plan['stairs'] if s['id']==stair['id']);x1,y1,x2,y2=definition['box']
  arrival=pixel(stair['route'][-1]);assert abs(arrival[1]-(y1+14))<.001
  assert abs(pixel(stair['route'][0])[1]-(y1+14))<.001
  landing=Polygon([(x1,y1),(x2,y1),(x2,y1+24),(x1,y1+24)])
  next_floor=unary_union([Polygon([pixel(p) for p in r[0]],[[pixel(p) for p in h] for h in r[1:]]) for r in data['floors'][i+1]['surfaceRegions']])
  assert next_floor.buffer(.001).covers(landing),'upper landing must reach corridor at full storey height'
  turns=[t for t in stair['treads'] if t['flight']==-1]
  assert len(turns)==1 and turns[0]['height']==data['floorHeight']/2
  assert len(stair['route'])==4 and all(sum(t['flight']==j for t in stair['treads'])==8 for j in [0,1])
  if i==0:
   assert definition['exteriorExit'] is False and 'groundExit' not in definition
   wall=unary_union([LineString([pixel(p) for p in w]) for w in f['walls']])
   assert wall.buffer(.001).covers(LineString([(x1+1,y2),(x2-1,y2)])),'outside wall must be continuous'
assert len(data['floors'][0]['entrances'])==1,'only the main lobby is an exterior entrance'
path=root/'buildings/foresight/interior.json';before=path.read_bytes();subprocess.run(['python',str(root/'scripts/build-jiyuan-interior.py')],check=True);assert before==path.read_bytes()
print('PASS: 8 private + 8 shared baths per floor; every bathroom entered from its room only; no corridor intrusion; all spaces reachable; uniform XYZ 1.1; unchanged site; repeat build identical. Main clear widths:',clearances)
