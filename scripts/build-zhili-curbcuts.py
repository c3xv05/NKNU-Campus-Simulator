"""Write the Zhili driveway / curb-cut geometry (world coordinates) into data/campus.json (campus.zhiliCurbCuts)."""
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
import zhili_curbcuts as zc
shapes,lay,t=zc.shapes(root);c=json.loads((root/'data/campus.json').read_text())
ring=lambda p:[[round(x,7),round(z,7)] for x,z in list(p.exterior.coords)[:-1]]
d=lay['driveway'];(x0,x1),(r0,r1)=d['x'],d['rampY'];mid=(x0+x1)/2
cc={'reference':lay['reference'],'driveway':{'ramp':ring(shapes['ramps']['driveway']),'open':ring(shapes['open']),'walls':[ring(w) for w in shapes['walls']['driveway']],
 'cut':ring(__import__('shapely.geometry',fromlist=['Polygon']).Polygon(zc.world(t,[[x0,50.0],[x1,50.0],[x1,r1],[x0,r1]]))),'axis':[[round(v,7) for v in zc.world(t,[[mid,r0]])[0]],[round(v,7) for v in zc.world(t,[[mid,r1]])[0]]],'width':round(x1-x0,3),'b1Level':-3.6,'wallAbove':d['wallAbove'],
 'parapet':{'line':[[round(v,7) for v in p] for p in zc.world(t,[[x0,d['parapetY']],[x1,d['parapetY']]])],'height':d['parapetHeight']}}}
a=lay['adaRamp'];(ax0,ax1),(ay0,ay1)=a['x'],a['y'];amid=(ay0+ay1)/2
cc['ada']={'ring':ring(shapes['ramps']['ada']),'axis':[[round(v,7) for v in zc.world(t,[[ax0,amid]])[0]],[round(v,7) for v in zc.world(t,[[ax1,amid]])[0]]],'width':round(ay1-ay0,3)}
items,sky,pillars=zc.plaza_items(t);cc['plaza']={'pillars':pillars,'planterHeight':0.9,'benchHeight':0.45,'items':items,'skylight':sky,'note':'2026-11-22使用者說明：兩條緊密線＝花圃（磁磚），外圍多一條線＝椅子（較矮、同為白色磁磚），花圃高約為椅子兩倍；方格打叉＝B1天窗（四角錐玻璃）。'}
cc['platforms']=[{'id':q['id'],'rel':q['rel'],'ring':ring(__import__('shapely.geometry',fromlist=['Polygon']).Polygon(zc.world(t,[[q['x'][0],q['y'][0]],[q['x'][1],q['y'][0]],[q['x'][1],q['y'][1]],[q['x'][0],q['y'][1]]])))} for q in lay.get('platforms',[])]
cc['driveway']['interiorRamp']=bool(lay['driveway'].get('interiorRamp'))
# 2F corner void details (user photo 2026-11-22): brick panels on the void's back walls, concrete beams under the 3F slab, and
# balustrade along the exposed edges of the upper plaza.
from shapely.geometry import Polygon as _P,box as _box,LineString as _L
from shapely.ops import unary_union as _U
W=lambda poly:[[round(x,7),round(z,7)] for x,z in zc.world(t,list(poly.exterior.coords)[:-1])]
cc['corner']={'brick':[W(_box(21.0,58.2,21.25,66.46)),W(_box(16.5,58.0,21.2,58.2))],
 'beams':[{'ring':W(_box(16.5,58.2,16.95,66.6)),'drop':.7},{'ring':W(_box(16.5,66.15,21.3,66.6)),'drop':.7},{'ring':W(_box(18.9,58.2,19.25,66.6)),'drop':.5},{'ring':W(_box(16.5,62.2,21.2,62.55)),'drop':.5}]}
up=_U([_P(r[0],r[1:]) for r in c['courtyard']['floorRegions']['upper']])
solid=_U([_P(a['ring']).buffer(.6) for a in c['places']+c['buildings'] if a.get('height')]+[_P(x['ring']).buffer(.4) for x in c['levelLink']['stairs']])
edges=up.boundary.difference(solid)
segs=[]
for g in (list(edges.geoms) if hasattr(edges,'geoms') else [edges]):
    if g.geom_type!='LineString' or g.length<.8:continue
    segs.append([[round(x,5),round(z,5)] for x,z in g.coords])
cc['railings']={'height':1.0,'lines':segs}
c['zhiliCurbCuts']=cc
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('zhiliCurbCuts written')
