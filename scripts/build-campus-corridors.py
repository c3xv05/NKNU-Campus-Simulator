"""S32 enters the lower plaza; Bio B's terminal defines the open upper T corridor."""
import json,math,subprocess
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles,set_precision
from biology_layout import derive_biology
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());source=json.loads((root/'facilities/campus-corridors/layout.json').read_text())
def coords(r):return [[round(x,7),round(z,7)]for x,z in list(r.coords)[:-1]]
def polygons(p):return [a for a in (list(p.geoms)if hasattr(p,'geoms')else[p])if a.geom_type=='Polygon' and a.area>1e-7]
def regions(p):return [[coords(a.exterior),*[coords(h)for h in a.interiors]]for a in polygons(p)]
def triangles(p):return [coords(t.exterior)for a in polygons(p)for t in constrained_delaunay_triangles(a).geoms if t.area>1e-7]
def from_regions(r):return unary_union([Polygon(a[0],a[1:])for a in r])
def ribbon(line,width):return LineString(line).buffer(width/2,cap_style=2,join_style=2)
def tessellate(p,step=.75,terrain_diagonal=False):
    result=[];w,n,e,s=p.bounds
    for i in range(math.floor(w/step),math.ceil(e/step)):
        for j in range(math.floor(n/step),math.ceil(s/step)):
            x,z=i*step,j*step
            cells=[Polygon([[x,z],[x+step,z],[x,z+step]]),Polygon([[x+step,z+step],[x,z+step],[x+step,z]])]if terrain_diagonal else[box(x,z,x+step,z+step)]
            for cell in cells:result.extend(triangles(p.intersection(cell)))
    return result
buildings=unary_union([Polygon(b['ring'])for b in c['places']+c['buildings']if b.get('height')])
js="""import fs from 'node:fs';import{createRoadNetwork}from'./roads.js';import{pavementIndex}from'./pavement.js';const c=JSON.parse(fs.readFileSync('data/campus.json')),n=createRoadNetwork(c.roads,()=>0,JSON.parse(fs.readFileSync('data/road-tags.json')),{apron:c.entranceApron,pavedAreas:c.pavedAreas,junctionFillets:c.junctionFillets}),entrance=new Set(c.roads.filter(r=>r.entrance).map(r=>r.osm));process.stdout.write(JSON.stringify(pavementIndex(n).all.filter(a=>!a.actual&&!entrance.has(a.osm)&&a.osm!=='entrance-apron').map(a=>a.points)));"""
motor=unary_union([set_precision(Polygon(p).buffer(0),.001)for p in json.loads(subprocess.check_output(['node','--input-type=module','-e',js],cwd=root))if Polygon(p).area>1e-7])
court=c['courtyard'];a=source['courtyardAccess'].copy()
if a.get('followRoad'):
    path=next(r for r in c['roads']if r['osm']==a['followRoad']);line=LineString(path['line']);end=line.project(Point(a['targetPoint']));nodes=[];distance=0
    for i,p in enumerate(path['line']):
        if i:distance+=math.dist(path['line'][i-1],p)
        if distance>=end:break
        nodes.append(p)
    nodes.append(list(line.interpolate(end).coords)[0]);path=LineString(nodes);obstacle=Polygon(next(b for b in c['places']if b['osm']==a['clearanceBuilding'])['ring']);safe=[]
    for j in range(math.ceil(path.length/.5)+1):
        p=list(path.interpolate(min(path.length,j*.5)).coords[0]);target=a['width']/2+a['buildingClearance']
        if obstacle.distance(Point(p))<target:
            lo,hi=0,6
            for _ in range(30):
                mid=(lo+hi)/2
                if obstacle.distance(Point(p[0]+mid,p[1]))<target:lo=mid
                else:hi=mid
            p[0]+=hi
        safe.append(p)
    a['sourceLine']=a['line'];a['line']=safe
elif a.get('cornerRadius'):

    line=a['line'];rounded=[line[0]]
    for p,q,r in zip(line,line[1:],line[2:]):
        cut=min(a['cornerRadius'],math.dist(p,q)*.3,math.dist(q,r)*.3);u=[q[i]+(p[i]-q[i])*cut/math.dist(p,q)for i in range(2)];v=[q[i]+(r[i]-q[i])*cut/math.dist(q,r)for i in range(2)]
        for j in range(11):
            t=j/10;rounded.append([(1-t)**2*u[i]+2*t*(1-t)*q[i]+t*t*v[i]for i in range(2)])
    rounded.append(line[-1]);a['sourceLine']=line;a['line']=rounded
shape=ribbon(a['line'],a['width']).difference(motor).difference(buildings)
# The complete restored access opening is covered by one continuous slope, down to 1F.
lower=from_regions(court['floorRegions']['lower']);end=Point(a['line'][-1]);cut=shape.difference(end.buffer(a['flatEnd'],resolution=8));lower=lower.difference(cut);shape=shape.difference(lower)
court['floorRegions']['lower']=regions(lower);court['floorTriangles']['lower']=triangles(lower);court['rampTargetFloor']=1
# Do not add any PR73 upper-level diagonal gallery or blanket interior soil flattening.
a.update(regions=regions(shape),triangles=tessellate(shape),footprints=triangles(shape))
# Seal the soil to the ramp with a continuous field, rather than leaving cut old path slivers.
blend=shape.buffer(a['groundBlend'],join_style=2).difference(shape).difference(motor).difference(buildings).difference(from_regions(court['floorRegions']['lower'])).difference(from_regions(court['floorRegions']['upper']))
a['groundBlendPlan']={'width':a['groundBlend'],'regions':regions(blend),'triangles':tessellate(blend,1,True),'footprints':triangles(blend)}
transitions=[a]
raw,apron=derive_biology(c,source);bio=c['bioConnection'];cfg=source['biology'];corridor=raw.difference(buildings);bio['corridor'].update(regions=regions(corridor),triangles=triangles(corridor));joint=bio['corridor']['joint'];east=bio['corridor']['east'];axis=bio['corridor']['axis'];road=next(r for r in c['roads']if r['osm']==cfg['accessRoad'])
# The stem follows S05's normal; its joint remains centred between the wings.
stemEast=source['biology'].get('southAlignment',{}).get('roadAxis')
stemEast=[stemEast[1],-stemEast[0]] if stemEast else east
ray=LineString([[joint[i]-stemEast[i]*100 for i in range(2)],joint]);hit=ray.intersection(LineString(road['line']));start=list(hit.coords)[0];length=math.dist(start,joint);normal=[-stemEast[1],stemEast[0]]
a={'id':'biology-s05','road':cfg['accessRoad'],'line':[start,joint],'width':cfg['accessWidth'],'sidewalkEntry':True,'entryRun':cfg['entryRun'],'entryFlare':cfg['entryFlare'],'targetFloor':2,'linearGrade':True,'entryStations':[]}
def at(along,across):return [start[i]+stemEast[i]*along+normal[i]*across for i in range(2)]
for j in range(round((a['width']+2*a['entryFlare'])/.5)+1):
    across=-(a['width']/2+a['entryFlare'])+j*.5;segment=LineString([at(0,across),at(length,across)]);hit=segment.intersection(motor);parts=[p for p in (list(hit.geoms)if hasattr(hit,'geoms')else[hit])if p.geom_type=='LineString'];point=max((list(p.coords)[-1]for p in parts),key=lambda p:segment.project(Point(p)));a['entryStations'].append({'across':across,'along':segment.project(Point(point)),'point':list(point)})
flare_end=max(s['along']for s in a['entryStations'])+a['entryRun'];flare=Polygon([at(0,-a['width']/2-a['entryFlare']),at(flare_end,-a['width']/2-a['entryFlare']),at(flare_end,a['width']/2+a['entryFlare']),at(0,a['width']/2+a['entryFlare'])]);shape=ribbon(a['line'],a['width']).union(flare).difference(buildings).difference(motor).difference(corridor)
entries=[]
for offset in [-a['width']/2,0,a['width']/2]:
    segment=LineString([at(0,offset),at(length,offset)]);hit=segment.intersection(corridor)
    for part in (list(hit.geoms)if hasattr(hit,'geoms')else[hit]):
        if part.geom_type=='LineString' and part.length>1e-5:entries.append(segment.project(Point(part.coords[0])))
a['flatEnd']=length-min(entries)+cfg['flatEnd'];a.update(regions=regions(shape),triangles=tessellate(shape,.2),footprints=triangles(shape));transitions.append(a);bio['ramp']=a['line'];bio['accessWidth']=a['width']
# Flat ground apron outside the strictly rectangular staircase, meeting the skew S01 edge.
shape=apron.difference(motor).difference(buildings).difference(Polygon(bio['stairs']['ring']));bottom=bio['stairs']['line'][1];reach=max(math.dist(bottom,p)for p in apron.exterior.coords)
a={'id':'biology-s01-apron','kind':'road-apron','road':cfg['stairs']['road'],'line':[bottom,[bottom[i]+east[i]*reach for i in range(2)]],'width':bio['stairs']['width'],'regions':regions(shape),'triangles':tessellate(shape),'footprints':triangles(shape)};transitions.append(a)
# Retain earth at 1F while leaving the east stair opening and both wing ends clear.
bio['corridor']['retainingEdges']=[];centerline=LineString(bio['line']);staircut=Polygon(bio['stairs']['ring']).buffer(.05)
if cfg['lowerRetainingWalls']:
 for region in bio['corridor']['regions']:
  for ring in region:
   for p,q in zip(ring,ring[1:]+ring[:1]):
    parts=LineString([p,q]).difference(staircut)
    for part in (list(parts.geoms)if hasattr(parts,'geoms')else[parts]):
     if part.geom_type!='LineString' or part.length<1:continue
     mid=part.interpolate(.5,normalized=True);u=centerline.project(mid)/centerline.length
     if not .1<u<.9 or buildings.distance(mid)<.05:continue
     center=centerline.interpolate(centerline.project(mid));vx=center.x-mid.x;vz=center.y-mid.y;l=math.hypot(vx,vz);offset=[vx/l*.03,vz/l*.03]if l else[0,0]
     bio['corridor']['retainingEdges'].append([[round(v[i]+offset[i],7)for i in range(2)]for v in [part.coords[0],part.coords[-1]]])
c['campusTransitions']=transitions;(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built lower S32 access; Bio B-width open T, 12m centred stem and rectangular lower stairs',round(bio['width'],3),bio['stairs']['width'])
