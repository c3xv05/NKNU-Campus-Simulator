"""Cut only a pass-through storey, keeping the building below and above solid."""
import json
from pathlib import Path
from shapely.geometry import Polygon,LineString
from shapely import constrained_delaunay_triangles
root=Path(__file__).resolve().parents[1]
for path in (root/'buildings').glob('*/building.json'):
 d=json.loads(path.read_text());a=d['geometry'];p=a.get('passage')
 if not p:continue
 shell=Polygon(a['ring']);cut=LineString(p['line']).buffer(p['width']/2,cap_style=2);opening=shell.intersection(cut);rest=shell.difference(cut)
 def coords(r):return [[round(x,7),round(z,7)]for x,z in list(r.coords)[:-1]]
 p['ring']=coords(opening.exterior);p['shellRegions']=[[coords(q.exterior),*[coords(h)for h in q.interiors]]for q in (list(rest.geoms)if hasattr(rest,'geoms')else[rest])]
 p['floorTriangles']=[coords(t.exterior)for t in constrained_delaunay_triangles(opening).geoms if t.area>1e-7]
 path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print('Built passage:',path.parent.name)
