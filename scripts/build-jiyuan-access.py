import json,math
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely import constrained_delaunay_triangles
root=Path(__file__).resolve().parents[1];cfg=json.loads((root/'facilities/jiyuan-access/layout.json').read_text());c=json.loads((root/'data/campus.json').read_text());a=cfg['grassParking'];shape=Polygon(a['ring']);a['triangles']=[]
for x in range(math.floor(shape.bounds[0]),math.ceil(shape.bounds[2])):
 for z in range(math.floor(shape.bounds[1]),math.ceil(shape.bounds[3])):a['triangles'] += [[list(p)for p in list(t.exterior.coords)[:-1]]for t in constrained_delaunay_triangles(shape.intersection(box(x,z,x+1,z+1))).geoms if t.area>1e-8]
c['grassParking']=a;(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
