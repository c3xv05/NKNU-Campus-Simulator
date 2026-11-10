import {ringDistance} from './terrain.js';
export function inLake(x,z,area){return ringDistance(x,z,area.ring)===0&&!(area.holes||[]).some(r=>ringDistance(x,z,r)===0);}
export function lakeAt(x,z,campus){return campus.water.find(a=>inLake(x,z,a));}
export function projectOnLine(x,z,a,b){const dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),t=((x-a[0])*dx+(z-a[1])*dz)/(length*length||1);return{t,distance:Math.abs((x-a[0])*dz-(z-a[1])*dx)/(length||1),length};}
export function bridgeHeight(x,z,currentY,link,level){if(!link)return null;const p=projectOnLine(x,z,...link.line);return p.t>=0&&p.t<=1&&p.distance<link.width/2&&currentY>=level-.7?level+.08:null;}
export function sidewalkSections(campus,network){
 const ids=new Set(campus.sidewalkRoadIds||[]),sections=[];
 for(const route of network.routes){if(!ids.has(route.osm))continue;
  for(let i=1;i<route.points.length;i++){
   const a=route.points[i-1],b=route.points[i],length=Math.hypot(b.x-a.x,b.z-a.z)||1,nx=-(b.z-a.z)/length,nz=(b.x-a.x)/length;
   for(const side of [-1,1]){
    if(route.entrance){const cx=(a.x+b.x)/2,cz=(a.z+b.z)/2,innerX=cx+nx*side*(route.width/2+1),innerZ=cz+nz*side*(route.width/2+1);if(campus.flowerbed&&ringDistance(innerX,innerZ,campus.flowerbed.ring)<1)continue;}
    const inner=side*route.width/2,outer=side*(route.width/2+1.8);
    sections.push({road:route.osm,points:[[a.x+nx*inner,a.z+nz*inner],[a.x+nx*outer,a.z+nz*outer],[b.x+nx*outer,b.z+nz*outer],[b.x+nx*inner,b.z+nz*inner]]});
   }
  }
 }
 return sections;
}
