import assert from 'node:assert/strict';
import fs from 'node:fs';
import {ringDistance,prepareRingContains} from '../planar.js';
import {roadRegions} from '../data/road-regions.js';
import {r04Vegetation} from '../data/r04-vegetation.js';
const campus=JSON.parse(fs.readFileSync(new URL('../data/campus.json',import.meta.url)));
const rings=[[],[[1,1]],[[0,0],[10,0],[10,10],[5,3],[0,10]],
 ...roadRegions.filter(r=>['R02','R09'].includes(r.id)).flatMap(r=>[r.ring,...r.holes||[]]),
 ...r04Vegetation.regions.flatMap(r=>r.regions.flat()),
 ...campus.junctionFillets.map(a=>a.ring),...campus.pavedAreas.map(a=>a.ring),campus.entranceApron.ring,...campus.entranceApron.holes||[]];
let seed=1821,samples=0;const random=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
for(const ring of rings){
 const contains=prepareRingContains(ring),check=(x,z)=>{assert.equal(contains(x,z),ringDistance(x,z,ring)===0,`containment at ${x},${z} (${ring.length} edges)`);samples++;};
 if(!ring.length){check(0,0);continue;}
 const xs=ring.map(p=>p[0]),zs=ring.map(p=>p[1]),w=Math.min(...xs),e=Math.max(...xs),n=Math.min(...zs),s=Math.max(...zs);
 for(let i=0;i<ring.length;i++){const a=ring[i],b=ring[(i+1)%ring.length],x=(a[0]+b[0])/2,z=(a[1]+b[1])/2;check(...a);check(x,z);check(x+1e-7,z-1e-7);check(x-1e-7,z+1e-7);}
 for(let i=0;i<350;i++)check(w-1+random()*(e-w+2),n-1+random()*(s-n+2));
 for(let k=0;k<=256;k++){const z=n+(s-n)*k/256;check(w+(e-w)*.37,z);}
}
console.log('PASS: indexed containment matches original distance==0 across random points, vertices, edges, band boundaries, concave polygons and holes', {rings:rings.length,samples});
