import assert from 'node:assert/strict';import fs from 'node:fs';
import {createTerrain,ringDistance} from '../terrain.js';import {createRoadNetwork} from '../roads.js';import {sidewalkSections,platformHeightAt} from '../site-physics.js';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url))),c=read('data/campus.json'),profiles=read('buildings/catalog.json'),grid=read('data/elevation.json');
const all=[...c.places,...c.buildings].filter(a=>a.height);assert.equal(Object.keys(profiles).length,all.length);
for(const a of all){const p=profiles[a.osm];assert(p);const own=read('buildings/'+p.id+'/building.json');assert.deepEqual(own.geometry,a);assert.deepEqual(own.appearance,p);}
for(const [name,style] of [['生科 A 館','biology'],['生科 B 館','biology'],['致理大樓','brick-frame'],['高斯大樓','brick-frame'],['歸燕食巢','canteen'],['霽遠樓','foresight']])assert.equal(profiles[c.places.find(a=>a.name===name).osm].style,style);
const t=createTerrain(grid,[...c.places,...c.buildings,...c.courts,...c.water],{levelLink:c.levelLink,courtyard:c.courtyard,bioConnection:c.bioConnection});
assert.equal(t.platformHeight(c.places.find(p=>p.osm===c.bioConnection.from)),t.platformHeight(c.places.find(p=>p.osm===c.bioConnection.to)));
const get=id=>t.platformHeight(c.places.find(p=>p.osm===id)),level=get(444867692)+7.2;
assert(Math.abs(level-get(444867693)-3.6)<1e-8);assert(Math.abs(level-get(444867694)-3.6)<1e-8);
assert.equal(platformHeightAt(-135,-210,level,c,t),level+.08);assert.equal(platformHeightAt(-135,-210,level-5,c,t),null);
const [a,b]=c.courtyard.ramp;assert(Math.abs(platformHeightAt(...b,level,c,t)-level)<1e-8);assert.equal(platformHeightAt(...a,0,c,t),t.height(...a));
assert.equal(c.gatehouse.center[1]-c.gatehouse.depth/2,Math.max(...c.flowerbed.ring.map(p=>p[1])),'Flowerbed tip must meet the guardhouse');
assert(c.gatehouse.gates[0][0]<c.gatehouse.center[0]-c.gatehouse.width/2);assert(c.gatehouse.gates[1][0]>c.gatehouse.center[0]+c.gatehouse.width/2);
const n=createRoadNetwork(c.roads,t.rawHeight,read('data/road-tags.json'));const sidewalks=sidewalkSections(c,n);
const bio=c.bioConnection,ra=bio.ramp[0],rb=bio.ramp[1],rl=Math.hypot(rb[0]-ra[0],rb[1]-ra[1]);for(const side of [-1,1]){const x=ra[0]-(rb[1]-ra[1])/rl*bio.accessWidth/2*side,z=ra[1]+(rb[0]-ra[0])/rl*bio.accessWidth/2*side;assert(!n.onMotorRoad(x,z),'Biology access ramp must start outside the carriageway');}

for(const s of sidewalks)for(let i=1;i<s.points.length-1;i++){const tri=[s.points[0],s.points[i],s.points[i+1]],x=tri.reduce((v,p)=>v+p[0]/3,0),z=tri.reduce((v,p)=>v+p[1]/3,0),r=n.nearest(x,z,true);assert(!r||r.d>=r.width/2-.015,'Sidewalk triangle covers a vehicle lane');}
// Same surface on both sides of pavement: no metre-high crack at a platform edge.
let worst=0;for(const s of n.segments.filter(s=>!s.route.style.path)){const x=(s.a.x+s.b.x)/2,z=(s.a.z+s.b.z)/2,nx=-s.dz/s.length,nz=s.dx/s.length;for(const side of [-1,1]){const edge=s.width/2*side,px=x+nx*edge,pz=z+nz*edge;assert(Math.abs(n.integratedHeight(px,pz,t.height(px,pz))-n.surfaceHeight(px,pz))<1e-8);const d=.004,h=n.walkHeight(px+nx*d,pz+nz*d,t.height(px+nx*d,pz+nz*d))-n.walkHeight(px-nx*d,pz-nz*d,t.height(px-nx*d,pz-nz*d));const sharedPlaza=n.siteLevelAt(px,pz)!==null;assert(Math.abs(h)<(sharedPlaza ? .17 : .04),'Unexpected seam exceeds the intentional 15cm plaza curb');if(!sharedPlaza)worst=Math.max(worst,Math.abs(h));}}
assert(worst<.04);console.log('PASS: independent building sources, photo facade styles, 3F/2F/2F shared platform, ramp access, guardhouse-flowerbed contact, separate gate lanes, clipped sidewalk triangles and continuous road/ground seam',{buildings:all.length,sidewalkPieces:sidewalks.length,maxSeamChange:worst});
