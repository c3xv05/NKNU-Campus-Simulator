"""Two plaza floors with a road-aligned, square L and the restored lower access cut."""
import json, math, subprocess, sys
from pathlib import Path
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());layout=json.loads((root/'facilities/teaching-courtyard/layout.json').read_text());court=c['courtyard'];lookup={b['osm']:b for b in c['places']}
legacy={int(k):v for k,v in layout.get('legacyRings',{}).items()}
def ringOf(osm):return legacy.get(osm,lookup[osm]['ring'])
def resolve(p):return ringOf(p['building'])[p['vertex']] if isinstance(p,dict)else p
def coords(r):return [[round(x,7),round(z,7)]for x,z in list(r.coords)[:-1]]
def polygons(p):return [a for a in (list(p.geoms)if hasattr(p,'geoms')else[p])if a.geom_type=='Polygon' and a.area>1e-7]
def triangles(p):return [coords(t.exterior)for a in polygons(p)for t in constrained_delaunay_triangles(a).geoms if t.area>1e-7]
def regions(p):return [[coords(a.exterior),*[coords(h)for h in a.interiors]]for a in polygons(p)]
rawring=[resolve(p)for p in layout['boundary']];alignment=layout['alignment'];road=next(r for r in c['roads']if r['osm']==alignment['road']);near=Point(alignment['near']);a,b=min(zip(road['line'],road['line'][1:]),key=lambda pair:LineString(pair).distance(near));length=math.dist(a,b);t=[(b[i]-a[i])/length for i in range(2)];n=[t[1],-t[0]];origin=c['teachingAccess']['anchor']
def uv(p):return [sum((p[i]-origin[i])*v[i]for i in range(2))for v in [n,t]]
def at(u,v):return [round(origin[i]+n[i]*u+t[i]*v,7)for i in range(2)]
def world_polygon(p):return Polygon([at(*v)for v in list(p.exterior.coords)[:-1]])
huanyu=lookup[444867694];zhili=lookup[444867693];gauss=lookup[444867692];store_u=max(uv(p)[0]for p in c['levelLink']['ring']);front_v=max(uv(p)[1]for p in c['levelLink']['ring']);corner_u=uv(huanyu['ring'][14])[0];corner_v=uv(ringOf(444867693)[8])[1]
# Both free long boundaries use exactly the same S05 tangent; building shells stay fixed.
newring=[at(corner_u,corner_v),*rawring[1:5],at(store_u,uv(rawring[5])[1]),at(store_u,front_v),at(uv(gauss['ring'][5])[0],front_v),*rawring[6:]]
buildings=unary_union([Polygon(a['ring']).buffer(.01,join_style=2)for a in c['places']+c['buildings']if a.get('height')]);original=unary_union([Polygon(rawring),Polygon(c['levelLink']['ring'])]).difference(buildings);shape=unary_union([Polygon(newring),Polygon(c['levelLink']['ring'])]).difference(buildings)
inner_u=max(uv(huanyu['ring'][i])[0]for i in layout['upperPlan']['huanyuEdges'])+layout['upperPlan']['huanyuWalkWidth']
# An exact perpendicular corner replaces the former global-Z diagonal band.
mask=unary_union([world_polygon(box(-1000,-1000,1000,front_v)),world_polygon(box(-1000,front_v,inner_u,1000))]);upper=shape.intersection(mask)
if court.get('stairs'):
 stair=court['stairs'][0];stair['line']=layout['centralStair']['line'];stair['width']=layout['centralStair']['width'];a,b=stair['line'];dx=b[0]-a[0];dz=b[1]-a[1];length=math.hypot(dx,dz);nx=-dz/length*stair['width']/2;nz=dx/length*stair['width']/2;stair['ring']=[[a[0]+nx,a[1]+nz],[b[0]+nx,b[1]+nz],[b[0]-nx,b[1]-nz],[a[0]-nx,a[1]-nz]]
for s in c['levelLink']['stairs']+court.get('stairs',[]):upper=upper.difference(Polygon(s['ring']))
# Revert the blanket fill; the corridor builder cuts the lower access along the existing path.
ramp=LineString(court['ramp']).buffer(court['width']/2,cap_style=2);extension=Polygon(legacy[444867693]).buffer(0) if 444867693 in legacy else Polygon()
# The former Zhili shell area beyond the drawing tower continues the lower plaza at Zhili 1F level.
lowerShape=shape.union(extension).union(Polygon(c['teachingAccess']['lowerLanding'])).difference(buildings);lower=lowerShape.difference(Polygon(c['levelLink']['stairs'][0]['ring']))
# Exposed rims of the extension get a solid base (drop side) or retaining wall (uphill side) at runtime.
extensionRegions=[];extensionEdges=[]
if not extension.is_empty:
 ext=extension.difference(buildings).intersection(lowerShape);closed=unary_union([lowerShape,buildings.buffer(.35,join_style=2),Polygon(c['levelLink']['ring']),Polygon(c['teachingAccess']['lowerLanding']),*[Polygon(s['ring']) for s in c['levelLink']['stairs']]])
 for piece in polygons(ext):
  if piece.area<1:continue
  extensionRegions.append(coords(piece.exterior))
  for rim in [piece.exterior,*piece.interiors]:
   pts=list(rim.coords)
   for p0,p1 in zip(pts,pts[1:]):
    L=math.dist(p0,p1)
    if L<.05:continue
    tan=((p1[0]-p0[0])/L,(p1[1]-p0[1])/L);nrm=(tan[1],-tan[0])
    mid=((p0[0]+p1[0])/2,(p0[1]+p1[1])/2)
    if Polygon(piece.exterior).contains(Point(mid[0]+nrm[0]*.3,mid[1]+nrm[1]*.3)):nrm=(-nrm[0],-nrm[1])
    if closed.contains(Point(mid[0]+nrm[0]*.3,mid[1]+nrm[1]*.3)):continue
    extensionEdges.append({'line':[[round(p0[0],7),round(p0[1],7)],[round(p1[0],7),round(p1[1],7)]],'outward':[round(nrm[0],7),round(nrm[1],7)]})
court.update(name=layout['name'],ring=newring,floors=2,floorHeight=layout['floorHeight'],floorRegions={'lower':regions(lower),'upper':regions(upper)},floorTriangles={'lower':triangles(lower),'upper':triangles(upper)},footprints=triangles(lowerShape),pillars=[p for p in layout['pillars']if upper.contains(Point(p))],upperShape='L',huanyuWalkWidth=layout['upperPlan']['huanyuWalkWidth'],accessRampRing=coords(ramp.exterior),rampTargetFloor=1,exteriorAccess=True,interiorFillReverted=True,desc=layout['reference'],alignment={'origin':origin,'along':t,'outward':n,'innerCorner':at(inner_u,front_v),'storeEdge':[at(store_u,uv(rawring[5])[1]),at(store_u,front_v)],'huanyuCornerEdge':[at(corner_u,corner_v),huanyu['ring'][14]],'frontLine':[at(inner_u,front_v),at(store_u,front_v)]},edgeRepairs={'regions':regions(shape.symmetric_difference(original))},zhiliExtension={'regions':extensionRegions,'edges':extensionEdges,'reference':layout.get('zhiliExtension',{}).get('reference','')})
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
subprocess.run([sys.executable,str(root/'scripts/build-campus-corridors.py')],check=True)
print('Built square S05-aligned L; reverted interior fill and restored lower access')
