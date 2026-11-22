import {s05FrontageGrade} from './data/s05-frontage-grade.js';
// One continuous additive height offset along a road: the centreline between two stations is pulled onto the
// straight line joining its original end heights; smooth ramps return to the original heights outside it.
const smooth=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
function stationAtZ(points,stations,z){for(let i=1;i<points.length;i++){const a=points[i-1].z,b=points[i].z;if((a-z)*(b-z)<=0&&a!==b)return stations[i-1]+(stations[i]-stations[i-1])*(z-a)/(b-a);}return null;}
export function createLocalRoadGrade(routes,config=s05FrontageGrade){
 const route=routes.find(r=>r.osm===config.road);if(!route)return null;const points=route.points,stations=[0];
 for(let i=1;i<points.length;i++)stations.push(stations.at(-1)+Math.hypot(points[i].x-points[i-1].x,points[i].z-points[i-1].z));
 const knots=config.knotsZ.map(z=>stationAtZ(points,stations,z));if(knots.some(k=>k===null)||knots.some((k,i)=>i&&k<=knots[i-1]+1))return null;const s0=knots[0],s1=knots.at(-1);
 const heightAt=s=>{for(let i=1;i<points.length;i++)if(s<=stations[i]||i===points.length-1){const t=(s-stations[i-1])/(stations[i]-stations[i-1]);return points[i-1].h+(points[i].h-points[i-1].h)*t;}return points.at(-1).h;};
 const kh=knots.map(heightAt),h0=kh[0],h1=kh.at(-1),a=Math.max(0,s0-config.rampNorth),b=Math.min(stations.at(-1),s1+config.rampSouth);
 const piece=s=>{let i=1;while(i<knots.length-1&&s>knots[i])i++;return kh[i-1]+(kh[i]-kh[i-1])*(s-knots[i-1])/(knots[i]-knots[i-1]);},w=config.smoothing||0,line=s=>{if(!w)return piece(s);let sum=0,n=0;for(let k=-4;k<=4;k++){const q=s+k*w/4,wt=5-Math.abs(k);sum+=piece(q)*wt;n+=wt;}return sum/n;},ramp=s=>s<s0?smooth((s-a)/(s0-a)):s>s1?smooth((b-s)/(b-s1)):1;
 const offsets=points.map((p,i)=>{const s=stations[i];return s<=a||s>=b?0:ramp(s)*(line(s)-p.h);});
 // Hermite interpolation of the offsets keeps the correction C1 (no creases at the road nodes).
 const tangents=offsets.map((_,i)=>{if(i===0||i===offsets.length-1)return 0;return(offsets[i+1]-offsets[i-1])/(stations[i+1]-stations[i-1]);});
 const offsetAt=(i,t)=>{const run=stations[i]-stations[i-1],d0=offsets[i-1],d1=offsets[i];if(d0===0&&d1===0)return 0;return(2*t**3-3*t*t+1)*d0+(t**3-2*t*t+t)*tangents[i-1]*run+(-2*t**3+3*t*t)*d1+(t**3-t*t)*tangents[i]*run;};
 let west=Infinity,east=-Infinity,north=Infinity,south=-Infinity;const margin=config.fade+2;
 for(let i=0;i<points.length;i++)if(stations[i]>a-5&&stations[i]<b+5){west=Math.min(west,points[i].x);east=Math.max(east,points[i].x);north=Math.min(north,points[i].z);south=Math.max(south,points[i].z);}
 west-=margin;east+=margin;north-=margin;south+=margin;
 function sample(x,z){if(x<west||x>east||z<north||z>south)return{offset:0,weight:0};let best=null;
  for(let i=1;i<points.length;i++){if(stations[i]<a-5||stations[i-1]>b+5)continue;const p=points[i-1],q=points[i],dx=q.x-p.x,dz=q.z-p.z,run=stations[i]-stations[i-1],t=Math.max(0,Math.min(1,((x-p.x)*dx+(z-p.z)*dz)/(run*run))),d=Math.hypot(x-p.x-dx*t,z-p.z-dz*t);if(best&&d>=best.distance)continue;best={distance:d,i,t};}
  if(!best)return{offset:0,weight:0};const u=smooth((best.distance-config.core)/(config.fade-config.core)),weight=1-u,offset=offsetAt(best.i,best.t);return{offset:offset*weight,weight:offset===0?0:weight,station:stations[best.i-1]+best.t*(stations[best.i]-stations[best.i-1]),distance:best.distance};}
 return{config,route,stations,offsets,knots,knotHeights:kh,from:s0,to:s1,lineStart:h0,lineEnd:h1,sample,offset:(x,z)=>sample(x,z).offset};
}
