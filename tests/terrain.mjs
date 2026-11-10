import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {sampleElevation,createTerrain} from '../terrain.js';
const grid=JSON.parse(fs.readFileSync(new URL('../data/elevation.json',import.meta.url)));
const html=fs.readFileSync(new URL('../index.html',import.meta.url),'utf8');
const campus=vm.runInNewContext('('+html.split('const campus = ')[1].split('\n};')[0]+'\n})');
assert.equal(grid.heights.length,grid.rows*grid.columns);
assert(grid.heights.every(h=>Number.isFinite(h)&&h>0&&h<300));
// Survey of the real campus footprint must have meaningful topographic relief.
const footprintElevations=campus.boundary.map(([x,z])=>sampleElevation(grid,x,z));
assert(Math.max(...footprintElevations)-Math.min(...footprintElevations)>40);
const terrain=createTerrain(grid,[...campus.places,...campus.buildings,...campus.courts,...campus.water]);
assert(terrain.datum>40&&terrain.datum<100);
// Exact node heights must match rendered mesh; all campus points must be covered.
const m=terrain.mesh;
for(const [x,z] of campus.boundary){assert(x>=m.west&&x<=m.west+(m.columns-1)*m.step);assert(z>=m.north&&z<=m.north+(m.rows-1)*m.step);}
for(let r=0;r<m.rows;r+=7)for(let c=0;c<m.columns;c+=7)
 assert.equal(terrain.height(m.west+c*m.step,m.north+r*m.step),m.heights[r*m.columns+c]);
// Continuity across grid edges and diagonals: movement cannot cause height jumps.
let maxJump=0;
for(let z=-500;z<530;z+=17)for(let x=-410;x<430;x+=19){
 const h=terrain.height(x,z);assert(Number.isFinite(h));
 for(const [dx,dz] of [[.001,0],[0,.001]])maxJump=Math.max(maxJump,Math.abs(h-terrain.height(x+dx,z+dz)));
}
assert(maxJump<.02,`Unexpected terrain discontinuity ${maxJump}`);
// The running track and its inner field must form one playable flat platform.
const track=campus.places.find(p=>p.name==='操場');
const trackHeights=track.holes[0].map(([x,z])=>terrain.height(x,z));
assert(Math.max(...trackHeights)-Math.min(...trackHeights)<.01);
console.log('PASS: source data coverage, campus relief, mesh/physics agreement, continuous interpolation and flat sports field');
console.log(`Satellite campus boundary elevation range: ${Math.min(...footprintElevations).toFixed(1)}–${Math.max(...footprintElevations).toFixed(1)} m; gate datum ${terrain.datum.toFixed(1)} m`);
