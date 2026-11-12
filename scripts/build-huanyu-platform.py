"""Build a T plaza: road-facing crossbar, entrance stem and a flat 3F landing."""
import json,math
from pathlib import Path
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());a=json.loads((root/'facilities/huanyu-platform/layout.json').read_text());b=next(b for b in c['places'] if b['osm']==a['building']);ring=b['ring'];p,q=ring[a['frontEdge']],ring[(a['frontEdge']+1)%len(ring)];entry=[(p[0]+q[0])/2,(p[1]+q[1])/2];road=next(r for r in c['roads'] if r['osm']==a['road']);line=LineString(road['line']);distance=line.project(Point(entry));near=line.interpolate(distance);stations=[];nearEdge=[];farEdge=[];offset=road['width']/2+3.6;count=math.ceil(a['platformWidth']/.75)
for i in range(count+1):
 d=distance-a['platformWidth']/2+a['platformWidth']*i/count;v=line.interpolate(d);prev=line.interpolate(d-.1);nxt=line.interpolate(d+.1);dx,dz=nxt.x-prev.x,nxt.y-prev.y;l=math.hypot(dx,dz);nx,nz=-dz/l,dx/l
 if (entry[0]-v.x)*nx+(entry[1]-v.y)*nz<0:nx,nz=-nx,-nz
 edge=[v.x+nx*offset,v.y+nz*offset];far=[v.x+nx*(offset+a['platformDepth']),v.y+nz*(offset+a['platformDepth'])];nearEdge.append(edge);farEdge.append(far);stations.append({'edge':edge,'far':far})
bar=Polygon(nearEdge+list(reversed(farEdge)));middle=len(stations)//2;start=stations[middle]['far'];dx,dz=entry[0]-start[0],entry[1]-start[1];length=math.hypot(dx,dz);nx,nz=-dz/length,dx/length;w=a['rampWidth']/2;stemRing=[[start[0]+nx*w-dx/length*.02,start[1]+nz*w-dz/length*.02],[entry[0]+nx*w,entry[1]+nz*w],[entry[0]-nx*w,entry[1]-nz*w],[start[0]-nx*w-dx/length*.02,start[1]-nz*w-dz/length*.02]];stem=Polygon(stemRing);buildings=unary_union([Polygon(b['ring']) for b in c['places']+c['buildings'] if b.get('height')]);bar=bar.difference(buildings);stem=stem.difference(buildings);shape=unary_union([bar,stem]).buffer(0)
def coords(r):return [[round(x,7),round(z,7)] for x,z in list(r.coords)[:-1]]
def mesh(shape):
 result=[];w,n,e,s=shape.bounds;step=1.25
 for row in range(math.floor(n/step),math.ceil(s/step)):
  for col in range(math.floor(w/step),math.ceil(e/step)):
   x,z=col*step,row*step
   for cell in [Polygon([[x,z],[x+step,z],[x,z+step]]),Polygon([[x+step,z+step],[x,z+step],[x+step,z]])]:
    for t in constrained_delaunay_triangles(shape.intersection(cell)).geoms:
     if t.area>1e-7:result.append(coords(t.exterior))
 return result
a.update(entry=entry,ring=coords(shape.exterior),bar={'ring':coords(bar.exterior),'stations':stations,'triangles':mesh(bar)},ramp={'line':[start,entry],'width':a['rampWidth'],'ring':stemRing,'triangles':mesh(stem.difference(bar))},footprints=[coords(t.exterior) for t in constrained_delaunay_triangles(shape).geoms if t.area>1e-7]);c['huanyuAccess']=a
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built road-facing T plaza at Huanyu 3F;',round(shape.area,1),'m²')
