import {r04Vegetation} from './data/r04-vegetation.js';
import {ringDistance} from './planar.js';
export {r04Vegetation};
const regions=r04Vegetation.regions.map(r=>({...r,prepared:r.regions.map(([ring,...holes])=>({ring,holes,w:Math.min(...ring.map(p=>p[0])),e:Math.max(...ring.map(p=>p[0])),n:Math.min(...ring.map(p=>p[1])),s:Math.max(...ring.map(p=>p[1]))}))}));
export function r04RegionAt(x,z){return regions.find(r=>r.prepared.some(p=>x>=p.w&&x<=p.e&&z>=p.n&&z<=p.s&&ringDistance(x,z,p.ring)===0&&!p.holes.some(h=>ringDistance(x,z,h)===0)))||null;}
