"""Write the user-confirmed Jiyuan shared-bathroom layouts into plan.json.

Two left-wing templates were read from source/dormitory-plans.pdf page 2 and
labelled by the user (2026-11-18):
  outer (202/203, also 204/205): 1 twin sinks, 2/5 squat stalls, 4/9 urinals,
        7/8 shower stalls, 3 exhaust cell (not built, closed vent window only).
  inner (208/209, also 210/211): 1 twin sinks, 2/4 squat stalls, 3/5 urinals,
        8/9 shower stalls, 6 exhaust cell (not built, closed vent window only).
Each shared bath is one open space for both rooms. A 2x2 wall cabinet hangs
above every urinal. Templates are in source-pixel units of their frame bath;
other baths are mapped by bounding box, the right wing is mirrored (x -> 1800-x).
Coordinates and door widths are model approximations of a low-resolution scan.
"""
import json, math
from pathlib import Path
root=Path(__file__).resolve().parents[1];path=root/'buildings/foresight/plan.json'
plan=json.loads(path.read_text())

def strip(p0,p1,t1,t2,depth,inward):
 """Compartment on a diagonal wall from p0 toward p1, t along wall, depth inward."""
 l=math.dist(p0,p1);u=[(p1[0]-p0[0])/l,(p1[1]-p0[1])/l]
 a=[p0[0]+u[0]*t1,p0[1]+u[1]*t1];b=[p0[0]+u[0]*t2,p0[1]+u[1]*t2]
 c=[b[0]+inward[0]*depth,b[1]+inward[1]*depth];d=[a[0]+inward[0]*depth,a[1]+inward[1]*depth]
 return [a,b,c,d]
def mid(a,b,w):
 """Opening of width w centred on segment ab."""
 l=math.dist(a,b);m=[(a[0]+b[0])/2,(a[1]+b[1])/2];u=[(b[0]-a[0])/l,(b[1]-a[1])/l]
 return [[m[0]-u[0]*w/2,m[1]-u[1]*w/2],[m[0]+u[0]*w/2,m[1]+u[1]*w/2]]
def norm(v):l=math.hypot(*v);return [v[0]/l,v[1]/l]
def at_t(p0,p1,t):
 l=math.dist(p0,p1);return [p0[0]+(p1[0]-p0[0])*t/l,p0[1]+(p1[1]-p0[1])*t/l]

# Stall openings are 17.5 units (~0.80m) so the 0.3m walker can step in; room doors 20 (~0.92m).
STALL=17.5
def outer():
 p0,p1=[335,824],[280,880];inward=norm([-(p1[1]-p0[1]),p1[0]-p0[0]])  # rotate wall dir to bath side
 if inward[0]>0:inward=[-inward[0],-inward[1]]
 showers=[strip(p0,p1,24,46,18,inward),strip(p0,p1,46,68,18,inward)]
 back=norm([-inward[0],-inward[1]])
 return {'frame':[245,790,335,880],
  'doors':[{'at':[245,827],'width':20},{'at':[276,790],'width':20}],
  'fixtures':[
   {'kind':'sink','at':[250.6,798],'back':[-1,0]},{'kind':'sink','at':[250.6,811],'back':[-1,0]},
   {'kind':'urinal','at':[249.7,843],'back':[-1,0]},{'kind':'urinal','at':[293,794.7],'back':[0,-1]},
   {'kind':'squat','at':[322,802.5],'back':[0,-1]},{'kind':'squat','at':[257.5,866],'back':[-1,0]},
   *[{'kind':'shower','at':[sum(v[0] for v in s)/4,sum(v[1] for v in s)/4],'back':back} for s in showers]],
  'cabinets':[{'at':[249.7,843],'back':[-1,0]},{'at':[293,794.7],'back':[0,-1]}],
  'stalls':[
   {'kind':'squat','polygon':[[309,790],[335,790],[335,815],[309,815]],'door':[[309,796],[309,796+STALL]]},
   {'kind':'squat','polygon':[[245,850],[270,850],[270,880],[245,880]],'door':[[249,850],[249+STALL,850]]},
   *[{'kind':'shower','polygon':s,'door':mid(s[2],s[3],STALL)} for s in showers]],
  'vents':[{'line':[[335,815.5],[335,823.5]]}]}
def inner():
 p0,p1=[390,851],[322,919];inward=norm([p1[1]-p0[1],-(p1[0]-p0[0])])
 if inward[0]<0:inward=[-inward[0],-inward[1]]
 showers=[strip(p0,p1,26,48,16,inward),strip(p0,p1,48,70,16,inward)]
 back=norm([-inward[0],-inward[1]])
 return {'frame':[322,851,412,943],
  'doors':[{'at':[379,943],'width':20},{'at':[412,904],'width':20}],
  'fixtures':[
   {'kind':'sink','at':[406.4,922],'back':[1,0]},{'kind':'sink','at':[406.4,935],'back':[1,0]},
   {'kind':'urinal','at':[407.3,886],'back':[1,0]},{'kind':'urinal','at':[360,938.3],'back':[0,1]},
   {'kind':'squat','at':[400,864],'back':[1,0]},{'kind':'squat','at':[333,931],'back':[0,1]},
   *[{'kind':'shower','at':[sum(v[0] for v in s)/4,sum(v[1] for v in s)/4],'back':back} for s in showers]],
  'cabinets':[{'at':[407.3,886],'back':[1,0]},{'at':[360,938.3],'back':[0,1]}],
  'stalls':[
   {'kind':'squat','polygon':[[390,851],[412,851],[412,878],[385,878],[385,856]],'door':[[388,878],[388+STALL,878]]},
   {'kind':'squat','polygon':[[322,919],[328,913],[345,913],[345,943],[322,943]],'door':[[345,914],[345,914+STALL]]},
   *[{'kind':'shower','polygon':s,'door':mid(s[2],s[3],STALL)} for s in showers]],
  'vents':[{'line':[at_t(p0,p1,85.5),at_t(p0,p1,93.5)]}]}
templates={'outer':outer(),'inner':inner()}
# Left-wing bath -> template; right-wing counterparts are mirrors of these.
assign={'left-shared-202-203':'outer','left-shared-204-205':'outer','left-shared-208-209':'inner','left-shared-210-211':'inner'}
for left,t in list(assign.items()):assign[left.replace('left-','right-')]=t

def mapper(template,bath,mirror):
 fx1,fy1,fx2,fy2=template['frame'];xs=[p[0] for p in bath['polygon']];ys=[p[1] for p in bath['polygon']]
 bx1,by1,bx2,by2=(1800-max(xs),min(ys),1800-min(xs),max(ys)) if mirror else (min(xs),min(ys),max(xs),max(ys))
 sx=(bx2-bx1)/(fx2-fx1);sy=(by2-by1)/(fy2-fy1)
 def point(p):
  x=bx1+(p[0]-fx1)*sx;y=by1+(p[1]-fy1)*sy
  return [round(1800-x if mirror else x,3),round(y,3)]
 def vector(v):return [round(-v[0] if mirror else v[0],6),round(v[1],6)]
 return point,vector

for bath in plan['bathrooms']:
 if bath['id'] not in assign:continue
 template=templates[assign[bath['id']]];mirror=bath['id'].startswith('right-')
 point,vector=mapper(template,bath,mirror)
 assert len(bath['doors'])==len(template['doors'])
 for entry,door in zip(bath['doors'],template['doors']):entry['at']=point(door['at']);entry['width']=door['width']
 bath['layout']={'template':assign[bath['id']],'mirrored':mirror,
  'fixtures':[{'kind':f['kind'],'at':point(f['at']),'back':vector(f['back'])} for f in template['fixtures']],
  'cabinets':[{'at':point(c['at']),'back':vector(c['back'])} for c in template['cabinets']],
  'stalls':[{'kind':s['kind'],'polygon':[point(p) for p in s['polygon']],'door':[point(p) for p in s['door']]} for s in template['stalls']],
  'vents':[{'line':[point(p) for p in v['line']]} for v in template['vents']]}
plan['source']['sharedBathLayout']='2026-11-18使用者逐號標註原圖第2頁202/203與208/209：兩個並排洗手台、兩間蹲式馬桶隔間、兩個小便斗（上方2×2壁掛儲物櫃）、兩間淋浴隔間，兩房共用同一空間；抽風機小隔間不建，只在朝走廊牆面做常關排風窗。204/205、210/211沿用同型，右翼鏡像。位置由低解析掃描量取，為模型近似。'
path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
print('shared bath layouts:',len([b for b in plan['bathrooms'] if 'layout' in b]))
