export const SIDEWALK_WIDTH=3.6;
export const SIDEWALK_RISE=.15;
export const ROAD_SURFACE_LIFT=.035;
// Sides use the route normal (-dz, dx); S06 runs north to south, so -1 is east.
export function sidewalkSides(campus,osm){return campus.sidewalkSides?.[osm]||[-1,1];}
export function mapSidewalkLines(campus){
 const ids=new Set(campus.sidewalkRoadIds||[]),out=[];
 for(const road of campus.roads){if(!ids.has(road.osm))continue;const sides=sidewalkSides(campus,road.osm);
  if(sides.length===2){out.push({line:road.line,width:road.width+2*SIDEWALK_WIDTH});continue;}
  for(const side of sides){const offset=side*(road.width/2+SIDEWALK_WIDTH/2),line=road.line.map(([x,z],i)=>{const a=road.line[Math.max(0,i-1)],b=road.line[Math.min(road.line.length-1,i+1)],dx=b[0]-a[0],dz=b[1]-a[1],l=Math.hypot(dx,dz)||1;return[x-dz/l*offset,z+dx/l*offset];});out.push({line,width:SIDEWALK_WIDTH});}
 }return out;
}
