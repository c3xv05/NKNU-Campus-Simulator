// Shared by the tests that compare against older baselines: the 2026-11-19 Jiyuan move (orthophoto + S22) and the
// 2026-11-22 move of 歸燕食巢/飛燕 change terrain, pads and plants only inside these windows. Everything else must
// stay identical to the old data, so the windows are derived from the old/new level-area rings (+ margin).
import {yongjiLiftInfluence} from '../terrain-calibration.js';
export function relocationWindow(campus,margin=15){
 const rings=[];
 for(const a of campus.levelAreas||[])if(['foresight-forecourt','restaurant-quarter'].includes(a.id))rings.push(a.ring,a.beforeRelocationRing||[]);
 for(const p of [...campus.places,...campus.buildings])if(p.osm===381732645||p.osm===381734405)rings.push(p.ring);
 rings.push([[-272,-34],[-220,28]]);
 const pts=rings.flat(),xs=pts.map(p=>p[0]),zs=pts.map(p=>p[1]),w=[Math.min(...xs)-margin,Math.min(...zs)-margin,Math.max(...xs)+margin,Math.max(...zs)+margin];
 // 2026-11-23: S06/S07 were returned to the real terrain (added rise 14m/8m -> 0), so the whole former lift region may differ (+6m for grade smoothing).
 const lifted=(x,z)=>[[0,0],[6,0],[-6,0],[0,6],[0,-6]].some(([dx,dz])=>yongjiLiftInfluence(x+dx,z+dz)>0);
 return(x,z)=>(x>=w[0]&&x<=w[2]&&z>=w[1]&&z<=w[3])||lifted(x,z);
}
