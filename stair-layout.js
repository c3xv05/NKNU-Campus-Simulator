import {SIDEWALK_RISE,ROAD_SURFACE_LIFT} from './sidewalk-layout.js';
import {projectOnLine} from './site-physics.js';
import {createCampusCorridors} from './facilities/campus-corridors/surface.js';
const bandCache=new Map(),bottomProfileCache=new WeakMap();
function roadBottomProfile(stairs,network){
 let cached=bottomProfileCache.get(network);if(!cached){cached=new WeakMap();bottomProfileCache.set(network,cached);}if(cached.has(stairs))return cached.get(stairs);
 const [a,b]=stairs.line,dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),nx=-dz/length,nz=dx/length,half=stairs.width/2,offsets=[-half,half],step=1.25;
 // Split at the same X/Z/diagonal grade-grid edges as the adjoining white tiles.
 for(const [origin,direction]of[[b[0],nx],[b[1],nz],[b[0]+b[1],nx+nz]])if(Math.abs(direction)>1e-10){const ends=[origin-direction*half,origin+direction*half];for(let k=Math.floor(Math.min(...ends)/step);k<=Math.ceil(Math.max(...ends)/step);k++){const v=(k*step-origin)/direction;if(v> -half+1e-7&&v<half-1e-7)offsets.push(v);}}
 const bottomStations=[...new Set(offsets)].sort((a,b)=>a-b).map(across=>({across,height:network.surfaceHeight(b[0]+nx*across,b[1]+nz*across)+ROAD_SURFACE_LIFT+(stairs.bottomProfile==='sidewalk'?SIDEWALK_RISE:0)}));
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
const terraceCache=new WeakMap();
// Bio terraced ramp/stairs (drawing +0 at S01 .. +510 at the hall floor): plan as drawn, rises scaled
// linearly to the model's S01 and hall floor (user 2026-11-23, option 1).
export function biologyTerraceScale(campus,terrain,network){const bio=campus.bioConnection,s=bio.stairs;if(s?.kind!=='terraces')return null;const foot=network.surfaceHeight(...s.line[1])+ROAD_SURFACE_LIFT,top=terrain.platformHeight(campus.places.find(a=>a.osm===bio.from)),k=(top-foot)/s.drawingTop;return{foot,top,k,height:h=>foot+h*k};}
function terraceStairs(campus,terrain,network){let cached=terraceCache.get(network);if(cached?.campus===campus&&cached.terrain===terrain)return cached.defs;const scale=biologyTerraceScale(campus,terrain,network),defs=campus.bioConnection.stairs.pieces.map(p=>{const def={...p,top:scale.height(p.hTop),bottom:scale.height(p.hBottom),ramp:p.type==='ramp',flights:1,landingFraction:0,landingSidewalls:false};
  // The +0 lane landings meet the skew, sloping S01 apron: they follow the real road height at their S01 end.
  if(p.type==='landing'&&p.hTop===0)Object.assign(def,{ramp:true,flat:[p.roadSlopeFrom??0,1],bottom:network.surfaceHeight(...p.line[1])+ROAD_SURFACE_LIFT});return def;});terraceCache.set(network,{campus,terrain,defs});return defs;}
// Bio +505 side stairs under the T stem (drawing, user 2026-11-23): a 1F door landing, then one straight
// flight whose top tread meets the stem floor at the top of its stair well.
const sideCache=new WeakMap();
function biologySideStairs(campus,terrain,network){const side=campus.bioConnection.sideStairs;if(!side?.length)return[];let cached=sideCache.get(network);if(cached?.campus===campus&&cached.terrain===terrain)return cached.defs;
 const surface=createCampusCorridors(campus,terrain,network),stem=surface.approaches.find(a=>a.id==='biology-s05'),lower=surface.bioLower;
 const defs=side.flatMap(s=>s.pieces.map(p=>({...p,top:p.level==='stem'?stem.profile(...p.line[0]):lower,bottom:lower,flights:1,landingFraction:0,landingSidewalls:false})));sideCache.set(network,{campus,terrain,defs});return defs;}
export function accessStairs(campus,terrain,network){
 const base=id=>terrain.platformHeight(campus.places.find(a=>a.osm===id)),bio=campus.bioConnection,link=campus.levelLink,road=s=>network.walkHeight(...s.line[1],terrain.height(...s.line[1]));
 let biology=[];if(bio.stairs.kind==='terraces')biology=terraceStairs(campus,terrain,network);else{const def={...bio.stairs,id:'biology',top:base(bio.from)+(bio.stairs.topLevel==='biology-lower'?0:3.6),bottom:road(bio.stairs)};if(bio.stairs.bottomProfile==='road'){Object.assign(def,roadBottomProfile(bio.stairs,network));def.bottom=def.bottomAt();}biology=[def];}
 biology=[...biology,...biologySideStairs(campus,terrain,network)];
 return [...biology,...[...(link.stairs||[]),...(campus.courtyard?.stairs||[])].map(s=>{const def={...s,top:base(link.from)+(s.topLevel==='teaching-courtyard'?3.6:0),bottom:s.bottomLevel==='road'?road(s):s.bottomLevel==='gauss-ground'?base(link.to):base(link.from)};if(s.topRel!==undefined)def.top=base(link.from)+s.topRel;if(s.bottomRel!==undefined)def.bottom=base(link.from)+s.bottomRel;if(s.bottomProfile==='sidewalk'){Object.assign(def,roadBottomProfile(s,network));def.bottom=def.bottomAt();}return def;})];
}
export function stairSurface(stairs,t,x,z){if(stairs.ramp){const [f0,f1]=stairs.flat||[0,1],u=Math.max(0,Math.min(1,(t-f0)/(f1-f0)));return stairs.top+(stairs.bottom-stairs.top)*u;}const bottom=stairs.bottomAt&&x!==undefined?stairs.bottomAt(x,z):stairs.bottom;if(t>=1-1e-9)return bottom;const band=stairBands(stairs).find(b=>t>=b.start-1e-9&&t<b.end-1e-9)||stairBands(stairs).at(-1);if(stairs.levelRestLanding){const mid=(stairs.top+stairs.bottom)/2;return band.drop<=.5?stairs.top+(mid-stairs.top)*band.drop*2:mid+(bottom-mid)*(band.drop-.5)*2;}return stairs.top+(bottom-stairs.top)*band.drop;}
// 2026-11-24: the walking footprint overlaps its neighbours (plaza deck, landings) by SEAM metres so a footstep can never land in a hairline gap between two supports and drop to the ground below.
const SEAM=.12;
export function supportOnStair(x,z,currentY,stairs){const p=projectOnLine(x,z,...stairs.line),length=Math.hypot(stairs.line[1][0]-stairs.line[0][0],stairs.line[1][1]-stairs.line[0][1]),seam=SEAM/Math.max(length,1e-6);if(p.t< -seam||p.t>1+seam||p.distance>stairWidth(stairs,Math.max(0,Math.min(1,p.t)))/2+SEAM)return null;const h=stairSurface(stairs,Math.max(0,Math.min(1,p.t)),x,z)+.08;return Math.abs(currentY-h)<.85?h:null;}
