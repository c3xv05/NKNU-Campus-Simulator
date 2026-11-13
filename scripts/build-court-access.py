"""Non-overlapping shoulders, two open gates, and road-connected access surfaces."""
import json,math,sys
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());p=c['sportsPerimeter'];u=p['axis'];v=[-u[1],u[0]]
def point(a,b):return [round(a*u[i]+b*v[i],7)for i in range(2)]
def coords(r):return [[round(x,7),round(z,7)]for x,z in list(r.coords)[:-1]]
def regions(shape):return [[coords(q.exterior)]+[coords(h)for h in q.interiors]for q in (list(shape.geoms)if hasattr(shape,'geoms')else[shape])if q.area>1e-7]
def triangles(shape):
 result=[];bounds=shape.bounds
 for row in range(math.floor(bounds[1]),math.ceil(bounds[3])):
  for col in range(math.floor(bounds[0]),math.ceil(bounds[2])):
   part=shape.intersection(box(col,row,col+1,row+1))
   if not part.is_empty:result.extend(coords(t.exterior)for t in constrained_delaunay_triangles(part).geoms if t.area>1e-8)
 return result
walk=json.loads((root/'data/sidewalk-plan.js').read_text().split('=',1)[1].rstrip(';\n'));walk=unary_union([Polygon(r[0],r[1:])for r in walk['regions']]);motor=json.loads((root/'data/motor-pavement-plan.js').read_text().split('=',1)[1].rstrip(';\n'));roads=unary_union([Polygon(r[0],r[1:])for r in motor['regions']]);target=roads.union(walk);zones={z['id']:Polygon(z['ring'])for z in c['sportsZones']};allCourts=unary_union([Polygon(z['ring'])for z in c['courts']]);garden=unary_union([Polygon(g['ring'])for g in c.get('sportsGardens',[])]);buildings=unary_union([Polygon(b['ring']).buffer(.1)for b in c['places']+c['buildings']if b.get('height')]);exclusions=target.union(buildings).union(garden)
def first_contact(line):
 inter=LineString(line).intersection(target);points=[]
 def collect(g):
  if hasattr(g,'geoms'):
   for q in g.geoms:collect(q)
  elif hasattr(g,'coords'):points.extend(list(g.coords))
 collect(inter);base=LineString(line);return list(min(points,key=lambda q:base.project(Point(q))))
# The southwest gate joins the nearest exterior road/sidewalk along the south normal.
g=p['southwest'];start=point(g['along'],g['across']);ray=[start,point(g['along']+25,g['across'])];end=first_contact(ray);swLine=[start,end];sw=LineString(swLine).buffer(p['gateWidth']/2,cap_style=2).difference(allCourts).difference(exclusions)
g=p['northeast'];stairLine=[point(g['along'],g['across']),point(g['along'],g['across']-g['run'])];stairs=LineString(stairLine).buffer(p['gateWidth']/2,cap_style=2);line=[point(*q)for q in g['rampLine']];end=first_contact(line);path=LineString(line);endDistance=path.project(Point(end));line=[q for q in line if path.project(Point(q))<endDistance-1e-7]+[end];east=LineString(line).buffer(1.2,cap_style=2,join_style=2).difference(allCourts).difference(exclusions).difference(stairs)
accesses=[{'id':'basketball-sw-ramp','kind':'ramp','court':444902481,'line':swLine,'startOffset':0,'regions':regions(sw),'triangles':triangles(sw)},{'id':'basketball-east-stairs','kind':'stairs','court':444902481,'line':stairLine,'steps':g['steps'],'rise':g['rise'],'regions':regions(stairs),'triangles':triangles(stairs)},{'id':'basketball-east-ramp','kind':'ramp','court':444902481,'line':line,'startOffset':-g['rise'],'regions':regions(east),'triangles':triangles(east)}]
for access,shape in [(accesses[0],sw),(accesses[2],east)]:
 boundary=shape.boundary.intersection(target.boundary.buffer(.00001));lines=[]
 def collect_edges(g):
  if hasattr(g,'geoms'):
   for q in g.geoms:collect_edges(q)
  elif g.geom_type=='LineString' and g.length>1e-6:lines.append([[round(x,7),round(z,7)]for x,z in g.coords])
 collect_edges(boundary);access['contactEdges']=lines
reserved=unary_union([sw,east,stairs]);mid=(c['sportsZones'][0]['bounds'][0]+c['sportsZones'][1]['bounds'][1])/2
shoulders=[]
for z in c['sportsZones']:
 rect=zones[z['id']];side=Polygon([point(x,b)for x,b in ([(-500,-500),(mid,-500),(mid,500),(-500,500)]if z['id']=='tennis'else[(mid,-500),(500,-500),(500,500),(mid,500)])]);envelope=rect.buffer(p['transitionWidth'],join_style=2).intersection(side).difference(exclusions);shape=envelope.difference(allCourts).difference(reserved)
 shoulders.append({'id':z['id']+'-shoulder','kind':'shoulder','court':z['courtIds'][0],'inner':z['ring'],'outer':regions(envelope),'regions':regions(shape),'triangles':triangles(shape)})
lo,hi,left,right=c['sportsZones'][0]['bounds'];swV=p['southwest']['across'];neU=p['northeast']['along'];half=p['gateWidth']/2;fences=[]
for side,a,b in [('east',point(lo,left),point(hi,left)),('south',point(hi,left),point(hi,right)),('west',point(hi,right),point(lo,right))]:
 if side=='east':parts=[(a,point(neU-half,left)),(point(neU+half,left),b)]
 elif side=='south':parts=[(a,point(hi,swV-half)),(point(hi,swV+half),b)]
 else:parts=[(a,b)]
 for a,b in parts:fences.append({'side':side,'line':[a,b],'height':p['fenceHeight']})
c['sportsAccess']={'surfaces':shoulders+accesses,'fences':fences,'footprints':[t for a in shoulders+accesses for t in a['triangles']]};(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built rectangular-court shoulders, SW ramp, short east stair and road-side ramp, and five fence runs')
