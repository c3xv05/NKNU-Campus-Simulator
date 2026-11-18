import {ringDistance} from '../../planar.js';
export const JIYUAN_OSM=381731688;
export const INTERIOR_FLOOR_LIFT=.04,PLAYER_CLEARANCE=.08;
const prepared=new WeakMap();
const inside=(p,regions)=>regions.some(r=>ringDistance(...p,r[0])===0&&!r.slice(1).some(h=>ringDistance(...p,h)===0));
export function segmentDistance(x,z,a,b){const dx=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz||1)));return Math.hypot(x-a[0]-dx*t,z-a[1]-dz*t);}
export function createJiyuanSurface(campus,terrain){
 if(prepared.has(campus))return prepared.get(campus);
 const data=campus.jiyuanInterior,building=[...campus.places,...campus.buildings].find(b=>b.osm===JIYUAN_OSM);
 if(!data||!building)return null;
 const scale=data.modelScale||1,base=terrain.platformHeight(building)+INTERIOR_FLOOR_LIFT*scale;
 const floors=data.floors.map(f=>({...f,level:base+f.height,bounds:[Math.min(...f.regions[0][0].map(p=>p[0]))-.5,Math.min(...f.regions[0][0].map(p=>p[1]))-.5,Math.max(...f.regions[0][0].map(p=>p[0]))+.5,Math.max(...f.regions[0][0].map(p=>p[1]))+.5]}));
 const near=(f,x,z)=>x>=f.bounds[0]&&z>=f.bounds[1]&&x<=f.bounds[2]&&z<=f.bounds[3];
 const furniture=[];
 for(const f of floors)for(const s of f.spaces)if(s.kind==='bathroom')for(const fixture of s.fixtures)if(['sink','urinal'].includes(fixture.kind))furniture.push({floor:f.floor,center:fixture.center,radius:(fixture.kind==='sink'?.27:.18)*scale});
 function supportAt(x,z,y){
  // Stairs precede floors: the lower floor under a tread must never pull a walker down.
  let best=null,error=Infinity;
  for(const f of floors){if(!near(f,x,z)||y<f.level-.5||y>f.level+data.floorHeight+.6)continue;
   for(const stairs of f.stairs)if(ringDistance(x,z,stairs.bounds)===0)for(const t of stairs.treads){const h=f.level+t.height+PLAYER_CLEARANCE,e=Math.abs(y-h);if(e<.44&&e<error&&ringDistance(x,z,t.ring)===0){best=h;error=e;}}
  }
  if(best!==null)return best;
  for(const f of floors)if(near(f,x,z)&&Math.abs(y-f.level-PLAYER_CLEARANCE)<.85&&inside([x,z],f.surfaceRegions))return f.level+PLAYER_CLEARANCE;
  return null;
 }
 function blocked(x,z,r,y,riding=false){
  for(const f of floors){if(!near(f,x,z)||y<f.level-.5||y>f.level+2.9*scale)continue;
   if(riding&&inside([x,z],f.regions))return true;
   for(const[a,b]of [...f.walls,...f.windows])if(segmentDistance(x,z,a,b)<r+.075*scale)return true;
   // Stall partitions are thin (4cm) but solid.
   for(const[a,b]of f.partitions||[])if(segmentDistance(x,z,a,b)<r+.02*scale)return true;
   for(const[a,b]of f.shaftWalls||[])if(segmentDistance(x,z,a,b)<r+.075*scale)return true;
   for(const item of furniture)if(item.floor===f.floor&&Math.hypot(x-item.center[0],z-item.center[1])<r+item.radius)return true;
   if(inside([x,z],f.regions)&&supportAt(x,z,y)===null)return true;
  }
  return false;
 }
 const result={base,floors,supportAt,blocked,contains:(x,z)=>inside([x,z],floors[0].regions)};prepared.set(campus,result);return result;
}
export function jiyuanSupportAt(x,z,y,campus,terrain){return createJiyuanSurface(campus,terrain)?.supportAt(x,z,y)??null;}
