"""Move S26/S27(top)/S28/S32 north onto the orthophoto positions (2026-11-25, user).

NLSC 2023 orthophoto: the asphalt apron leaves S05 about 6 m further north than the OSM node
and runs along the south wall of Gauss; the striped lane (S27) starts at (-85.4,-157.9).
S05 (nodes, grade) is untouched.  Idempotent; keeps the old lines in beforeGaussSouthShift.
"""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'data/campus.json';c=json.loads(p.read_text())
J=[-87.6,-164.0]                      # new S26/S27/S28 junction (was [-87.6,-155])
NEW={
 418049573:[[-64.8,-162.4],[-69.5,-165.8],[-75.0,-167.3],[-81.5,-166.6],J],
 418049575:[J,[-93.6,-164.4],[-102.4,-161.3],[-111.1,-158.2],[-117.5,-157.3],[-124.0,-158.0]],
 495017564:[[-124.0,-158.0],[-131.0,-153.5],[-140.0,-151.0],[-151.5,-148.3]],   # west stub: far end stays, clear of Huanyu's south wall
}
DZ=-10.5
for r in c['roads']:
    o=r['osm']
    if o not in(418049573,418049574,418049575,495017564):continue
    r.setdefault('beforeGaussSouthShift',r['line'])
    if o==418049574:
        old=r['beforeGaussSouthShift'];r['line']=[J,[-79.3,-144.0]]+old[1:]
    else:r['line']=NEW[o]
    for k in('beforeBuildingBypass','buildingBypass'):r.pop(k,None)
    for k in('sourceLine','preservedLine'):
        if k in r:r[k]=[pt[:] for pt in r['line']]
    r['gaussSouthShift']='2026-11-25 依國土測繪中心2023正射影像向北移，緊貼高斯南牆；S05不動'
# the S32 footpath into the lower plaza starts at the new junction
for r in c['roads']:
    if r['osm']==742398750:
        r.setdefault('beforeGaussSouthShift',r['line']);l=[pt[:] for pt in r['beforeGaussSouthShift']];l[0]=[-124.0,-158.0];r['line']=l
        for k in('sourceLine','preservedLine'):
            if k in r:r[k]=[pt[:] for pt in l]
p.write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
lp=root/'facilities/campus-corridors/layout.json';L=json.loads(lp.read_text());a=L['courtyardAccess']
a.setdefault('beforeGaussSouthShift',a['line']);a['line']=[[-124,-158]]+a['beforeGaussSouthShift'][1:]
lp.write_text(json.dumps(L,ensure_ascii=False,indent=2)+'\n');print('shifted')
