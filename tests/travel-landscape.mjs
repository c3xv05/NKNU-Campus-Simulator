import assert from 'node:assert/strict';import fs from 'node:fs';
import {createTerrain,ringDistance} from '../terrain.js';import {createRoadNetwork} from '../roads.js';
import {findDestinations,stepScooter,MAX_SCOOTER_SPEED} from '../travel.js';import {createLandscapeLayout,entranceBed} from '../landscape.js';import {coverAt,landcover} from '../landcover.js';
const c=JSON.parse(fs.readFileSync(new URL('../data/campus.json',import.meta.url))),g=JSON.parse(fs.readFileSync(new URL('../data/elevation.json',import.meta.url))),tags=JSON.parse(fs.readFileSync(new URL('../data/road-tags.json',import.meta.url)));
const areas=[...c.places,...c.buildings,...c.courts,...c.water],terrain=createTerrain(g,areas),roads=createRoadNetwork(c.roads,terrain.height,tags),height=(x,z)=>roads.walkHeight(x,z,terrain.height(x,z));
const destinations=findDestinations(c,roads);assert.deepEqual(destinations.map(d=>d.label),['大門','歸燕食巢','致理大樓']);
for(const d of destinations){assert(roads.onMotorRoad(d.x,d.z));assert(!areas.filter(a=>a.height).some(a=>ringDistance(d.x,d.z,a.ring)<2.5));}
for(const [id,name] of [['canteen','歸燕食巢'],['zhili','致理大樓']]){const d=destinations.find(d=>d.id===id),p=c.places.find(p=>p.name===name);assert(ringDistance(d.x,d.z,p.ring)<19,'Teleport must arrive within interaction range');}
const state={speed:0,heading:0};for(let i=0;i<100;i++)stepScooter(state,.05,1,0,true);assert(state.speed<=MAX_SCOOTER_SPEED&&state.speed>MAX_SCOOTER_SPEED-1);const start=state.heading;stepScooter(state,.05,1,1);assert(state.heading<start);for(let i=0;i<120;i++)stepScooter(state,.05,0,0);assert.equal(state.speed,0);const stoppedHeading=state.heading;stepScooter(state,.05,0,1);assert(state.heading<stoppedHeading,'Scooter must allow steering at a stop');
assert.equal(coverAt(-330,310),'forest');assert.equal(coverAt(-160,340),'flowers');assert.equal(coverAt(155,-310),'weeds');assert.equal(coverAt(-125,-390),'forest');assert.equal(coverAt(-125,-180),'weeds');assert.equal(coverAt(40,75),'unknown');
const layout=createLandscapeLayout(c,roads,height);assert(layout.trees.length>300);assert(layout.flowers.length>1000);assert(layout.weeds.length>100);assert(layout.wall.length>20);
for(const t of layout.trees){assert.equal(coverAt(t.x,t.z),'forest');assert(!areas.some(a=>ringDistance(t.x,t.z,a.ring)<3));const r=roads.nearest(t.x,t.z);assert(!r||r.d>=r.width/2+3);}
for(const d of destinations)assert(!layout.blocked(d.x,d.z,.8),'Teleport obstructed by vegetation or wall');
const bed=entranceBed(),south=bed.reduce((a,b)=>a[1]>b[1]?a:b);assert.equal(south[1],519);assert(Math.abs(south[0]+267.5)<1e-8);assert(ringDistance(-267.5,495,bed)===0);
console.log('PASS: safe/nearby teleports, scooter acceleration/braking/steering, confirmed vegetation, no road/building tree overlap, retaining wall and south-pointing flowerbed');
console.log({trees:layout.trees.length,flowers:layout.flowers.length,weeds:layout.weeds.length,wallSections:layout.wall.length,destinations});
