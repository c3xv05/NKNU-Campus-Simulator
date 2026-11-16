import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHepingWorld} from '../heping-world.js';
const d=JSON.parse(readFileSync(new URL('../campuses/heping/campus.json',import.meta.url))),world=createHepingWorld(d);
assert.equal(d.id,'heping');assert(d.buildings.length>=19);assert.equal(d.excludedSchool,179137001);
for(const place of [{name:'spawn',position:d.spawn},...d.places])for(const radius of [.35,.8])assert(!world.blocked(...place.position,radius),`${place.name}: safe arrival ${radius}`);
for(const building of d.buildings){const t=building.ring[0];assert(world.blocked(...t,.35));}
assert(world.blocked(9999,9999));
// A long attempted move cannot pass through a solid footprint.
for(const b of d.buildings){const zs=b.ring.map(p=>p[1]),xs=b.ring.map(p=>p[0]),z=(Math.min(...zs)+Math.max(...zs))/2,p={x:Math.min(...xs)-2,z};if(!world.blocked(p.x,p.z)){world.move(p,Math.max(...xs)-p.x+2,0);assert(!world.blocked(p.x,p.z));}}
console.log('PASS: separate Heping data, safe walk/ride arrivals, footprint/boundary collisions, substep movement');
