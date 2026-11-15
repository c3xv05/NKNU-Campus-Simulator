"""Enlarge only the S05/S06 inside turn; preserve all centre lines and grade inputs."""
import json,math
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from road_shapes import motor_shape
root=Path(__file__).resolve().parents[1];cfg=json.loads((root/'facilities/s05-s06-junction/layout.json').read_text());c=json.loads((root/'data/campus.json').read_text());j=cfg['junction'];roads=[next(r for r in c['roads']if r['osm']==id)for id in cfg['roads']];arms=[]
for r in roads:
 line=r['line']if r['line'][0]==j else list(reversed(r['line']));p=next(p for p in line if math.dist(p,j)>8);d=math.dist(p,j);arms.append([j[i]+(p[i]-j[i])*cfg['extent']/d for i in range(2)])
sector=Polygon([j,*arms]);base=motor_shape();buildings=unary_union([Polygon(a['ring']).buffer(.25)for a in c['places']+c['buildings']if a.get('height')]);patch=base.buffer(cfg['radius'],quad_segs=32).buffer(-cfg['radius'],quad_segs=32).difference(base).intersection(sector).difference(buildings);parts=list(patch.geoms)if hasattr(patch,'geoms')else[patch]
coords=lambda ring:[[round(x,7),round(z,7)]for x,z in list(ring.coords)[:-1]]
c['junctionFillets']=[a for a in c['junctionFillets']if not a['id'].startswith('s05-s06-wide-')and not sector.contains(Polygon(a['ring']).representative_point())]
for i,p in enumerate(parts):
 if p.area<.01:continue
 c['junctionFillets'].append({'id':f's05-s06-wide-{i}','ring':coords(p.exterior),'triangles':[coords(t.exterior)for t in constrained_delaunay_triangles(p).geoms if t.area>1e-8]})
full=unary_union([base,*[Polygon(a['ring'])for a in c['junctionFillets']]]);walk=patch.buffer(cfg['sidewalkWidth'],quad_segs=32).difference(full).difference(buildings);parts=list(walk.geoms)if hasattr(walk,'geoms')else[walk];layout=json.loads((root/'facilities/campus-plazas/layout.json').read_text());layout['pedestrianAreas']=[a for a in layout['pedestrianAreas']if not a['id'].startswith('s05-s06-turn-walk-')]
for i,p in enumerate(parts):
 if p.area>.02:layout['pedestrianAreas'].append({'id':f's05-s06-turn-walk-{i}','name':'S05接S06加大圓弧白磚','ring':coords(p.exterior),'reference':cfg['reference']})
c['s05S06Turn']=cfg;(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');(root/'facilities/campus-plazas/layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n');print('Wide S05/S06 turn:',round(patch.area,2),'m² asphalt;',round(walk.area,2),'m² following sidewalk')
