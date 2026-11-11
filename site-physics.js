import {sidewalkSides} from './sidewalk-layout.js';
import {routeSections,pavementIndex} from './pavement.js';
import {ringDistance} from './terrain.js';
export function inLake(x,z,area){return ringDistance(x,z,area.ring)===0&&!(area.holes||[]).some(r=>ringDistance(x,z,r)===0);}
export function lakeAt(x,z,campus){return campus.water.find(a=>inLake(x,z,a));}
export function projectOnLine(x,z,a,b){const dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),t=((x-a[0])*dx+(z-a[1])*dz)/(length*length||1);return{t,distance:Math.abs((x-a[0])*dz-(z-a[1])*dx)/(length||1),length};}
export function bridgeHeight(x,z,currentY,link,level){if(!link)return null;const p=projectOnLine(x,z,...link.line);return p.t>=0&&p.t<=1&&p.distance<link.width/2&&currentY>=level-.7?level+.08:null;}
export function sidewalkSections(campus,network){
 const ids=new Set(campus.sidewalkRoadIds||[]),sections=[],pavement=pavementIndex(network);
 for(const route of network.routes){if(!ids.has(route.osm))continue;const nodes=routeSections(route);
  for(let i=1;i<nodes.length;i++){const a=nodes[i-1],b=nodes[i];
   for(const side of sidewalkSides(campus,route.osm)){
    const at=(p,offset)=>[p.x+p.nx*offset,p.z+p.nz*offset],inner=side*route.width/2,outer=side*(route.width/2+1.8),points=[at(a,inner),at(a,outer),at(b,outer),at(b,inner)];
    const mid=points.reduce((s,p)=>[s[0]+p[0]/4,s[1]+p[1]/4],[0,0]);if(route.entrance&&campus.flowerbed&&ringDistance(...mid,campus.flowerbed.ring)<1)continue;
    for(const polygon of pavement.clip(points))sections.push({road:route.osm,points:polygon});
   }
  }
 }
 return sections;
}
export function platformHeightAt(x,z,currentY,campus,terrain){
 const bio=campus.bioConnection;if(bio?.ramp){const q=projectOnLine(x,z,...bio.ramp);if(q.t>=0&&q.t<=1&&q.distance<(bio.accessWidth||4)/2){const base=terrain.platformHeight(campus.places.find(a=>a.osm===bio.from))+3.6,start=terrain.height(...bio.ramp[0]);return start+(base-start)*q.t;}}

 const upper=terrain.platformHeight(campus.places.find(a=>a.osm===campus.levelLink.from))+3.6;if(campus.levelLink.ring?.length&&ringDistance(x,z,campus.levelLink.ring)===0&&currentY>=upper-.8)return upper+.08;
 const p=campus.courtyard;if(!p)return null;const gauss=campus.places.find(a=>a.osm===444867692),level=terrain.platformHeight(gauss)+7.2;
 const projection=projectOnLine(x,z,...p.ramp);if(projection.t>=0&&projection.t<=1&&projection.distance<p.width/2){const start=terrain.height(...p.ramp[0]),t=projection.t;return start+(level-start)*t;}
 return ringDistance(x,z,p.ring)===0&&currentY>=level-.8?level+.08:null;
}
