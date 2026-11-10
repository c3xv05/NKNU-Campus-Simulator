import assert from 'node:assert/strict';import fs from 'node:fs';
import {createTerrain,ringDistance} from '../terrain.js';import {createRoadNetwork} from '../roads.js';
import {lakeAt,inLake,bridgeHeight,sidewalkSections} from '../site-physics.js';import {stepScooter,MAX_SCOOTER_SPEED,findDestinations} from '../travel.js';import {entranceBed} from '../landscape.js';
const c=JSON.parse(fs.readFileSync(new URL('../data/campus.json',import.meta.url))),g=JSON.parse(fs.readFileSync(new URL('../data/elevation.json',import.meta.url))),tags=JSON.parse(fs.readFileSync(new URL('../data/road-tags.json',import.meta.url)));
const t=createTerrain(g,[...c.places,...c.buildings,...c.courts,...c.water],{levelLink:c.levelLink}),n=createRoadNetwork(c.roads,t.rawHeight,tags);
const zhili=c.places.find(a=>a.name==='致理大樓'),gauss=c.places.find(a=>a.name==='高斯大樓');
assert(Math.abs(t.platformHeight(zhili)-t.platformHeight(gauss)-3.6)<1e-8,'Zhili 1F must align with Gauss 2F');
const link=c.levelLink,level=t.platformHeight(zhili),mid=link.line[0].map((v,i)=>(v+link.line[1][i])/2);
assert.equal(bridgeHeight(...mid,level,link,level),level+.08);assert.equal(bridgeHeight(...mid,level-3.6,link,level),null,'Walking under a bridge must not snap up a storey');
for(const building of c.places.filter(a=>['科技大樓','生科 A 館','生科 B 館','致理大樓','高斯大樓','寰宇大樓','圖資大樓'].includes(a.name))){assert(building.floors>=5);assert.equal(building.height,building.floors*building.floorHeight);}
assert(c.buildings.some(a=>a.name==='詠絮樓'&&a.ring.every(p=>p[1]<0)));
const facilityRows=[c.courts.find(a=>a.sport==='volleyball'),c.buildings.find(a=>a.osm===444902480),c.courts.find(a=>a.sport==='tennis'),c.courts.find(a=>a.sport==='basketball')].map(a=>({name:a.name,z:a.ring.reduce((s,p)=>s+p[1],0)/a.ring.length}));
assert(facilityRows.every((a,i)=>!i||a.z>facilityRows[i-1].z));assert(c.courts.every(a=>a.covered&&a.canopyHeight>=7));
assert.equal(MAX_SCOOTER_SPEED*3.6,75);const state={speed:0,heading:0};for(let i=0;i<300;i++)stepScooter(state,.05,1,0,true);assert(Math.abs(state.speed*3.6-75)<1e-8);for(let i=0;i<300;i++)stepScooter(state,.05,1,0,true);assert(state.speed<=MAX_SCOOTER_SPEED);
for(const lake of c.water){assert.equal(lake.kind,'lake');const x=lake.ring.reduce((s,p)=>s+p[0],0)/lake.ring.length,z=lake.ring.reduce((s,p)=>s+p[1],0)/lake.ring.length;if(inLake(x,z,lake)){assert(lakeAt(x,z,c));assert(t.height(x,z)<t.platformHeight(lake)-.2,'Lake must have a basin below its water level');}}
const sidewalks=sidewalkSections(c,n);assert(sidewalks.length>200);for(const id of [399030880,399030881,293423728,382869349,293423729])assert(sidewalks.some(s=>s.road===id));
for(const s of sidewalks){assert(s.points.length>=3);const x=s.points.reduce((t,p)=>t+p[0],0)/s.points.length,z=s.points.reduce((t,p)=>t+p[1],0)/s.points.length;const r=n.nearest(x,z,true);assert(!r||r.d>=r.width/2-.015,'Sidewalk intrudes onto a vehicle lane');}
// Entrance road inner edges follow the flowerbed, rather than leaving a grass strip.
for(const id of [218881805,293423732]){const road=c.roads.find(r=>r.osm===id);const distances=road.line.filter(p=>p[1]<520&&p[1]>483).map(([x,z])=>ringDistance(x,z,entranceBed()));assert(distances.every(d=>d>3.35&&d<3.95));}
// Detect steps at road overlaps and shoulders in both directions, not just at centres.
let largest=0;for(const s of n.segments.filter(s=>!s.route.style.path))for(const side of [-.4,0,.4]){const x=(s.a.x+s.b.x)/2-s.dz/s.length*s.width*side,z=(s.a.z+s.b.z)/2+s.dx/s.length*s.width*side;largest=Math.max(largest,Math.abs(n.surfaceHeight(x+.002,z)-n.surfaceHeight(x-.002,z)),Math.abs(n.surfaceHeight(x,z+.002)-n.surfaceHeight(x,z-.002)));}
assert(largest<.04,'Road slope has a discontinuous step');
console.log('PASS: connected building levels, 5+ storeys, named dorm, ordered covered courts, 75 km/h cap, real lake basins, attached sidewalks, entrance road/flowerbed contact and continuous road surfaces');console.log({largestFourMillimetreHeightChange:largest,sidewalkSections:sidewalks.length,facilityRows});
