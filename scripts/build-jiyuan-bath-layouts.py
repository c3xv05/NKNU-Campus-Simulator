"""Write the user-confirmed Jiyuan bathroom layouts (shared and private) into plan.json.

Two left-wing templates were read from source/dormitory-plans.pdf page 2 and
labelled by the user (2026-11-18):
  outer (202/203, also 204/205): 1 twin sinks, 2/5 squat stalls, 4/9 urinals,
        7/8 shower stalls, 3 exhaust cell (not built, closed vent window only).
  inner (208/209, also 210/211): 1 twin sinks, 2/4 squat stalls, 3/5 urinals,
        8/9 shower stalls, 6 exhaust cell (not built, closed vent window only).
Each shared bath is one open space for both rooms. A 2x2 wall cabinet hangs
above every urinal. Templates are in source-pixel units of their frame bath;
other baths are mapped by bounding box, the right wing is mirrored (x -> 1800-x).
Private baths (user labels, 2026-11-18): 201 sink / seat toilet / shower head;
206 sink, urinal, squat stall, shower stall (door not built), pipe shaft (closed,
its vent window on the 207 side); 207 sink, urinal, shower stall, squat stall;
212 shower head, sink, seat toilet. Every 2x2 cabinet above a urinal is open
(no doors). Coordinates and door widths are model approximations of a low-resolution scan.
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
 # Corridor wall follows the original hatched diagonal (moved out 11 units on 2026-11-18).
 p0,p1=[374.44,851],[322,903.44];inward=norm([p1[1]-p0[1],-(p1[0]-p0[0])])
 if inward[0]<0:inward=[-inward[0],-inward[1]]
 showers=[strip(p0,p1,21,43,18,inward),strip(p0,p1,43,65,18,inward)]
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
   {'kind':'squat','polygon':[[385,851],[412,851],[412,878],[385,878]],'door':[[388,878],[388+STALL,878]]},
   {'kind':'squat','polygon':[[322,913],[345,913],[345,943],[322,943]],'door':[[345,914],[345,914+STALL]]},
   *[{'kind':'shower','polygon':s,'door':mid(s[2],s[3],STALL)} for s in showers]],
  'vents':[{'line':[at_t(p0,p1,65.5),at_t(p0,p1,73.5)]}]}
def private():
 # Absolute source coordinates of the left-wing private baths; frame = own bounding box.
 return {
 'p201':{'frame':[157,880,205,920],'doors':[{'at':[170,920],'width':20}],
  'fixtures':[{'kind':'sink','at':[190.4,898],'back':[1,0]},{'kind':'seat','at':[187.9,911],'back':[1,0]},{'kind':'showerhead','at':[194.1,886],'back':[1,0]}],
  'cabinets':[],'stalls':[{'kind':'shaft','polygon':[[196,880],[205,880],[205,920],[196,920]]}],'vents':[]},
 'p206':{'frame':[550,518,607,588],'doors':[{'at':[570,518],'width':18}],
  'fixtures':[{'kind':'sink','at':[555.6,530],'back':[-1,0]},{'kind':'urinal','at':[554.7,551],'back':[-1,0]},
   {'kind':'squat','at':[560,577],'back':[-1,0]},{'kind':'shower','at':[598.4,531],'back':[1,0]}],
  'cabinets':[{'at':[554.7,551],'back':[-1,0]}],
  'stalls':[{'kind':'squat','polygon':[[550,562],[572,562],[572,588],[550,588]],'door':[[552,562],[552+STALL,562]]},
   {'kind':'shower','polygon':[[578,518],[607,518],[607,548],[578,548]],'door':[[578,518],[578,548]]},
   {'kind':'shaft','polygon':[[572,548],[607,548],[607,588],[572,588]]}],
  'vents':[{'line':[[607,564],[607,574]]}]},
 'p207':{'frame':[607,546,679,588],'doors':[{'at':[641,546],'width':18}],
  'fixtures':[{'kind':'sink','at':[614,551.6],'back':[0,-1]},{'kind':'urinal','at':[617,583.3],'back':[0,1]},
   {'kind':'shower','at':[670.2,556.5],'back':[1,0]},{'kind':'squat','at':[667,577],'back':[1,0]}],
  'cabinets':[{'at':[617,583.3],'back':[0,1]}],
  'stalls':[{'kind':'shower','polygon':[[652,546],[679,546],[679,566],[652,566]],'door':[[652,548],[652,548+STALL]]},
   {'kind':'squat','polygon':[[652,566],[679,566],[679,588],[652,588]],'door':[[652,568],[652,568+STALL]]}],'vents':[]},
 'p212':{'frame':[642,636,714,670],'doors':[{'at':[714,653],'width':20}],
  'fixtures':[{'kind':'showerhead','at':[648,638.2],'back':[0,-1]},{'kind':'sink','at':[659,641.6],'back':[0,-1]},{'kind':'seat','at':[676,644.1],'back':[0,-1]}],
  'cabinets':[],'stalls':[],'vents':[]}}
templates={'outer':outer(),'inner':inner(),**private()}
# Left-wing bath -> template; right-wing counterparts are mirrors of these.
assign={'left-shared-202-203':'outer','left-shared-204-205':'outer','left-shared-208-209':'inner','left-shared-210-211':'inner'}
assign.update({'left-private-201':'p201','left-private-206':'p206','left-private-207':'p207','left-private-212':'p212'})
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
  'stalls':[{'kind':s['kind'],'polygon':[point(p) for p in s['polygon']],**({'door':[point(p) for p in s['door']]} if 'door' in s else {})} for s in template['stalls']],
  'vents':[{'line':[point(p) for p in v['line']]} for v in template['vents']]}
plan['source']['privateBathLayout']='2026-11-18使用者逐號標註原圖第2頁獨立衛浴：201洗手台／坐式馬桶／蓮蓬頭；206洗手台、小便斗、蹲式馬桶隔間、淋浴隔間（門不做）、管道間（封閉，朝207側常關通風窗）；207洗手台、小便斗、淋浴隔間、蹲式馬桶隔間；212蓮蓬頭、洗手台、坐式馬桶。201、212無小便斗與蹲式馬桶。小便斗上方皆有2×2無門開放櫃。右翼鏡像。位置由低解析掃描量取，為模型近似。'
plan['source']['sharedBathLayout']='2026-11-18使用者逐號標註原圖第2頁202/203與208/209：兩個並排洗手台、兩間蹲式馬桶隔間、兩個小便斗（上方2×2無門開放櫃）、兩間淋浴隔間，兩房共用同一空間；抽風機小隔間不建，只在朝走廊牆面做常關排風窗。204/205、210/211沿用同型，右翼鏡像。位置由低解析掃描量取，為模型近似。'
path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
print('bath layouts:',len([b for b in plan['bathrooms'] if 'layout' in b]))
