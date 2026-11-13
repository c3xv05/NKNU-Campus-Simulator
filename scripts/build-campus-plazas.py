"""Synchronize shared quarters and gently curved pedestrian connections."""
import json,math
from pathlib import Path
from shapely.geometry import LineString,Polygon
from shapely import constrained_delaunay_triangles
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
c['yongxuAccess']=json.loads((root/'facilities/yongxu-access/layout.json').read_text());layout['yongxuAccess']=c['yongxuAccess']
road=next(r for r in c['roads'] if r['osm']==c['yongxuAccess']['road']);road.setdefault('beforeEntryExtension',road['line']);road['line']=road['beforeEntryExtension']+rounded_line(c['yongxuAccess'].get('approachExtension',[c['yongxuAccess']['roadEnd']]),5);road['entryExtensionReference']='facilities/yongxu-access/layout.json'
photo=json.loads((root/'facilities/yongxu-access/satellite-sketch.json').read_text());c['pavedAreas']=[a for a in c['pavedAreas']if a['id']not in ['yongxu-forecourt','yongxu-entry-apron']]+[dict(id='yongxu-forecourt',name='詠絮樓內側道路',ring=photo['roadRing'],anchor=[-187.1,-59.7],reference=photo['reference'])];c['yongxuLandscape']={'lawn':{'ring':photo['lawnRing'],'name':'詠絮樓內側草皮'},'reference':photo['reference']}
entry=next(a for a in c['pavedAreas']if a['id']=='yongxu-forecourt');entry['triangles']=[[[round(x,7),round(z,7)]for x,z in list(t.exterior.coords)[:-1]]for t in constrained_delaunay_triangles(Polygon(entry['ring'])).geoms]
south=json.loads((root/'facilities/sports-courts/south-sidewalk.json').read_text());c['roads']=[r for r in c['roads']if r['osm']!=south['removeFootpath']['osm']]
for key in ['levelAreas','pedestrianAreas','pedestrianLinks']:c[key]=layout[key]
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
(root/'data/site-layout.js').write_text('// Shared flat campus quarters and pedestrian additions; source: facilities/campus-plazas/layout.json.\nexport const campusSiteLayout='+json.dumps(layout,ensure_ascii=False,separators=(',',':'))+';\n')
print('Built',len(layout['levelAreas']),'shared level areas and',len(layout['pedestrianLinks']),'pedestrian connections')
