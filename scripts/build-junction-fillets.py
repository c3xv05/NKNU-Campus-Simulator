"""Round inside junction corners without moving shared junction nodes."""
import json
from road_shapes import motor_shape
from pathlib import Path
from collections import Counter
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text())
roads=[r for r in c['roads'] if r['width']>2.5 and not r.get('entrance')]
counts=Counter(tuple(p) for r in roads for p in r['line'])
junctions=[Point(p).buffer(14,quad_segs=16) for p,n in counts.items() if n>1]
pavement=motor_shape()
landmarks=unary_union([Polygon(a['ring']).buffer(.2) for a in c['places']+c['buildings'] if a.get('height')])
patch=pavement.buffer(5,quad_segs=16).buffer(-5,quad_segs=16).difference(pavement).intersection(unary_union(junctions)).difference(landmarks).difference(Polygon(c['entranceApron']['ring']).buffer(1))
polygons=list(patch.geoms) if hasattr(patch,'geoms') else [patch]
c['junctionFillets']=[{'id':f'junction-fillet-{i}', 'ring':[[round(x,6),round(z,6)] for x,z in list(p.exterior.coords)[:-1]], 'triangles':[[[round(x,6),round(z,6)] for x,z in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(p).geoms if t.area>0.00001]} for i,p in enumerate(polygons) if p.geom_type=='Polygon' and p.area>.04 and not p.interiors]
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
print('Built',len(c['junctionFillets']),'round junction patches; radii are model estimates')
