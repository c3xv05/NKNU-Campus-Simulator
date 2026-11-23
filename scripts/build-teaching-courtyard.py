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
gauss1F=zw(gplan['outlines']['1']);gaussDeck=zw(gplan['deck2F']['ring']).difference(buildings if not (root/'buildings/gauss/interior.json').exists() else unary_union([zw(f['outline']) for f in json.loads((root/'buildings/gauss/interior.json').read_text())['floors'] if f['key'] in ('1','2')]).difference(zw(gplan['deck2F']['ring'])));gaussOld=Polygon(json.loads((root/'buildings/gauss/building.json').read_text())['geometry']['beforeDrawingFootprint']['ring'])
gaussClosed=unary_union([gauss1F,gaussOld]).difference(zw(gplan['deck2F']['ring'])).buffer(0)
# The built Gauss east wall (interior outline, x≈-0.9 in drawing metres) sits inside the drawing's 1F outline (x≈0.53):
# pave the strip between them as lower plaza so no terrain slot opens between Gauss and the plaza (user 2026-11-19).
gaussEast=Polygon()
if (root/'buildings/gauss/interior.json').exists():
 _gi=json.loads((root/'buildings/gauss/interior.json').read_text())
 _zi=json.loads((root/'buildings/zhili/interior.json').read_text()) if (root/'buildings/zhili/interior.json').exists() else {'floors':[]}
 _zhili1F=unary_union([zw(f['outline']) for f in _zi['floors'] if f['label'] in ('B1','1F')])
 # Also the sliver between the Gauss 1F roof and Zhili's 1F west wall (open down to Zhili B1 otherwise).
 gaussEast=unary_union([zw([[-1.2,48.3],[1.7,48.3],[1.7,62.35],[-1.2,62.35]]),zw([[0.2,33.45],[1.35,33.45],[1.35,48.4],[0.2,48.4]])]).difference(unary_union([zw(f['outline']) for f in _gi['floors'] if f['key'] in ('1','2')])).difference(_zhili1F)
 gaussClosed=gaussClosed.difference(gaussEast)
zplan=json.loads((root/'buildings/zhili/plan.json').read_text())['site']
# Upper plaza (user 2026-11-18 "L型連接到上層廣場如你圖示那樣畫"): only the drawn pieces — Zhili 2F central plaza (+ podium roof),
# the 2F walkway, the 化學系廣場 and the Huanyu 2F deck; the earlier game-only L arm is replaced.
upper=unary_union([*[Polygon(r).buffer(0) for r in zsite['plaza']],zw(zplan['walkway2F']['ring']),zw(hplan['chemPlaza']['ring']),affinity.translate(zw(hplan['deck2F']['ring']),*hplan['deck2F'].get('gameOffset',[0,0]))]).buffer(.6,join_style=2).buffer(-.6,join_style=2)
upper=upper.difference(buildings).difference(gauss1F.buffer(.3,join_style=2)).difference(gaussOld)
# Huanyu's 2F through-passage (user 2026-11-13) must still land on the upper plaza: a passage-width link from its
# plaza end to the nearest drawn upper piece (user confirmed 2026-11-18).
# The drawn Huanyu 2F balcony strip along its east face (the long arm of the L) lies inside the game's Huanyu outline,
# so it is laid just outside that face with the existing Huanyu walk width, joining the 化學系廣場 / podium roof.
huanyuArm=shape.intersection(world_polygon(box(-1000,-1000,inner_u,1000))).difference(buildings).difference(gauss1F.buffer(.3,join_style=2)).difference(gaussOld)
upper=unary_union([upper,huanyuArm]).buffer(.3,join_style=2).buffer(-.3,join_style=2)
hpass=lookup[444867694].get('passage')
if hpass:
 from shapely.ops import nearest_points
 end=Point(hpass['line'][1]);q=nearest_points(upper,end)[0]
 if end.distance(q)>.05:upper=unary_union([upper,LineString([hpass['line'][1],(q.x,q.y)]).buffer(hpass['width']/2,cap_style=2,join_style=2)]).difference(buildings)
# User 2026-11-23: the 2F plaza's S06-side (west) edge is the near-right-angle polyline P1 (-164.59,-241.73) -> C (-159.46,-225.47) -> P2 (-167.05,-222.77)
# on Huanyu's wall; any upper floor protruding beyond it toward S06 is removed.
_C=(-159.46,-225.47);_P2=(-167.05,-222.77);_Q=(_P2[0]+(_P2[0]-_C[0])*3,_P2[1]+(_P2[1]-_C[1])*3)
upper=upper.difference(Polygon([(-173.5,-270),_C,_P2,_Q,(-260,_Q[1]),(-260,-270)]))
gaussCourt=unary_union([zw(gplan['court1F']['ring']),*[zw(q) for f in gplan.get('floors',[]) if f['key']=='1' for sp in f['spaces'] if sp['name']=='平台' for q in sp['polys']]]).buffer(.15,join_style=2).buffer(-.15,join_style=2)
def tiers(cfg,plan):
 out=[]
 for k,(y0,y1,top) in enumerate(cfg['rows']):
  t={'ring':[list(p) for p in list(zw([[cfg['x'][0],y0],[cfg['x'][1],y0],[cfg['x'][1],y1],[cfg['x'][0],y1]]).exterior.coords)[:-1]],'top':top,'source':plan}
  if cfg.get('aboveSidewalk'):t['above']=cfg['aboveSidewalk'][k]
  out.append(t)
 return out
court['planters']=tiers(zplan['planterTiers'],'zhili')+tiers(gplan['westPlanters'],'gauss')
planterShape=unary_union([Polygon(p['ring']) for p in court['planters']])
zhiliPlanters=unary_union([Polygon(p['ring']) for p in court['planters'] if p['source']=='zhili'])
if court.get('stairs'):
 stair=court['stairs'][0];stair['line']=layout['centralStair']['line'];stair['width']=layout['centralStair']['width'];a,b=stair['line'];dx=b[0]-a[0];dz=b[1]-a[1];length=math.hypot(dx,dz);nx=-dz/length*stair['width']/2;nz=dx/length*stair['width']/2;stair['ring']=[[a[0]+nx,a[1]+nz],[b[0]+nx,b[1]+nz],[b[0]-nx,b[1]-nz],[a[0]-nx,a[1]-nz]]
# Close the slit between Zhili's 1F west wall (lecture hall, roofed by the plaza) and the upper deck edge (user 2026-11-19).
if (root/'buildings/zhili/interior.json').exists():
 _zf={f['label']:zw(f['outline']) for f in json.loads((root/'buildings/zhili/interior.json').read_text())['floors']}
 upper=unary_union([upper,zw([[0.9,33.0],[1.7,33.0],[1.7,44.6],[0.9,44.6]]).intersection(_zf['1F']).difference(_zf.get('2F',Polygon()))])
for s in c['levelLink']['stairs']+court.get('stairs',[]):upper=upper.difference(Polygon(s['ring']))
# Revert the blanket fill; the corridor builder cuts the lower access along the existing path.
ramp=LineString(court['ramp']).buffer(court['width']/2,cap_style=2);extension=Polygon(legacy[444867693]).buffer(0) if 444867693 in legacy else Polygon()
# The former Zhili shell area beyond the drawing tower continues the lower plaza at Zhili 1F level.
# Zhili's upper floors overhang outdoor ±0 paving (drawing): for the lower plaza only Zhili's 1F footprint is building.
gaussInt=json.loads((root/'buildings/gauss/interior.json').read_text()) if (root/'buildings/gauss/interior.json').exists() else None
# Gauss's upper floors also overhang the 2F deck: with its interior, only its 1F/2F rooms are building for the lower plaza.
gaussRooms=unary_union([zw(gaussInt['floors'][0]['outline']).difference(zw(gplan['deck2F']['ring'])),zw(gaussInt['floors'][1]['outline'])]) if gaussInt else None
buildingsLower=unary_union([Polygon(a['ring']).buffer(.01,join_style=2) for a in c['places']+c['buildings'] if a.get('height') and a['osm']!=444867693 and not (gaussInt and a['osm']==444867692)]+[podium.buffer(.01,join_style=2)]+([gaussRooms.buffer(.01,join_style=2)] if gaussInt else []))
gauss1FRooms=zw(gaussInt['floors'][0]['outline']) if gaussInt else Polygon()
extension=extension.union(gaussEast).union(Polygon()).union(gaussDeck.difference(gauss1FRooms)).union(unary_union([zw(r) for r in zplan['paving1F']['rings']]).difference(gauss1F.difference(gaussDeck)))
sidewalkGrade=unary_union([Polygon(st['ring']) for st in c['levelLink']['stairs'] if st.get('topLevel','zhili-ground')=='zhili-ground']+[Polygon(c['teachingAccess'][k]) for k in ('frontApron','gapFootprint') if c['teachingAccess'].get(k)]).buffer(.02,join_style=2)
extension=extension.difference(sidewalkGrade)
# User 2026-11-23: the lower tile rectangle west of the Zhili west-wall line (through (-173.81,-244.22), straight toward Huanyu) is deleted;
# facilities/campus-plazas 'zhili-huanyu-lawn' makes that wedge a flat lawn at plaza height.
extension=extension.difference(Polygon([(-183.0,-270),(-158.0,-200),(-300,-200),(-300,-270)]))
# Zhili driveway ramp (user 2026-11-22): the lower plaza/extension is open over the ramp aisle (rims become the low perimeter wall).
import sys;sys.path.insert(0,str(root/'scripts'))
import zhili_curbcuts as zc
driveOpen=zc.shapes(root)[0]['open']
# User 2026-11-23: the 1F deck covers the ramp up to its south edge (y62.45); only the ramp south of it stays open (no notch in the platform).
driveOpen=driveOpen.difference(zw([[1.75,59.62],[7.07,59.62],[7.07,62.45],[1.75,62.45]]))
extension=extension.difference(driveOpen)
lowerShape=shape.union(extension).union(gaussDeck).union(Polygon(c['teachingAccess']['lowerLanding'])).difference(driveOpen).difference(buildingsLower).difference(gaussClosed).difference(sidewalkGrade).difference(planterShape);lowerShape=lowerShape.buffer(0);lower=lowerShape.difference(unary_union([Polygon(st['ring']) for st in c['levelLink']['stairs'] if st.get('topLevel','zhili-ground')=='zhili-ground']));lower=lower.buffer(0)
# Exposed rims of the extension get a solid base (drop side) or retaining wall (uphill side) at runtime.
extensionRegions=[];extensionEdges=[];extensionBase=[]
if not extension.is_empty:
 ext=extension.difference(buildingsLower).intersection(lowerShape);closed=unary_union([lowerShape,buildingsLower.buffer(.35,join_style=2),podium.buffer(.35,join_style=2),*([_zhili1F.buffer(.35,join_style=2)] if gaussInt else []),planterShape.buffer(.35,join_style=2),Polygon(c['levelLink']['ring']),Polygon(c['teachingAccess']['lowerLanding']),*[Polygon(s['ring']) for s in c['levelLink']['stairs']]])
 tunnel=zw([[1.75,53.0],[7.07,53.0],[7.07,59.62],[1.75,59.62]])
 # User 2026-11-23: the solid base fills the ground up to plaza level; where the B1 basement (walkable driveway etc.) is underneath it showed
 # up inside B1 as red walls you could walk through. Keep it out of the basement outline.
 _zi=json.loads((root/'buildings/zhili/interior.json').read_text());tunnel=unary_union([tunnel,zw(_zi['floors'][0]['outline'])])
 for piece in polygons(ext):
  if piece.area<1:continue
  extensionRegions.append(coords(piece.exterior))
  for bp in polygons(piece.difference(tunnel)):
   if bp.area>=.5:extensionBase.append([coords(bp.exterior)]+[coords(h) for h in bp.interiors])
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
# Each Gauss 1F door that opens toward the court gets a floor strip from its threshold to the court (drawn 平台 notch).
if gaussInt:
 for e in gaussInt['floors'][0]['exits']:
  (ax,az),(bx,bz)=e['line'];ox,oz=e['outside'];mx,mz=(ax+bx)/2,(az+bz)/2;l=math.hypot(ox-mx,oz-mz);ux,uz=(ox-mx)/l,(oz-mz)/l
  strip=Polygon([(ax,az),(bx,bz),(bx+ux*1.6,bz+uz*1.6),(ax+ux*1.6,az+uz*1.6)])
  if gaussCourt.distance(Point(ox,oz))<1.5:gaussCourt=unary_union([gaussCourt,strip]).buffer(0)
gaussCourt=gaussCourt.difference(allStairs).difference(planterShape)
# The 1F 花園 between room 103/104 and the court (user 2026-11-18): open garden at Gauss 1F level.
gaussGarden=unary_union([zw(q) for f in gplan.get('floors',[]) if f['key']=='1' for sp in f['spaces'] if sp['name']=='花園' for q in sp['polys']]).buffer(.7,join_style=2).difference(zw(gaussInt['floors'][0]['outline'])).difference(gaussCourt).difference(allStairs).difference(planterShape) if gaussInt else Polygon()
downStairs=unary_union([Polygon(st['ring']) for st in c['levelLink']['stairs'] if st.get('bottomLevel')=='gauss-ground'])
gaussPodium=gauss1F.difference(gaussDeck).difference(zw(gplan['court1F']['ring'])).difference(buildings).difference(allStairs).difference(planterShape).difference(lower.buffer(.01))
# With Gauss's walkable interior (buildings/gauss/interior.json) the 1F rooms are real; no stand-in solids.
if (root/'buildings/gauss/interior.json').exists():gaussPodium=Polygon()
court['gaussPodium']=[coords(a.exterior) for a in polygons(gaussPodium) if a.area>.5]
c['levelLink']['insideGauss']=bool((root/'buildings/gauss/interior.json').exists())
court.update(name=layout['name'],ring=newring,floors=2,floorHeight=layout['floorHeight'],floorRegions={'lower':regions(lower),'upper':regions(upper),'gaussCourt':regions(gaussCourt),'gaussGarden':regions(gaussGarden)},floorTriangles={'lower':triangles(lower),'upper':triangles(upper),'gaussCourt':triangles(gaussCourt),'gaussGarden':triangles(gaussGarden)},footprints=triangles(unary_union([lowerShape.difference(downStairs),gaussCourt,gaussGarden,planterShape])),pillars=[p for p in layout['pillars']if upper.contains(Point(p))and not podium.buffer(.5).contains(Point(p))],upperShape='L',huanyuWalkWidth=layout['upperPlan']['huanyuWalkWidth'],accessRampRing=coords(ramp.exterior),rampTargetFloor=1,exteriorAccess=True,interiorFillReverted=True,desc=layout['reference'],alignment={'origin':origin,'along':t,'outward':n,'innerCorner':at(inner_u,front_v),'storeEdge':[at(store_u,uv(rawring[5])[1]),at(store_u,front_v)],'huanyuCornerEdge':[at(corner_u,corner_v),huanyu['ring'][14]],'frontLine':[at(inner_u,front_v),at(store_u,front_v)]},edgeRepairs={'regions':regions(shape.symmetric_difference(original))},zhiliExtension={'regions':extensionRegions,'baseRegions':extensionBase,'edges':extensionEdges,'reference':layout.get('zhiliExtension',{}).get('reference','')})
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
subprocess.run([sys.executable,str(root/'scripts/build-campus-corridors.py')],check=True)
print('Built square S05-aligned L; reverted interior fill and restored lower access')
