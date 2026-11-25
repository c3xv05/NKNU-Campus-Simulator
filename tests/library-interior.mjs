// 圖資大樓 (user floor plans 2026-11-25): walkable B1/1F, fan plaza, stairs. Walks real collision/support along
// routes given in drawing metres (scripts/library_drawing.py frame) and checks the data contract.
import fs from 'node:fs';import assert from 'node:assert/strict';import {createTerrain} from '../terrain.js';
import {createLibrarySurface,LIBRARY_OSM} from '../buildings/library/interior.js';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url))),c=read('data/campus.json'),d=read('buildings/library/interior.json');
const t=createTerrain(read('data/elevation.json'),[...c.places,...c.buildings,...c.water,...c.courts],{levelLink:c.levelLink,courtyard:c.courtyard,bioConnection:c.bioConnection});
const lib=[...c.places,...c.buildings].find(b=>b.osm===LIBRARY_OSM),base=t.platformHeight(lib);
// B1 floor sits on the building's own terrain pad; 1F (entrance level) is 4.5 m higher; nothing above.
assert(Math.abs(base-d.base)<.01,`pad ${base} vs B1 ${d.base}`);assert.equal(d.floorHeight,4.5);assert.deepEqual(d.floors.map(f=>f.label),['B1','1F']);
assert(lib.terrainRing&&lib.beforeRelocationRing&&lib.platformAnchor,'relocation keeps the old ring and its own pad');
// Room numbers only (user: no names): every drawn number of both sheets is present.
const nums=new Set(d.labels.map(l=>l.n));for(let n=101;n<=161;n++)if(![103,145,151].includes(n))assert(nums.has(String(n)),'missing '+n);for(let n=201;n<=251;n++)assert(nums.has(String(n)),'missing '+n);
// Ground cuts are convex pieces (road-ground.js subtracts convex footprints only).
for(const tri of d.site.cuts)assert.equal(tri.length,3);
c.libraryInterior=d;const s=createLibrarySurface(c,t);
const T=d.transform,W=(x,y)=>[T.a*x-T.b*y+T.tx,T.b*x+T.a*y+T.tz];
function route(name,start,y0,moves,expectEnd){
 let [x,y]=start,[wx,wz]=W(x,y),h=s.supportAt(wx,wz,y0);assert(h!==null,name+': no floor at start');
 for(const[dx,dy]of moves){const L=Math.hypot(dx,dy),n=Math.ceil(L/.2);for(let i=0;i<n;i++){x+=dx/n;y+=dy/n;[wx,wz]=W(x,y);
  assert(!s.blocked(wx,wz,.35,h),`${name}: blocked at drawing (${x.toFixed(2)},${y.toFixed(2)}) y ${h.toFixed(2)}`);
  const g=s.supportAt(wx,wz,h);assert(g!==null,`${name}: no support at (${x.toFixed(2)},${y.toFixed(2)})`);assert(g-h<=.46,`${name}: step too high`);h=g;}}
 if(expectEnd!==null)assert(Math.abs(h-(base+expectEnd))<.1,`${name}: ends at ${(h-base).toFixed(2)} m, expected ${expectEnd}`);return h;
}
const top=d.prisms&&s.supportAt(...W(9.0,88.8),base+8);   // S04 side of the fan
// S04 sidewalk side -> 202 steps -> 203 -> 204 plaza -> 218 main entrance -> lobby (1F).
route('fan to lobby',[9.4,88.8],top,[[25,0],[0,-3.6],[12,0]],4.5);
// Lobby -> C stair north flight -> landing -> central flight -> B1 hall 126.
route('C stair',[46,85.2],base+4.5,[[7.5,0],[1,0],[0,2.6],[-8,0],[-4,0]],0);
// B1 corridor 133 -> lobby 132 -> D stair up -> 1F lobby 222.
route('D stair',[44.5,72.0],base,[[-2.6,0],[0,-6.3],[-1.6,0],[0,5.2],[0,1.2]],4.5);
// Half-open 125 under the plaza -> B1 lobby 126 through the west glazing door.
route('125 to 126',[30,85.2],base,[[11,0]],0);
// Voids: 1F floor stops at the atrium / wing voids (balustrade), B1 below.
assert.equal(s.blocked(...W(61.3,90),.35,base+4.5),true,'atrium balustrade beside the bridge');assert.equal(s.blocked(...W(62.2,90),.35,base+4.5),false,'bridge across the atrium');
assert(Math.abs(s.supportAt(...W(52,116),base+4.6)-base-.02)<.05,'wing void opens to B1');
// The ㄇ wall's middle is a beam over the plaza: walkers pass under it, its legs block.
assert.equal(s.blocked(...W(34.3,90),.35,base+4.5),false,'pass under the ㄇ beam');
// G/H stairs: from the approach walk at the S04 side all the way down to the B1 ground by the fan corners.
for(const[name,a0,a1,b1]of[['H',[24.09,73.58],[14.76,66.50],[15.95,64.93]],['G',[21.01,91.50],[9.86,95.06],[10.51,97.13]]]){const L=Math.hypot(a1[0]-a0[0],a1[1]-a0[1]),u=[(a1[0]-a0[0])/L,(a1[1]-a0[1])/L],st=[(a1[0]+b1[0])/2+u[0],(a1[1]+b1[1])/2+u[1]];{let h=base+9;const end=route(name+' stair down',st,h,[[-u[0]*(L+1.5),-u[1]*(L+1.5)]],null);assert(end-base<.5,name+' stair reaches the bottom treads');}}
// Iron rolling doors (double line with a dashed middle, user 2026-11-25) are open passages, not walls.
route('2F shutters 236',[58,75],base+4.5,[[0,-4.5]],4.5);
route('2F shutter 221/233',[50.5,82],base+4.5,[[0,-3.5]],4.5);
console.log(JSON.stringify({result:'PASS',base:+base.toFixed(2),prisms:d.prisms.length,walks:d.walks.length,labels:d.labels.length}));
