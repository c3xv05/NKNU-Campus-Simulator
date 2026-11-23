import {courtyardSupportAt} from '../teaching-courtyard/surface.js';
import {ringDistance} from '../../planar.js';
import {biologyTerraceScale} from '../../stair-layout.js';
const cache=new WeakMap();
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function project(x,z,line){let best=null,along=0,total=0;for(let i=1;i<line.length;i++){const a=line[i-1],b=line[i],dx=b[0]-a[0],dz=b[1]-a[1],l=Math.hypot(dx,dz),t=clamp(((x-a[0])*dx+(z-a[1])*dz)/(l*l),0,1),px=a[0]+dx*t,pz=a[1]+dz*t,d=Math.hypot(x-px,z-pz);if(!best||d<best.d)best={d,along:along+t*l,across:((x-px)*-dz+(z-pz)*dx)/l};along+=l;total+=l;}return{...best,total};}
function at(line,distance,across){for(let i=1;i<line.length;i++){const a=line[i-1],b=line[i],dx=b[0]-a[0],dz=b[1]-a[1],l=Math.hypot(dx,dz);if(distance<=l||i===line.length-1){const t=clamp(distance/l,0,1);return[a[0]+dx*t-dz/l*across,a[1]+dz*t+dx/l*across];}distance-=l;}}
function triangleSurface(points,height){const vertices=[],cells=new Map(),cell=4;for(const tri of points){const p=tri.map(([x,z])=>[Math.fround(x),Math.fround(height(x,z)),Math.fround(z)]);if((p[1][0]-p[0][0])*(p[2][2]-p[0][2])-(p[1][2]-p[0][2])*(p[2][0]-p[0][0])>0)[p[1],p[2]]=[p[2],p[1]];vertices.push(...p.flat());const den=(p[1][2]-p[2][2])*(p[0][0]-p[2][0])+(p[2][0]-p[1][0])*(p[0][2]-p[2][2]);if(Math.abs(den)<1e-10)continue;const item={p,den};for(let z=Math.floor((Math.min(...p.map(a=>a[2]))-.0001)/cell);z<=Math.floor((Math.max(...p.map(a=>a[2]))+.0001)/cell);z++)for(let x=Math.floor((Math.min(...p.map(a=>a[0]))-.0001)/cell);x<=Math.floor((Math.max(...p.map(a=>a[0]))+.0001)/cell);x++){const key=x+','+z;if(!cells.has(key))cells.set(key,[]);cells.get(key).push(item);}}
 const heightAt=(x,z)=>{for(const {p,den}of cells.get(Math.floor(x/cell)+','+Math.floor(z/cell))||[]){const u=((p[1][2]-p[2][2])*(x-p[2][0])+(p[2][0]-p[1][0])*(z-p[2][2]))/den,v=((p[2][2]-p[0][2])*(x-p[2][0])+(p[0][0]-p[2][0])*(z-p[2][2]))/den,w=1-u-v;if(Math.min(u,v,w)>=-.00003)return u*p[0][1]+v*p[1][1]+w*p[2][1];}return null;};return{vertices,heightAt};}
export function createCampusCorridors(campus,terrain,network){
 const saved=cache.get(network);if(saved?.campus===campus&&saved.terrain===terrain)return saved.value;
 const lower=terrain.platformHeight(campus.places.find(a=>a.osm===campus.levelLink.from)),bioLower=terrain.platformHeight(campus.places.find(a=>a.osm===campus.bioConnection.from));
 const approaches=(campus.campusTransitions||[]).map(a=>{
  const level=a.id==='courtyard-s32'?lower+((a.targetFloor||1)-1)*campus.courtyard.floorHeight:bioLower+((a.targetFloor||2)-1)*(campus.bioConnection.corridor?.floorHeight||3.6);
  function entry(across){const stations=a.entryStations;if(!stations)return null;let i=1;while(i<stations.length-1&&across>stations[i].across)i++;const p=stations[i-1],q=stations[i],t=clamp((across-p.across)/(q.across-p.across),0,1);return{along:p.along+(q.along-p.along)*t,point:p.point.map((v,k)=>v+(q.point[k]-v)*t)};}
  function centerX(z){for(let i=1;i<a.line.length;i++){const p=a.line[i-1],q=a.line[i];if(z>=q[1]){const t=clamp((z-p[1])/(q[1]-p[1]),0,1);return p[0]+(q[0]-p[0])*t;}}return a.line.at(-1)[0];}
  const profile=(x,z)=>{
   if(a.id==='courtyard-s32'){const start=a.line[0][1]-(a.roadInset+1),end=a.line.at(-1)[1]+a.flatEnd;if(z>=start)return network.surfaceHeight(x,z)+.035;const length=start-end,d=clamp(start-z,0,length),e=Math.min(1.5,length/3),mix=(d<e?d*d/(2*e):d>length-e?length-e-(length-d)**2/(2*e):d-e/2)/(length-e),initial=network.surfaceHeight(centerX(start)+x-centerX(z),start)+.035;return initial+(level-initial)*mix;}
   if(a.kind==='road-apron')return network.surfaceHeight(x,z)+.035;
   if(a.kind==='biology-landing')return level;
   const p=project(x,z,a.line),station=entry(p.across),initialDistance=station?.along??(a.roadInset?a.roadInset+1:0),length=p.total-a.flatEnd-initialDistance,d=clamp(p.along-initialDistance,0,length),u=d/length,e=Math.min(a.sidewalkEntry?.75:1.5,length/3),mix=a.linearGrade?(d<e?d*d/(2*e):d>length-e?length-e-(length-d)**2/(2*e):d-e/2)/(length-e):u*u*(3-2*u),q=station?.point??(a.roadInset&&p.along<=initialDistance?[x,z]:at(a.line,initialDistance,p.across)),initial=network.surfaceHeight(...q)+.035,h=initial+(level-initial)*mix;
   if(a.sidewalkEntry){const distance=p.along-initialDistance,fade=clamp((distance-a.entryRun)/1.5,0,1),edge=clamp((Math.abs(p.across)-a.width/2)/a.entryFlare,0,1)*(1-fade*fade*(3-2*fade)),side=network.surfaceHeight(x,z)+.035+.15*clamp(distance/.3,0,1);return h+(side-h)*edge;}
   return h;
  };
  return{...a,...triangleSurface(a.triangles,profile),profile,level};
 });
 const corridor=campus.bioConnection.corridor,bioFloors= corridor?corridor.floors.map(floor=>{const deck=floor>1&&corridor.deckTriangles;return{floor,level:bioLower+(floor-1)*corridor.floorHeight,regions:deck?corridor.deckRegions:corridor.regions,...triangleSurface(deck?corridor.deckTriangles:corridor.triangles,()=>bioLower+(floor-1)*corridor.floorHeight)};}):[];
 const value={approaches,bioFloors,lower,bioLower,heightAt(x,z,currentY){for(const s of [...approaches,...bioFloors]){const h=s.heightAt(x,z);if(h!==null&&Math.abs(currentY-h-.08)<.85)return h+.08;}return null;}};cache.set(network,{campus,terrain,value});return value;
}
export function corridorSupportAt(x,z,currentY,campus,terrain,network){return createCampusCorridors(campus,terrain,network).heightAt(x,z,currentY)??courtyardSupportAt(x,z,currentY,campus,terrain);}
// Keep the neighboring soil below the same surface; do not raise soil under elevated galleries.
export function gradeCampusCorridors(terrain,campus,network){
 const surface=createCampusCorridors(campus,terrain,network),court=campus.courtyard,terraces=biologyTerraceScale(campus,terrain,network),groups=[{regions:court.edgeRepairs?.regions||[],profile:()=>surface.lower},{regions:campus.bioConnection.corridor.regions,profile:()=>surface.bioLower},...(terraces?[{regions:[[campus.bioConnection.stairs.ring]],profile:(x,z)=>{const s=campus.bioConnection.stairs,p=project(x,z,s.line);return terraces.height(Math.max(0,Math.min(1,1-p.along/p.total))*500)+.035;}}]:[]),...surface.approaches].filter(s=>s.regions?.length),buildings=[...campus.places,...campus.buildings].filter(b=>b.height),mesh=terrain.mesh,blend=3;let changed=0;
 for(const s of groups){const rings=s.regions.map(r=>r[0]),points=rings.flat(),west=Math.min(...points.map(p=>p[0]))-blend,east=Math.max(...points.map(p=>p[0]))+blend,north=Math.min(...points.map(p=>p[1]))-blend,south=Math.max(...points.map(p=>p[1]))+blend;
  for(let row=Math.max(0,Math.floor((north-mesh.north)/mesh.step));row<mesh.rows&&mesh.north+row*mesh.step<=south;row++)for(let col=Math.max(0,Math.floor((west-mesh.west)/mesh.step));col<mesh.columns&&mesh.west+col*mesh.step<=east;col++){const x=mesh.west+col*mesh.step,z=mesh.north+row*mesh.step,d=Math.min(...rings.map(r=>ringDistance(x,z,r)));if((s.id&&[...court.floorRegions.lower,...campus.bioConnection.corridor.regions].some(([r])=>ringDistance(x,z,r)===0))||d>=blend||network.onMotorRoad(x,z)||buildings.some(b=>ringDistance(x,z,b.ring)===0)||[...campus.levelLink.stairs,...court.stairs,campus.bioConnection.stairs].some(b=>ringDistance(x,z,b.ring)===0))continue;const u=d/blend,w=1-u*u*(3-2*u),i=row*mesh.columns+col,target=s.profile(x,z)-.035;mesh.heights[i]+=(target-mesh.heights[i])*w;changed++;}
 }
 return changed;
}

const groundCache=new WeakMap();
// Build only after the terrain grading pass; this joins the exact terrain triangles at the outer edge.
export function createCorridorGround(campus,terrain,network){
 const saved=groundCache.get(network);if(saved?.campus===campus&&saved.terrain===terrain)return saved.surface;
 const ramps=createCampusCorridors(campus,terrain,network),surfaces=ramps.approaches.filter(a=>a.groundBlendPlan).map(a=>{
  const rings=a.regions.map(r=>r[0]),profile=(x,z)=>{const d=Math.min(...rings.map(r=>ringDistance(x,z,r))),u=clamp(d/a.groundBlendPlan.width,0,1),mix=u*u*(3-2*u);return(a.profile(x,z)-.035)*(1-mix)+terrain.height(x,z)*mix;};
  return{id:a.id+'-soil-blend',profile,...triangleSurface(a.groundBlendPlan.triangles,profile)};
 });
 const surface={surfaces,heightAt(x,z){for(const s of surfaces){const h=s.heightAt(x,z);if(h!==null)return h;}return null;}};groundCache.set(network,{campus,terrain,surface});return surface;
}
