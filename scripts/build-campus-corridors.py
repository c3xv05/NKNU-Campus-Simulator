"""Shared, non-overlapping footprints for the S32 approach and two-floor bio T corridor."""
import json, math, subprocess
from pathlib import Path
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles, set_precision
root=Path(__file__).resolve().parents[1]
c=json.loads((root/'data/campus.json').read_text());source=json.loads((root/'facilities/campus-corridors/layout.json').read_text())
def coords(r):return [[round(x,7),round(z,7)] for x,z in list(r.coords)[:-1]]
def polygons(p):return [a for a in (list(p.geoms) if hasattr(p,'geoms') else [p]) if a.geom_type=='Polygon' and a.area>1e-7]
def regions(p):return [[coords(a.exterior),*[coords(h) for h in a.interiors]] for a in polygons(p)]
def triangles(p):return [coords(t.exterior) for a in polygons(p) for t in constrained_delaunay_triangles(a).geoms if t.area>1e-7]
def from_regions(r):return unary_union([Polygon(a[0],a[1:]) for a in r])
def ribbon(line,width):return LineString(line).buffer(width/2,cap_style=2,join_style=2)
def tessellate(p,step=.75):
    result=[];w,n,e,s=p.bounds
    for i in range(math.floor(w/step),math.ceil(e/step)):
        for j in range(math.floor(n/step),math.ceil(s/step)):
            result.extend(triangles(p.intersection(box(i*step,j*step,(i+1)*step,(j+1)*step))))
    return result
buildings=unary_union([Polygon(b['ring']) for b in c['places']+c['buildings'] if b.get('height')])
court=c['courtyard'];lower=from_regions(court['floorRegions']['lower']);upper=from_regions(court['floorRegions']['upper'])
# Close centimetre shell buffers along the floor boundary without filling stairwells.
for floor,shape in [('lower',lower),('upper',upper)]:
    shape=shape.buffer(.012,join_style=2).buffer(-.012,join_style=2).difference(buildings)
    for stair in c['levelLink']['stairs']+court['stairs']:shape=shape.difference(Polygon(stair['ring']))
    if floor=='lower':lower=shape
    else:upper=shape
# A horizontal gallery keeps every slope outside the plaza. It meets the original L walkway.
gallery=ribbon(**source['courtyardGallery']).difference(buildings)
upper=upper.union(gallery.intersection(lower)).union(ribbon(source['courtyardAccess']['line'],source['courtyardAccess']['width']).intersection(lower))
for floor,shape in [('lower',lower),('upper',upper)]:
    court['floorRegions'][floor]=regions(shape);court['floorTriangles'][floor]=triangles(shape)
court['exteriorAccess']=True
# Leave actual carriageways untouched. The S32 ramp starts flush at their southern edge.
js="""import fs from 'node:fs';import{createRoadNetwork}from'./roads.js';import{pavementIndex}from'./pavement.js';const c=JSON.parse(fs.readFileSync('data/campus.json')),n=createRoadNetwork(c.roads,()=>0,JSON.parse(fs.readFileSync('data/road-tags.json')),{apron:c.entranceApron,pavedAreas:c.pavedAreas,junctionFillets:c.junctionFillets}),entrance=new Set(c.roads.filter(r=>r.entrance).map(r=>r.osm));process.stdout.write(JSON.stringify(pavementIndex(n).all.filter(a=>!a.actual&&!entrance.has(a.osm)&&a.osm!=='entrance-apron').map(a=>a.points)));"""
motor=unary_union([set_precision(Polygon(p).buffer(0),.001) for p in json.loads(subprocess.check_output(['node','--input-type=module','-e',js],cwd=root)) if Polygon(p).area>1e-7])
a=source['courtyardAccess'].copy();shape=ribbon(a['line'],a['width']).difference(motor).difference(buildings).difference(lower)
a.update(regions=regions(shape),triangles=tessellate(shape),footprints=triangles(shape));transitions=[a]
bio=c['bioConnection'];b=source['biology'];bio['corridor']={k:b[k] for k in ['line','width','floors','floorHeight','slab','clearance','lowerRetainingWalls']}
shape=ribbon(b['line'],b['width']).difference(buildings).difference(Polygon(bio['stairs']['ring']))
bio['corridor'].update(regions=regions(shape),triangles=triangles(shape))
road=next(r for r in c['roads'] if r['osm']==b['accessRoad']);joint=b['accessJoint'];line=LineString(road['line']);along=line.project(__import__('shapely').geometry.Point(joint));p=line.interpolate(along);dx=joint[0]-p.x;dz=joint[1]-p.y;length=math.hypot(dx,dz);distance=road['width']/2
start=[p.x+dx/length*distance,p.y+dz/length*distance]
a={'id':'biology-s05','road':b['accessRoad'],'line':[start,joint],'width':b['accessWidth'],'flatEnd':b['flatEnd'],'roadInset':0,'sidewalkEntry':True,'entryRun':b['entryRun'],'entryFlare':b['entryFlare']}
center=LineString(a['line']);nx=-dz/length;nz=dx/length;ux=dx/length;uz=dz/length
at=lambda along,across:[start[0]+ux*along+nx*across,start[1]+uz*along+nz*across]
flare=Polygon([at(0,-a['width']/2-a['entryFlare']),at(a['entryRun'],-a['width']/2-a['entryFlare']),at(a['entryRun'],a['width']/2+a['entryFlare']),at(0,a['width']/2+a['entryFlare'])])
raw=ribbon(a['line'],a['width']).union(flare).difference(buildings).difference(motor)
corridor=from_regions(bio['corridor']['regions']);shape=raw.difference(corridor)
# End the slope before the earliest full-width intersection with the level deck.
entries=[]
for offset in [-a['width']/2,0,a['width']/2]:
    segment=LineString([at(0,offset),at(center.length,offset)])
    hit=segment.intersection(corridor)
    for part in (list(hit.geoms) if hasattr(hit,'geoms') else [hit]):
        if part.geom_type=='LineString' and part.length>1e-5:entries.append(segment.project(Point(part.coords[0])))
a['flatEnd']=center.length-min(entries)+b['flatEnd']
a.update(regions=regions(shape),triangles=tessellate(shape,.35),footprints=triangles(shape));transitions.append(a)
bio['ramp']=[start,joint];bio['accessWidth']=b['accessWidth']
axis=LineString(b['line']);bio['corridor']['retainingEdges']=[]
for region in bio['corridor']['regions']:
 for ring in region:
  for p,q in zip(ring,ring[1:]+ring[:1]):
   mid=Point((p[0]+q[0])/2,(p[1]+q[1])/2);u=axis.project(mid)/axis.length
   if .14<u<.86 and math.dist(p,q)>1 and buildings.distance(mid)>.05:
    center=axis.interpolate(axis.project(mid));vx=center.x-mid.x;vz=center.y-mid.y;l=math.hypot(vx,vz)
    # Keep the interior face clear of the adjacent ramp/stair foundation face.
    offset=[vx/l*.03,vz/l*.03] if l else [0,0]
    bio['corridor']['retainingEdges'].append([[round(a[i]+offset[i],7)for i in range(2)]for a in [p,q]])
c['campusTransitions']=transitions
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
print('Built S32 / S05 approaches, level gallery and open 1F/2F bio corridor')
