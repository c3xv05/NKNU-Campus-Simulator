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
 if(f.label==='B1'){const r=f.stairs.find(s=>s.tiers);assert(r&&r.id==='理學院階梯教室'&&r.treads.length===12);assert(Math.abs(Math.max(...r.treads.map(t=>t.height))-d.floorHeight)<1e-3,'rake reaches 1F');}
 for(const s of cores){const h=s.treads.map(t=>t.height);assert.equal(s.treads.length,23);assert(Math.abs(Math.max(...h)-d.floorHeight)<1e-3,'flight reaches next floor');
  for(const t of s.treads){assert(t.rect[0]>=s.rect[0]-1e-6&&t.rect[2]<=s.rect[2]+1e-6&&t.rect[1]>=s.rect[1]-1e-6&&t.rect[3]<=s.rect[3]+1e-6);treads++;
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
console.log('PASS: Zhili B1–2F empty-room interior (3F+ solid), stacked four-core stairwells reaching every floor, stair openings, doors for numbered rooms',{treads,doors});
