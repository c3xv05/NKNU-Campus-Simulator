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
 low,high=a['teachingStairs'];front=-cfg['frontInset'];north=cfg['northClearance'];lowV=north+low['width']/2;highV=north+high['width']/2
 low['line']=[at(front-cfg['lowerRun'],lowV),at(front,lowV)];high['line']=[at(-cfg['upperTopInset'],highV),at(-cfg['upperTopInset']+cfg['upperRun'],highV)]
 gapBuilding=json.loads((root/('buildings/'+cfg.get('gapBuilding','gauss')+'/building.json')).read_text())['geometry'];gapCorner=gapBuilding['ring'][cfg.get('gapCorner',0)];gapEnd=sum((gapCorner[i]-anchor[i])*t[i]for i in [0,1])
 c['teachingAccess']={'reference':cfg['reference'],'anchor':anchor,'outward':n,'along':t,'frontInset':cfg['frontInset'],'northClearance':north,'lowerLanding':rect(-cfg['lowerLandingBack'],front-cfg['lowerRun'],north,north+low['width']),'frontApron':rect(front,cfg['frontApronReach'],north,north+low['width']),'reclaimedFootprint':ring(a['beforeEightStepLayout'][0]),'gapFootprint':rect(-cfg.get('gapBackInset',6.5),cfg['frontApronReach'],north,gapEnd),'infillId':cfg['infillId']}
c['bioConnection']['stairs']=a['bioStairs'];c['bioConnection']['stairs']['ring']=ring(a['bioStairs']);
from biology_layout import derive_biology
derive_biology(c,json.loads((root/'facilities/campus-corridors/layout.json').read_text()))
c['levelLink']['stairs']=a['teachingStairs'];c['levelLink']['communicationAlias']=a.get('communicationAlias')
c['courtyard']['stairs']=a.get('courtyardStairs',[])
for s in c['levelLink']['stairs']+c['courtyard']['stairs']:s['ring']=ring(s)
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built wide biology flights and two-stage teaching access')
