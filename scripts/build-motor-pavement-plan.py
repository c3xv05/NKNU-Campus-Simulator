"""Use the same convex road envelope that clips the walkways as the rendered asphalt."""
import json,subprocess,math
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.prepared import prep
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles,set_precision
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text())
js="""import fs from 'node:fs';import{createRoadNetwork}from'./roads.js';import{pavementIndex}from'./pavement.js';const c=JSON.parse(fs.readFileSync('data/campus.json')),n=createRoadNetwork(c.roads,()=>0,JSON.parse(fs.readFileSync('data/road-tags.json')),{apron:c.entranceApron,pavedAreas:c.pavedAreas,junctionFillets:c.junctionFillets}),entrance=new Set(c.roads.filter(r=>r.entrance).map(r=>r.osm));process.stdout.write(JSON.stringify(pavementIndex(n).all.filter(a=>!a.actual&&!entrance.has(a.osm)&&a.osm!=='entrance-apron').map(a=>a.points)));"""
polygons=json.loads(subprocess.check_output(['node','--input-type=module','-e',js],cwd=root));shape=unary_union([set_precision(Polygon(p).buffer(0),.001) for p in polygons if Polygon(p).area>1e-7]).buffer(0)
shape=shape.difference(Polygon(c['entranceApron']['ring'],c['entranceApron']['holes']))
for a in c['places']+c['buildings']:
 if a.get('height'):shape=shape.difference(Polygon(a['ring'],a.get('holes',[])).buffer(.015,join_style=2))
walk_text=(root/'data/sidewalk-plan.js').read_text();walk=json.loads(walk_text.split('=',1)[1].rstrip(';\n'));walk_shape=unary_union([Polygon(r[0],r[1:]) for r in walk['regions']]);original=shape
# Close only the narrow gaps beside a real kerb; the walkway remains unchanged.
apron=Polygon(c['entranceApron']['ring'],c['entranceApron']['holes']);kerb_source=shape.union(apron)
near_kerb=kerb_source.buffer(.4,quad_segs=16).intersection(walk_shape.boundary.buffer(.41,quad_segs=16)).difference(apron);shape=shape.union(near_kerb).difference(walk_shape).difference(Polygon(c['flowerbed']['ring']))
for a in c['places']+c['buildings']:
 if a.get('height'):shape=shape.difference(Polygon(a['ring'],a.get('holes',[])).buffer(.015,join_style=2))
infill=shape.difference(original);infill_triangles=[[[round(x,7),round(z,7)] for x,z in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(infill).geoms if t.area>.0000001]
regions=list(shape.geoms) if hasattr(shape,'geoms') else [shape];step=1.25;points=[];indices=[];lookup={};rings=[]
def coords(r):return [[round(x,7),round(z,7)] for x,z in list(r.coords)[:-1]]
def vertex(p):
 k=tuple(p)
 if k not in lookup:lookup[k]=len(points);points.append(p)
 return lookup[k]
for p in regions:
 if p.area<.00000001:continue
 rings.append([coords(p.exterior)]+[coords(h) for h in p.interiors if Polygon(h).area>.000001]);w,n,e,s=p.bounds;prepared=prep(p);tile=20
 for row0 in range(math.floor(n/tile),math.ceil(s/tile)):
  for col0 in range(math.floor(w/tile),math.ceil(e/tile)):
   bounds=box(col0*tile,row0*tile,(col0+1)*tile,(row0+1)*tile)
   if not prepared.intersects(bounds):continue
   local=p.intersection(bounds);local_prepared=prep(local)
   for row in range(row0*16,(row0+1)*16):
    for col in range(col0*16,(col0+1)*16):
     x,z=col*step,row*step
     if not local_prepared.intersects(box(x,z,x+step,z+step)):continue
     for grid in [Polygon([[x,z],[x+step,z],[x,z+step]]),Polygon([[x+step,z+step],[x,z+step],[x+step,z]])]:
      part=local.intersection(grid)
      if part.is_empty:continue
      for t in constrained_delaunay_triangles(part).geoms:
       if t.area>1e-7:indices.extend(vertex(v) for v in coords(t.exterior))
data=dict(step=step,regions=rings,points=points,indices=indices,infillTriangles=infill_triangles,area=round(shape.area,4));(root/'data/motor-pavement-plan.js').write_text('// Generated shared asphalt boundary and grade-grid mesh.\nexport const motorPavementPlan='+json.dumps(data,separators=(',',':'))+';\n');print('Built',len(indices)//3,'shared asphalt triangles and',len(points),'unique points')

# Match the graded Yongxu terrain hole to the exact asphalt union, not the older envelope.
if c.get('yongxuAccess'):
 local=shape.intersection(box(-225,-96,-120,-25));c['yongxuAccess']['groundClipRing']=[[-225,-96],[-120,-96],[-120,-25],[-225,-25]]
 c['yongxuAccess']['groundFootprints']=[coords(t.exterior) for t in constrained_delaunay_triangles(local).geoms if t.area>1e-7]
 (root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
