import {SIDEWALK_RISE,ROAD_SURFACE_LIFT} from './sidewalk-layout.js';
import {projectOnLine} from './site-physics.js';
const bandCache=new Map(),bottomProfileCache=new WeakMap();
function sidewalkBottomProfile(stairs,network){
 let cached=bottomProfileCache.get(network);if(!cached){cached=new WeakMap();bottomProfileCache.set(network,cached);}if(cached.has(stairs))return cached.get(stairs);
 const [a,b]=stairs.line,dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),nx=-dz/length,nz=dx/length,half=stairs.width/2,offsets=[-half,half],step=1.25;
 // Split at the same X/Z/diagonal grade-grid edges as the adjoining white tiles.
 for(const [origin,direction]of[[b[0],nx],[b[1],nz],[b[0]+b[1],nx+nz]])if(Math.abs(direction)>1e-10){const ends=[origin-direction*half,origin+direction*half];for(let k=Math.floor(Math.min(...ends)/step);k<=Math.ceil(Math.max(...ends)/step);k++){const v=(k*step-origin)/direction;if(v> -half+1e-7&&v<half-1e-7)offsets.push(v);}}
 const bottomStations=[...new Set(offsets)].sort((a,b)=>a-b).map(across=>({across,height:network.surfaceHeight(b[0]+nx*across,b[1]+nz*across)+ROAD_SURFACE_LIFT+SIDEWALK_RISE}));
 const bottomAt=(x=b[0],z=b[1])=>{const v=Math.max(-half,Math.min(half,(x-b[0])*nx+(z-b[1])*nz));let i=1;while(i<bottomStations.length-1&&v>bottomStations[i].across)i++;const p=bottomStations[i-1],q=bottomStations[i];return p.height+(q.height-p.height)*(v-p.across)/(q.across-p.across);};
 const result={bottomAt,bottomStations};cached.set(stairs,result);return result;
}
// Every rendered tread and walk-height query uses these same flight/landing bands.
export function stairBands(stairs){
 const key=[stairs.steps,stairs.flights||1,stairs.landingFraction||0].join(':');if(bandCache.has(key))return bandCache.get(key);
 const flights=stairs.flights||1,landing=stairs.landingFraction||0,run=(1-landing*(flights-1))/flights,bands=[];let index=0;
 for(let f=0;f<flights;f++){const count=Math.floor(stairs.steps/flights)+(f<stairs.steps%flights?1:0),start=f*(run+landing);for(let i=0;i<count;i++){bands.push({start:start+run*i/count,end:start+run*(i+1)/count,drop:index/stairs.steps,landing:false});index++;}if(f<flights-1)bands.push({start:start+run,end:start+run+landing,drop:index/stairs.steps,landing:true});}
 bandCache.set(key,bands);return bands;
}
export function stairWidth(stairs,t){return (stairs.topWidth||stairs.width)+(stairs.width-(stairs.topWidth||stairs.width))*t;}
export function stairRing(stairs,start=0,end=1){const [a,b]=stairs.line,dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),at=(t,side)=>[a[0]+dx*t-dz/length*stairWidth(stairs,t)/2*side,a[1]+dz*t+dx/length*stairWidth(stairs,t)/2*side];return[at(start,1),at(end,1),at(end,-1),at(start,-1)];}
export function accessStairs(campus,terrain,network){
 const base=id=>terrain.platformHeight(campus.places.find(a=>a.osm===id)),bio=campus.bioConnection,link=campus.levelLink,road=s=>network.walkHeight(...s.line[1],terrain.height(...s.line[1]));
 return [{...bio.stairs,id:'biology',top:base(bio.from)+3.6,bottom:road(bio.stairs)},...[...(link.stairs||[]),...(campus.courtyard?.stairs||[])].map(s=>{const def={...s,top:base(link.from)+(s.topLevel==='teaching-courtyard'?3.6:0),bottom:s.bottomLevel==='road'?road(s):base(link.from)};if(s.bottomProfile==='sidewalk'){Object.assign(def,sidewalkBottomProfile(s,network));def.bottom=def.bottomAt();}return def;})];
}
export function stairSurface(stairs,t,x,z){const bottom=stairs.bottomAt&&x!==undefined?stairs.bottomAt(x,z):stairs.bottom;if(t>=1-1e-9)return bottom;const band=stairBands(stairs).find(b=>t>=b.start-1e-9&&t<b.end-1e-9)||stairBands(stairs).at(-1);return stairs.top+(bottom-stairs.top)*band.drop;}
export function supportOnStair(x,z,currentY,stairs){const p=projectOnLine(x,z,...stairs.line);if(p.t< -1e-7||p.t>1+1e-7||p.distance>stairWidth(stairs,p.t)/2)return null;const h=stairSurface(stairs,Math.max(0,Math.min(1,p.t)),x,z)+.08;return Math.abs(currentY-h)<.85?h:null;}
