import {parkingSupportAt} from './facilities/basketball-parking/surface.js';
import {passageSupportAt} from './building-passages.js';
import {courtyardSupportAt} from './facilities/teaching-courtyard/surface.js';
import {huanyuSupportAt} from './facilities/huanyu-platform/surface.js';
import {subtract} from './road-ground.js';
import {sidewalkSides,SIDEWALK_WIDTH} from './sidewalk-layout.js';
import {routeSections,pavementIndex} from './pavement.js';
import {ringDistance} from './terrain.js';
export function inLake(x,z,area){return ringDistance(x,z,area.ring)===0&&!(area.holes||[]).some(r=>ringDistance(x,z,r)===0);}
export function lakeAt(x,z,campus){return campus.water.find(a=>inLake(x,z,a));}
export function projectOnLine(x,z,a,b){const dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),t=((x-a[0])*dx+(z-a[1])*dz)/(length*length||1);return{t,distance:Math.abs((x-a[0])*dz-(z-a[1])*dx)/(length||1),length};}
export function bridgeHeight(x,z,currentY,link,level){if(!link)return null;const p=projectOnLine(x,z,...link.line);return p.t>=0&&p.t<=1&&p.distance<link.width/2&&Math.abs(currentY-level-.08)<.85?level+.08:null;}
export function sidewalkSections(campus,network){
 const buildings=(campus.walkObstacles||[...campus.places,...campus.buildings].filter(b=>b.height)).map(b=>({ring:b.ring,west:Math.min(...b.ring.map(p=>p[0])),east:Math.max(...b.ring.map(p=>p[0])),north:Math.min(...b.ring.map(p=>p[1])),south:Math.max(...b.ring.map(p=>p[1]))}));
 const ids=new Set(campus.sidewalkRoadIds||[]),sections=[],pavement=pavementIndex(network);
 for(const route of network.routes){if(!ids.has(route.osm))continue;const nodes=routeSections(route);
  for(let i=1;i<nodes.length;i++){const a=nodes[i-1],b=nodes[i];
   for(const side of sidewalkSides(campus,route.osm)){
    const at=(p,offset)=>[p.x+p.nx*offset,p.z+p.nz*offset],inner=side*a.width/2,outer=side*(a.width/2+SIDEWALK_WIDTH),points=[at(a,inner),at(a,outer),at(b,side*(b.width/2+SIDEWALK_WIDTH)),at(b,side*b.width/2)];
    const mid=points.reduce((s,p)=>[s[0]+p[0]/4,s[1]+p[1]/4],[0,0]);if(route.entrance&&campus.flowerbed&&ringDistance(...mid,campus.flowerbed.ring)<1)continue;
    let pieces=pavement.clip(points);const xs=points.map(p=>p[0]),zs=points.map(p=>p[1]),w=Math.min(...xs),e=Math.max(...xs),n=Math.min(...zs),s=Math.max(...zs);for(const b of buildings)if(b.west<=e&&b.east>=w&&b.north<=s&&b.south>=n)pieces=pieces.flatMap(p=>subtract(p.map(([x,z])=>[x,0,z]),b.ring).map(q=>q.map(([x,,z])=>[x,z])));for(const polygon of pieces)sections.push({road:route.osm,points:polygon,across:{x:a.x,z:a.z,nx:a.nx*side,nz:a.nz*side,inner:a.width/2}});
   }
  }
 }
 for(const f of campus.sidewalkFrontages||[]){let pieces=pavement.clip(f.ring);for(const b of buildings)pieces=pieces.flatMap(p=>subtract(p.map(([x,z])=>[x,0,z]),b.ring).map(q=>q.map(([x,,z])=>[x,z])));for(const points of pieces)sections.push({road:f.road,points,across:{x:0,z:0,nx:1,nz:0,inner:0}});}
 for(const p of campus.pedestrianPatches||[])sections.push({points:p.ring,road:p.id,across:{x:0,z:0,nx:1,nz:0,inner:0}});
 return sections;
}
export function platformHeightAt(x,z,currentY,campus,terrain,network){
 const parking=parkingSupportAt(x,z,currentY,campus,terrain);if(parking!==null)return parking;
 const passage=passageSupportAt(x,z,currentY,campus,terrain);if(passage!==null)return passage;
 const huanyu=huanyuSupportAt(x,z,currentY,campus,terrain,network);if(huanyu!==null)return huanyu;
 const bio=campus.bioConnection;if(bio?.ramp){const q=projectOnLine(x,z,...bio.ramp);if(q.t>=0&&q.t<=1&&q.distance<(bio.accessWidth||4)/2){const base=terrain.platformHeight(campus.places.find(a=>a.osm===bio.from))+3.6,start=terrain.height(...bio.ramp[0]);return start+(base-start)*q.t;}}

 const upper=terrain.platformHeight(campus.places.find(a=>a.osm===campus.levelLink.from))+3.6;if(!campus.courtyard?.floorRegions&&campus.levelLink.ring?.length&&ringDistance(x,z,campus.levelLink.ring)===0&&currentY>=upper-.8)return upper+.08;
 const p=campus.courtyard;if(!p)return null;const gauss=campus.places.find(a=>a.osm===444867692),level=terrain.platformHeight(gauss)+7.2;
 const projection=projectOnLine(x,z,...p.ramp);if(projection.t>=0&&projection.t<=1&&projection.distance<p.width/2){const start=network?network.walkHeight(...p.ramp[0],terrain.height(...p.ramp[0])):terrain.height(...p.ramp[0]),t=projection.t;const rampLevel=level-(p.rampTargetFloor===1?p.floorHeight:0),h=start+(rampLevel-start)*t;if(Math.abs(currentY-h)<.85)return h;}
 const courtyard=courtyardSupportAt(x,z,currentY,campus,terrain);if(courtyard!==null)return courtyard;
 if(p.floorRegions)return null;
 return ringDistance(x,z,p.ring)===0&&currentY>=level-.8?level+.08:null;
}
