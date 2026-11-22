"""Move 歸燕食巢 and 飛燕 together to their orthophoto position (user choice, 2026-11-22).

Fit: IoU of the OSM-derived canteen outline against the roof traced on the 2023 NLSC orthophoto,
constrained to stay clear of the S22 asphalt; rotate 1.0 deg about the canteen centroid then shift
[10.0, 6.25] m. The pair moves rigidly, so the user-fixed 7.2 m canteen/Feiyan gap is unchanged.
Idempotent: the original rings are kept as beforeRelocationRing and always used as the source.
Run before build-building-catalog.py / build-campus-plazas.py. Yongxu is NOT moved.
"""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely.affinity import rotate, translate
root=Path(__file__).resolve().parents[1]
TH,SHIFT=1.0,(10.0,6.25)
def load(p):return json.loads((root/p).read_text())
def save(p,o,indent=2):(root/p).write_text(json.dumps(o,ensure_ascii=False,indent=indent)+'\n')
kp,fp='buildings/swallow-restaurant/building.json','buildings/osm-381734405/building.json'
k,f=load(kp),load(fp)
src_k=k['geometry'].setdefault('beforeRelocationRing',k['geometry']['ring']);src_f=f['geometry'].setdefault('beforeRelocationRing',f['geometry']['ring'])
CEN=tuple(Polygon(src_k).centroid.coords[0])
def T(pt):
    g=translate(rotate(Polygon([pt,(pt[0]+1e-9,pt[1]),(pt[0],pt[1]+1e-9)]),TH,origin=CEN),*SHIFT);x,y=list(g.exterior.coords)[0];return [round(x,6),round(y,6)]
Tm=lambda pts:[T(p) for p in pts]
k['geometry']['ring']=Tm(src_k);f['geometry']['ring']=Tm(src_f)
k['appearance']['frontHint']=T([sum(src_k[i][j] for i in (6,7))/2 for j in (0,1)])
f['appearance']['frontHint']=T(f['appearance'].get('beforeRelocationFrontHint',f['appearance']['frontHint']));f['appearance'].setdefault('beforeRelocationFrontHint',f['appearance']['frontHint'])
note='2026-11-22依國土測繪中心2023正射影像：歸燕食巢與飛燕以剛體一起移動（繞食巢重心轉1.0°、平移[10.0,6.25]m），食巢與飛燕7.2m間距不變；擬合時避開S22瀝青。取代先前向S07人行道貼齊的位置。'
k.setdefault('frontageAlignment',{})['relocation']=note
f['appearance']['reference']=f['appearance']['reference'].split('；2026-11-22')[0]+'；'+note
save(kp,k);save(fp,f)
# --- shared level area, walkways
lp='facilities/campus-plazas/layout.json';L=load(lp)
K,F=Polygon(k['geometry']['ring']),Polygon(f['geometry']['ring'])
c=load('data/campus.json')
motor=unary_union([LineString(r['line']).buffer(r['width']/2+.3) for r in c['roads'] if r['width']>=4])
qa=[a for a in L['levelAreas'] if a['id']=='restaurant-quarter'][0]
old=Polygon(qa.setdefault('beforeRelocationRing',qa['ring']))
YG=load('buildings/yongxu/building.json')['geometry'];Yp=Polygon(YG['ring'])   # 詠絮樓 may have been relocated too (scripts/relocate-yongxu.py)
area=unary_union([old,K.buffer(4),F.buffer(4),Yp.buffer(4)]).difference(motor.difference(old))
area=max(getattr(area,'geoms',[area]),key=lambda g:g.area);area=Polygon(area.exterior).simplify(.1)
qa['ring']=[[round(x,6),round(y,6)] for x,y in list(area.exterior.coords)[:-1]]
qa['relocationNote']='2026-11-22歸燕食巢／飛燕依正射影像移動；原平台範圍全保留，補入兩棟新輪廓外4m（不含車道）。'
links={x['id']:x for x in L['pedestrianLinks']}
p01=links['P01'];p01.setdefault('beforeRelocationLine',p01['line']);p01['line']=Tm(p01['beforeRelocationLine'])
for pid in ('P02','P03'):
    p=links[pid];p.setdefault('beforeRelocationLine',p['line'])
    # the far end may have been re-routed by scripts/relocate-yongxu.py (relocatedEnd)
    p['line']=[p01['line'][-1]]+p['beforeRelocationLine'][1:-1]+[p.get('relocatedEnd',p['beforeRelocationLine'][-1])]
p04=links['P04'];p04.setdefault('beforeRelocationLine',p04['line']);p04['line']=[T(p04['beforeRelocationLine'][0])]+p04['beforeRelocationLine'][1:]
# entrance (NW wall centre) is ~13 m from the nearest walkway after the move: add a 3 m entrance path
if not any(x['id']=='P06' for x in L['pedestrianLinks']):
    L['pedestrianLinks'].append({'id':'P06','name':'歸燕食巢入口步道','line':[[-231.33,-19.4],[-240.0,-29.2]],'width':3,'reference':'2026-11-22食巢依正射影像移動後，入口（西北牆中央）離最近人行道約13m，補一條3m入口步道接到S07側人行道；路線為模型近似。'})
# canteen entrance infill sat in front of the old S07-side facade: drop it
L['pedestrianAreas']=[a for a in L['pedestrianAreas'] if a['id']!='swallow-entrance-infill']
save(lp,L)
# --- generated frontage strips belong to the old facade position
cp=root/'data/campus.json';c['sidewalkFrontages']=[x for x in c.get('sidewalkFrontages',[]) if str(x['building'])!='381732645'];c.get('entranceRoadIds',{}).pop('381732645',None);cp.write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
print('relocated: canteen/Feiyan rings, restaurant-quarter',round(old.area),'->',round(area.area),'m2, P01-P04, entrance infill removed')
