import {yongjiTerrain as config} from './data/yongji-terrain.js';
const clamp=v=>Math.max(0,Math.min(1,v));const ease=(a,b,v)=>{const t=clamp((v-a)/(b-a));return t*t*(3-2*t);};
function prepare(line){let station=0;const segments=[];for(let i=1;i<line.length;i++){const a=line[i-1],b=line[i],dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz);segments.push({a,b,dx,dz,length,station});station+=length;}return{segments,length:station};}
const s06=prepare(config.s06),combined=prepare([...config.s06,...config.s07.slice(1)]);
function project(x,z,path){let best=null;for(const s of path.segments){const raw=((x-s.a[0])*s.dx+(z-s.a[1])*s.dz)/(s.length*s.length),t=clamp(raw),px=s.a[0]+s.dx*t,pz=s.a[1]+s.dz*t,dx=x-px,dz=z-pz,distance=Math.hypot(dx,dz);if(!best||distance<best.distance)best={station:s.station+s.length*t,distance,side:(-s.dz*dx+s.dx*dz)/s.length,beyond:Math.sqrt(Math.max(0,distance*distance-((-s.dz*dx+s.dx*dz)/s.length)**2))};}return best;}
export function yongjiHeightAdjustment(x,z){
 const p=project(x,z,combined);if(p.distance>Math.max(config.westRiseFadeEnd,config.eastLiftFade,150)+10)return 0;
 const station=p.station,lift=station<=s06.length?config.s06AddedRise*station/s06.length:config.s06AddedRise+config.s07AddedRise*(station-s06.length)/(combined.length-s06.length);
 const across=p.side>=0?1-ease(config.nearRoad,config.westLiftFade,p.side):1-ease(config.eastLiftNear,config.eastLiftFade,-p.side),endFade=1-ease(70,150,p.beyond);
 const west=project(x,z,s06),ridge=west.side>0?config.westRiseHeight*ease(config.westRiseStart,config.westRiseFull,west.side)*(1-ease(config.westRiseFadeStart,config.westRiseFadeEnd,west.side))*ease(0,30,west.station)*(1-ease(s06.length-20,s06.length,west.station))*(1-ease(0,35,west.beyond)):0;
 return lift*across*endFade+ridge;
}
export function isS06WestForest(x,z){if(z<config.s06[0][1]||z>config.s06.at(-1)[1])return false;for(const s of s06.segments)if(z>=Math.min(s.a[1],s.b[1])&&z<=Math.max(s.a[1],s.b[1])){const t=(z-s.a[1])/s.dz;return x<s.a[0]+s.dx*t;}return false;}
export const yongjiCalibration=config;
