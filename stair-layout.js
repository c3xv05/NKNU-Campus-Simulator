import {projectOnLine} from './site-physics.js';
const bandCache=new Map();
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
 return [{...bio.stairs,id:'biology',top:base(bio.from)+3.6,bottom:road(bio.stairs)},...[...(link.stairs||[]),...(campus.courtyard?.stairs||[])].map(s=>({...s,top:base(link.from)+(s.topLevel==='teaching-courtyard'?3.6:0),bottom:s.bottomLevel==='road'?road(s):base(link.from)}))];
}
export function stairSurface(stairs,t){if(t>=1-1e-9)return stairs.bottom;const band=stairBands(stairs).find(b=>t>=b.start-1e-9&&t<b.end-1e-9)||stairBands(stairs).at(-1);return stairs.top+(stairs.bottom-stairs.top)*band.drop;}
export function supportOnStair(x,z,currentY,stairs){const p=projectOnLine(x,z,...stairs.line);if(p.t< -1e-7||p.t>1+1e-7||p.distance>stairWidth(stairs,p.t)/2)return null;const h=stairSurface(stairs,Math.max(0,Math.min(1,p.t)))+.08;return Math.abs(currentY-h)<.85?h:null;}
