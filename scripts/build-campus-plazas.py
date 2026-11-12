"""Synchronize shared quarters and gently curved pedestrian connections."""
import json,math
from pathlib import Path
from shapely.geometry import LineString
root=Path(__file__).resolve().parents[1];layout=json.loads((root/'facilities/campus-plazas/layout.json').read_text());c=json.loads((root/'data/campus.json').read_text())
def rounded_line(line,radius):
 if not radius or len(line)<3:return line
 result=[line[0]]
 for a,b,d in zip(line,line[1:],line[2:]):
  before=math.dist(a,b);after=math.dist(b,d);cut=min(radius,before*.3,after*.3)
  start=[b[k]+(a[k]-b[k])*cut/before for k in range(2)];end=[b[k]+(d[k]-b[k])*cut/after for k in range(2)];count=max(4,math.ceil(cut*2/.35))
  for i in range(count+1):
   t=i/count;result.append([round((1-t)**2*start[k]+2*(1-t)*t*b[k]+t*t*end[k],6) for k in range(2)])
 result.append(line[-1]);return result
for link in layout['pedestrianLinks']:
 original=link.get('sourceLine',link['line']);link['line']=rounded_line(original,link.get('cornerRadius',0))
 if link.get('cornerRadius'):link['sourceLine']=original
 shape=LineString(link['line']).buffer(link['width']/2,cap_style=1 if link.get('endCap')=='round' else 2,join_style=1,quad_segs=8)
 link['ring']=[[round(x,6),round(z,6)] for x,z in list(shape.exterior.coords)[:-1]]
for key in ['levelAreas','pedestrianAreas','pedestrianLinks']:c[key]=layout[key]
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
(root/'data/site-layout.js').write_text('// Shared flat campus quarters and pedestrian additions; source: facilities/campus-plazas/layout.json.\nexport const campusSiteLayout='+json.dumps(layout,ensure_ascii=False,separators=(',',':'))+';\n')
print('Built',len(layout['levelAreas']),'shared level areas and',len(layout['pedestrianLinks']),'pedestrian connections')
