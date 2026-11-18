import assert from 'node:assert/strict';import fs from 'node:fs';
// Gauss (物理館) 1F–3F empty-room interior from the confirmed plan reading; 4F–7F solid with plan windows.
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url))),d=read('buildings/gauss/interior.json'),b=read('buildings/gauss/building.json'),c=read('data/campus.json');
assert.equal(b.appearance.interiorKind,'plan');assert.equal(b.appearance.interiorFile,'./buildings/gauss/interior.json');assert.equal(d.building,444867692);
assert.deepEqual(d.floors.map(f=>f.label),['1F','2F','3F']);assert(Math.abs(d.solidAbove.from-10.8)<1e-9&&Math.abs(d.solidAbove.to-25.2)<1e-9);assert.equal(d.signText,'高斯大樓');
for(const [i,f] of d.floors.entries()){assert(Math.abs(f.level-i*3.6)<1e-9);if(i===2){assert.equal(f.stairs.length,0);continue;}
 assert.deepEqual(f.stairs.map(s=>s.id).sort(),['丁梯','丙梯','乙梯','甲梯'].sort());
 for(const s of f.stairs){assert.equal(s.treads.length,23);assert(Math.abs(Math.max(...s.treads.map(t=>t.height))-3.6)<1e-3);}
 if(i===1){const below=d.floors[0].stairs;for(const s of f.stairs)assert.deepEqual(s.rect,below.find(q=>q.id===s.id).rect,'stacked stair cores');}}
assert.equal(d.floors[0].exits.filter(e=>e.manual).length,3,'east main, west entrance, west court');
assert.equal(d.floors[1].exits.filter(e=>e.manual).length,2,'two 2F doors onto the 接未來廣場 deck');
const rooms=d.floors.flatMap(f=>f.doors.filter(x=>/^\d{3}/.test(x.name)).map(x=>x.name));for(const n of ['101','102','105','106','107','108','109','110','201','202','203','204','205','206','207','301','302','303','304','305','306'])assert(rooms.some(r=>r.startsWith(n)),'door for '+n);
assert(c.courtyard.floorRegions.gaussCourt.length&&c.courtyard.floorRegions.gaussGarden.length);assert.equal(c.courtyard.gaussPodium.length,0);assert.equal(c.levelLink.insideGauss,true);
console.log('PASS: Gauss 1F–3F interior, stacked four stair cores, exterior/deck doors, court and garden at Gauss 1F, 4F–7F solid');
