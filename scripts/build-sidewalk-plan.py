"""Union walkways before meshing, so intersecting strips cannot overlap or crack."""
import json,subprocess,math
from pathlib import Path
from sidewalk_finishing import finish_sidewalks
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles,set_precision
root=Path(__file__).resolve().parents[1]
js="""import fs from 'node:fs';import{createRoadNetwork}from'./roads.js';import{sidewalkSections}from'./site-physics.js';const c=JSON.parse(fs.readFileSync('data/campus.json')),n=createRoadNetwork(c.roads,()=>0,JSON.parse(fs.readFileSync('data/road-tags.json')),{apron:c.entranceApron,pavedAreas:c.pavedAreas,junctionFillets:c.junctionFillets});process.stdout.write(JSON.stringify(sidewalkSections(c,n).map(s=>s.points)));"""
polygons=json.loads(subprocess.check_output(['node','--input-type=module','-e',js],cwd=root))
shape=unary_union([set_precision(Polygon(p),.001) for p in polygons if Polygon(p).area>1e-7]).buffer(0)
# Stairs have their own stepped surface and support heights, never overlapping tiles.
c=json.loads((root/'data/campus.json').read_text())
for s in [c['bioConnection']['stairs']]+c['levelLink'].get('stairs',[])+c['courtyard'].get('stairs',[]):shape=shape.difference(Polygon(s['ring']))
shape=finish_sidewalks(shape,c)
# Drawing-placed shells (Gauss 2026-11-18) can sit inside the former facade line: pave the strip between the
# new S05 facade (edge 0) and the existing walkway so the paving still meets the wall.
from shapely.geometry import LineString
from sidewalk_finishing import motor_shape
for b in c['places']+c['buildings']:
 meta=json.loads((root/'buildings/gauss/building.json').read_text())['geometry'] if b.get('osm')==444867692 else None
 if not meta or 'drawingFootprint' not in meta:continue
 r=b['ring'];strip=LineString([r[0],r[1]]).buffer(-3.0,single_sided=True,cap_style=2)
 others=unary_union([Polygon(a['ring']).buffer(.015,join_style=2) for a in c['places']+c['buildings'] if a.get('height')])
 fill=strip.difference(motor_shape(fillets=True)).difference(others)
 for st in [c['bioConnection']['stairs']]+c['levelLink'].get('stairs',[]):fill=fill.difference(Polygon(st['ring']))
 shape=unary_union([shape,fill]).buffer(0)
if c.get('huanyuAccess'):
 for a in [c['huanyuAccess'],c['huanyuAccess']['ramp']]:shape=shape.difference(Polygon(a['ring']))
for region in [r for a in c.get('campusTransitions',[]) for r in a['regions']]+c['bioConnection'].get('corridor',{}).get('regions',[]):shape=shape.difference(Polygon(region[0],region[1:]))
if c['courtyard'].get('floorRegions'):
 for region in c['courtyard']['floorRegions']['lower']+c['courtyard']['floorRegions']['upper']:shape=shape.difference(Polygon(region[0],region[1:]))
if c.get('courtParking',{}).get('entrance'):shape=shape.difference(Polygon(c['courtParking']['entrance']['ring']))
parts=list(shape.geoms) if hasattr(shape,'geoms') else [shape]
shape=unary_union([Polygon(p.exterior,[h for h in p.interiors if Polygon(h).area>=.01]) for p in parts if p.geom_type=='Polygon'])
# Remove micrometre clipping slivers; retain curb outlines to within a millimetre.
shape=shape.simplify(.0005,preserve_topology=True)
# Compact teaching stairs retain exact shared edges after outline simplification.
if c.get('teachingAccess'):
 for s in c['levelLink']['stairs']:shape=shape.difference(Polygon(s['ring']))
# Preserve the exact access boundary after hole cleanup / outline simplification.
for region in [r for a in c.get('campusTransitions',[])for r in a['regions']]+c['bioConnection'].get('corridor',{}).get('regions',[]):shape=shape.difference(Polygon(region[0],region[1:]))
if c.get('courtParking',{}).get('entrance'):shape=shape.difference(Polygon(c['courtParking']['entrance']['ring']))
# Zhili driveway ramp and curb-cut pads (user 2026-11-22): the ramp is asphalt, the pads are tile at road level; both leave the
# raised sidewalk. The sidewalk surface draws curbs along these cut edges.
import sys;sys.path.insert(0,str(root/'scripts'))
import zhili_curbcuts as zc
cc,_,_=zc.shapes(root);curbCuts=[]
for name,pad in cc['pads'].items():
 part=shape.intersection(pad).buffer(0)
 for q in (list(part.geoms) if hasattr(part,'geoms') else [part]):
  if q.area<.05:continue
  curbCuts.append(dict(id=name,ring=[[round(x,7),round(z,7)] for x,z in list(q.exterior.coords)[:-1]],triangles=[[[round(x,7),round(z,7)] for x,z in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(q).geoms if t.area>1e-7]))
shape=shape.difference(unary_union([*cc['pads'].values(),*cc['ramps'].values()])).buffer(0)
regions=[p for p in (list(shape.geoms) if hasattr(shape,'geoms') else [shape]) if p.area>=.002]
shape=unary_union(regions)
step=1.25;triangles=[];rings=[]
def coords(r):return [[round(x,7),round(z,7)] for x,z in list(r.coords)[:-1]]
for p in regions:
 if p.area<.002:continue
 rings.append([coords(p.exterior)]+[coords(h) for h in p.interiors])
 w,n,e,s=p.bounds
 for row in range(math.floor(n/step),math.ceil(s/step)):
  for col in range(math.floor(w/step),math.ceil(e/step)):
   w0,n0=col*step,row*step;e0,s0=w0+step,n0+step
   for grid in [Polygon([[w0,n0],[e0,n0],[w0,s0]]),Polygon([[e0,s0],[w0,s0],[e0,n0]])]:
    part=p.intersection(grid)
    if part.is_empty:continue
    for t in constrained_delaunay_triangles(part).geoms:
     if t.area>1e-7:triangles.append(coords(t.exterior))
footprints=[coords(t.exterior) for t in constrained_delaunay_triangles(shape).geoms if t.area>1e-7]
data=dict(step=step,regions=rings,triangles=triangles,footprints=footprints,area=round(shape.area,4),curbCuts=curbCuts)
(root/'data/sidewalk-plan.js').write_text('// Generated by scripts/build-sidewalk-plan.py. Unioned, non-overlapping walkway surface.\nexport const sidewalkPlan='+json.dumps(data,separators=(',',':'))+';\n')
print('Built',len(rings),'walkway regions and',len(triangles),'triangles;',round(shape.area,2),'m²')
