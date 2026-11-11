"""Convex building cutouts for widened sidewalks, including concave footprints."""
import json
from pathlib import Path
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());c['walkObstacles']=[]
for a in c['places']+c['buildings']:
 if not a.get('height'):continue
 p=Polygon(a['ring'],a.get('holes',[])).buffer(.015,join_style=2)
 for t in constrained_delaunay_triangles(p).geoms:c['walkObstacles'].append({'ring':[[round(x,6),round(z,6)] for x,z in list(t.exterior.coords)[:-1]]})
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built',len(c['walkObstacles']),'convex building cutouts')
