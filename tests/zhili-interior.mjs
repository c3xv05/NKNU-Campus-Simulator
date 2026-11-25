import assert from 'node:assert/strict';import fs from 'node:fs';import {ringDistance} from '../planar.js';
// Zhili empty-room interior: B1–8F inside the tower outline, stacked stairwells, a door per numbered room.
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url))),d=read('buildings/zhili/interior.json'),b=read('buildings/zhili/building.json');
assert.equal(b.appearance.interiorKind,'zhili');assert.equal(b.appearance.interiorFile,'./buildings/zhili/interior.json');
assert.deepEqual(d.floors.map(f=>f.label),['B1','1F','2F']);assert.deepEqual(d.solidAbove,{from:7.2,to:28.8});
assert.equal(d.floorHeight,3.6);assert(Math.abs(d.roofLevel-7.2)<1e-9);
d.floors.forEach((f,i)=>assert(Math.abs(f.level-(i-1)*3.6)<1e-9));
const inRect=(p,r)=>p[0]>r[0]+1e-6&&p[0]<r[2]-1e-6&&p[1]>r[1]+1e-6&&p[1]<r[3]-1e-6;
let treads=0,doors=0;
for(const [i,f] of d.floors.entries()){
 for(const w of f.walls)for(const [x,y] of [[(w[0]+w[2])/2,(w[1]+w[3])/2]])assert(ringDistance(x,y,f.outline)<.3,'wall outside outline '+f.label);
 for(const sp of f.spaces)if(sp.num!=null&&['classroom','office','library','hall'].includes(sp.type)&&/^\d/.test(String(sp.num))){assert(f.doors.some(dr=>dr.name===String(sp.num)),'door for '+sp.num);doors++;}
 if(f.label==='2F'){assert.equal(f.stairs.length,0);continue;}
 const cores=f.stairs.filter(s=>!s.tiers);assert.deepEqual(cores.map(s=>s.id).sort(),['丁梯','丙梯','乙梯','甲梯'].sort(),f.label+' four cores');
 // B1 also carries the 理學院階梯教室 rake (double-height B1+1F auditorium).
 if(f.label==='B1'){const r=f.stairs.find(s=>s.tiers);assert(r&&r.id==='理學院階梯教室'&&r.treads.length===11);assert(Math.abs(Math.max(...r.treads.map(t=>t.height))-d.floorHeight)<1e-3,'rake reaches 1F');}
 for(const s of cores){const h=s.treads.map(t=>t.height);assert.equal(s.treads.filter(t=>!t.bay).length,23);  // 1F 乙梯: extra half-landing strips run into the glazed bay (bay:true, 2026-11-24)
  if(s.id==='乙梯'&&f.label==='1F')assert(s.treads.some(t=>t.bay&&t.rect[2]>66.4),'乙梯 landing reaches the bay glass');
 assert(Math.abs(Math.max(...h)-d.floorHeight)<1e-3,'flight reaches next floor');
  for(const t of s.treads.filter(t=>!t.bay)){assert(t.rect[0]>=s.rect[0]-1e-6&&t.rect[2]<=s.rect[2]+1e-6&&t.rect[1]>=s.rect[1]-1e-6&&t.rect[3]<=s.rect[3]+1e-6);treads++;
   for(const w of f.walls){const c=[(t.rect[0]+t.rect[2])/2,(t.rect[1]+t.rect[3])/2];assert(!inRect(c,w),'wall inside stair tread '+f.label+' '+s.id);}}
  // Typical floors share one stacked stairwell per core.
  if(i>=2){const prev=d.floors[i-1].stairs.find(q=>q.id===s.id);assert.deepEqual(prev.rect,s.rect);assert.equal(prev.entrance,s.entrance);}
 }
 // Slab above each flight opens over the flights, keeping the entrance landing solid.
 const up=d.floors[i+1];for(const s of f.stairs){if(s.tiers)continue;const [x0,y0,x1,y1]=s.hole,c=[(x0+x1)/2,(y0+y1)/2];assert(!up.slab.some(([o,...holes])=>ringDistance(c[0],c[1],o)===0&&!holes.some(h=>ringDistance(c[0],c[1],h)===0)),'stair hole in '+up.label);}
}
assert.equal(d.floors[1].exits.filter(e=>e.manual).length,4,'1F north lobby, south corridor end, east main entrance and the west lobby door (current sheet: the other west doors are inside 全家超商B區)');
assert(treads>150&&doors>20,JSON.stringify({treads,doors}));
// Furniture from room names (scripts/furnish.py): key rooms furnished, every piece inside its floor outline, nothing in doorways.
{const rooms=new Set(d.floors.flatMap(f=>(f.furniture||[]).map(i=>i.room)));for(const r of ['112 ','113-1 ','116 ','108 ','101 ','102-1 ','111 ','215 ','216 ','202 ','201 ','211 ','208 ','理學院階梯教室'])assert([...rooms].some(n=>n.startsWith(r)),'furnished '+r);  // 1F names from the current sheet (2026-11-19)
 for(const f of d.floors){for(const it of f.furniture||[]){const c=[(it.r[0]+it.r[2])/2,(it.r[1]+it.r[3])/2];assert(ringDistance(c[0],c[1],f.outline)===0,'furniture inside '+f.label);}
  const T=d.transform,dr=(x,z)=>[T.a*(x-T.tx)+T.b*(z-T.tz),-T.b*(x-T.tx)+T.a*(z-T.tz)];
  for(const door of f.doors){const [a,b]=door.line.map(p=>dr(...p)),m=[(a[0]+b[0])/2,(a[1]+b[1])/2];for(const r of f.furnitureBlocks||[])assert(Math.hypot(Math.max(r[0]-m[0],0,m[0]-r[2]),Math.max(r[1]-m[1],0,m[1]-r[3]))>1.0,'doorway kept clear '+f.label+' '+door.name);}}}
// 2026-11-19: hairlines across one space (the 1F north–south corridor at y≈40.5, world X≈-145.7) must not become walls.
{const f1=d.floors.find(f=>f.label==='1F');for(let y=34;y<=46;y+=.1)assert(!f1.walls.some(r=>54.2>=r[0]&&54.2<=r[2]&&y>=r[1]&&y<=r[3])&&!f1.walls.some(r=>54.8>=r[0]&&54.8<=r[2]&&y>=r[1]&&y<=r[3]),'1F corridor open at y '+y.toFixed(1));}
// 2026-11-24 (user): every door gets a frame (jambs + head) as thick as its wall.
for(const f of d.floors)for(const door of f.doors)assert(Array.isArray(door.frame)&&door.frame[0]>=.05&&door.frame[0]<=.7,'door frame '+f.label+' '+door.name);
// 2026-11-24: stage platform (+0.8 m, 準備室 on the same platform), 0.2 m curbs as rotated boxes, 戊梯 climbing from the 門廳 to 1F.
{const b1=d.floors[0],stage=b1.stairs.find(q=>q.id==='舞台'),wu=b1.stairs.find(q=>q.id==='戊梯');
 assert(stage&&Math.max(...stage.treads.map(t=>t.height))===.8&&stage.treads.some(t=>t.height===.2)&&stage.treads.some(t=>t.height===.6),'stage platform and corner steps');
 assert(b1.diagWalls.length===6&&b1.diagWalls.filter(w=>w.top===1.0).length===4&&b1.diagWalls.filter(w=>w.top==null).length===2&&b1.blockOnly.length>20,'diagonal curbs are rotated boxes with collision rects; the slanted 準備室 walls are full height (user 2026-11-25)');
 assert(wu&&Math.abs(Math.max(...wu.treads.map(t=>t.height))-3.6)<1e-6&&wu.hole[2]<=5.0,'戊梯 reaches the 1F floor');
 const hs=[...new Set(wu.treads.map(t=>t.height))].sort((x,y)=>x-y);for(let i=1;i<hs.length;i++)assert(hs[i]-hs[i-1]<.2001+1e-9,'戊梯 risers <= 0.2 m '+hs[i]);}
// 2026-11-24: the 乙梯 is hollowed out of the solid upper floors and stacked up to 8F (data.upperFloors), roofed and glazed at the bay.
{const up=d.upperFloors,inSlab=(f,p)=>f.slab.some(([o,...hs])=>ringDistance(p[0],p[1],o)===0&&!hs.some(h=>ringDistance(p[0],p[1],h)===0));
 assert.deepEqual(up.map(f=>f.label),['2F','3F','4F','5F','6F','7F','8F']);
 const ji=d.floors[1].stairs.find(s=>s.id==='乙梯'),centre=[(ji.hole[0]+ji.hole[2])/2,(ji.hole[1]+ji.hole[3])/2];
 for(const f of up){assert(Math.abs(f.level-(+f.label[0]-1)*3.6)<1e-9,'level '+f.label);
  if(f.label!=='8F'){const s=f.stairs.find(q=>q.id==='乙梯');assert(s&&JSON.stringify(s.rect)===JSON.stringify(ji.rect),'stacked rect '+f.label);assert.equal(s.treads.filter(t=>!t.bay).length,23);assert(Math.abs(Math.max(...s.treads.map(t=>t.height))-3.6)<1e-3,'flight reaches next floor '+f.label);}
  else assert.equal(f.stairs.length,0);
  if(f.label!=='2F'){assert(f.walls.length>=5&&f.windows.length===2,'hall walls and bay glass '+f.label);assert(inSlab(f,[ji.rect[0]+.4,(ji.rect[1]+ji.rect[3])/2]),'west landing solid '+f.label);assert(!inSlab(f,centre),'flight opening '+f.label);
   for(const w of f.walls)assert(ringDistance((w[0]+w[2])/2,(w[1]+w[3])/2,f.outline)<.3,'hall wall inside outline '+f.label);}}
 assert(d.solidRing&&ringDistance(centre[0],centre[1],d.solidRing)>0&&ringDistance(centre[0],centre[1],d.towerOutline)===0,'solid tower has the hall cut out');
 assert(d.hallRoofTriangles.length>0&&d.hallRoofLevel===28.8);
 // the 2F→3F roof slab must open over the flight
 const tri=(x,y)=>d.roofTriangles.some(t=>{const T=d.transform,q=t.map(([wx,wz])=>[T.a*(wx-T.tx)+T.b*(wz-T.tz),-T.b*(wx-T.tx)+T.a*(wz-T.tz)]),sg=(p,a,b)=>(p[0]-b[0])*(a[1]-b[1])-(a[0]-b[0])*(p[1]-b[1]),p=[x,y],d1=sg(p,q[0],q[1]),d2=sg(p,q[1],q[2]),d3=sg(p,q[2],q[0]);return !((d1<0||d2<0||d3<0)&&(d1>0||d2>0||d3>0));});
 assert(!tri(centre[0],centre[1]),'roof slab opening over the 2F→3F flight');assert(tri(ji.rect[0]+.4,(ji.rect[1]+ji.rect[3])/2),'roof slab over the west landing');}
// 2026-11-25 (user B1 corrections).
{const b1=d.floors[0],f1=d.floors.find(f=>f.label==='1F'),rect=(r,x,y)=>x>=r[0]&&x<=r[2]&&y>=r[1]&&y<=r[3];
 // driveway east wall: continuous from the garage mouth to the ramp end (no hole at y61.3-62.2)
 for(let y=58.5;y<=66.5;y+=.05)assert(b1.walls.some(r=>rect(r,7.3,y))||b1.sills.some(q=>rect(q.rect,7.05,y)||rect(q.rect,7.3,y)),'driveway east wall closed at y '+y.toFixed(2));
 for(let y=60.2;y<=62.3;y+=.05)assert(b1.walls.some(r=>rect(r,7.3,y)),'full-height wall beside B03 at y '+y.toFixed(2));
 // every door is square in its wall; the raised doors beside the stage lift their frame and header with the floor
 const T=d.transform,dr=p=>{const x=p[0]-T.tx,z=p[1]-T.tz;return[T.a*x+T.b*z,-T.b*x+T.a*z];};
 for(const f of d.floors.filter(f=>['B1','1F','2F'].includes(f.label)))for(const door of f.doors){const[a,b]=door.line.map(dr);assert(Math.min(Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1]))<.011,'door square in its wall '+f.label+' '+door.name+' '+a.map(v=>v.toFixed(2)));}
 assert(b1.doors.some(q=>q.raise===.8)&&b1.lintels.some(l=>l[4]===.8),'doors on the stage-height floor are raised');
 // no door standing in front of another (B1 甲梯 had a drawn and a hand-placed door in one opening)
 for(const f of d.floors.filter(f=>['B1','1F','2F'].includes(f.label)))for(let i=0;i<f.doors.length;i++)for(let j=i+1;j<f.doors.length;j++){const[a,b]=f.doors[i].line.map(dr),[c,e]=f.doors[j].line.map(dr);const vert=Math.abs(a[0]-b[0])<.02&&Math.abs(c[0]-e[0])<.02,hor=Math.abs(a[1]-b[1])<.02&&Math.abs(c[1]-e[1])<.02;
  const ov=vert?Math.min(Math.max(a[1],b[1]),Math.max(c[1],e[1]))-Math.max(Math.min(a[1],b[1]),Math.min(c[1],e[1])):hor?Math.min(Math.max(a[0],b[0]),Math.max(c[0],e[0]))-Math.max(Math.min(a[0],b[0]),Math.min(c[0],e[0])):-1;
  const gap=vert?Math.abs(a[0]-c[0]):hor?Math.abs(a[1]-c[1]):9;assert(!(ov>.3&&gap<.6),'doors stacked '+f.label+' '+f.doors[i].name+'/'+f.doors[j].name);}
 // sealed B06 / B07 doors, closed little 蓄水池 room beside 丁梯, its interior cleared
 for(const y of[28.6,29.2,29.8])assert(b1.walls.some(r=>rect(r,53.35,y)),'B07 door sealed at y '+y);
 for(const y of[30.9,31.3])assert(b1.walls.some(r=>rect(r,53.3,y)),'B06 door sealed at y '+y);
 assert(!b1.doors.some(q=>{const[a]=q.line.map(dr);return Math.abs(a[0]-53.3)<.2&&a[1]>28&&a[1]<31.7;}),'no B06/B07 door left to walk through');
 assert(b1.doorLeaves.some(l=>l[0]<45&&l[2]>43.9&&l[1]<10.9&&l[3]>10.5),'小蓄水池室 door is a closed leaf');
 assert(!b1.walls.some(r=>r[0]>42&&r[2]<44.3&&r[1]>5&&r[3]<10),'小蓄水池室 interior walls cleared');
 // slanted 1F walls round the stage void are rotated boxes now
 assert(f1.diagWalls.length>=3&&f1.diagWalls.every(w=>w.top==null),'1F stage void rim is smooth');
}
// 2026-11-25: floor containment — low partitions never reach below their own floor; door frames meet walls.
{const f1=d.floors.find(f=>f.label==='1F');const st=f1.sills.filter(q=>q.rect[0]>=21.4&&q.rect[2]<=26.4&&q.rect[1]>=46.2&&q.rect[3]<=55.0&&q.top<2.0);assert(st.length>3&&st.every(q=>q.low===true),'己梯旁廁所隔間 stand on the 1F floor, not in B1');}
for(const f of d.floors)for(const q of f.sills)if(q.top<2.0&&q.rect[0]>20&&q.rect[0]<45&&q.rect[1]>46&&q.rect[1]<50&&f.label==='1F')assert(q.low===true,'interior partition '+q.rect);
console.log('PASS: Zhili B1–2F empty-room interior (3F+ solid), stacked four-core stairwells reaching every floor, stair openings, doors for numbered rooms',{treads,doors});
