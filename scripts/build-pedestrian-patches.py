"""Clip pedestrian plazas and connections before the shared sidewalk union."""
import json
from pathlib import Path
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from road_shapes import motor_shape
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text())
levels=unary_union([Polygon(a['ring']) for a in c.get('levelAreas',[])])
shapes=[Polygon(a['ring']) for a in c.get('pedestrianAreas',[])+c.get('pedestrianLinks',[])]
for r in c['roads']:
 if r['width']<=2.5:shapes.append(LineString(r['line']).buffer(r['width']/2,cap_style=1,join_style=1).intersection(levels))
shape=unary_union(shapes).difference(motor_shape(fillets=True)).difference(unary_union([Polygon(a['ring']).buffer(.015,join_style=2) for a in c['places']+c['buildings'] if a.get('height')]))
c['pedestrianPatches']=[{'id':'campus-pedestrian-plazas','ring':[[round(x,7),round(z,7)] for x,z in list(t.exterior.coords)[:-1]]} for t in constrained_delaunay_triangles(shape).geoms if t.area>1e-7]
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built',len(c['pedestrianPatches']),'non-overlapping pedestrian patches;',round(shape.area,1),'m²')
