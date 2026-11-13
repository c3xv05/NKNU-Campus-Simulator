"""A two-ended arrival drive with a smooth stop in front of Wencui."""
import json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());a=json.loads((root/'facilities/wencui-arrival/layout.json').read_text());source=a['line'];out=[source[0]]
for p,q,r in zip(source,source[1:],source[2:]):
 d=math.dist(p,q);e=math.dist(q,r);cut=min(4,d*.3,e*.3);b=[q[i]+(p[i]-q[i])*cut/d for i in range(2)];v=[q[i]+(r[i]-q[i])*cut/e for i in range(2)]
 for k in range(17):
  t=k/16;out.append([round((1-t)**2*b[i]+2*(1-t)*t*q[i]+t*t*v[i],7)for i in range(2)])
out.append(source[-1])
if a.get('beziers'):
 out=[]
 for curve in a['beziers']:
  for k in range(41):
   if out and k==0:continue
   t=k/40;v=1-t;out.append([round(v**3*curve[0][i]+3*v*v*t*curve[1][i]+3*v*t*t*curve[2][i]+t**3*curve[3][i],7)for i in range(2)])
road=next(r for r in c['roads']if r['osm']==a['road']);road.setdefault('beforeArrivalDrive',{'line':road['line'],'sourceLine':road.get('sourceLine')});road.update(line=out,sourceLine=source,preservedLine=out,width=a['width'],arrivalDriveReference='facilities/wencui-arrival/layout.json');c['junctionFillets']=[p for p in c['junctionFillets']if not(p['id']in a.get('replacedJunctionFillets',[])and all(-261<x< -243 and -43<z< -29 for x,z in p['ring']))];c['wencuiArrival']={**a,'line':out};(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
