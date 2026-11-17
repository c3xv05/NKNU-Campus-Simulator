// Pure geometry for the Xiangyang planter, court wall and fence (no THREE); shared by renderer, game physics and tests.
import {xiangyangPlanter as config} from './layout.js';
import {ringDistance} from '../../terrain.js';
export {config as xiangyangPlanterConfig};
export function createXiangyangPlanter(campus,network,terrain,source=config){
 const empty={config:source,stations:[],heightAt:()=>null,blocked:()=>false,wallDistance:()=>Infinity};
 const route=network.routes.find(r=>r.osm===source.road);if(!route)return empty;
 const areas=[...campus.places,...campus.buildings,...campus.courts].filter(a=>a.ring?.length>2);
 const P=route.points,half=route.width/2,raw=[];let station=0;
 for(let i=1;i<P.length;i++){const a=P[i-1],b=P[i],L=Math.hypot(b.x-a.x,b.z-a.z);if(!L)continue;const nx=-(b.z-a.z)/L*source.side,nz=(b.x-a.x)/L*source.side;
  for(let s=Math.max(source.from,Math.ceil(station*2)/2);s<=Math.min(source.to,station+L)+1e-9;s+=.5){const u=(s-station)/L;if(u<0||u>1||raw.length&&Math.abs(raw.at(-1).station-s)<1e-6)continue;
   const cx=a.x+(b.x-a.x)*u,cz=a.z+(b.z-a.z)*u,inner=[cx+nx*half,cz+nz*half];let hit=null;
   let area=null;for(let d=0;d<=source.search;d+=.05){const x=inner[0]+nx*d,z=inner[1]+nz*d;area=areas.find(r=>ringDistance(x,z,r.ring)===0);if(area){hit=d;break;}}
   raw.push({station:s,inner,normal:[nx,nz],hit,level:area&&terrain.platformHeight?terrain.platformHeight(area):null});}
  station+=L;}
 if(!raw.length)return empty;
 // Fill stations with no court/building ahead by interpolating neighbours, then smooth the wall line.
 const known=raw.map((r,i)=>r.hit===null?null:i).filter(i=>i!==null);if(!known.length)return empty;
 const width=raw.map((r,i)=>{if(r.hit!==null)return r.hit-source.courtGap;const prev=known.filter(k=>k<i).at(-1),next=known.find(k=>k>i);if(prev===undefined)return raw[next].hit-source.courtGap;if(next===undefined)return raw[prev].hit-source.courtGap;const t=(i-prev)/(next-prev);return (raw[prev].hit*(1-t)+raw[next].hit*t)-source.courtGap;});
 const smooth=width.map((_,i)=>{let sum=0,n=0;for(let k=Math.max(0,i-4);k<=Math.min(width.length-1,i+4);k++){sum+=width[k];n++;}return Math.max(source.minWidth,sum/n);});
 const levels=raw.map((r,i)=>{if(r.level!=null)return r.level;let best=null,bd=Infinity;for(const k of known){if(raw[k].level!=null&&Math.abs(k-i)<bd){bd=Math.abs(k-i);best=raw[k].level;}}return best;});
 const stations=raw.map((r,i)=>{const [nx,nz]=r.normal,[ix,iz]=r.inner,d=smooth[i],road=network.surfaceHeight(ix-nx*.05,iz-nz*.05);
  const wallIn=[ix+nx*d,iz+nz*d],wallOut=[ix+nx*(d+source.wallThickness),iz+nz*(d+source.wallThickness)],cutOuter=[ix+nx*(d+source.courtGap+.05),iz+nz*(d+source.courtGap+.05)];
  const courtSide=levels[i]??terrain.height(ix+nx*(d+source.courtGap+.6),iz+nz*(d+source.courtGap+.6)),ground=Math.min(courtSide,terrain.height(...wallOut));
  const grass=road+source.grassAbove,wallTop=grass+source.wallLip;
  return{station:r.station,normal:r.normal,inner:r.inner,cutOuter,curbOuter:[ix+nx*source.curbWidth,iz+nz*source.curbWidth],wallIn,wallOut,width:d,road,curbTop:road+source.curbAbove,grass,wallTop,courtSide,wallBottom:Math.min(ground,road-.3)-source.footing,fenceTop:wallTop+source.fenceHeight};});
 // Planter footprint as quads between consecutive stations; heightAt returns curb or grass level inside it.
 function locate(x,z){for(let i=1;i<stations.length;i++){const a=stations[i-1],b=stations[i],ax=a.inner[0],az=a.inner[1],tx=b.inner[0]-ax,tz=b.inner[1]-az,tl=tx*tx+tz*tz;if(!tl)continue;const t=((x-ax)*tx+(z-az)*tz)/tl;if(t<-1e-6||t>1+1e-6)continue;const nx=a.normal[0]*(1-t)+b.normal[0]*t,nz=a.normal[1]*(1-t)+b.normal[1]*t,nl=Math.hypot(nx,nz),px=ax+tx*t,pz=az+tz*t,s=((x-px)*nx+(z-pz)*nz)/nl,w=a.width*(1-t)+b.width*t;if(s>=0&&s<=w)return{a,b,t,s};}return null;}
 // Station-relative position (t along the segment, s outward from the road edge) without width limits.
 function project(x,z){for(let i=1;i<stations.length;i++){const a=stations[i-1],b=stations[i],ax=a.inner[0],az=a.inner[1],tx=b.inner[0]-ax,tz=b.inner[1]-az,tl=tx*tx+tz*tz;if(!tl)continue;const t=((x-ax)*tx+(z-az)*tz)/tl;if(t<-1e-6||t>1+1e-6)continue;const nx=a.normal[0]*(1-t)+b.normal[0]*t,nz=a.normal[1]*(1-t)+b.normal[1]*t,nl=Math.hypot(nx,nz),px=ax+tx*t,pz=az+tz*t,s=((x-px)*nx+(z-pz)*nz)/nl;return{a,b,t,s};}return null;}
 function heightAt(x,z){const hit=locate(x,z);if(!hit)return null;const {a,b,t,s}=hit;return s<=source.curbWidth?a.curbTop*(1-t)+b.curbTop*t:a.grass*(1-t)+b.grass*t;}
 function wallDistance(x,z){let best=Infinity;for(let i=1;i<stations.length;i++){const p=stations[i-1],q=stations[i],ax=(p.wallIn[0]+p.wallOut[0])/2,az=(p.wallIn[1]+p.wallOut[1])/2,bx=(q.wallIn[0]+q.wallOut[0])/2,bz=(q.wallIn[1]+q.wallOut[1])/2,dx=bx-ax,dz=bz-az,l=dx*dx+dz*dz,t=l?Math.max(0,Math.min(1,((x-ax)*dx+(z-az)*dz)/l)):0;best=Math.min(best,Math.hypot(x-ax-dx*t,z-az-dz*t));}return best;}
 // Terrain is clipped from the road edge to just past the wall; the renderer supplies planter and court-side ground.
 const footprints=stations.slice(1).map((b,i)=>{const a=stations[i];return[a.inner,b.inner,b.cutOuter,a.cutOuter];});
 return{config:source,stations,footprints,heightAt,project,wallDistance,blocked:(x,z,r)=>stations.length>1&&wallDistance(x,z)<source.wallThickness/2+r};
}

