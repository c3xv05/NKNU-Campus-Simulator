"""Synchronize photo-based stairs with the shared spatial index."""
import json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());a=json.loads((root/'facilities/building-access/layout.json').read_text())
def ring(s):
 (x,z),(xx,zz)=s['line'];dx,dz=xx-x,zz-z;l=math.hypot(dx,dz);nx,nz=-dz/l,dx/l;top=s.get('topWidth',s['width'])/2;bottom=s['width']/2
 return [[x+nx*top,z+nz*top],[xx+nx*bottom,zz+nz*bottom],[xx-nx*bottom,zz-nz*bottom],[x-nx*top,z-nz*top]]
if a.get('compactAccess'):
 cfg=a['compactAccess'];building=json.loads((root/('buildings/'+cfg['building']+'/building.json')).read_text())['geometry'];fa,anchor=cfg['frontLine'] if cfg.get('frontLine') else [building['ring'][i]for i in [cfg['frontEdge'],(cfg['frontEdge']+1)%len(building['ring'])]];length=math.dist(fa,anchor);t=[(anchor[i]-fa[i])/length for i in [0,1]];n=[t[1],-t[0]]
 def at(u,v):return [round(anchor[i]+n[i]*u+t[i]*v,7)for i in [0,1]]
 def rect(u0,u1,v0,v1):return [at(u0,v0),at(u1,v0),at(u1,v1),at(u0,v1)]
 low=a['teachingStairs'][0];front=-cfg['frontInset'];north=cfg['northClearance']
 ds=cfg.get('drawingStair')
 if ds:
  # Zhili 1F drawing (user 2026-11-18 "完全照著平面圖"): one straight flight between the S05 sidewalk and the 1F ±0 paving.
  (u0,u1),(v0,v1)=ds['u'],ds['v'];low['width']=low['topWidth']=round(v1-v0,3);low['line']=[at(u0,(v0+v1)/2),at(u1,(v0+v1)/2)]
 else:
  high=a['teachingStairs'][1];lowV=north+low['width']/2;highV=north+high['width']/2
  low['line']=[at(front-cfg['lowerRun'],lowV),at(front,lowV)];high['line']=[at(-cfg['upperTopInset'],highV),at(-cfg['upperTopInset']+cfg['upperRun'],highV)]
 gapBuilding=json.loads((root/('buildings/'+cfg.get('gapBuilding','gauss')+'/building.json')).read_text())['geometry'];gapCorner=gapBuilding['ring'][cfg.get('gapCorner',0)];gapEnd=sum((gapCorner[i]-anchor[i])*t[i]for i in [0,1])
 c['teachingAccess']={'reference':cfg['reference'],'anchor':anchor,'outward':n,'along':t,'frontInset':cfg['frontInset'],'northClearance':north,'lowerLanding':rect(ds['u'][0]-ds['landingBack'],ds['u'][0],*ds['v']) if ds else rect(-cfg['lowerLandingBack'],front-cfg['lowerRun'],north,north+low['width']),'frontApron':rect(ds['u'][1],cfg['frontApronReach'],*ds['v']) if ds else rect(front,cfg['frontApronReach'],north,north+low['width']),'reclaimedFootprint':ring(a['beforeEightStepLayout'][0]),'gapFootprint':rect(-cfg.get('gapBackInset',6.5),cfg['frontApronReach'],ds['v'][1] if ds else north,gapEnd),'infillId':cfg['infillId']}
c['bioConnection']['stairs']=a['bioStairs'];c['bioConnection']['stairs']['ring']=ring(a['bioStairs']);
from biology_layout import derive_biology
derive_biology(c,json.loads((root/'facilities/campus-corridors/layout.json').read_text()))
c['levelLink']['stairs']=a['teachingStairs'];c['levelLink']['communicationAlias']=a.get('communicationAlias')
c['courtyard']['stairs']=a.get('courtyardStairs',[])
for s in c['levelLink']['stairs']+c['courtyard']['stairs']:s['ring']=ring(s)
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built wide biology flights and two-stage teaching access')
