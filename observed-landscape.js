import {observedLandscape} from './data/observed-landscape.js';
export {observedLandscape};
import {roadRegions} from './data/road-regions.js';
import {ringDistance} from './planar.js';
const regions=roadRegions.filter(r=>['R02','R09'].includes(r.id)).map(r=>({...r,w:Math.min(...r.ring.map(p=>p[0])),e:Math.max(...r.ring.map(p=>p[0])),n:Math.min(...r.ring.map(p=>p[1])),s:Math.max(...r.ring.map(p=>p[1]))}));
export function observedRegionAt(x,z){return regions.find(r=>x>=r.w&&x<=r.e&&z>=r.n&&z<=r.s&&ringDistance(x,z,r.ring)===0&&!(r.holes||[]).some(h=>ringDistance(x,z,h)===0))?.id||null;}
export const flowerPalette=observedLandscape.r02.palette.map(hex=>parseInt(hex.slice(1),16));
