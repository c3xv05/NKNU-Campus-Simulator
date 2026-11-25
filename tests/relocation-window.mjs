// Shared by the tests that compare against older baselines: the 2026-11-19 Jiyuan move (orthophoto + S22) and the
// 2026-11-22 move of 歸燕食巢/飛燕 change terrain, pads and plants only inside these windows. Everything else must
// stay identical to the old data, so the windows are derived from the old/new level-area rings (+ margin).
import {yongjiLiftInfluence} from '../terrain-calibration.js';
function windowOf(rings,margin){const pts=rings.flat(),xs=pts.map(p=>p[0]),zs=pts.map(p=>p[1]);return[Math.min(...xs)-margin,Math.min(...zs)-margin,Math.max(...xs)+margin,Math.max(...zs)+margin];}
export function relocationWindow(campus,margin=15){
 const rings=[];
 for(const a of campus.levelAreas||[])if(['foresight-forecourt','restaurant-quarter'].includes(a.id))rings.push(a.ring,a.beforeRelocationRing||[]);
 for(const p of [...campus.places,...campus.buildings])if(p.osm===381732645||p.osm===381734405)rings.push(p.ring);
 rings.push([[-272,-34],[-220,28]]);
 // 2026-11-25: S26/S27(top)/S28/S32 moved north onto the orthophoto (scripts/shift-gauss-south-roads.py); old and new lines.
 for(const r of campus.roads||[])if(r.beforeGaussSouthShift)rings.push(r.beforeGaussSouthShift,r.line);
 const w0=windowOf(rings,margin);
 // 2026-11-23: Bio A/B redrawn from the floor plans (new pads, 1F 0.9 m lower, terraced ramps to S01): own window.
 const bio=[...campus.places].filter(p=>p.osm===444867696||p.osm===444867695).flatMap(p=>[p.ring,p.beforeDrawingFootprint?.ring||[]]);if(campus.bioConnection?.stairs?.ring)bio.push(campus.bioConnection.stairs.ring);const w1=bio.length?windowOf(bio,margin):null;
 // 2026-11-23: S06/S07 were returned to the real terrain (added rise 14m/8m -> 0), so the whole former lift region may differ (+6m for grade smoothing).
 const lifted=(x,z)=>[[0,0],[6,0],[-6,0],[0,6],[0,-6]].some(([dx,dz])=>yongjiLiftInfluence(x+dx,z+dz)>0);
 const inside=(w,x,z)=>w&&x>=w[0]&&x<=w[2]&&z>=w[1]&&z<=w[3];
 return(x,z)=>inside(w0,x,z)||inside(w1,x,z)||lifted(x,z);
}
