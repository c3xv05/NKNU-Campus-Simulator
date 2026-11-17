import {campusSiteLayout} from './data/site-layout.js';
import {ringDistance} from './planar.js';
const ease=v=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t);};
const prepared=campusSiteLayout.levelAreas.map(a=>({...a,west:Math.min(...a.ring.map(p=>p[0])),east:Math.max(...a.ring.map(p=>p[0])),north:Math.min(...a.ring.map(p=>p[1])),south:Math.max(...a.ring.map(p=>p[1]))}));
const near=(a,x,z,margin=0)=>x>=a.west-margin&&x<=a.east+margin&&z>=a.north-margin&&z<=a.south+margin;
export function siteLawnAt(x,z){return prepared.some(a=>a.groundCover==='lawn'&&near(a,x,z)&&ringDistance(x,z,a.ring)===0);}
export function createSiteLevels(height){const areas=prepared.map(a=>({...a,level:height(...a.anchor)+(a.heightOffset||0)}));
 function levelAt(x,z){for(const a of areas)if(near(a,x,z)&&ringDistance(x,z,a.ring)===0)return a.level;return null;}
 function heightAt(x,z,original,ground=false){let total=0,target=0,strength=0;for(const a of areas){if(!near(a,x,z,a.blend))continue;const d=ringDistance(x,z,a.ring),level=a.level+(ground ? .185 : 0);if(d===0)return level;if(d>=a.blend)continue;const w=1-ease(d/a.blend),influence=w**4/(d*d+.0025);total+=influence;target+=level*influence;strength=Math.max(strength,w);}return total?original+(target/total-original)*strength:original;}
 // Distance from a point inside a level area to that area's ring edge (null outside every area).
 function insideDepth(x,z){for(const a of areas)if(near(a,x,z)&&ringDistance(x,z,a.ring)===0){let best=Infinity;for(let i=0;i<a.ring.length;i++){const p=a.ring[i],q=a.ring[(i+1)%a.ring.length],dx=q[0]-p[0],dz=q[1]-p[1],l=dx*dx+dz*dz,t=l?Math.max(0,Math.min(1,((x-p[0])*dx+(z-p[1])*dz)/l)):0;best=Math.min(best,Math.hypot(x-p[0]-dx*t,z-p[1]-dz*t));}return best;}return null;}
 return{areas,levelAt,heightAt,insideDepth};
}
