import {ringDistance} from './planar.js';
// The recovered white paving and its neighboring soil share the original road
// grade. Blend only this local ground mesh; road elevations/building pads stay fixed.
export function gradeTeachingAccess(terrain,campus,network){
 const access=campus.teachingAccess;if(!access)return 0;
 const rings=[access.frontApron,access.reclaimedFootprint],points=rings.flat(),blend=3;
 const west=Math.min(...points.map(p=>p[0]))-blend,east=Math.max(...points.map(p=>p[0]))+blend,north=Math.min(...points.map(p=>p[1]))-blend,south=Math.max(...points.map(p=>p[1]))+blend;
 const buildings=[...campus.places,...campus.buildings].filter(a=>a.height),mesh=terrain.mesh;let changed=0;
 for(let row=Math.max(0,Math.floor((north-mesh.north)/mesh.step));row<mesh.rows&&mesh.north+row*mesh.step<=south;row++)for(let col=Math.max(0,Math.floor((west-mesh.west)/mesh.step));col<mesh.columns&&mesh.west+col*mesh.step<=east;col++){
  const x=mesh.west+col*mesh.step,z=mesh.north+row*mesh.step,d=Math.min(...rings.map(r=>ringDistance(x,z,r)));
  if(d>=blend||buildings.some(a=>ringDistance(x,z,a.ring)===0))continue;
  const u=d/blend,weight=1-u*u*(3-2*u),i=row*mesh.columns+col;
  mesh.heights[i]+=(network.surfaceHeight(x,z)-.015-mesh.heights[i])*weight;changed++;
 }
 return changed;
}
