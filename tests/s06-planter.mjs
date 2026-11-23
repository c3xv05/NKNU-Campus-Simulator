import assert from 'node:assert/strict';import fs from 'node:fs';import {createTerrain,ringDistance} from '../terrain.js';import {createRoadNetwork} from '../roads.js';import {motorPavementPlan} from '../data/motor-pavement-plan.js';import {sidewalkPlan} from '../data/sidewalk-plan.js';import {createSidewalkSurface} from '../sidewalk-surface.js';import {routeSections} from '../pavement.js';import {createS06Planter} from '../facilities/s06-planter/surface.js';import {s06Planter as cfg,setbackPair} from '../facilities/s06-planter/layout.js';import {SIDEWALK_WIDTH,SIDEWALK_RISE,ROAD_SURFACE_LIFT} from '../sidewalk-layout.js';
// Same terrain/road pipeline as index.html (ungraded extras are not needed for this check).
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url))),c=read('data/campus.json'),t=createTerrain(read('data/elevation.json'),[...c.places,...c.buildings,...c.courts,...c.water],{levelLink:c.levelLink,courtyard:c.courtyard,bioConnection:c.bioConnection});
const n=createRoadNetwork(c.roads,t.rawHeight,read('data/road-tags.json'),{apron:c.entranceApron,pavedAreas:c.pavedAreas,junctionFillets:c.junctionFillets,sharedGradeGrid:true,edgePavement:motorPavementPlan.infillTriangles,gradeObstacles:[...c.places,...c.buildings].filter(a=>a.height)});
const planter=createS06Planter(c,n),surface=createSidewalkSurface(n,sidewalkPlan,t.height);
const route=n.routes.find(r=>r.osm===cfg.road),nodes=routeSections(route);
assert(planter.pieces.length>20,'Planter pieces exist');
// Setback ramps in smoothly, holds 100 cm, and is zero outside the stretch.
assert.deepEqual(setbackPair(cfg.road,100,102),[0,0]);assert.deepEqual(setbackPair(cfg.road,cfg.from-1,cfg.from),[0,0]);
assert.equal(setbackPair(cfg.road,cfg.from+cfg.taper+5,cfg.from+cfg.taper+7)[0],cfg.width);assert.equal(setbackPair(cfg.road,cfg.to+10,cfg.to+12)[0],0);assert.equal(setbackPair(1,200,202)[0],0);
let previous=0;for(let d=cfg.from;d<=cfg.from+cfg.taper;d+=.25){const s=setbackPair(cfg.road,d,d)[0];assert(s>=previous-1e-12&&s-previous<.1,'Ease is gradual');previous=s;}
// Cross sections: grass spans road edge -> walkway edge, walkway keeps 3.6 m.
const across=(p,q)=>{const near=n.nearest(...p,true);return near?near.d-near.width/2:null;};
for(const d of [200,215,230,250,270]){const i=nodes.findIndex(s=>s.distance>=d),a=nodes[i],side=cfg.side,at=o=>[a.x+a.nx*side*(a.width/2+o),a.z+a.nz*side*(a.width/2+o)];
 assert(planter.heightAt(...at(cfg.width/2))!==null,'Grass at 15 cm @'+d);assert.equal(planter.heightAt(...at(cfg.width+.15)),null,'No grass under walkway @'+d);
 const walk=surface.heightAt(...at(cfg.width+.15)),curbSide=surface.heightAt(...at(cfg.width-.1));assert(walk!==null&&curbSide===null,'Walkway starts at the setback @'+d);
 assert(surface.heightAt(...at(cfg.width+SIDEWALK_WIDTH-.05))!==null&&surface.heightAt(...at(cfg.width+SIDEWALK_WIDTH+.1))===null,'Walkway stays 3.6 m wide @'+d);
 const top=planter.heightAt(...at(cfg.width/2));assert(Math.abs(top-(n.surfaceHeight(...at(cfg.width/2))+ROAD_SURFACE_LIFT+cfg.rise))<1e-9);
 assert(walk-top>.02&&walk-top<.08,'Walkway curb face 2-8 cm above the grass');
 // Rendered walkway and walking height agree and the terrain beside the outer edge stays within the old tolerance.
 const outer=at(cfg.width+SIDEWALK_WIDTH+.3);assert(Math.abs(t.height(...outer)-walk)<2.5,'Terrain beside the walkway edge is continuous');}
// Planter never overlaps asphalt or the walkway.
for(const piece of planter.pieces)for(const p of piece){const r=n.nearest(p[0],p[1],true);assert(r.d>=r.width/2-.03,'Planter outside asphalt');assert(r.d<=r.width/2+cfg.width+.03,'Planter at most 100 cm wide');}
assert(planter.lips.length>20,'Road-side lip');
console.log('PASS: S06 planter 100 cm grass strip between road and set-back walkway',{pieces:planter.pieces.length,lips:planter.lips.length});
