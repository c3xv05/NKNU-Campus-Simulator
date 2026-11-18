import assert from 'node:assert/strict';import fs from 'node:fs';import {ringDistance} from '../planar.js';
// Zhili empty-room interior: B1–8F inside the tower outline, stacked stairwells, a door per numbered room.
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url))),d=read('buildings/zhili/interior.json'),b=read('buildings/zhili/building.json');
assert.equal(b.appearance.interiorKind,'zhili');assert.equal(b.appearance.interiorFile,'./buildings/zhili/interior.json');
assert.deepEqual(d.floors.map(f=>f.label),['B1','1F','2F','3F','4F','5F','6F','7F','8F']);
assert.equal(d.floorHeight,3.6);assert.equal(d.roofLevel,8*3.6);
d.floors.forEach((f,i)=>assert(Math.abs(f.level-(i-1)*3.6)<1e-9));
const inRect=(p,r)=>p[0]>r[0]+1e-6&&p[0]<r[2]-1e-6&&p[1]>r[1]+1e-6&&p[1]<r[3]-1e-6;
let treads=0,doors=0;
for(const [i,f] of d.floors.entries()){
 for(const w of f.walls)for(const [x,y] of [[(w[0]+w[2])/2,(w[1]+w[3])/2]])assert(ringDistance(x,y,d.outline)<.3,'wall outside outline '+f.label);
 for(const sp of f.spaces)if(sp.num!=null&&['classroom','office','library','hall'].includes(sp.type)&&/^\d/.test(String(sp.num))){assert(f.doors.some(dr=>dr.name===String(sp.num)),'door for '+sp.num);doors++;}
 if(f.label==='8F'){assert.equal(f.stairs.length,0);continue;}
 assert.deepEqual(f.stairs.map(s=>s.id).sort(),['丁梯','丙梯','乙梯','甲梯'].sort(),f.label+' four cores');
 for(const s of f.stairs){const h=s.treads.map(t=>t.height);assert.equal(s.treads.length,23);assert(Math.abs(Math.max(...h)-d.floorHeight)<1e-3,'flight reaches next floor');
  for(const t of s.treads){assert(t.rect[0]>=s.rect[0]-1e-6&&t.rect[2]<=s.rect[2]+1e-6&&t.rect[1]>=s.rect[1]-1e-6&&t.rect[3]<=s.rect[3]+1e-6);treads++;
   for(const w of f.walls){const c=[(t.rect[0]+t.rect[2])/2,(t.rect[1]+t.rect[3])/2];assert(!inRect(c,w),'wall inside stair tread '+f.label+' '+s.id);}}
  // Typical floors share one stacked stairwell per core.
  if(i>=2){const prev=d.floors[i-1].stairs.find(q=>q.id===s.id);assert.deepEqual(prev.rect,s.rect);assert.equal(prev.entrance,s.entrance);}
 }
 // Slab above each flight opens over the flights, keeping the entrance landing solid.
 const up=d.floors[i+1];for(const s of f.stairs){const [x0,y0,x1,y1]=s.hole,c=[(x0+x1)/2,(y0+y1)/2];assert(!up.slab.some(([o,...holes])=>ringDistance(c[0],c[1],o)===0&&!holes.some(h=>ringDistance(c[0],c[1],h)===0)),'stair hole in '+up.label);}
}
assert(treads>500&&doors>150,JSON.stringify({treads,doors}));
console.log('PASS: Zhili B1–8F empty-room interior, stacked four-core stairwells reaching every floor, stair openings, doors for numbered rooms',{treads,doors});
