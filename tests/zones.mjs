import assert from 'node:assert/strict';import fs from 'node:fs';import {zones} from '../zones.js';import {ringDistance} from '../terrain.js';
const c=JSON.parse(fs.readFileSync(new URL('../data/campus.json',import.meta.url))),inside=(x,z,p)=>ringDistance(x,z,p.ring)===0&&!(p.holes||[]).some(h=>ringDistance(x,z,h)===0);
assert.equal(zones.length,12);assert.equal(new Set(zones.map(z=>z.id)).size,12);
for(const z of zones){assert(/^R\d{2}$/.test(z.id));assert(!z.box,'New regions must be polygons, not a rectangular grid');assert(z.ring.length>=3);assert(inside(...z.label,z),z.id+' label is outside its road-bounded polygon');assert.equal(ringDistance(...z.label,c.boundary),0);assert.equal(z.status,'unconfirmed');for(const id of z.roadIds)assert(c.roads.some(r=>r.osm===id));}
let samples=0;for(let z=-540;z<530;z+=9)for(let x=-410;x<425;x+=11){const found=zones.filter(p=>inside(x,z,p));assert(found.length<=1,'Regions overlap');if(found.length)samples++;}assert(samples>2000);
console.log('PASS: 12 unique road-bounded polygon regions, interior labels, no rectangular boxes, non-overlap and no inherited A1-D3 answers');
