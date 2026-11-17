import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createTerrain,ringDistance} from '../terrain.js';
import {createRoadNetwork} from '../roads.js';
import {createCampusCorridors,gradeCampusCorridors,corridorSupportAt} from '../facilities/campus-corridors/surface.js';
import {gradeTeachingAccess} from '../teaching-access-ground.js';
import {findBuildingDestinations} from '../travel.js';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url))),c=read('data/campus.json'),t=createTerrain(read('data/elevation.json'),[...c.places,...c.buildings,...c.courts,...c.water],c),n=createRoadNetwork(c.roads,t.rawHeight,read('data/road-tags.json'),{pavedAreas:c.pavedAreas,apron:c.entranceApron,junctionFillets:c.junctionFillets,sharedGradeGrid:true}),s=createCampusCorridors(c,t,n);
assert.equal(s.approaches.find(a=>a.id==='courtyard-s32').level,s.lower);assert.equal(c.bioConnection.corridor.roof,false);assert.equal(s.approaches.find(a=>a.id==='biology-s05').width,12);assert.equal(s.bioFloors.length,2);assert(Math.abs(s.bioFloors[1].level-s.bioFloors[0].level-3.6)<1e-9);
let vertices=0,maxProfileError=0,maxGrade=0;
for(const a of s.approaches){
 for(let i=0;i<a.vertices.length;i+=9){const p=a.vertices.slice(i,i+9),x=(p[0]+p[3]+p[6])/3,z=(p[2]+p[5]+p[8])/3,h=(p[1]+p[4]+p[7])/3;assert(Math.abs(a.heightAt(x,z)-h)<.0001);assert.equal(corridorSupportAt(x,z,h-4,c,t,n),null,'No snapping up from a lower floor');maxProfileError=Math.max(maxProfileError,Math.abs(a.profile(x,z)-h));vertices++;}
 // Continuous centre-line slope all the way to the level deck, including its last triangle.
 let previous=null;for(let i=1;i<a.line.length;i++){const p=a.line[i-1],q=a.line[i],length=Math.hypot(q[0]-p[0],q[1]-p[1]),steps=Math.ceil(length/.02);for(let j=0;j<=steps;j++){const u=j/steps,x=p[0]+(q[0]-p[0])*u,z=p[1]+(q[1]-p[1])*u,h=a.heightAt(x,z)??a.profile(x,z);if(h!==null&&previous&&Math.hypot(x-previous.x,z-previous.z)>1e-5){const grade=Math.abs(h-previous.h)/Math.hypot(x-previous.x,z-previous.z);maxGrade=Math.max(maxGrade,grade);assert(grade<.19,JSON.stringify({id:a.id,x,z,grade}));}previous={x,z,h};}}
}
assert(maxProfileError<.025,'Surface tessellation must follow the smooth profile');
const heights=n.routes.flatMap(r=>r.points.map(p=>n.surfaceHeight(p.x,p.z))),bases=c.places.map(b=>t.platformHeight(b));n.gradeTerrain(t.mesh);const priorGround=Array.from(t.mesh.heights);assert(gradeCampusCorridors(t,c,n)>0);gradeTeachingAccess(t,c,n);assert.deepEqual(c.places.map(b=>t.platformHeight(b)),bases);assert.deepEqual(n.routes.flatMap(r=>r.points.map(p=>n.surfaceHeight(p.x,p.z))),heights);
let revertedInteriorSamples=0;for(let i=0;i<t.mesh.heights.length;i++){const x=t.mesh.west+(i%t.mesh.columns)*t.mesh.step,z=t.mesh.north+Math.floor(i/t.mesh.columns)*t.mesh.step;if(x>=-155&&x<=-135&&z>=-235&&z<=-205&&ringDistance(x,z,c.courtyard.ring)===0){assert.equal(t.mesh.heights[i],priorGround[i],'No blanket interior flattening');revertedInteriorSamples++;}}assert(revertedInteriorSamples>15);
const d=findBuildingDestinations(c,n,read('buildings/catalog.json')).find(d=>d.osm===444867692);assert.equal(n.nearest(d.x,d.z,true).segment.route.osm,218881800);assert(Math.hypot(d.x+87.57351,d.z+192.089336)<13);
console.log('PASS: shared smooth ramp mesh/support, no floor snapping, fixed road grades/building bases, local ground blend and Gauss S05 entrance',{vertices,maxProfileError,maxGrade});

const landing=s.approaches.find(a=>a.id==='biology-east-landing');assert.equal(landing.level,s.bioLower);assert.equal(c.bioConnection.stairs.steps,32);for(let i=0;i<landing.vertices.length;i+=3)assert(Math.abs(landing.vertices[i+1]-s.bioLower)<.00001,'The complete pre-stair rectangle must stay horizontal at 1F');
