"""Synchronize photo-based stairs with the shared spatial index."""
import json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());a=json.loads((root/'facilities/building-access/layout.json').read_text())
def ring(s):
 (x,z),(xx,zz)=s['line'];dx,dz=xx-x,zz-z;l=math.hypot(dx,dz);nx,nz=-dz/l,dx/l;top=s.get('topWidth',s['width'])/2;bottom=s['width']/2
 return [[x+nx*top,z+nz*top],[xx+nx*bottom,zz+nz*bottom],[xx-nx*bottom,zz-nz*bottom],[x-nx*top,z-nz*top]]
c['bioConnection']['stairs']=a['bioStairs'];c['bioConnection']['stairs']['ring']=ring(a['bioStairs']);c['levelLink']['stairs']=a['teachingStairs']
for s in c['levelLink']['stairs']:s['ring']=ring(s)
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built wide biology flights and two-stage teaching access')
