"""Orthogonalize the user's Bio A/B map sketch around the preserved joint."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=json.loads((root/'facilities/biology-layout/layout.json').read_text())
t=source['axis'];e=[t[1],-t[0]];joint=source['joint'];u,v=source['localJoint']
def world(p):return [round(joint[i]+e[i]*(p[0]-u)+t[i]*(p[1]-v),7)for i in range(2)]
for name,sketch in source['buildings'].items():
 path=root/f'buildings/{name}/building.json';d=json.loads(path.read_text());g=d['geometry'];g.setdefault('beforeOrthogonalSketch',{'ring':g['ring'],'frontHint':d['appearance']['frontHint']});g['ring']=[world(p)for p in sketch['localRing']];g['alignmentReference']='facilities/biology-layout/layout.json';d['appearance']['frontHint']=world([7,26]if name=='bio-a'else[7,60]);d['appearance']['frontRoadIds']=[218881800];d['appearance']['reference']=source['reference'];path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('Built S05-orthogonal Bio A/B map-sketch footprints; preserved joint and level anchors')
