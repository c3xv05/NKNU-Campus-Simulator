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
 const w0=windowOf(rings,margin);
 // 2026-11-23: Bio A/B redrawn from the floor plans (new pads, 1F 0.9 m lower, terraced ramps to S01): own window.
 const bio=[...campus.places].filter(p=>p.osm===444867696||p.osm===444867695).flatMap(p=>[p.ring,p.beforeDrawingFootprint?.ring||[]]);if(campus.bioConnection?.stairs?.ring)bio.push(campus.bioConnection.stairs.ring);const w1=bio.length?windowOf(bio,margin):null;
 // 2026-11-23: S06/S07 were returned to the real terrain (added rise 14m/8m -> 0), so the whole former lift region may differ (+6m for grade smoothing).
 // 2026-11-25: 圖資大樓 placed from the floor plans on the orthophoto (new shell, terrain pad and fan plaza): own window.
 const lib=[...campus.places,...campus.buildings].filter(p=>p.osm===381963953).flatMap(p=>[p.ring,p.beforeRelocationRing||[],p.terrainRing||[]]).filter(r=>r.length);const terrace=(campus.levelAreas||[]).filter(a=>a.id==='library-west-terrace').map(a=>a.ring);const w2=lib.length?windowOf([...lib,...terrace],margin+10):null;
 const lifted=(x,z)=>[[0,0],[6,0],[-6,0],[0,6],[0,-6]].some(([dx,dz])=>yongjiLiftInfluence(x+dx,z+dz)>0);
 // 2026-11-26: removed footpaths east of the S04 sidewalk (terrain grading follows paths): +30 m around their lines (shared road grading).
 const gone=(campus.removeFootpaths||[]).map(r=>r.line);const nearLine=(x,z)=>gone.some(l=>{for(let i=0;i<l.length-1;i++){const[a,b]=[l[i],l[i+1]],dx=b[0]-a[0],dz=b[1]-a[1],q=dx*dx+dz*dz,u=q?Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/q)):0;if(Math.hypot(x-a[0]-dx*u,z-a[1]-dz*u)<30)return true;}return false;});
 const inside=(w,x,z)=>w&&x>=w[0]&&x<=w[2]&&z>=w[1]&&z<=w[3];
 return(x,z)=>inside(w0,x,z)||inside(w1,x,z)||inside(w2,x,z)||nearLine(x,z)||lifted(x,z);
}
