import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRoadNetwork,roadStyle} from '../roads.js';
import {createTerrain,ringDistance} from '../terrain.js';
const noise=z=>20+.08*z+Math.sin(z*.7)*.5;
const synthetic=[{osm:1,width:7,line:[[0,0],[0,100],[0,200]]},{osm:2,width:7,line:[[-60,100],[0,100],[60,100]]}];
const network=createRoadNetwork(synthetic,(x,z)=>noise(z)+.25*x);
let rawRoughness=0,smoothRoughness=0;
for(let z=25;z<75;z+=2){
 rawRoughness+=Math.abs(noise(z-2)-2*noise(z)+noise(z+2));
 smoothRoughness+=Math.abs(network.surfaceHeight(0,z-2)-2*network.surfaceHeight(0,z)+network.surfaceHeight(0,z+2));
 assert(Math.abs(network.surfaceHeight(-2.8,z)-network.surfaceHeight(2.8,z))<1e-6,'Road cross-section must be level');
}
assert(smoothRoughness<rawRoughness*.2,'Grading must remove short wavelength bumps');
assert(network.surfaceHeight(0,190)-network.surfaceHeight(0,10)>10,'Uphill grade must remain');
for(const [x,z] of [[0,100],[3,100],[-3,100],[0,103],[0,97]])assert(Math.abs(network.surfaceHeight(x,z)-network.surfaceHeight(0,100))<.02,'Intersection apron heights disagree');
assert.equal(roadStyle({width:7},{oneway:'yes'}).center,false);
assert.equal(roadStyle({width:7},{oneway:'no'}).center,true);
assert.equal(roadStyle({width:7},{lanes:'1'}).center,false);
assert.equal(roadStyle({width:2},{highway:'footway'}).edges,false);
assert.equal(roadStyle({width:4.5},{highway:'service',oneway:'yes'}).oneWay,true);
assert.equal(network.walkHeight(0,50,0),network.surfaceHeight(0,50)+.06);
const campus=JSON.parse(fs.readFileSync(new URL('../data/campus.json',import.meta.url))),grid=JSON.parse(fs.readFileSync(new URL('../data/elevation.json',import.meta.url))),tags=JSON.parse(fs.readFileSync(new URL('../data/road-tags.json',import.meta.url)));
const areas=[...campus.places,...campus.buildings,...campus.water,...campus.courts];
const terrain=createTerrain(grid,areas),roads=createRoadNetwork(campus.roads,terrain.height,tags);
const protectedAreas=areas.map(area=>{const xs=area.ring.map(p=>p[0]),zs=area.ring.map(p=>p[1]);return{west:Math.min(...xs),east:Math.max(...xs),north:Math.min(...zs),south:Math.max(...zs),contains:(x,z)=>ringDistance(x,z,area.ring)===0};});
roads.gradeTerrain(terrain.mesh,protectedAreas);
assert.equal(roads.routes.length,campus.roads.length);
assert(roads.routes.some(r=>r.style.path));assert(roads.routes.some(r=>r.style.center));
assert.equal(roads.routes.find(r=>r.osm===218881805).style.oneWay,true);
assert(terrain.mesh.heights.every(Number.isFinite));
for(const segment of roads.segments){
 const x=(segment.a.x+segment.b.x)/2,z=(segment.a.z+segment.b.z)/2;
 assert(Number.isFinite(roads.surfaceHeight(x,z)));
 assert(Math.abs(roads.walkHeight(x,z,terrain.height(x,z))-roads.surfaceHeight(x,z)-.06)<1e-6,'Walking height does not match pavement');
}
const track=campus.places.find(p=>p.name==='操場'),field=track.holes[0].map(([x,z])=>terrain.height(x,z));
assert(Math.max(...field)-Math.min(...field)<.01,'Road grading must preserve the sports field');
console.log(`PASS: level cross-sections, ${Math.round((1-smoothRoughness/rawRoughness)*100)}% less synthetic bump noise, uphill grade retained, junction agreement, one-way/path markings, pavement walking height, protected platforms`);
console.log(`Campus road sections: ${roads.segments.length}; shared junctions: ${roads.junctions.length}`);
// Exact geometric cutouts prevent terrain showing through graded pavement.
const {cutRoadsFromGround}=await import('../road-ground.js');
const square={west:0,north:0,step:10,columns:2,rows:2,heights:new Float32Array([0,2,4,6])};
function groundArea(positions){let total=0;for(let i=0;i<positions.length;i+=9){const a=positions.slice(i,i+3),b=positions.slice(i+3,i+6),c=positions.slice(i+6,i+9);total+=Math.abs((b[0]-a[0])*(c[2]-a[2])-(b[2]-a[2])*(c[0]-a[0]))/2;}return total;}
const rectangle=(w,n,e,s)=>[[w,n],[e,n],[e,s],[w,s]];
for(const [footprints,expected] of [
 [[],100],[[rectangle(2,2,8,8)],64],[[rectangle(2,2,8,8).reverse()],64],
 [[rectangle(2,2,8,8),rectangle(5,2,9,8)],58],[[rectangle(0,0,2,10)],80],
 [[rectangle(-1,-1,11,11)],0],[[rectangle(12,12,15,15)],100]
]){
 const normals=new Float32Array([0,1,0,0,1,0,0,1,0,0,1,0]);
 const cut=cutRoadsFromGround(square,footprints,normals);
 assert(Math.abs(groundArea(cut.positions)-expected)<1e-7,`Ground cutout area differs from ${expected}`);
 for(let i=0;i<cut.positions.length;i+=3)assert(Math.abs(cut.positions[i+1]-(cut.positions[i]*.2+cut.positions[i+2]*.4))<1e-7,'Cutout must preserve the original sloping ground');
 assert.equal(cut.normals.length,cut.positions.length);
}
console.log('PASS: exact cutout area, overlapping road footprints, coincident edges, polygon winding and terrain height/normal preservation');
