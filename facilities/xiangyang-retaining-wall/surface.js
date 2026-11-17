// Pure geometry for the Xiangyang retaining wall (no THREE), shared by renderer and tests.
import {xiangyangRetainingWall as config} from './layout.js';
export {config as xiangyangWallConfig};
export function createXiangyangWall(network,terrain,source=config){
 const route=network.routes.find(r=>r.osm===source.road);if(!route)return{points:[],blocked:()=>false,near:()=>false};
 const P=route.points,half=route.width/2,points=[];let station=0;
 const push=(x,z,nx,nz,s)=>{const ex=x+nx*half*source.side,ez=z+nz*half*source.side,ox=nx*source.side,oz=nz*source.side;
  const top=network.surfaceHeight(ex-ox*.05,ez-oz*.05)+source.capAbove;
  const ground=Math.min(terrain.height(ex+ox*(source.thickness+.05),ez+oz*(source.thickness+.05)),top-.3);
  points.push({station:s,x:ex+ox*source.thickness/2,z:ez+oz*source.thickness/2,inner:[ex,ez],outer:[ex+ox*source.thickness,ez+oz*source.thickness],top,bottom:ground-source.footing});};
 for(let i=1;i<P.length;i++){const a=P[i-1],b=P[i],L=Math.hypot(b.x-a.x,b.z-a.z);if(!L)continue;const nx=-(b.z-a.z)/L,nz=(b.x-a.x)/L;
  for(let s=Math.max(source.from,Math.ceil(station*2)/2);s<=Math.min(source.to,station+L)+1e-9;s+=.5){const u=(s-station)/L;if(u<0||u>1)continue;if(points.length&&Math.abs(points.at(-1).station-s)<1e-6)continue;push(a.x+(b.x-a.x)*u,a.z+(b.z-a.z)*u,nx,nz,s);}
  station+=L;}
 const halfThick=source.thickness/2;
 function distance(x,z){let best=Infinity;for(let i=1;i<points.length;i++){const a=points[i-1],b=points[i],dx=b.x-a.x,dz=b.z-a.z,l=dx*dx+dz*dz,t=l?Math.max(0,Math.min(1,((x-a.x)*dx+(z-a.z)*dz)/l)):0;best=Math.min(best,Math.hypot(x-a.x-dx*t,z-a.z-dz*t));}return best;}
 return{config:source,points,distance,near:(x,z,margin=0)=>points.length>1&&distance(x,z)<halfThick+margin,blocked:(x,z,r)=>points.length>1&&distance(x,z)<halfThick+r};
}
