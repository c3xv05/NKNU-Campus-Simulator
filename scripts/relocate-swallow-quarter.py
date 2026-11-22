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
# 2026-11-23 shapes (user: canteen per floor plans, Feiyan per orthophoto) replace the moved OSM outlines
import math as _m
_u=(_m.cos(_m.radians(-41.2)),_m.sin(_m.radians(-41.2)));_n=(-_u[1],_u[0])   # canteen long axis / normal (+n = towards Feiyan)
_c=(-213.9+1.6*_n[0],-20.05+1.6*_n[1])                                       # +1.6 m keeps the front wall >=1.5 m from the S22 asphalt
def _pt(a,b,c0=_c):return [round(c0[0]+a*_u[0]+b*_n[0],6),round(c0[1]+a*_u[1]+b*_n[1],6)]
KL,KW=57.6,20.6                                                              # axes A-C 7+13 m plus walls, plan 1F-4F
k['geometry']['ring']=[_pt(KL/2,-KW/2),_pt(KL/2,KW/2),_pt(-KL/2,KW/2),_pt(-KL/2,-KW/2)]   # edge 3 = front (NW) wall
_o=(-196.05+1.6*_n[0],0.2+1.6*_n[1]);_r=12.3;_m_=(_o[0]-2.9*_n[0],_o[1]-2.9*_n[1]);_h=_m.sqrt(_r*_r-2.9*2.9)
_a1=_m.atan2(_m_[1]-_h*_u[1]-_o[1],_m_[0]-_h*_u[0]-_o[0]);_a2=_m.atan2(_m_[1]+_h*_u[1]-_o[1],_m_[0]+_h*_u[0]-_o[0])
_sweep=(_a2-_a1)%(2*_m.pi);_mid=_a1+_sweep/2
if (_m.cos(_mid)*_n[0]+_m.sin(_mid)*_n[1])<0:_sweep-=2*_m.pi             # arc must bulge away from the canteen
f['geometry']['ring']=[[round(_o[0]+_r*_m.cos(_a1+_sweep*i/28),6),round(_o[1]+_r*_m.sin(_a1+_sweep*i/28),6)] for i in range(29)]
kr=k['geometry']['ring'];k['appearance']['frontHint']=[round((kr[3][j]+kr[0][j])/2,6) for j in (0,1)];k['appearance']['frontEdge']=3;k['appearance']['frontEdges']=[3];k.setdefault('frontageAlignment',{}).update(edges=[3],entryEdge=3)
f['appearance'].setdefault('beforeRelocationFrontHint',f['appearance']['frontHint']);f['appearance']['frontHint']=f['geometry']['ring'][14]
note='2026-11-22依國土測繪中心2023正射影像：歸燕食巢與飛燕以剛體一起移動（繞食巢重心轉1.0°、平移[10.0,6.25]m），食巢與飛燕7.2m間距不變；擬合時避開S22瀝青。取代先前向S07人行道貼齊的位置。'
k['frontageAlignment']['relocation']=note+'；2026-11-23外型改依平面圖：57.6×20.6m矩形（A–C軸7+13m加牆厚），與S22瀝青間距≥1.5m；飛燕改依空拍為半徑12.3m圓弓形（弦平行食巢，離食巢後牆約13.8m），取代7.2m間距。'
f['appearance']['reference']=f['appearance']['reference'].split('；2026-11-22')[0]+'；'+note+'；2026-11-23外型依空拍改為圓弓形（半徑12.3m）。'
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
