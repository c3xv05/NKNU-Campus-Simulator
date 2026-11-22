// Pure geometry for the S06 east-side planter (no THREE): grass pieces, road-side lip edges, terrain cut and walking height.
// Pieces are the same road-edge-to-walkway strips sidewalkSections() leaves behind when the walkway is set back
// (facilities/s06-planter/layout.js), so the planter, the walkway and the terrain cut share exact boundaries.
import {s06Planter as config} from './layout.js';
import {sidewalkSections} from '../../site-physics.js';
import {ROAD_SURFACE_LIFT} from '../../sidewalk-layout.js';
export {config as s06PlanterConfig};
const cell=4;
export function createS06Planter(campus,network,source=config){
 const pieces=sidewalkSections(campus,network,'planter').map(s=>s.points).filter(p=>p.length>=3&&Math.abs(p.reduce((a,v,i)=>{const q=p[(i+1)%p.length];return a+v[0]*q[1]-q[0]*v[1];},0))/2>1e-4);
 const topAt=(x,z)=>network.surfaceHeight(x,z)+ROAD_SURFACE_LIFT+source.rise;
 const grid=new Map(),entries=pieces.map(points=>{const xs=points.map(p=>p[0]),zs=points.map(p=>p[1]),item={points};for(let z=Math.floor(Math.min(...zs)/cell);z<=Math.floor(Math.max(...zs)/cell);z++)for(let x=Math.floor(Math.min(...xs)/cell);x<=Math.floor(Math.max(...xs)/cell);x++){const k=x+','+z;if(!grid.has(k))grid.set(k,[]);grid.get(k).push(item);}return item;});
 // Points exactly on a shared piece edge (e.g. a route node) count as inside, so no hairline lets the walking height fall through.
 const onEdge=(x,z,a,b)=>{const dx=b[0]-a[0],dz=b[1]-a[1],l=dx*dx+dz*dz,t=l?Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/l)):0;return Math.hypot(x-a[0]-dx*t,z-a[1]-dz*t)<1e-7;};
 const inside=(x,z,points)=>{let hit=false;for(let i=0,j=points.length-1;i<points.length;j=i++){const a=points[i],b=points[j];if(onEdge(x,z,a,b))return true;if((a[1]>z)!==(b[1]>z)&&x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])hit=!hit;}return hit;};
 const heightAt=(x,z)=>{for(const {points} of grid.get(Math.floor(x/cell)+','+Math.floor(z/cell))||[])if(inside(x,z,points))return topAt(x,z);return null;};
 // Road-side lip: piece edges that lie on the asphalt edge (their midpoint is half a road width from the centreline).
 const lips=[];
 for(const points of pieces)for(let i=0;i<points.length;i++){const a=points[i],b=points[(i+1)%points.length],m=[(a[0]+b[0])/2,(a[1]+b[1])/2],r=network.nearest(m[0],m[1],true);if(r&&Math.abs(r.d-r.width/2)<.03)lips.push([a,b]);}
 return{config:source,pieces,footprints:pieces,heightAt,topAt,lips};
}
