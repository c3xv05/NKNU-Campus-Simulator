"""Two plaza floors with a road-aligned, square L and the restored lower access cut."""
import json, math, subprocess, sys
from pathlib import Path
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity
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
newring=[at(corner_u,corner_v),*rawring[1:5],at(store_u,uv(rawring[5])[1]),at(store_u,front_v),at(uv(ringOf(444867692)[5])[0],front_v),*rawring[6:]]
buildings=unary_union([Polygon(a['ring']).buffer(.01,join_style=2)for a in c['places']+c['buildings']if a.get('height')]);original=unary_union([Polygon(rawring),Polygon(c['levelLink']['ring'])]).difference(buildings);shape=unary_union([Polygon(newring),Polygon(c['levelLink']['ring'])]).difference(buildings)
inner_u=max(uv(huanyu['ring'][i])[0]for i in layout['upperPlan']['huanyuEdges'])+layout['upperPlan']['huanyuWalkWidth']
# An exact perpendicular corner replaces the former global-Z diagonal band.
mask=unary_union([world_polygon(box(-1000,-1000,1000,front_v)),world_polygon(box(-1000,front_v,inner_u,1000))]);upper=shape.intersection(mask)
# Zhili drawings (user 2026-11-18): the 1F podium is building, and the 2F central plaza follows the Zhili 2F drawing
# (drawing plaza + podium roof) in addition to the existing Huanyu-side L arm.
zsite=json.loads((root/'buildings/zhili/interior.json').read_text()).get('site') if (root/'buildings/zhili/interior.json').exists() else None
podium=Polygon(zsite['groundOutline']).buffer(0) if zsite else Polygon()
if zsite:upper=unary_union([upper,*[Polygon(r).buffer(0) for r in zsite['plaza']]]).difference(buildings)
# Gauss / Huanyu drawings (user 2026-11-18): Zhili 1F = Huanyu 1F = Gauss 2F (lower plaza); Zhili 2F = Huanyu 2F = Gauss 3F
# (upper plaza, Gauss not connected). Gauss's 2F deck over its 1F audio-visual wing belongs to the lower plaza; the rest of
# Gauss's 1F footprint and its former shell area are not plaza. The 化學系廣場 and Huanyu 2F deck join the upper plaza.
ztr=json.loads((root/'buildings/zhili/building.json').read_text())['geometry']['drawingFootprint']['transform']
def zw(r):return Polygon([(ztr['a']*x-ztr['b']*y+ztr['tx'],ztr['b']*x+ztr['a']*y+ztr['tz']) for x,y in r]).buffer(0)
gplan=json.loads((root/'buildings/gauss/plan.json').read_text());hplan=json.loads((root/'buildings/huanyu/plan.json').read_text())
gauss1F=zw(gplan['outlines']['1']);gaussDeck=zw(gplan['deck2F']['ring']).difference(buildings);gaussOld=Polygon(json.loads((root/'buildings/gauss/building.json').read_text())['geometry']['beforeDrawingFootprint']['ring'])
gaussClosed=unary_union([gauss1F.difference(gaussDeck),gaussOld]).buffer(0)
zplan=json.loads((root/'buildings/zhili/plan.json').read_text())['site']
# Upper plaza (user 2026-11-18 "L型連接到上層廣場如你圖示那樣畫"): only the drawn pieces — Zhili 2F central plaza (+ podium roof),
# the 2F walkway, the 化學系廣場 and the Huanyu 2F deck; the earlier game-only L arm is replaced.
upper=unary_union([*[Polygon(r).buffer(0) for r in zsite['plaza']],zw(zplan['walkway2F']['ring']),zw(hplan['chemPlaza']['ring']),affinity.translate(zw(hplan['deck2F']['ring']),*hplan['deck2F'].get('gameOffset',[0,0]))]).buffer(.6,join_style=2).buffer(-.6,join_style=2)
upper=upper.difference(buildings).difference(gauss1F.buffer(.3,join_style=2)).difference(gaussOld)
# Huanyu's 2F through-passage (user 2026-11-13) must still land on the upper plaza: a passage-width link from its
# plaza end to the nearest drawn upper piece (pending user confirmation, 2026-11-18).
# The drawn Huanyu 2F balcony strip along its east face (the long arm of the L) lies inside the game's Huanyu outline,
# so it is laid just outside that face with the existing Huanyu walk width, joining the 化學系廣場 / podium roof.
huanyuArm=shape.intersection(world_polygon(box(-1000,-1000,inner_u,1000))).difference(buildings).difference(gauss1F.buffer(.3,join_style=2)).difference(gaussOld)
upper=unary_union([upper,huanyuArm]).buffer(.3,join_style=2).buffer(-.3,join_style=2)
hpass=lookup[444867694].get('passage')
if hpass:
 from shapely.ops import nearest_points
 end=Point(hpass['line'][1]);q=nearest_points(upper,end)[0]
 if end.distance(q)>.05:upper=unary_union([upper,LineString([hpass['line'][1],(q.x,q.y)]).buffer(hpass['width']/2,cap_style=2,join_style=2)]).difference(buildings)
gaussCourt=zw(gplan['court1F']['ring'])
def tiers(cfg,plan):
 out=[]
 for y0,y1,top in cfg['rows']:out.append({'ring':[list(p) for p in list(zw([[cfg['x'][0],y0],[cfg['x'][1],y0],[cfg['x'][1],y1],[cfg['x'][0],y1]]).exterior.coords)[:-1]],'top':top,'source':plan})
 return out
court['planters']=tiers(zplan['planterTiers'],'zhili')+tiers(gplan['westPlanters'],'gauss')
planterShape=unary_union([Polygon(p['ring']) for p in court['planters']])
zhiliPlanters=unary_union([Polygon(p['ring']) for p in court['planters'] if p['source']=='zhili'])
if court.get('stairs'):
 stair=court['stairs'][0];stair['line']=layout['centralStair']['line'];stair['width']=layout['centralStair']['width'];a,b=stair['line'];dx=b[0]-a[0];dz=b[1]-a[1];length=math.hypot(dx,dz);nx=-dz/length*stair['width']/2;nz=dx/length*stair['width']/2;stair['ring']=[[a[0]+nx,a[1]+nz],[b[0]+nx,b[1]+nz],[b[0]-nx,b[1]-nz],[a[0]-nx,a[1]-nz]]
for s in c['levelLink']['stairs']+court.get('stairs',[]):upper=upper.difference(Polygon(s['ring']))
# Revert the blanket fill; the corridor builder cuts the lower access along the existing path.
ramp=LineString(court['ramp']).buffer(court['width']/2,cap_style=2);extension=Polygon(legacy[444867693]).buffer(0) if 444867693 in legacy else Polygon()
# The former Zhili shell area beyond the drawing tower continues the lower plaza at Zhili 1F level.
# Zhili's upper floors overhang outdoor ±0 paving (drawing): for the lower plaza only Zhili's 1F footprint is building.
buildingsLower=unary_union([Polygon(a['ring']).buffer(.01,join_style=2) for a in c['places']+c['buildings'] if a.get('height') and a['osm']!=444867693]+[podium.buffer(.01,join_style=2)])
extension=extension.union(zhiliPlanters.buffer(.4,join_style=2).difference(zhiliPlanters)).union(gaussDeck).union(unary_union([zw(r) for r in zplan['paving1F']['rings']]).difference(gauss1F.difference(gaussDeck)))
sidewalkGrade=unary_union([Polygon(st['ring']) for st in c['levelLink']['stairs'] if st.get('topLevel','zhili-ground')=='zhili-ground']+[Polygon(c['teachingAccess'][k]) for k in ('frontApron','gapFootprint') if c['teachingAccess'].get(k)]).buffer(.02,join_style=2)
extension=extension.difference(sidewalkGrade)
lowerShape=shape.union(extension).union(Polygon(c['teachingAccess']['lowerLanding'])).difference(buildingsLower).difference(gaussClosed).difference(sidewalkGrade).difference(planterShape);lower=lowerShape.difference(unary_union([Polygon(st['ring']) for st in c['levelLink']['stairs'] if st.get('topLevel','zhili-ground')=='zhili-ground']))
# Exposed rims of the extension get a solid base (drop side) or retaining wall (uphill side) at runtime.
extensionRegions=[];extensionEdges=[]
if not extension.is_empty:
 ext=extension.difference(buildingsLower).intersection(lowerShape);closed=unary_union([lowerShape,buildingsLower.buffer(.35,join_style=2),podium.buffer(.35,join_style=2),planterShape.buffer(.35,join_style=2),Polygon(c['levelLink']['ring']),Polygon(c['teachingAccess']['lowerLanding']),*[Polygon(s['ring']) for s in c['levelLink']['stairs']]])
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
allStairs=unary_union([Polygon(st['ring']) for st in c['levelLink']['stairs']])
gaussCourt=gaussCourt.difference(allStairs).difference(planterShape)
gaussPodium=gauss1F.difference(gaussDeck).difference(zw(gplan['court1F']['ring'])).difference(buildings).difference(allStairs).difference(planterShape).difference(lower.buffer(.01))
court['gaussPodium']=[coords(a.exterior) for a in polygons(gaussPodium) if a.area>.5]
court.update(name=layout['name'],ring=newring,floors=2,floorHeight=layout['floorHeight'],floorRegions={'lower':regions(lower),'upper':regions(upper),'gaussCourt':regions(gaussCourt)},floorTriangles={'lower':triangles(lower),'upper':triangles(upper),'gaussCourt':triangles(gaussCourt)},footprints=triangles(lowerShape),pillars=[p for p in layout['pillars']if upper.contains(Point(p))and not podium.buffer(.5).contains(Point(p))],upperShape='L',huanyuWalkWidth=layout['upperPlan']['huanyuWalkWidth'],accessRampRing=coords(ramp.exterior),rampTargetFloor=1,exteriorAccess=True,interiorFillReverted=True,desc=layout['reference'],alignment={'origin':origin,'along':t,'outward':n,'innerCorner':at(inner_u,front_v),'storeEdge':[at(store_u,uv(rawring[5])[1]),at(store_u,front_v)],'huanyuCornerEdge':[at(corner_u,corner_v),huanyu['ring'][14]],'frontLine':[at(inner_u,front_v),at(store_u,front_v)]},edgeRepairs={'regions':regions(shape.symmetric_difference(original))},zhiliExtension={'regions':extensionRegions,'edges':extensionEdges,'reference':layout.get('zhiliExtension',{}).get('reference','')})
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
subprocess.run([sys.executable,str(root/'scripts/build-campus-corridors.py')],check=True)
print('Built square S05-aligned L; reverted interior fill and restored lower access')
