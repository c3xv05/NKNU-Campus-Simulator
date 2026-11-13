import {ringDistance} from '../../planar.js';
export function inRegions(x,z,regions){return regions.some(([outer,...holes])=>ringDistance(x,z,outer)<.00002&&!holes.some(r=>ringDistance(x,z,r)===0));}
export function edgeDistance(x,z,regions){let distance=Infinity;for(const region of regions)for(const ring of region)for(let i=0;i<ring.length;i++){const a=ring[i],b=ring[(i+1)%ring.length],dx=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz||1)));distance=Math.min(distance,Math.hypot(x-a[0]-dx*t,z-a[1]-dz*t));}return distance;}
export function progressOnLine(x,z,line){let best=null,distance=0,total=0;for(let i=1;i<line.length;i++)total+=Math.hypot(line[i][0]-line[i-1][0],line[i][1]-line[i-1][1]);for(let i=1;i<line.length;i++){const a=line[i-1],b=line[i],dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(length*length))),d=Math.hypot(x-a[0]-dx*t,z-a[1]-dz*t);if(!best||d<best.d)best={d,t:(distance+length*t)/total};distance+=length;}return best.t;}
export function createCourtAccess(campus,terrain,network,sidewalk){
 const source=campus.sportsAccess;if(!source)return{surfaces:[],heightAt:()=>null,blocked:()=>false};
 const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);},base=a=>terrain.platformHeight(campus.courts.find(c=>c.osm===a.court))+.07;
 const outside=(x,z)=>{const s=sidewalk.heightAt(x,z);if(s!==null)return{floor:s,foot:s};return{floor:network.onMotorRoad(x,z)?network.surfaceHeight(x,z)+.015:terrain.height(x,z),foot:network.walkHeight(x,z,terrain.height(x,z))};};
 const surfaces=source.surfaces.map(a=>{
  const level=base(a),end=a.line?outside(...a.line.at(-1)):null,vertices=[],feet=[],cells=new Map(),triangles=[];
  if(a.kind!=='stairs')for(const triangle of a.triangles){const points=[],walk=[];
   for(const [xx,zz]of triangle){const x=Math.fround(xx),z=Math.fround(zz),out=outside(x,z);let weight,start=level+(a.startOffset||0);
    if(a.kind==='shoulder'){const inner=ringDistance(x,z,a.inner),outer=edgeDistance(x,z,a.outer);weight=inner<.0001?0:ease(inner/(inner+outer));}
    else weight=ease(progressOnLine(x,z,a.line));
    let floor=start+((a.kind==='ramp'?end.floor:out.floor)-start)*weight,foot=start+.08+((a.kind==='ramp'?end.foot:out.foot)-start-.08)*weight;
    if(a.kind==='ramp'&&a.contactEdges?.length){const d=edgeDistance(x,z,a.contactEdges.map(line=>[line])),blend=1-ease(d/.5);floor+=(out.floor-floor)*blend;foot+=(out.foot-foot)*blend;}points.push([x,Math.fround(floor),z]);walk.push(Math.fround(foot));
   }
   if((points[1][0]-points[0][0])*(points[2][2]-points[0][2])-(points[1][2]-points[0][2])*(points[2][0]-points[0][0])>0){[points[1],points[2]]=[points[2],points[1]];[walk[1],walk[2]]=[walk[2],walk[1]];}
   const den=(points[1][2]-points[2][2])*(points[0][0]-points[2][0])+(points[2][0]-points[1][0])*(points[0][2]-points[2][2]);if(Math.abs(den)<1e-8)continue;const item={p:points,walk,den};triangles.push(item);vertices.push(...points.flat());feet.push(...walk);
   for(let iz=Math.floor(Math.min(...points.map(p=>p[2]))/4);iz<=Math.floor(Math.max(...points.map(p=>p[2]))/4);iz++)for(let ix=Math.floor(Math.min(...points.map(p=>p[0]))/4);ix<=Math.floor(Math.max(...points.map(p=>p[0]))/4);ix++){const k=ix+','+iz;if(!cells.has(k))cells.set(k,[]);cells.get(k).push(item);}
  }
  function heightAt(x,z,floor=false){if(a.kind==='stairs'){if(!inRegions(x,z,a.regions))return null;const t=progressOnLine(x,z,a.line),step=Math.max(0,Math.min(a.steps,Math.ceil(t*a.steps-1e-5)));return level-step*a.rise/a.steps+(floor?0:.08);}
   for(const {p,walk,den}of cells.get(Math.floor(x/4)+','+Math.floor(z/4))||[]){const u=((p[1][2]-p[2][2])*(x-p[2][0])+(p[2][0]-p[1][0])*(z-p[2][2]))/den,v=((p[2][2]-p[0][2])*(x-p[2][0])+(p[0][0]-p[2][0])*(z-p[2][2]))/den,w=1-u-v;if(Math.min(u,v,w)>=-.0002)return floor?u*p[0][1]+v*p[1][1]+w*p[2][1]:u*walk[0]+v*walk[1]+w*walk[2];}return null;
  }
  return{...a,level,vertices,feet,triangles,heightAt,floorAt:(x,z)=>heightAt(x,z,true)};
 });
 function heightAt(x,z){for(const a of [...surfaces.filter(a=>a.kind==='stairs'),...surfaces.filter(a=>a.kind==='ramp'),...surfaces.filter(a=>a.kind==='shoulder')]){const h=a.heightAt(x,z);if(h!==null)return h;}return null;}
 const court=campus.courts.find(c=>c.sport==='basketball'),fenceBase=terrain.platformHeight(court)+.07;
 function blocked(x,z,r,y){return y<fenceBase+3&&source.fences.some(f=>{const [a,b]=f.line,dx=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz)));return Math.hypot(x-a[0]-dx*t,z-a[1]-dz*t)<r+.06;});}
 return{surfaces,heightAt,blocked,fenceBase,outsideFloorAt:(x,z)=>outside(x,z).floor};
}
