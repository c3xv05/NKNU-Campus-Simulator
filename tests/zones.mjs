import assert from 'node:assert/strict';
import fs from 'node:fs';
import {zones} from '../zones.js';
import {ringDistance} from '../terrain.js';
const campus=JSON.parse(fs.readFileSync(new URL('../data/campus.json',import.meta.url)));
assert.equal(zones.length,12);
assert.equal(new Set(zones.map(z=>z.id)).size,12);
for(const zone of zones){
 const [w,n,e,s]=zone.box,[x,z]=zone.label;
 assert(w<e&&n<s);assert(x>w&&x<e&&z>n&&z<s,`${zone.id} label outside its sector`);
 assert.equal(ringDistance(x,z,campus.boundary),0,`${zone.id} label outside campus`);
}
// Each interior location gets exactly one sector, without holes or overlap.
for(let z=-560;z<550;z+=11)for(let x=-435;x<445;x+=13){
 if(ringDistance(x,z,campus.boundary)>0)continue;
 assert.equal(zones.filter(q=>{const[w,n,e,s]=q.box;return x>=w&&x<e&&z>=n&&z<s;}).length,1,`Coverage at ${x},${z}`);
}
console.log('PASS: 12 unique sectors, labels inside campus, complete non-overlapping campus coverage');
