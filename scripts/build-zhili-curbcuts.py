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
c['zhiliCurbCuts']=cc
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('zhiliCurbCuts written')
