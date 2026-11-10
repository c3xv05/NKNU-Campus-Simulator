import {ringDistance} from './terrain.js';
export function findDestinations(campus,network){
 const buildings=[...campus.places.filter(p=>p.height),...campus.buildings];
 const centre=ring=>({x:ring.reduce((s,p)=>s+p[0],0)/ring.length,z:ring.reduce((s,p)=>s+p[1],0)/ring.length});
 const gate=network.nearest(-279,512,true);
 const result=[{id:'gate',label:'大門',x:gate?gate.segment.a.x+gate.segment.dx*gate.t:-279,z:gate?gate.segment.a.z+gate.segment.dz*gate.t:512,yaw:0}];
 for(const [id,name] of [['canteen','歸燕食巢'],['zhili','致理大樓']]){
  const target=campus.places.find(p=>p.name===name),c=centre(target.ring);let best=null;
  for(const segment of network.segments){
   if(segment.route.style.path)continue;
   const x=(segment.a.x+segment.b.x)/2,z=(segment.a.z+segment.b.z)/2;
   if(buildings.some(b=>ringDistance(x,z,b.ring)<2.5))continue;
   const distance=ringDistance(x,z,target.ring),score=distance+Math.hypot(x-c.x,z-c.z)*.02;
   if(!best||score<best.score)best={x,z,score,distance};
  }
  if(!best)throw new Error('無法找到安全傳送點：'+name);
  result.push({id,label:name,x:best.x,z:best.z,yaw:Math.atan2(best.x-c.x,best.z-c.z)});
 }
 return result;
}
export const MAX_SCOOTER_SPEED=80/3.6;
export function stepScooter(state,dt,throttle,steer,onRoad=true){
 const forward=onRoad?MAX_SCOOTER_SPEED:4,target=throttle>=0?throttle*forward:throttle*2.5;
 const acceleration=throttle===0?5:state.speed*target<0?11:6;
 state.speed+=Math.max(-acceleration*dt,Math.min(acceleration*dt,target-state.speed));
 if(Math.abs(state.speed)<.005)state.speed=0;
 const turn=1.35*Math.max(.3,Math.min(1,Math.abs(state.speed)/3));
 state.heading-=steer*turn*dt*(state.speed<0?-1:1);
 return {dx:-Math.sin(state.heading)*state.speed*dt,dz:-Math.cos(state.heading)*state.speed*dt};
}
