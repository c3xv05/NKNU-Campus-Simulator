import {ringDistance} from './planar.js';
export const groundHeight=()=>0;
export function triangleContains(x,z,t){
 const cross=(a,b)=>(b[0]-a[0])*(z-a[1])-(b[1]-a[1])*(x-a[0]);
 const c=t.map((a,i)=>cross(a,t[(i+1)%3]));return c.every(v=>v>=-.0001)||c.every(v=>v<=.0001);
}
export function createHepingWorld(data){
 const trees=[];
 const inCampus=(x,z)=>data.campusTriangles.some(t=>triangleContains(x,z,t));
 function blocked(x,z,r=.35){
  if(!inCampus(x,z))return true;
  if(trees.some(t=>Math.hypot(x-t.x,z-t.z)<r+.28))return true;
  if(data.buildings.some(b=>ringDistance(x,z,b.ring)<r))return true;
  return data.courts.some(c=>c.sport==='swimming'&&ringDistance(x,z,c.ring)<r);
 }
 function move(position,dx,dz,r=.35){
  // Short substeps prevent fast riding from tunnelling through a narrow building.
  const n=Math.max(1,Math.ceil(Math.hypot(dx,dz)/.15));let moved=false;
  for(let i=0;i<n;i++){
   const x=position.x+dx/n,z=position.z+dz/n;
   if(!blocked(x,z,r)){position.x=x;position.z=z;moved=true;}
   else if(!blocked(x,position.z,r)){position.x=x;moved=true;}
   else if(!blocked(position.x,z,r)){position.z=z;moved=true;}
  }return moved;
 }
 return {inCampus,blocked,move,height:groundHeight,trees};
}
