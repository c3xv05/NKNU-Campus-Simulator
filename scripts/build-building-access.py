"""Synchronize photo-based stairs with the shared spatial index."""
import json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());a=json.loads((root/'facilities/building-access/layout.json').read_text())
def ring(s):
 (x,z),(xx,zz)=s['line'];dx,dz=xx-x,zz-z;l=math.hypot(dx,dz);nx,nz=-dz/l,dx/l;top=s.get('topWidth',s['width'])/2;bottom=s['width']/2
 return [[x+nx*top,z+nz*top],[xx+nx*bottom,zz+nz*bottom],[xx-nx*bottom,zz-nz*bottom],[x-nx*top,z-nz*top]]
c['bioConnection']['stairs']=a['bioStairs'];c['bioConnection']['stairs']['ring']=ring(a['bioStairs']);c['levelLink']['stairs']=a['teachingStairs'];c['levelLink']['communicationAlias']=a.get('communicationAlias')
c['courtyard']['stairs']=a.get('courtyardStairs',[])
for s in c['levelLink']['stairs']+c['courtyard']['stairs']:s['ring']=ring(s)
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built wide biology flights and two-stage teaching access')

latest=json.loads((root/'facilities/building-access/latest-ground-access.json').read_text());
from shapely.geometry import LineString,box
from shapely import constrained_delaunay_triangles
drive=latest['basementDrive'];shape=LineString(drive['line']).buffer(drive['width']/2,join_style=1,cap_style=2);drive['ring']=[list(p)for p in list(shape.exterior.coords)[:-1]];drive['triangles']=[]
for x in range(math.floor(shape.bounds[0]),math.ceil(shape.bounds[2])):
 for z in range(math.floor(shape.bounds[1]),math.ceil(shape.bounds[3])):drive['triangles'] += [[list(p)for p in list(t.exterior.coords)[:-1]]for t in constrained_delaunay_triangles(shape.intersection(box(x,z,x+1,z+1))).geoms if t.area>1e-8]
c['zhiliBasementDrive']=drive;c['zhiliLoweredTiles']=latest['loweredTiles'];c['roads']=[r for r in c['roads']if r['osm']!=latest['basementDrive']['osm']]
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
