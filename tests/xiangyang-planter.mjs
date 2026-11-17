import assert from 'node:assert/strict';import fs from 'node:fs';import {createTerrain,ringDistance} from '../terrain.js';import {createRoadNetwork} from '../roads.js';import {motorPavementPlan} from '../data/motor-pavement-plan.js';import {gradeCampusCorridors} from '../facilities/campus-corridors/surface.js';import {gradeTeachingAccess} from '../teaching-access-ground.js';import {createXiangyangPlanter} from '../facilities/xiangyang-planter/surface.js';
// Same terrain/road pipeline as index.html.
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url))),c=read('data/campus.json'),t=createTerrain(read('data/elevation.json'),[...c.places,...c.buildings,...c.courts,...c.water],{levelLink:c.levelLink,courtyard:c.courtyard,bioConnection:c.bioConnection});
const n=createRoadNetwork(c.roads,t.rawHeight,read('data/road-tags.json'),{apron:c.entranceApron,pavedAreas:c.pavedAreas,junctionFillets:c.junctionFillets,sharedGradeGrid:true,edgePavement:motorPavementPlan.infillTriangles,gradeObstacles:[...c.places,...c.buildings].filter(a=>a.height)});
n.gradeTerrain(t.mesh,[...c.places.filter(a=>!a.height),...c.water,...c.courts].map(a=>{const xs=a.ring.map(p=>p[0]),zs=a.ring.map(p=>p[1]);return{west:Math.min(...xs),east:Math.max(...xs),north:Math.min(...zs),south:Math.max(...zs),contains:(x,z)=>ringDistance(x,z,a.ring)===0};}));gradeCampusCorridors(t,c,n);gradeTeachingAccess(t,c,n);
const p=createXiangyangPlanter(c,n,t),S=p.stations,cfg=p.config;assert(S.length>100,'Planter must cover the Xiangyang stretch');assert.equal(S[0].station,cfg.from);assert.equal(S.at(-1).station,cfg.to);
const courts=[...c.places,...c.buildings,...c.courts];
for(const q of S){const [nx,nz]=q.normal;
 // No railing at the road edge: the road edge itself must stay open (only the curb).
 assert(!p.blocked(q.inner[0]-nx*.4,q.inner[1]-nz*.4,.3),'Road edge must not be blocked');
 // Planter is level with the road (curb then grass) and walkable.
 assert(Math.abs(p.heightAt(q.inner[0]+nx*.05,q.inner[1]+nz*.05)-(q.road+cfg.curbAbove))<.01,'Curb height');
 const mid=q.width/2;assert(Math.abs(p.heightAt(q.inner[0]+nx*mid,q.inner[1]+nz*mid)-(q.road+cfg.grassAbove))<.02,'Grass bed must sit just above road level');
 assert(q.width>=cfg.minWidth&&q.width<6,'Planter width');
 // Wall stands at the court/building edge, reaches below court level, and carries the fence above road level.
 for(const a of courts)for(const e of [q.inner,q.wallIn])assert(ringDistance(...e,a.ring)>0,'Planter/wall must stay outside courts and buildings');
 assert(q.wallBottom<q.courtSide,'Wall must reach below court-side ground');assert(q.wallTop>q.road&&q.wallTop-q.road<.3,'Wall top at road level');assert(Math.abs(q.fenceTop-q.wallTop-cfg.fenceHeight)<1e-9);
 assert(p.blocked(...q.wallIn,.3),'Fence must stop walkers at the court edge');}
const known=S.filter(q=>courts.some(a=>{const [nx,nz]=q.normal,d=q.width+cfg.courtGap+.2;return ringDistance(q.inner[0]+nx*d,q.inner[1]+nz*d,a.ring)===0;})).length;assert(known/S.length>.6,'Wall must follow the court/building edge');
const route=n.routes.find(r=>r.osm===cfg.road);for(const q of route.points)assert(!p.blocked(q.x,q.z,.3),'Road centre must stay open');
console.log('PASS: Xiangyang east planter is road-level grass with curb, no road-edge railing, wall at the court edge with chain-link above road level',{stations:S.length,width:[Math.min(...S.map(q=>q.width)),Math.max(...S.map(q=>q.width))].map(v=>+v.toFixed(2)),followsEdge:known});
