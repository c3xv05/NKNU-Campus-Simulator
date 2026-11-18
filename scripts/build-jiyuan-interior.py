"""Compile the reviewed Jiyuan plan into shared render/collision surfaces.
No campus footprint, terrain, paving or road data is rewritten by this generator.
"""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
root=Path(__file__).resolve().parents[1]
plan=json.loads((root/'buildings/foresight/plan.json').read_text())
model_scale=plan.get('modelScale',1);floor_height=plan['floorHeight']
assert math.isclose(floor_height,3*model_scale), 'uniform XYZ scale must include floor heights'
place=plan['placement']; angle=place['angle']; scale=place['scale']; cs=math.cos(angle); sn=math.sin(angle)
def world(p):
 u=(p[0]-place['sourceOrigin'][0])*scale;v=(p[1]-place['sourceOrigin'][1])*scale
 return [round(place['origin'][0]+cs*u+sn*v,7),round(place['origin'][1]+sn*u-cs*v,7)]
def local(p):return world(p)
def heading(back):
 # Renderer local +z is the fixture back (wall side); convert a source-pixel direction to that yaw.
 wx=cs*back[0]+sn*back[1];wz=sn*back[0]-cs*back[1];return round(math.atan2(wx,wz),7)
def pixel(p):
 x=(p[0]-place['origin'][0])/scale;z=(p[1]-place['origin'][1])/scale
 return [x*cs+z*sn+place['sourceOrigin'][0],x*sn-z*cs+place['sourceOrigin'][1]]
def boundary_segment(segment,polygon):
 a,b=segment;return polygon.boundary.distance(Point(pixel([(a[0]+b[0])/2,(a[1]+b[1])/2])))<.2

def rings(poly):return [[local(p) for p in list(poly.exterior.coords)[:-1]]]+[[local(p) for p in list(r.coords)[:-1]] for r in poly.interiors]
def polygons(g):return [g] if g.geom_type=='Polygon' else [p for p in g.geoms if p.geom_type=='Polygon']
def triangles(g):return [[world(p) for p in list(t.exterior.coords)[:3]] for t in constrained_delaunay_triangles(g).geoms]
def edge_door(poly,at,width=30):
 # Project onto the nearest real boundary so passage cut and label never drift.
 line=poly.boundary;pt=line.interpolate(line.project(Point(at)));dist=line.project(pt);a=line.interpolate(dist-width/2);b=line.interpolate(dist+width/2)
 # Avoid wrapping at the polygon origin, which would cut an unrelated edge.
 for p,q in zip(poly.exterior.coords,list(poly.exterior.coords)[1:]):
  edge=LineString([p,q])
  if edge.distance(pt)<.01:
   dx=q[0]-p[0];dy=q[1]-p[1];n=math.hypot(dx,dy);return LineString([(pt.x-dx/n*width/2,pt.y-dy/n*width/2),(pt.x+dx/n*width/2,pt.y+dy/n*width/2)])
 raise ValueError(at)
floors=[]
for floor in range(5):
 spaces=[];doors=[];core=unary_union([Polygon(p) for p in plan['corridors']])
 for definition in plan['rooms']:
  n=definition['number']; number=str(plan['groundRoomNumbers'].get(str(n))) if floor==0 else str(n+(floor-1)*100)
  kind='manager' if floor==0 and number=='None' else 'room';name='管理員室' if kind=='manager' else number
  p=Polygon(definition['polygon']);assert p.intersection(core).area<1e-7,('room invades reserved corridor',n);door=edge_door(p,definition['door']);doors.append({'line':door,'kind':'room','name':name,'from':name,'to':'corridor'})
  assert core.boundary.buffer(.1).covers(door),('room door must open to corridor',n)
  spaces.append({'id':name,'kind':kind,'name':name,'polygon':p,'door':door})
 for definition in plan['bathrooms']:
  p=Polygon(definition['polygon']);served=[s for n in definition['rooms'] for s in spaces if s['name']==('管理員室' if floor==0 and plan['groundRoomNumbers'][str(n)] is None else str(plan['groundRoomNumbers'][str(n)] if floor==0 else n+(floor-1)*100))]
  assert p.intersection(core).area<1e-7,('bathroom invades reserved corridor',definition['id'])
  assert len(served)==len(definition['rooms'])
  for entry in definition['doors']:
   n=entry['room'];name='管理員室' if floor==0 and plan['groundRoomNumbers'][str(n)] is None else str(plan['groundRoomNumbers'][str(n)] if floor==0 else n+(floor-1)*100)
   room=next(r for r in served if r['name']==name);door=edge_door(p,entry['at'],entry.get('width',24))
   assert room['polygon'].boundary.buffer(.1).covers(door),('bathroom door must open from room',definition['id'],n)
   doors.append({'line':door,'kind':'bathroom','name':definition['id'],'from':name,'to':definition['id']})
  spaces.append({'id':definition['id'],'kind':'bathroom','name':'浴室','polygon':p,'sets':len(served),'serves':[s['name'] for s in served],'layout':definition.get('layout')})
 for definition in plan['publicSpaces']:
  p=Polygon(definition['polygon']).buffer(0);door=edge_door(p,definition['door'],48 if definition['id'] in ['lounge','semicircle'] else 26);doors.append({'line':door,'kind':'public','name':definition['name']})
  center=door.interpolate(.5,normalized=True)
  assert center.distance(core)<1,('public door outside corridor',definition['id'])
  spaces.append({'id':definition['id'],'kind':'laundry' if 'laundry' in definition['id'] else 'public','name':definition.get('groundName',definition['name']) if floor==0 else definition['name'],'polygon':p,'door':door})
 if floor:
  p=Polygon(plan['standardTerrace']['polygon']);door=edge_door(p,plan['standardTerrace']['door'],48);doors.append({'line':door,'kind':'public','name':'露台'})
  spaces.append({'id':'terrace','kind':'terrace','name':'露台','polygon':p,'door':door})
 stairs=[box(*s['box']) for s in plan['stairs']]
 footprint=unary_union([s['polygon'] for s in spaces]+stairs+[core]).buffer(2,join_style='mitre').buffer(-2,join_style='mitre')
 # Only short source drafting gaps are closed; no bridging across the courtyard.
 footprint=unary_union([Polygon(p.exterior) for p in polygons(footprint)])
 assert footprint.geom_type=='Polygon',f'disconnected floor {floor}: {footprint.geom_type}'
 holes=[]
 for stair in plan['stairs']:
  x1,y1,x2,y2=stair['box']
  if stair.get('corridorSide')=='north':
   # Every end stair, including 1F to 2F, turns south and lands at the inner north hall.
   holes.append(box(x1+2,y1+25,x2-2,y2-2))
  else:holes.append(box(x1+2,y1+2,x2-2,y2-25))
 holes=unary_union(holes) if floor else Polygon()
 floor_surface=footprint.difference(holes)
 walls=unary_union([s['polygon'].boundary for s in spaces]+[footprint.boundary])
 openings=unary_union([d['line'].buffer(2,cap_style='flat') for d in doors])
 # Only the central lobby opens outdoors. End stair exterior walls remain sealed.
 if floor==0:
  exits=[LineString([(875,854),(925,854)])]
  openings=unary_union([openings]+[e.buffer(4,cap_style='square') for e in exits])
 else:exits=[]
 windows=[]
 for room in [s for s in spaces if s['kind'] in ['room','manager']]:
  exterior=room['polygon'].boundary.intersection(footprint.boundary.buffer(.1))
  candidates=[exterior] if exterior.geom_type=='LineString' else [v for v in getattr(exterior,'geoms',[]) if v.geom_type=='LineString']
  candidates=[v for v in candidates if v.length>40]
  if candidates:
   line=max(candidates,key=lambda v:v.length);pt=line.interpolate(.5,normalized=True);window=edge_door(room['polygon'],[pt.x,pt.y],min(48,line.length*.6));windows.append(window)
 window_cut=unary_union([w.buffer(1,cap_style='square') for w in windows])
 cut=walls.difference(openings.union(window_cut))
 wall_lines=[cut] if cut.geom_type=='LineString' else [x for x in cut.geoms if x.geom_type=='LineString']
 segments=[]
 for line in wall_lines:
  for a,b in zip(line.coords,list(line.coords)[1:]):
   if math.dist(a,b)>1:segments.append([world(a),world(b)])
 # Room to shared bathroom openings must cut the room-side wall too, not just the bath side.
 rec={'floor':floor+1,'height':floor*floor_height,'corridorRoutes':[[world(p) for p in route] for route in plan['corridorRoutes']],'corridorRegions':[rings(p) for p in polygons(core.difference(unary_union([s['polygon'] for s in spaces])))],'regions':[rings(p) for p in polygons(footprint)],'roofTriangles':triangles(footprint.difference(Polygon(plan['standardTerrace']['polygon'])) if floor else footprint),'windows':[[world(p) for p in w.coords] for w in windows],'surfaceRegions':[rings(p) for p in polygons(floor_surface)],'floorTriangles':triangles(floor_surface),'lowWallIndices':[i for i,segment in enumerate(segments) if floor and boundary_segment(segment,Polygon(plan['standardTerrace']['polygon'])) and not boundary_segment(segment,Polygon(plan['publicSpaces'][1]['polygon']))],'walls':segments,'exteriorWallIndices':[i for i,segment in enumerate(segments) if boundary_segment(segment,footprint)],'spaces':[],'doors':[],'entrances':[[world(p) for p in e.coords] for e in exits],'stairs':[],'partitions':[],'stallDoors':[],'cabinets':[],'vents':[]}
 for s in spaces:
  center=s['polygon'].representative_point();r={k:v for k,v in s.items() if k not in ['polygon','door','layout']};r.update(ring=rings(s['polygon'])[0],center=world([center.x,center.y]),triangles=triangles(s['polygon']))
  if 'door' in s:r['door']=[world(v) for v in s['door'].coords]
  if s['kind']=='bathroom' and s.get('layout'):
   # User-confirmed shared layout: fixed fixtures, stall partitions, wall cabinets and a closed vent.
   layout=s['layout'];poly=s['polygon'];bathdoors=[d['line'] for d in doors if d['kind']=='bathroom' and d['name']==s['id']]
   r['fixtures']=[{'kind':f['kind'],'center':world(f['at']),'angle':heading(f['back'])} for f in layout['fixtures']]
   assert sorted(f['kind'] for f in r['fixtures'])==sorted(['sink','urinal','squat','shower']*s['sets']),s['id']
   lines=[];openings=[]
   for stall in layout['stalls']:
    sp=Polygon(stall['polygon']);assert sp.difference(poly).area<1,('stall outside bath',s['id'])
    door_line=LineString(stall['door']);assert sp.boundary.distance(door_line.interpolate(.5,normalized=True))<.05,('stall door off edge',s['id'])
    openings.append(door_line);coords=list(sp.exterior.coords)
    for a,b in zip(coords,coords[1:]):
     edge=LineString([a,b])
     if poly.boundary.buffer(.6).covers(edge):continue  # existing bath wall
     lines.append(edge)
    # Door leaf stands open about 75 degrees into the stall from the hinge end.
    (ax,ay),(bx,by)=stall['door'];l=math.dist((ax,ay),(bx,by));ux,uy=(bx-ax)/l,(by-ay)/l;c=sp.centroid;nx,ny=-uy,ux
    if (c.x-ax)*nx+(c.y-ay)*ny<0:nx,ny=-nx,-ny
    ang=math.radians(75);leaf=[(ax,ay),(ax+(ux*math.cos(ang)+nx*math.sin(ang))*l*.92,ay+(uy*math.cos(ang)+ny*math.sin(ang))*l*.92)]
    rec['stallDoors'].append({'kind':stall['kind'],'line':[world(v) for v in leaf]})
   walls_cut=unary_union(lines).difference(unary_union([o.buffer(.3,cap_style='flat') for o in openings]))
   for line in ([walls_cut] if walls_cut.geom_type=='LineString' else [g for g in getattr(walls_cut,'geoms',[]) if g.geom_type=='LineString']):
    for a,b in zip(line.coords,list(line.coords)[1:]):
     if math.dist(a,b)>.5:
      seg=LineString([a,b]);assert not any(seg.distance(d)<1 for d in bathdoors),('partition blocks bath door',s['id']);rec['partitions'].append([world(a),world(b)])
   for c in layout['cabinets']:rec['cabinets'].append({'center':world(c['at']),'angle':heading(c['back'])})
   for v in layout['vents']:
    line=LineString(v['line']);assert poly.boundary.buffer(.3).covers(line),('vent off bath wall',s['id']);rec['vents'].append([world(p) for p in v['line']])
  elif s['kind']=='bathroom':
   # Pack equipment inside the real service polygon, clear of all bathroom doors.
   candidates=[];x1,y1,x2,y2=s['polygon'].bounds
   bathdoors=[d['line'] for d in doors if d['kind']=='bathroom' and d['name']==s['id']]
   for ix in range(15):
    for iy in range(15):
     q=Point(x1+10+(x2-x1-20)*ix/14,y1+10+(y2-y1-20)*iy/14)
     if s['polygon'].buffer(-8).contains(q) and all(q.distance(dl)>13 for dl in bathdoors):candidates.append(q)
   walks=[]
   for door in bathdoors:
    a,b=list(door.coords);dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy);m=door.interpolate(.5,normalized=True)
    walks.append(LineString([(m.x-dy/length*14,m.y+dx/length*14),(m.x+dy/length*14,m.y-dx/length*14)]))
   kinds=['sink','urinal','squat','shower'];chosen=[];chosen_boxes=[]
   sizes={'sink':(.54,.44),'urinal':(.38,.36),'squat':(.48,.65),'shower':(.68,.68)}
   def equipment_box(q,kind):
    w,h=[v*model_scale for v in sizes[kind]];return box(q.x-w/scale/2,q.y-h/scale/2,q.x+w/scale/2,q.y+h/scale/2)
   for k in range(s['sets']*4):
    eligible=[q for q in candidates if all(q.distance(v)>14 for v in chosen) and (kinds[k%4] not in ['sink','urinal'] or all(q.distance(v)>14 for v in walks)) and s['polygon'].buffer(-.5).contains(equipment_box(q,kinds[k%4])) and all(equipment_box(q,kinds[k%4]).intersection(v).area<.001 for v in chosen_boxes)]
    assert eligible,('equipment overflow',s['id'],k,[(v.x,v.y) for v in chosen])
    q=max(eligible,key=lambda q:(min([q.distance(v) for v in chosen] or [min(q.distance(v) for v in walks)]))-s['polygon'].boundary.distance(q)*.2);chosen.append(q);chosen_boxes.append(equipment_box(q,kinds[k%4]))
   r['fixtures']=[{'kind':kinds[i%4],'center':world([q.x,q.y]),'angle':-angle} for i,q in enumerate(chosen)]
  rec['spaces'].append(r)
 for d in doors:rec['doors'].append({**{k:v for k,v in d.items() if k!='line'},'line':[world(p) for p in d['line'].coords]})
 # The same treads feed geometry and support; two parallel flights with a level turn.
 if floor<4:
  for s in plan['stairs']:
   x1,y1,x2,y2=s['box'];gap=6;mid=(x1+x2)/2;landing=25;start=y2-landing;end=y1+landing;w=(x2-x1-gap)/2
   tread=[]
   for flight in range(2):
    for j in range(8):
     if flight==0:top=floor_height/2*(j+1)/8;xa=x1;xb=mid-gap/2;ya=start+(end-start)*(j+1)/8;yb=start+(end-start)*j/8
     else:top=floor_height/2+floor_height/2*(j+1)/8;xa=mid+gap/2;xb=x2;ya=end+(start-end)*j/8;yb=end+(start-end)*(j+1)/8
     tread.append({'ring':[world(p) for p in [(xa,ya),(xb,ya),(xb,yb),(xa,yb)]],'height':top,'flight':flight})
   tread.append({'ring':[world(p) for p in [(x1,y1),(x2,y1),(x2,end),(x1,end)]],'height':floor_height/2,'flight':-1})
   route=[((x1+mid-gap/2)/2,y2-14),((x1+mid-gap/2)/2,end-12),((mid+gap/2+x2)/2,end-12),((mid+gap/2+x2)/2,y2-14)]
   if s.get('corridorSide')=='north':
    # Mirror both the shared treads and route, keeping the full-floor landing at the hall.
    for t in tread:t['ring']=[world((pixel(p)[0],y1+y2-pixel(p)[1])) for p in t['ring']]
    route=[(x,y1+y2-y) for x,y in route]
   rec['stairs'].append({'id':s['id'],'treads':tread,'route':[world(p) for p in route],'bounds':[world(p) for p in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]]})
 floors.append(rec)
result={'version':1,'building':381731688,'modelScale':model_scale,'scalePivot':place['origin'],'floorHeight':floor_height,'floorCount':5,'source':plan['source'],'floors':floors}
(root/'buildings/foresight/interior.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
print('Jiyuan:',len(floors),'floors;',sum(s['kind']=='room' for f in floors for s in f['spaces']),'rooms;',sum(s['kind']=='bathroom' for f in floors for s in f['spaces']),'bathrooms')
