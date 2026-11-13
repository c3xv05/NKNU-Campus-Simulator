import {ringDistance} from './terrain.js';
export function findDestinations(campus,network){
 const buildings=[...campus.places.filter(p=>p.height),...campus.buildings];
 const centre=ring=>({x:ring.reduce((s,p)=>s+p[0],0)/ring.length,z:ring.reduce((s,p)=>s+p[1],0)/ring.length});
 const gate=network.nearest(-279,512,true);
 const result=[{id:'gate',label:'大門',x:gate?gate.segment.a.x+gate.segment.dx*gate.t:-279,z:gate?gate.segment.a.z+gate.segment.dz*gate.t:512,yaw:0}];
 for(const [id,name] of [['canteen','歸燕食巢'],['zhili','致理大樓'],['library','圖資大樓'],['technology','科技大樓']]){
  const target=campus.places.find(p=>p.name===name),c=centre(target.ring);let best=null,roadBest=null;
  for(const segment of network.segments){
   if(segment.route.style.path&&id!=='library')continue;
   if(campus.entranceRoadIds?.[target.osm]&&!campus.entranceRoadIds[target.osm].includes(segment.route.osm))continue;
   const x=(segment.a.x+segment.b.x)/2,z=(segment.a.z+segment.b.z)/2;
   if(buildings.some(b=>ringDistance(x,z,b.ring)<2.5)||campus.water.some(a=>ringDistance(x,z,a.ring)<1))continue;
   const distance=ringDistance(x,z,target.ring),score=distance+Math.hypot(x-c.x,z-c.z)*.02;
   if(!best||score<best.score)best={x,z,score,distance};
   if(!segment.route.style.path&&(!roadBest||score<roadBest.score))roadBest={x,z,score};
  }
  if(!best)throw new Error('無法找到安全傳送點：'+name);
  result.push({id,label:name,x:best.x,z:best.z,yaw:Math.atan2(best.x-c.x,best.z-c.z),...(id==='library'&&roadBest?{roadArrival:{x:roadBest.x,z:roadBest.z,yaw:Math.atan2(roadBest.x-c.x,roadBest.z-c.z)}}:{})});
 }
 return result;
}
// Developer arrivals use clear motor-road positions so walking and riding share safe landings.
export function findBuildingDestinations(campus,network,profiles={},publicDestinations=findDestinations(campus,network)){
 const buildings=[...campus.places,...campus.buildings].filter(b=>b.height),result=[],candidates=[];
 for(const segment of network.segments)if(!segment.route.style.path)candidates.push({x:(segment.a.x+segment.b.x)/2,z:(segment.a.z+segment.b.z)/2});
 for(const area of campus.pavedAreas||[]){const xs=area.ring.map(p=>p[0]),zs=area.ring.map(p=>p[1]);for(let z=Math.min(...zs);z<=Math.max(...zs);z+=2)for(let x=Math.min(...xs);x<=Math.max(...xs);x+=2)if(ringDistance(x,z,area.ring)===0&&network.onMotorRoad(x,z))candidates.push({x,z});}
 const clear=candidates.filter(({x,z})=>!buildings.some(b=>ringDistance(x,z,b.ring)<2.5)&&!campus.water.some(a=>ringDistance(x,z,a.ring)<1));
 for(const target of buildings){
  const existing=publicDestinations.find(d=>d.label===target.name);if(existing){result.push({...existing,osm:target.osm});continue;}
  const cx=target.ring.reduce((s,p)=>s+p[0]/target.ring.length,0),cz=target.ring.reduce((s,p)=>s+p[1]/target.ring.length,0);let best=null;
  for(const {x,z}of clear){const distance=ringDistance(x,z,target.ring),score=distance+Math.hypot(x-cx,z-cz)*.02;if(!best||score<best.score)best={x,z,score};}
  if(!best)throw new Error('無法找到建築傳送點：'+target.osm);
  result.push({id:'building-'+target.osm,osm:target.osm,label:target.name&&!target.name.startsWith('未命名')?target.name:(profiles[target.osm]?.name||'附屬建築')+'（'+target.osm+'）',x:best.x,z:best.z,yaw:Math.atan2(best.x-cx,best.z-cz),developerOnly:true});
 }
 return result;
}
export const MAX_SCOOTER_SPEED=75/3.6;
export function stepScooter(state,dt,throttle,steer,onRoad=true){
 const forward=onRoad?MAX_SCOOTER_SPEED:4,target=throttle>=0?throttle*forward:throttle*2.5;
 const acceleration=throttle===0?5:state.speed*target<0?11:6;
 state.speed+=Math.max(-acceleration*dt,Math.min(acceleration*dt,target-state.speed));
 if(Math.abs(state.speed)<.005)state.speed=0;
 const turn=1.35*Math.max(.3,Math.min(1,Math.abs(state.speed)/3));
 state.heading-=steer*turn*dt*(state.speed<0?-1:1);
 return {dx:-Math.sin(state.heading)*state.speed*dt,dz:-Math.cos(state.heading)*state.speed*dt};
}
